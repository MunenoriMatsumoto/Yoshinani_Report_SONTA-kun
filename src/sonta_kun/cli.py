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


def run_gui() -> None:
    """GUIアプリケーションを起動する"""
    load_dotenv()
    from .gui import MainWindow

    app = MainWindow()
    app.run()


def main() -> None:
    """メインエントリーポイント"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "test":
            test_bedrock_connection()
        elif command == "gui":
            run_gui()
        else:
            print(f"不明なコマンド: {command}")
            sys.exit(1)
    else:
        # デフォルトでGUIを起動
        run_gui()


if __name__ == "__main__":
    main()
