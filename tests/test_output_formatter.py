"""出力フォーマッターのテスト"""

import tempfile
from pathlib import Path

import pytest

from sonta_kun.output_formatter import (
    FormattedOutput,
    OutputFormat,
    OutputFormatter,
    ReportExporter,
)
from sonta_kun.report_generator import GeneratedReport


@pytest.fixture
def sample_report():
    """サンプル報告書"""
    return GeneratedReport(
        executive_summary="今週はプロジェクトAの主要機能を完成させました。スケジュール通りに進捗しています。",
        details="プロジェクトAについて、認証機能とデータベース連携を実装しました。テストも完了しています。",
        next_actions=["プロジェクトBの要件定義を開始", "コードレビューの実施", "ドキュメント更新"],
        raw_response="",
    )


def test_output_format_enum():
    """OutputFormat列挙型のテスト"""
    assert OutputFormat.TEXT.value == "text"
    assert OutputFormat.MARKDOWN.value == "markdown"


def test_output_formatter_markdown(sample_report):
    """Markdownフォーマットのテスト"""
    formatter = OutputFormatter(max_summary_chars=300)
    result = formatter.format(
        sample_report,
        output_format=OutputFormat.MARKDOWN,
        report_type="weekly",
        target_name="山田課長",
    )

    assert result.format_type == OutputFormat.MARKDOWN
    assert "## エグゼクティブサマリ" in result.executive_summary
    assert "## 詳細内容" in result.details
    assert "## ネクストアクション" in result.next_actions
    assert "# 週報" in result.full_report
    assert "山田課長向け" in result.full_report
    assert "- プロジェクトBの要件定義を開始" in result.next_actions


def test_output_formatter_text(sample_report):
    """テキストフォーマットのテスト"""
    formatter = OutputFormatter(max_summary_chars=300)
    result = formatter.format(
        sample_report,
        output_format=OutputFormat.TEXT,
        report_type="monthly",
        target_name="佐藤室長",
    )

    assert result.format_type == OutputFormat.TEXT
    assert "【エグゼクティブサマリ】" in result.executive_summary
    assert "【詳細内容】" in result.details
    assert "【ネクストアクション】" in result.next_actions
    assert "月報" in result.full_report
    assert "佐藤室長" in result.full_report
    assert "1. プロジェクトBの要件定義を開始" in result.next_actions


def test_output_formatter_truncate():
    """文字数制限のテスト"""
    formatter = OutputFormatter(max_summary_chars=50)

    long_text = "あ" * 100
    truncated = formatter._truncate_text(long_text, 50)

    assert len(truncated) <= 53  # 50 + "..."


def test_output_formatter_truncate_at_period():
    """句点での切り詰めテスト"""
    formatter = OutputFormatter(max_summary_chars=50)

    text = "これは最初の文です。これは2番目の文です。これは3番目の文です。"
    truncated = formatter._truncate_text(text, 30)

    # 句点で終わることを確認
    assert truncated.endswith("。") or truncated.endswith("...")


def test_output_formatter_summary_only(sample_report):
    """サマリのみ取得テスト"""
    formatter = OutputFormatter(max_summary_chars=100)
    summary = formatter.format_summary_only(sample_report, max_chars=50)

    assert len(summary) <= 53


def test_output_formatter_next_actions_only_markdown(sample_report):
    """ネクストアクションのみ取得テスト（Markdown）"""
    formatter = OutputFormatter()
    actions = formatter.format_next_actions_only(sample_report, OutputFormat.MARKDOWN)

    assert actions.startswith("- ")
    assert "プロジェクトBの要件定義を開始" in actions


def test_output_formatter_next_actions_only_text(sample_report):
    """ネクストアクションのみ取得テスト（テキスト）"""
    formatter = OutputFormatter()
    actions = formatter.format_next_actions_only(sample_report, OutputFormat.TEXT)

    assert actions.startswith("1.")
    assert "プロジェクトBの要件定義を開始" in actions


def test_report_exporter_to_file(sample_report):
    """ファイルエクスポートテスト"""
    exporter = ReportExporter()

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        temp_path = f.name

    try:
        result_path = exporter.export_to_file(
            sample_report,
            temp_path,
            output_format=OutputFormat.MARKDOWN,
            report_type="weekly",
            target_name="テスト",
        )

        with open(result_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "# 週報" in content
        assert "エグゼクティブサマリ" in content
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_formatted_output_dataclass():
    """FormattedOutputデータクラスのテスト"""
    output = FormattedOutput(
        executive_summary="サマリ",
        details="詳細",
        next_actions="アクション",
        full_report="フルレポート",
        format_type=OutputFormat.MARKDOWN,
    )

    assert output.executive_summary == "サマリ"
    assert output.format_type == OutputFormat.MARKDOWN
