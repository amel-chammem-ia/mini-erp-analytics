"""Fixtures partagées : l'API branchée sur une base SQLite en mémoire, recréée pour chaque test."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import get_session
from app.main import app
from app.models import Base


@pytest.fixture
def engine():
    # StaticPool : une seule connexion, partagée par les threads du client de test.
    moteur = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(moteur)
    yield moteur
    moteur.dispose()


@pytest.fixture
def api(engine):
    def session_de_test():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_de_test
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def nouveau_client(api):
    """Crée un client par l'API et renvoie sa réponse JSON."""
    def creer(nom="Atelier Dupont", email="contact@dupont.example", numero_tva="FR12345678901", ville="Lyon"):
        reponse = api.post("/api/clients", json={"nom": nom, "email": email, "numero_tva": numero_tva, "ville": ville})
        assert reponse.status_code == 201, reponse.text
        return reponse.json()
    return creer


@pytest.fixture
def nouveau_produit(api):
    def creer(reference="P-0042", nom="Écran 27 pouces", categorie="Écrans", prix_ht="249.90", seuil_alerte=5):
        reponse = api.post("/api/produits", json={"reference": reference, "nom": nom, "categorie": categorie,
                                                  "prix_ht": prix_ht, "seuil_alerte": seuil_alerte})
        assert reponse.status_code == 201, reponse.text
        return reponse.json()
    return creer
