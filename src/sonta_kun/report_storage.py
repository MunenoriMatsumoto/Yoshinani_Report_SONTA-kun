"""報告データの保存・読み込みモジュール"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ReportData:
    """報告データ"""

    report_type: str  # "weekly" or "monthly"
    target_person: str  # 報告対象者
    created_at: str  # ISO形式の日時
    todo_summary: str  # ToDoリストの要約
    executive_summary: str  # エグゼクティブサマリ
    details: str  # 詳細内容
    next_actions: list[str] = field(default_factory=list)  # ネクストアクション
    source_file: Optional[str] = None  # 元のExcelファイル

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "report_type": self.report_type,
            "target_person": self.target_person,
            "created_at": self.created_at,
            "todo_summary": self.todo_summary,
            "executive_summary": self.executive_summary,
            "details": self.details,
            "next_actions": self.next_actions,
            "source_file": self.source_file,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReportData":
        """辞書から作成"""
        return cls(
            report_type=data.get("report_type", "weekly"),
            target_person=data.get("target_person", ""),
            created_at=data.get("created_at", ""),
            todo_summary=data.get("todo_summary", ""),
            executive_summary=data.get("executive_summary", ""),
            details=data.get("details", ""),
            next_actions=data.get("next_actions", []),
            source_file=data.get("source_file"),
        )

    def to_text(self) -> str:
        """テキスト形式に変換"""
        lines = [
            f"報告タイプ: {'週報' if self.report_type == 'weekly' else '月報'}",
            f"報告対象: {self.target_person}",
            f"作成日時: {self.created_at}",
            "",
            "【エグゼクティブサマリ】",
            self.executive_summary,
            "",
            "【詳細】",
            self.details,
            "",
            "【ネクストアクション】",
        ]
        for i, action in enumerate(self.next_actions, 1):
            lines.append(f"{i}. {action}")

        return "\n".join(lines)


class ReportStorage:
    """報告データの保存・読み込みを管理するクラス"""

    DEFAULT_STORAGE_DIR = ".sonta_kun"
    REPORTS_FILE = "reports.json"

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Args:
            storage_dir: 保存先ディレクトリ。Noneの場合はユーザーホームに作成
        """
        if storage_dir:
            self._storage_dir = Path(storage_dir)
        else:
            self._storage_dir = Path.home() / self.DEFAULT_STORAGE_DIR

        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._reports_file = self._storage_dir / self.REPORTS_FILE

    def save_report(self, report: ReportData) -> None:
        """
        報告データを保存する

        Args:
            report: 保存する報告データ
        """
        reports = self._load_all_reports()
        reports.append(report.to_dict())
        self._save_all_reports(reports)

    def get_latest_report(
        self,
        report_type: Optional[str] = None,
        target_person: Optional[str] = None,
    ) -> Optional[ReportData]:
        """
        最新の報告データを取得する

        Args:
            report_type: フィルタする報告タイプ（"weekly" or "monthly"）
            target_person: フィルタする報告対象者

        Returns:
            最新の報告データ、見つからない場合はNone
        """
        reports = self._load_all_reports()

        # フィルタリング
        filtered = reports
        if report_type:
            filtered = [r for r in filtered if r.get("report_type") == report_type]
        if target_person:
            filtered = [r for r in filtered if r.get("target_person") == target_person]

        if not filtered:
            return None

        # 日時でソートして最新を取得
        sorted_reports = sorted(
            filtered, key=lambda r: r.get("created_at", ""), reverse=True
        )
        return ReportData.from_dict(sorted_reports[0])

    def get_reports(
        self,
        report_type: Optional[str] = None,
        target_person: Optional[str] = None,
        limit: int = 10,
    ) -> list[ReportData]:
        """
        報告データのリストを取得する

        Args:
            report_type: フィルタする報告タイプ
            target_person: フィルタする報告対象者
            limit: 取得する最大件数

        Returns:
            報告データのリスト（新しい順）
        """
        reports = self._load_all_reports()

        # フィルタリング
        filtered = reports
        if report_type:
            filtered = [r for r in filtered if r.get("report_type") == report_type]
        if target_person:
            filtered = [r for r in filtered if r.get("target_person") == target_person]

        # 日時でソートして制限
        sorted_reports = sorted(
            filtered, key=lambda r: r.get("created_at", ""), reverse=True
        )

        return [ReportData.from_dict(r) for r in sorted_reports[:limit]]

    def load_from_file(self, file_path: str | Path) -> ReportData:
        """
        ファイルから報告データを読み込む

        Args:
            file_path: 読み込むファイルパス

        Returns:
            読み込んだ報告データ

        Raises:
            StorageError: 読み込みに失敗した場合
        """
        path = Path(file_path)
        if not path.exists():
            raise StorageError(f"ファイルが見つかりません: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ReportData.from_dict(data)
        except json.JSONDecodeError as e:
            raise StorageError(f"JSONの解析に失敗しました: {e}") from e
        except Exception as e:
            raise StorageError(f"ファイルの読み込みに失敗しました: {e}") from e

    def load_from_text(self, text: str) -> str:
        """
        自由記述テキストを前回報告として読み込む

        Args:
            text: 前回の報告内容テキスト

        Returns:
            読み込んだテキスト（そのまま返す）
        """
        return text.strip()

    def export_report(self, report: ReportData, file_path: str | Path) -> None:
        """
        報告データをファイルにエクスポートする

        Args:
            report: エクスポートする報告データ
            file_path: 出力先ファイルパス
        """
        path = Path(file_path)

        if path.suffix.lower() == ".json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report.to_text())

    def _load_all_reports(self) -> list[dict]:
        """すべての報告データを読み込む"""
        if not self._reports_file.exists():
            return []

        try:
            with open(self._reports_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return []

    def _save_all_reports(self, reports: list[dict]) -> None:
        """すべての報告データを保存する"""
        with open(self._reports_file, "w", encoding="utf-8") as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)


class StorageError(Exception):
    """ストレージ関連のエラー"""

    pass
