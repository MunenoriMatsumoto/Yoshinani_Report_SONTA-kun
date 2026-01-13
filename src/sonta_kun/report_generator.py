"""報告書生成モジュール"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .bedrock_client import BedrockClient, BedrockError
from .config import BedrockConfig
from .diff_analyzer import DiffAnalyzer, DiffResult
from .excel_reader import TodoList
from .profile_manager import ProfileManager, TargetProfile
from .prompt_builder import PromptBuilder, ReportContext
from .report_storage import ReportData, ReportStorage


@dataclass
class GeneratedReport:
    """生成された報告書"""

    executive_summary: str
    details: str
    next_actions: list[str]
    raw_response: str  # AIの生のレスポンス
    diff_result: Optional[DiffResult] = None


class ReportGenerator:
    """報告書を生成するクラス"""

    def __init__(
        self,
        bedrock_config: Optional[BedrockConfig] = None,
        profile_manager: Optional[ProfileManager] = None,
        report_storage: Optional[ReportStorage] = None,
    ):
        """
        Args:
            bedrock_config: Bedrock設定
            profile_manager: プロファイルマネージャー
            report_storage: 報告ストレージ
        """
        self._bedrock = BedrockClient(bedrock_config)
        self._profile_manager = profile_manager or ProfileManager()
        self._storage = report_storage or ReportStorage()
        self._prompt_builder = PromptBuilder()
        self._diff_analyzer = DiffAnalyzer()

    def generate(
        self,
        todo_list: TodoList,
        target_profile: TargetProfile,
        report_type: str = "weekly",
        previous_report: Optional[str] = None,
        previous_todos: Optional[TodoList] = None,
        additional_notes: Optional[str] = None,
        save_report: bool = True,
    ) -> GeneratedReport:
        """
        報告書を生成する

        Args:
            todo_list: ToDoリスト
            target_profile: 報告対象者プロファイル
            report_type: 報告タイプ（"weekly" or "monthly"）
            previous_report: 前回の報告内容（テキスト）
            previous_todos: 前回のToDoリスト
            additional_notes: 追加メモ
            save_report: 生成した報告を保存するかどうか

        Returns:
            生成された報告書

        Raises:
            ReportGenerationError: 生成に失敗した場合
        """
        # 差分分析
        diff_result = None
        diff_context = ""

        if previous_todos:
            diff_result = self._diff_analyzer.analyze(todo_list, previous_todos)
            diff_context = f"\n\n### 前回からの差分\n{diff_result.to_text()}"

        # ToDoリストをテキスト化
        todo_text = todo_list.to_text()
        if diff_context:
            todo_text += diff_context

        # プロンプト生成コンテキスト
        context = ReportContext(
            report_type=report_type,
            todo_text=todo_text,
            target_profile=target_profile,
            previous_report=previous_report,
            additional_notes=additional_notes,
        )

        # プロンプト生成
        system_prompt = self._prompt_builder.build_system_prompt()
        user_prompt = self._prompt_builder.build_user_prompt(context)

        # AI呼び出し
        try:
            response = self._bedrock.generate(user_prompt, system_prompt)
        except BedrockError as e:
            raise ReportGenerationError(f"AI呼び出しに失敗しました: {e}") from e

        # レスポンス解析
        generated = self._parse_response(response, diff_result)

        # 保存
        if save_report:
            report_data = ReportData(
                report_type=report_type,
                target_person=target_profile.name,
                created_at=datetime.now().isoformat(),
                todo_summary=todo_list.to_text()[:500],
                executive_summary=generated.executive_summary,
                details=generated.details,
                next_actions=generated.next_actions,
                source_file=todo_list.source_file,
            )
            self._storage.save_report(report_data)

        return generated

    def generate_with_profile_name(
        self,
        todo_list: TodoList,
        profile_name: str,
        report_type: str = "weekly",
        **kwargs,
    ) -> GeneratedReport:
        """
        プロファイル名を指定して報告書を生成する

        Args:
            todo_list: ToDoリスト
            profile_name: プロファイル名
            report_type: 報告タイプ
            **kwargs: その他の引数（generateに渡される）

        Returns:
            生成された報告書

        Raises:
            ReportGenerationError: プロファイルが見つからない場合
        """
        profile = self._profile_manager.get_profile(profile_name)
        if not profile:
            available = ", ".join(self._profile_manager.get_profile_names())
            raise ReportGenerationError(
                f"プロファイル '{profile_name}' が見つかりません。"
                f"利用可能: {available}"
            )

        return self.generate(
            todo_list=todo_list,
            target_profile=profile,
            report_type=report_type,
            **kwargs,
        )

    def _parse_response(
        self, response: str, diff_result: Optional[DiffResult]
    ) -> GeneratedReport:
        """AIレスポンスを解析"""
        # セクションを抽出
        executive_summary = self._extract_section(
            response, ["エグゼクティブサマリ", "Executive Summary", "サマリ"]
        )
        details = self._extract_section(
            response, ["詳細内容", "詳細", "Details", "Detail"]
        )
        next_actions_text = self._extract_section(
            response, ["ネクストアクション", "Next Action", "次のアクション"]
        )

        # ネクストアクションをリスト化
        next_actions = self._parse_bullet_list(next_actions_text)

        return GeneratedReport(
            executive_summary=executive_summary,
            details=details,
            next_actions=next_actions,
            raw_response=response,
            diff_result=diff_result,
        )

    def _extract_section(self, text: str, headers: list[str]) -> str:
        """セクションを抽出"""
        for header in headers:
            # マークダウンヘッダーパターン
            pattern = rf"#{{1,3}}\s*{re.escape(header)}[^\n]*\n(.*?)(?=\n#|\Z)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def _parse_bullet_list(self, text: str) -> list[str]:
        """箇条書きをリストに変換"""
        if not text:
            return []

        items = []
        # 数字付きリスト: 1. xxx or 1) xxx
        # 箇条書き: - xxx or * xxx or • xxx
        pattern = r"(?:^|\n)\s*(?:[\d]+[.)]\s*|[-*•]\s*)(.+?)(?=\n\s*(?:[\d]+[.)]\s*|[-*•]\s*)|\Z)"
        matches = re.findall(pattern, text, re.DOTALL)

        for match in matches:
            item = match.strip()
            if item:
                items.append(item)

        return items

    def get_available_profiles(self) -> list[str]:
        """利用可能なプロファイル名を取得"""
        return self._profile_manager.get_profile_names()


class ReportGenerationError(Exception):
    """報告書生成エラー"""

    pass
