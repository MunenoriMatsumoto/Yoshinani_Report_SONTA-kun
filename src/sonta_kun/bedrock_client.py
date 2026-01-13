"""Amazon Bedrock APIクライアント"""

import json
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from .config import BedrockConfig


class BedrockClient:
    """Amazon Bedrock Claude APIクライアント"""

    def __init__(self, config: Optional[BedrockConfig] = None):
        """
        クライアントを初期化する

        Args:
            config: Bedrock設定。Noneの場合は環境変数から読み込む
        """
        self.config = config or BedrockConfig.from_env()
        self._client = boto3.client(
            "bedrock-runtime", region_name=self.config.region_name
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Claudeモデルを使用してテキストを生成する

        Args:
            prompt: ユーザープロンプト
            system_prompt: システムプロンプト（オプション）

        Returns:
            生成されたテキスト

        Raises:
            BedrockError: API呼び出しに失敗した場合
        """
        messages = [{"role": "user", "content": prompt}]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": messages,
        }

        if system_prompt:
            body["system"] = system_prompt

        try:
            response = self._client.invoke_model(
                modelId=self.config.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())
            return response_body["content"][0]["text"]

        except ClientError as e:
            raise BedrockError(f"Bedrock API呼び出しに失敗しました: {e}") from e

    def test_connection(self) -> bool:
        """
        Bedrock APIへの接続をテストする

        Returns:
            接続成功の場合True
        """
        try:
            response = self.generate("こんにちは。簡潔に挨拶を返してください。")
            return bool(response)
        except BedrockError:
            return False


class BedrockError(Exception):
    """Bedrock API関連のエラー"""

    pass
