"""出力フォーマッターモジュール"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from .report_generator import GeneratedReport


class OutputFormat(Enum):
    """出力形式"""

    TEXT = "text"
    MARKDOWN = "markdown"


@dataclass
class FormattedOutput:
    """フォーマット済み出力"""

    executive_summary: str
    details: str
    next_actions: str
    full_report: str
    format_type: OutputFormat


class OutputFormatter:
    """報告書の出力をフォーマットするクラス"""

    def __init__(self, max_summary_chars: int = 300):
        """
        Args:
            max_summary_chars: エグゼクティブサマリの最大文字数
        """
        self._max_summary_chars = max_summary_chars

    def format(
        self,
        report: GeneratedReport,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        report_type: str = "weekly",
        target_name: str = "",
    ) -> FormattedOutput:
        """
        報告書をフォーマットする

        Args:
            report: 生成された報告書
            output_format: 出力形式
            report_type: 報告タイプ（"weekly" or "monthly"）
            target_name: 報告対象者名

        Returns:
            フォーマット済み出力
        """
        if output_format == OutputFormat.MARKDOWN:
            return self._format_markdown(report, report_type, target_name)
        else:
            return self._format_text(report, report_type, target_name)

    def _format_markdown(
        self, report: GeneratedReport, report_type: str, target_name: str
    ) -> FormattedOutput:
        """Markdown形式でフォーマット"""
        report_type_text = "週報" if report_type == "weekly" else "月報"
        date_str = datetime.now().strftime("%Y年%m月%d日")

        # エグゼクティブサマリ（文字数制御）
        summary = self._truncate_text(
            report.executive_summary, self._max_summary_chars
        )
        summary_section = f"## エグゼクティブサマリ\n\n{summary}"

        # 詳細内容
        details_section = f"## 詳細内容\n\n{report.details}"

        # ネクストアクション
        next_actions_list = "\n".join(
            f"- {action}" for action in report.next_actions
        )
        next_actions_section = f"## ネクストアクション\n\n{next_actions_list}"

        # フルレポート
        header = f"# {report_type_text}"
        if target_name:
            header += f"（{target_name}向け）"
        header += f"\n\n**作成日**: {date_str}\n"

        full_report = "\n\n".join(
            [header, summary_section, details_section, next_actions_section]
        )

        return FormattedOutput(
            executive_summary=summary_section,
            details=details_section,
            next_actions=next_actions_section,
            full_report=full_report,
            format_type=OutputFormat.MARKDOWN,
        )

    def _format_text(
        self, report: GeneratedReport, report_type: str, target_name: str
    ) -> FormattedOutput:
        """テキスト形式でフォーマット"""
        report_type_text = "週報" if report_type == "weekly" else "月報"
        date_str = datetime.now().strftime("%Y年%m月%d日")

        # エグゼクティブサマリ（文字数制御）
        summary = self._truncate_text(
            report.executive_summary, self._max_summary_chars
        )
        summary_section = f"【エグゼクティブサマリ】\n{summary}"

        # 詳細内容
        details_section = f"【詳細内容】\n{report.details}"

        # ネクストアクション
        next_actions_list = "\n".join(
            f"  {i}. {action}" for i, action in enumerate(report.next_actions, 1)
        )
        next_actions_section = f"【ネクストアクション】\n{next_actions_list}"

        # フルレポート
        header_parts = [f"{'=' * 50}", f"{report_type_text}"]
        if target_name:
            header_parts.append(f"報告対象: {target_name}")
        header_parts.extend([f"作成日: {date_str}", f"{'=' * 50}"])
        header = "\n".join(header_parts)

        full_report = "\n\n".join(
            [header, summary_section, details_section, next_actions_section]
        )

        return FormattedOutput(
            executive_summary=summary_section,
            details=details_section,
            next_actions=next_actions_section,
            full_report=full_report,
            format_type=OutputFormat.TEXT,
        )

    def _truncate_text(self, text: str, max_chars: int) -> str:
        """テキストを指定文字数で切り詰める"""
        if len(text) <= max_chars:
            return text

        # 文末で切る（句読点を探す）
        truncated = text[:max_chars]
        last_period = max(
            truncated.rfind("。"),
            truncated.rfind("．"),
            truncated.rfind("."),
        )

        if last_period > max_chars * 0.7:  # 70%以上の位置に句点があれば
            return truncated[: last_period + 1]

        return truncated.rstrip() + "..."

    def format_summary_only(
        self, report: GeneratedReport, max_chars: Optional[int] = None
    ) -> str:
        """エグゼクティブサマリのみを取得"""
        chars = max_chars or self._max_summary_chars
        return self._truncate_text(report.executive_summary, chars)

    def format_next_actions_only(
        self,
        report: GeneratedReport,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
    ) -> str:
        """ネクストアクションのみを取得"""
        if output_format == OutputFormat.MARKDOWN:
            return "\n".join(f"- {action}" for action in report.next_actions)
        else:
            return "\n".join(
                f"{i}. {action}" for i, action in enumerate(report.next_actions, 1)
            )


class ReportExporter:
    """報告書をファイルにエクスポートするクラス"""

    def __init__(self, formatter: Optional[OutputFormatter] = None):
        self._formatter = formatter or OutputFormatter()

    def export_to_file(
        self,
        report: GeneratedReport,
        file_path: str,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        report_type: str = "weekly",
        target_name: str = "",
    ) -> str:
        """
        報告書をファイルにエクスポートする

        Args:
            report: 生成された報告書
            file_path: 出力ファイルパス
            output_format: 出力形式
            report_type: 報告タイプ
            target_name: 報告対象者名

        Returns:
            出力したファイルパス
        """
        formatted = self._formatter.format(
            report, output_format, report_type, target_name
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(formatted.full_report)

        return file_path

    def export_to_clipboard(
        self,
        report: GeneratedReport,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        report_type: str = "weekly",
        target_name: str = "",
    ) -> str:
        """
        報告書をクリップボードにコピーする

        Args:
            report: 生成された報告書
            output_format: 出力形式
            report_type: 報告タイプ
            target_name: 報告対象者名

        Returns:
            コピーしたテキスト
        """
        formatted = self._formatter.format(
            report, output_format, report_type, target_name
        )

        try:
            import pyperclip

            pyperclip.copy(formatted.full_report)
        except ImportError:
            pass  # pyperclipがない場合は何もしない

        return formatted.full_report
