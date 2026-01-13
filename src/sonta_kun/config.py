"""設定管理モジュール"""

import os
from dataclasses import dataclass


@dataclass
class BedrockConfig:
    """Amazon Bedrock設定"""

    region_name: str = "ap-northeast-1"
    model_id: str = "anthropic.claude-sonnet-4-5-20250514-v1:0"
    max_tokens: int = 4096
    temperature: float = 0.7

    @classmethod
    def from_env(cls) -> "BedrockConfig":
        """環境変数から設定を読み込む"""
        return cls(
            region_name=os.getenv("AWS_REGION", "ap-northeast-1"),
            model_id=os.getenv(
                "BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-5-20250514-v1:0"
            ),
            max_tokens=int(os.getenv("BEDROCK_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("BEDROCK_TEMPERATURE", "0.7")),
        )


@dataclass
class AppConfig:
    """アプリケーション設定"""

    bedrock: BedrockConfig

    @classmethod
    def load(cls) -> "AppConfig":
        """設定を読み込む"""
        return cls(bedrock=BedrockConfig.from_env())
