from dynamo import DynamoClient


def test_production_dynamo_keeps_configured_aws_credentials(monkeypatch):
    monkeypatch.delenv("DYNAMODB_URL", raising=False)
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret-key")

    client = DynamoClient()

    assert client.creds["region_name"] == "ap-south-1"
    assert client.creds["aws_access_key_id"] == "test-access-key"
    assert client.creds["aws_secret_access_key"] == "test-secret-key"


def test_local_dynamo_ignores_dummy_credentials(monkeypatch):
    monkeypatch.setenv("DYNAMODB_URL", "http://dynamodb:8000")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "dummy")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "dummy")

    client = DynamoClient()

    assert client.creds["endpoint_url"] == "http://dynamodb:8000"
    assert "aws_access_key_id" not in client.creds
    assert "aws_secret_access_key" not in client.creds
