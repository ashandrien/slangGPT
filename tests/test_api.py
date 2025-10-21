import pytest
from fastapi.testclient import TestClient

import os
import slang
from backend import main as backend_main
from backend.main import app


@pytest.fixture(autouse=True)
def prepare(monkeypatch):
    # Ensure tests don't pick up a real OPENAI API key from the environment
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Provide a dummy nlp object so endpoints don't 503 during tests
    monkeypatch.setattr(backend_main, "nlp", object(), raising=False)
    # Stub out the conversion function used by the backend module so
    # endpoints don't run the real spaCy-based conversion during tests.
    monkeypatch.setattr(backend_main, "convert_to_philly_slang", lambda nlp, text: f"converted:{text}", raising=False)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_slang_endpoint_ok(client):
    resp = client.post("/slang", json={"text": "Hello world"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["converted"] == "converted:Hello world"


def test_slang_endpoint_empty(client):
    resp = client.post("/slang", json={"text": "\x00\x00  "})
    assert resp.status_code == 400


def test_openai_slang_empty_prompt(client):
    resp = client.post("/openai_slang", json={"prompt": "\x00\x00  "})
    # No API key in test env; endpoint should return fallback message (200)
    assert resp.status_code == 200
    data = resp.json()
    assert "original" in data and "converted" in data
