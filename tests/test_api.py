"""Unit and integration tests for FastAPI REST endpoints and Web routes."""

import pytest
from starlette.testclient import TestClient
from app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Fact-Checker & Daily News Digest" in response.text


def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_fact_check(client):
    payload = {"claim": "James Webb Telescope detected potential biosignatures on exoplanet K2-18b"}
    response = client.post("/api/fact-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "verdict" in data
    assert "credibility_score" in data
    assert "confidence" in data
    assert "summary" in data


def test_api_news_digest(client):
    response = client.get("/api/digest?category=Technology&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "Technology"
    assert len(data["articles"]) >= 1


def test_api_tools_credibility(client):
    response = client.post("/api/tools/credibility", json={"domain": "bbc.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["score"] >= 90


def test_api_tools_clickbait(client):
    response = client.post("/api/tools/clickbait", json={"text": "SHOCKING SECRET YOU WON'T BELIEVE!!!"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_clickbait"] is True


def test_api_mcp_manifest(client):
    response = client.get("/api/mcp/manifest")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "resources" in data
