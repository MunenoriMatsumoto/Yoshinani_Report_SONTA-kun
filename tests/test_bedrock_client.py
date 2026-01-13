"""Bedrockクライアントのテスト"""

import json
from unittest import mock

import pytest

from sonta_kun.bedrock_client import BedrockClient, BedrockError
from sonta_kun.config import BedrockConfig


@pytest.fixture
def mock_boto3_client():
    """boto3クライアントのモック"""
    with mock.patch("sonta_kun.bedrock_client.boto3.client") as mock_client:
        yield mock_client


def test_bedrock_client_init(mock_boto3_client):
    """クライアント初期化のテスト"""
    config = BedrockConfig()
    client = BedrockClient(config)

    mock_boto3_client.assert_called_once_with(
        "bedrock-runtime", region_name="ap-northeast-1"
    )
    assert client.config == config


def test_bedrock_client_generate_success(mock_boto3_client):
    """テキスト生成成功のテスト"""
    mock_response = {
        "body": mock.Mock(
            read=mock.Mock(
                return_value=json.dumps(
                    {"content": [{"text": "こんにちは！"}]}
                ).encode()
            )
        )
    }
    mock_boto3_client.return_value.invoke_model.return_value = mock_response

    client = BedrockClient()
    result = client.generate("テスト")

    assert result == "こんにちは！"


def test_bedrock_client_generate_with_system_prompt(mock_boto3_client):
    """システムプロンプト付きテキスト生成のテスト"""
    mock_response = {
        "body": mock.Mock(
            read=mock.Mock(
                return_value=json.dumps(
                    {"content": [{"text": "応答"}]}
                ).encode()
            )
        )
    }
    mock_boto3_client.return_value.invoke_model.return_value = mock_response

    client = BedrockClient()
    client.generate("テスト", system_prompt="あなたはアシスタントです")

    call_args = mock_boto3_client.return_value.invoke_model.call_args
    body = json.loads(call_args.kwargs["body"])
    assert body["system"] == "あなたはアシスタントです"
