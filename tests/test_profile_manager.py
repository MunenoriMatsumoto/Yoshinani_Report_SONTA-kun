"""プロファイルマネージャーのテスト"""

import tempfile
from pathlib import Path

import pytest

from sonta_kun.profile_manager import ProfileManager, TargetProfile


@pytest.fixture
def temp_storage_dir():
    """一時ストレージディレクトリ"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_target_profile_to_dict():
    """TargetProfileの辞書変換テスト"""
    profile = TargetProfile(
        name="山田課長",
        role="課長",
        focus="納期重視",
        description="スケジュール管理を重視",
        summary_max_chars=300,
    )
    result = profile.to_dict()

    assert result["name"] == "山田課長"
    assert result["role"] == "課長"
    assert result["focus"] == "納期重視"
    assert result["summary_max_chars"] == 300


def test_target_profile_from_dict():
    """辞書からTargetProfileへの変換テスト"""
    data = {
        "name": "佐藤室長",
        "role": "室長",
        "focus": "方針重視",
        "detail_level": "medium",
    }
    profile = TargetProfile.from_dict(data)

    assert profile.name == "佐藤室長"
    assert profile.role == "室長"
    assert profile.detail_level == "medium"


def test_target_profile_get_prompt_context():
    """プロンプトコンテキスト生成テスト"""
    profile = TargetProfile(
        name="田中部長",
        role="部長",
        focus="コスト重視",
        description="ROIを重視する",
    )
    context = profile.get_prompt_context()

    assert "田中部長" in context
    assert "部長" in context
    assert "コスト重視" in context
    assert "ROI" in context


def test_profile_manager_default_profiles(temp_storage_dir):
    """デフォルトプロファイル初期化テスト"""
    manager = ProfileManager(storage_dir=temp_storage_dir)
    profiles = manager.list_profiles()

    assert len(profiles) == 4
    names = manager.get_profile_names()
    assert "課長" in names
    assert "室長" in names
    assert "部長" in names
    assert "メンバー" in names


def test_profile_manager_add_profile(temp_storage_dir):
    """プロファイル追加テスト"""
    manager = ProfileManager(storage_dir=temp_storage_dir)

    new_profile = TargetProfile(
        name="カスタム報告先",
        role="マネージャー",
        focus="品質重視",
    )
    manager.add_profile(new_profile)

    retrieved = manager.get_profile("カスタム報告先")
    assert retrieved is not None
    assert retrieved.focus == "品質重視"


def test_profile_manager_delete_profile(temp_storage_dir):
    """プロファイル削除テスト"""
    manager = ProfileManager(storage_dir=temp_storage_dir)

    assert manager.delete_profile("課長") is True
    assert manager.get_profile("課長") is None

    assert manager.delete_profile("存在しない") is False


def test_profile_manager_persistence(temp_storage_dir):
    """プロファイル永続化テスト"""
    manager1 = ProfileManager(storage_dir=temp_storage_dir)
    manager1.add_profile(
        TargetProfile(name="新規プロファイル", role="テスト", focus="テスト重視")
    )

    # 新しいインスタンスを作成
    manager2 = ProfileManager(storage_dir=temp_storage_dir)
    profile = manager2.get_profile("新規プロファイル")

    assert profile is not None
    assert profile.focus == "テスト重視"


def test_profile_manager_reset_to_defaults(temp_storage_dir):
    """デフォルトへのリセットテスト"""
    manager = ProfileManager(storage_dir=temp_storage_dir)
    manager.delete_profile("課長")
    manager.delete_profile("室長")

    assert len(manager.list_profiles()) == 2

    manager.reset_to_defaults()
    assert len(manager.list_profiles()) == 4
