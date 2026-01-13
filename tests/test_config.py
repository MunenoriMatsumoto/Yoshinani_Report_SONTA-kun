"""設定モジュールのテスト"""

import os
from unittest import mock

from sonta_kun.config import AppConfig, BedrockConfig


def test_bedrock_config_defaults():
    """デフォルト設定のテスト"""
    config = BedrockConfig()
    assert config.region_name == "ap-northeast-1"
    assert config.model_id == "anthropic.claude-sonnet-4-5-20250514-v1:0"
    assert config.max_tokens == 4096
    assert config.temperature == 0.7


def test_bedrock_config_from_env():
    """環境変数からの設定読み込みテスト"""
    env_vars = {
        "AWS_REGION": "us-west-2",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-opus-20240229-v1:0",
        "BEDROCK_MAX_TOKENS": "8192",
        "BEDROCK_TEMPERATURE": "0.5",
    }

    with mock.patch.dict(os.environ, env_vars, clear=False):
        config = BedrockConfig.from_env()
        assert config.region_name == "us-west-2"
        assert config.model_id == "anthropic.claude-3-opus-20240229-v1:0"
        assert config.max_tokens == 8192
        assert config.temperature == 0.5


def test_app_config_load():
    """アプリケーション設定の読み込みテスト"""
    config = AppConfig.load()
    assert isinstance(config.bedrock, BedrockConfig)
