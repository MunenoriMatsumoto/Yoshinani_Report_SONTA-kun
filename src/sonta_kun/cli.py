"""コマンドラインインターフェース"""

import sys

from dotenv import load_dotenv

from .bedrock_client import BedrockClient, BedrockError
from .config import AppConfig


def test_bedrock_connection() -> None:
    """Bedrock APIへの接続をテストする"""
    load_dotenv()
    config = AppConfig.load()

    print("SONTA-kun: Bedrock接続テスト")
    print(f"  リージョン: {config.bedrock.region_name}")
    print(f"  モデル: {config.bedrock.model_id}")
    print()

    client = BedrockClient(config.bedrock)

    try:
        print("接続テスト中...")
        response = client.generate("こんにちは。一言で挨拶を返してください。")
        print(f"成功! レスポンス: {response}")
    except BedrockError as e:
        print(f"エラー: {e}")
        sys.exit(1)


def main() -> None:
    """メインエントリーポイント"""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_bedrock_connection()
    else:
        print("SONTA-kun v0.1.0 - 週報・月報作成支援ツール")
        print()
        print("使用方法:")
        print("  python -m sonta_kun test  - Bedrock接続テスト")


if __name__ == "__main__":
    main()
