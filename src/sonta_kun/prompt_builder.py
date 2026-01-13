"""プロンプト設計・生成モジュール"""

from dataclasses import dataclass
from typing import Optional

from .profile_manager import TargetProfile


@dataclass
class ReportContext:
    """報告書生成のコンテキスト"""

    report_type: str  # "weekly" or "monthly"
    todo_text: str  # ToDoリストのテキスト
    target_profile: TargetProfile  # 報告対象者
    previous_report: Optional[str] = None  # 前回の報告内容
    additional_notes: Optional[str] = None  # 追加のメモ


class PromptBuilder:
    """報告書生成用プロンプトを構築するクラス"""

    # システムプロンプトのテンプレート
    SYSTEM_PROMPT = """あなたは週報・月報作成を支援するアシスタントです。
与えられたToDoリストと報告対象者の特性に基づいて、最適な報告書を作成してください。

## 報告書作成のガイドライン

1. **エグゼクティブサマリ**:
   - 報告対象者の関心事に焦点を当てる
   - 指定された文字数以内で簡潔にまとめる
   - 重要なポイントを優先的に記載

2. **詳細内容**:
   - 報告対象者の詳細度レベルに応じて情報量を調整
   - 具体的な成果と進捗を明確に記載
   - 課題やリスクがあれば明記

3. **ネクストアクション**:
   - 報告対象者の関心事を反映した提案
   - 具体的で実行可能なアクション
   - 優先度を考慮した順序

## 報告対象者の特性に応じた調整

- **納期重視**: スケジュール、マイルストーン、遅延リスクを強調
- **方針重視**: 全体戦略との整合性、方向性を強調
- **コスト重視**: リソース効率、ROI、予算影響を強調
- **詳細重視**: 技術的詳細、具体的な実装内容を詳しく記載"""

    # ユーザープロンプトのテンプレート
    USER_PROMPT_TEMPLATE = """## 報告書作成依頼

### 報告タイプ
{report_type}

### 報告対象者情報
{target_info}

### 出力設定
- エグゼクティブサマリ: {summary_max_chars}文字以内
- 詳細度レベル: {detail_level}
- 出力形式: {output_format}

### ToDoリスト（今回の作業内容）
{todo_text}

{previous_section}
{additional_section}

## 出力形式

以下の形式で報告書を作成してください：

### エグゼクティブサマリ
（{summary_max_chars}文字以内で、報告対象者の関心事に焦点を当てて記載）

### 詳細内容
（進捗状況、成果、課題などを{detail_level_desc}）

### ネクストアクション
（報告対象者の関心事を反映した、具体的なアクションを箇条書きで記載）"""

    DETAIL_LEVEL_DESC = {
        "low": "簡潔に記載",
        "medium": "適度な詳細度で記載",
        "high": "詳細に記載",
    }

    def build_system_prompt(self) -> str:
        """システムプロンプトを生成"""
        return self.SYSTEM_PROMPT

    def build_user_prompt(self, context: ReportContext) -> str:
        """
        ユーザープロンプトを生成

        Args:
            context: 報告書生成のコンテキスト

        Returns:
            生成されたユーザープロンプト
        """
        report_type_text = "週報" if context.report_type == "weekly" else "月報"

        # 前回報告セクション
        previous_section = ""
        if context.previous_report:
            previous_section = f"""### 前回の報告内容（差分比較用）
{context.previous_report}

※前回からの進捗差分を考慮して報告書を作成してください。"""

        # 追加メモセクション
        additional_section = ""
        if context.additional_notes:
            additional_section = f"""### 追加メモ
{context.additional_notes}"""

        # 詳細度の説明
        detail_level_desc = self.DETAIL_LEVEL_DESC.get(
            context.target_profile.detail_level, "適度な詳細度で記載"
        )

        # 出力形式
        output_format = (
            "Markdown形式"
            if context.target_profile.preferred_format == "markdown"
            else "テキスト形式"
        )

        return self.USER_PROMPT_TEMPLATE.format(
            report_type=report_type_text,
            target_info=context.target_profile.get_prompt_context(),
            summary_max_chars=context.target_profile.summary_max_chars,
            detail_level=context.target_profile.detail_level,
            detail_level_desc=detail_level_desc,
            output_format=output_format,
            todo_text=context.todo_text,
            previous_section=previous_section,
            additional_section=additional_section,
        )

    def build_diff_analysis_prompt(
        self, current_todos: str, previous_report: str
    ) -> str:
        """
        差分分析用のプロンプトを生成

        Args:
            current_todos: 現在のToDoリスト
            previous_report: 前回の報告内容

        Returns:
            差分分析用プロンプト
        """
        return f"""## 進捗差分分析依頼

以下の情報を比較して、前回からの進捗差分を分析してください。

### 前回の報告内容
{previous_report}

### 現在のToDoリスト
{current_todos}

## 分析観点
1. 完了したタスク
2. 新規追加されたタスク
3. 進行中のタスク（進捗度合い）
4. 遅延または停滞しているタスク
5. 変更されたタスク（優先度変更など）

## 出力形式
上記の観点ごとに箇条書きで分析結果を記載してください。"""
