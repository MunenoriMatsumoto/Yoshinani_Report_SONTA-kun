"""報告データストレージのテスト"""

import json
import tempfile
from pathlib import Path

import pytest

from sonta_kun.report_storage import ReportData, ReportStorage, StorageError


@pytest.fixture
def temp_storage_dir():
    """一時ストレージディレクトリ"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_report():
    """サンプル報告データ"""
    return ReportData(
        report_type="weekly",
        target_person="山田課長",
        created_at="2024-12-01T10:00:00",
        todo_summary="タスクA、タスクBを実施",
        executive_summary="今週は計画通り進捗しました",
        details="詳細な報告内容...",
        next_actions=["次のタスクA", "次のタスクB"],
        source_file="/path/to/todo.xlsx",
    )


def test_report_data_to_dict(sample_report):
    """ReportDataの辞書変換テスト"""
    result = sample_report.to_dict()

    assert result["report_type"] == "weekly"
    assert result["target_person"] == "山田課長"
    assert result["executive_summary"] == "今週は計画通り進捗しました"
    assert len(result["next_actions"]) == 2


def test_report_data_from_dict():
    """辞書からReportDataへの変換テスト"""
    data = {
        "report_type": "monthly",
        "target_person": "佐藤室長",
        "created_at": "2024-12-01T10:00:00",
        "todo_summary": "サマリ",
        "executive_summary": "サマリ内容",
        "details": "詳細",
        "next_actions": ["アクション1"],
    }
    report = ReportData.from_dict(data)

    assert report.report_type == "monthly"
    assert report.target_person == "佐藤室長"


def test_report_data_to_text(sample_report):
    """ReportDataのテキスト変換テスト"""
    text = sample_report.to_text()

    assert "週報" in text
    assert "山田課長" in text
    assert "今週は計画通り進捗しました" in text
    assert "次のタスクA" in text


def test_report_storage_save_and_get(temp_storage_dir, sample_report):
    """報告データの保存と取得テスト"""
    storage = ReportStorage(storage_dir=temp_storage_dir)

    storage.save_report(sample_report)
    latest = storage.get_latest_report()

    assert latest is not None
    assert latest.target_person == "山田課長"


def test_report_storage_filter_by_type(temp_storage_dir):
    """報告タイプでのフィルタリングテスト"""
    storage = ReportStorage(storage_dir=temp_storage_dir)

    weekly_report = ReportData(
        report_type="weekly",
        target_person="山田課長",
        created_at="2024-12-01T10:00:00",
        todo_summary="",
        executive_summary="週報",
        details="",
    )
    monthly_report = ReportData(
        report_type="monthly",
        target_person="佐藤室長",
        created_at="2024-12-02T10:00:00",
        todo_summary="",
        executive_summary="月報",
        details="",
    )

    storage.save_report(weekly_report)
    storage.save_report(monthly_report)

    weekly_latest = storage.get_latest_report(report_type="weekly")
    assert weekly_latest.executive_summary == "週報"

    monthly_latest = storage.get_latest_report(report_type="monthly")
    assert monthly_latest.executive_summary == "月報"


def test_report_storage_load_from_file(temp_storage_dir, sample_report):
    """ファイルからの読み込みテスト"""
    storage = ReportStorage(storage_dir=temp_storage_dir)
    file_path = temp_storage_dir / "report.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_report.to_dict(), f, ensure_ascii=False)

    loaded = storage.load_from_file(file_path)
    assert loaded.target_person == "山田課長"


def test_report_storage_export_json(temp_storage_dir, sample_report):
    """JSONエクスポートテスト"""
    storage = ReportStorage(storage_dir=temp_storage_dir)
    export_path = temp_storage_dir / "export.json"

    storage.export_report(sample_report, export_path)

    with open(export_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["target_person"] == "山田課長"


def test_report_storage_export_text(temp_storage_dir, sample_report):
    """テキストエクスポートテスト"""
    storage = ReportStorage(storage_dir=temp_storage_dir)
    export_path = temp_storage_dir / "export.txt"

    storage.export_report(sample_report, export_path)

    with open(export_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "山田課長" in content
    assert "週報" in content
