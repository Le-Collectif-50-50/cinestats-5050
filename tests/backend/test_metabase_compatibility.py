"""Validate Metabase signing through FastAPI's synchronous request execution."""

import time

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers.metabase import router


SECRET = "test-only-metabase-signing-secret-32-bytes"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("METABASE_SITE_URL", "https://metabase.example.test")
    monkeypatch.setenv("METABASE_SECRET_KEY", SECRET)
    monkeypatch.setenv("METABASE_DASHBOARD_ID", "42")
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as test_client:
        yield test_client


def issued_token(client):
    response = client.get("/metabase/iframe-url")
    assert response.status_code == 200
    url = response.json()["iframe_url"]
    assert url.startswith("https://metabase.example.test/embed/dashboard/")
    assert url.endswith("#theme=night&background=false&bordered=false&titled=false")
    return url.split("/embed/dashboard/", 1)[1].split("#", 1)[0]


def test_embed_token_claims_and_lifetime(client):
    before = round(time.time())
    claims = jwt.decode(issued_token(client), SECRET, algorithms=["HS256"])
    assert claims["resource"] == {"dashboard": 42}
    assert claims["params"] == {}
    assert before + 600 <= claims["exp"] <= round(time.time()) + 600


@pytest.mark.parametrize(
    "missing", ["METABASE_SITE_URL", "METABASE_SECRET_KEY", "METABASE_DASHBOARD_ID"]
)
def test_missing_configuration_returns_503(client, monkeypatch, missing):
    monkeypatch.delenv(missing)
    response = client.get("/metabase/iframe-url")
    assert response.status_code == 503
    assert response.json() == {"detail": "Metabase config missing"}


def test_embed_token_rejects_wrong_secret(client):
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(issued_token(client), "different-test-secret-of-at-least-32-bytes", algorithms=["HS256"])


def test_embed_token_rejects_expiration(client):
    claims = jwt.decode(issued_token(client), SECRET, algorithms=["HS256"])
    claims["exp"] = int(time.time()) - 60
    expired = jwt.encode(claims, SECRET, algorithm="HS256")
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(expired, SECRET, algorithms=["HS256"])
