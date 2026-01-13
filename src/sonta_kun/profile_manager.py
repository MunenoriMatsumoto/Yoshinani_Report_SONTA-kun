"""報告対象者プロファイル管理モジュール"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TargetProfile:
    """報告対象者のプロファイル"""

    name: str  # 名前（例：山田さん）
    role: str  # 役職（例：課長、室長、部長、メンバー）
    focus: str  # 関心事（例：納期重視、方針重視、コスト重視、詳細重視）
    description: str = ""  # 追加の説明

    # 報告書生成時の設定
    summary_max_chars: int = 300  # サマリの最大文字数
    detail_level: str = "medium"  # 詳細度: "low", "medium", "high"
    preferred_format: str = "markdown"  # 出力形式: "text", "markdown"

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "name": self.name,
            "role": self.role,
            "focus": self.focus,
            "description": self.description,
            "summary_max_chars": self.summary_max_chars,
            "detail_level": self.detail_level,
            "preferred_format": self.preferred_format,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TargetProfile":
        """辞書から作成"""
        return cls(
            name=data.get("name", ""),
            role=data.get("role", ""),
            focus=data.get("focus", ""),
            description=data.get("description", ""),
            summary_max_chars=data.get("summary_max_chars", 300),
            detail_level=data.get("detail_level", "medium"),
            preferred_format=data.get("preferred_format", "markdown"),
        )

    def get_prompt_context(self) -> str:
        """プロンプト用のコンテキスト情報を生成"""
        context_parts = [
            f"報告対象者: {self.name}（{self.role}）",
            f"関心事: {self.focus}",
        ]
        if self.description:
            context_parts.append(f"補足情報: {self.description}")

        return "\n".join(context_parts)


# デフォルトプロファイルのテンプレート
DEFAULT_PROFILES = [
    TargetProfile(
        name="課長",
        role="課長",
        focus="納期重視",
        description="スケジュール遵守と進捗状況を重視。遅延リスクがあれば早期に報告を求める。",
        summary_max_chars=300,
        detail_level="medium",
    ),
    TargetProfile(
        name="室長",
        role="室長",
        focus="方針重視",
        description="全体方針との整合性を重視。戦略的な観点からの報告を好む。",
        summary_max_chars=400,
        detail_level="medium",
    ),
    TargetProfile(
        name="部長",
        role="部長",
        focus="コスト重視",
        description="コスト効率とROIを重視。予算への影響を明確にした報告を求める。",
        summary_max_chars=250,
        detail_level="low",
    ),
    TargetProfile(
        name="メンバー",
        role="メンバー",
        focus="詳細重視",
        description="技術的な詳細や具体的な作業内容を重視。実装レベルの情報を求める。",
        summary_max_chars=500,
        detail_level="high",
    ),
]


class ProfileManager:
    """報告対象者プロファイルを管理するクラス"""

    PROFILES_FILE = "profiles.json"

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Args:
            storage_dir: 保存先ディレクトリ。Noneの場合はユーザーホームに作成
        """
        if storage_dir:
            self._storage_dir = Path(storage_dir)
        else:
            self._storage_dir = Path.home() / ".sonta_kun"

        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._profiles_file = self._storage_dir / self.PROFILES_FILE
        self._profiles: dict[str, TargetProfile] = {}

        self._load_profiles()

    def _load_profiles(self) -> None:
        """プロファイルを読み込む"""
        if self._profiles_file.exists():
            try:
                with open(self._profiles_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._profiles = {
                    name: TargetProfile.from_dict(profile_data)
                    for name, profile_data in data.items()
                }
            except (json.JSONDecodeError, Exception):
                self._profiles = {}
        else:
            # デフォルトプロファイルを設定
            self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """デフォルトプロファイルを初期化"""
        for profile in DEFAULT_PROFILES:
            self._profiles[profile.name] = profile
        self._save_profiles()

    def _save_profiles(self) -> None:
        """プロファイルを保存"""
        data = {name: profile.to_dict() for name, profile in self._profiles.items()}
        with open(self._profiles_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_profile(self, profile: TargetProfile) -> None:
        """
        プロファイルを追加または更新する

        Args:
            profile: 追加するプロファイル
        """
        self._profiles[profile.name] = profile
        self._save_profiles()

    def get_profile(self, name: str) -> Optional[TargetProfile]:
        """
        プロファイルを取得する

        Args:
            name: プロファイル名

        Returns:
            プロファイル、見つからない場合はNone
        """
        return self._profiles.get(name)

    def delete_profile(self, name: str) -> bool:
        """
        プロファイルを削除する

        Args:
            name: 削除するプロファイル名

        Returns:
            削除成功の場合True
        """
        if name in self._profiles:
            del self._profiles[name]
            self._save_profiles()
            return True
        return False

    def list_profiles(self) -> list[TargetProfile]:
        """
        全プロファイルを取得する

        Returns:
            プロファイルのリスト
        """
        return list(self._profiles.values())

    def get_profile_names(self) -> list[str]:
        """
        プロファイル名のリストを取得する

        Returns:
            プロファイル名のリスト
        """
        return list(self._profiles.keys())

    def reset_to_defaults(self) -> None:
        """デフォルトプロファイルにリセットする"""
        self._profiles = {}
        self._initialize_defaults()
