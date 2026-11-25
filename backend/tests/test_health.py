from fastapi.testclient import TestClient

from app import database
from app.main import app

client = TestClient(app)


def test_health_base_connectee(monkeypatch):
    monkeypatch.setattr(database, "check_database", lambda: True)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"api": "ok", "database": "ok"}


def test_health_base_indisponible(monkeypatch):
    monkeypatch.setattr(database, "check_database", lambda: False)
    response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json()["database"] == "indisponible"
