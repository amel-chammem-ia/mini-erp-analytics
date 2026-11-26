"""Fixtures partagées : l'API branchée sur une base SQLite en mémoire, recréée pour chaque test.

Depuis l'épisode 10, toutes les routes métier exigent une connexion :
- `api`      : un client connecté en administrateur (tous les droits) ;
- `anonyme`  : un client sans jeton ;
- `connecter("vendeur")` : crée un compte de ce rôle et renvoie l'en-tête Authorization.
"""
from itertools import count

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import securite
from app.database import get_session
from app.main import app
from app.models import Base, Utilisateur
from app.routers.auth import limiteur

SECRET_DE_TEST = "secret-reserve-aux-tests-pytest-0123456789abcdef"
MOT_DE_PASSE = "Mot-de-passe-de-test-2026"


@pytest.fixture(autouse=True)
def configuration_de_test(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET_DE_TEST)
    monkeypatch.setattr(securite, "SCRYPT_N", 2**10)  # hachage allégé : les tests restent rapides
    limiteur.reinitialiser()
    yield
    limiteur.reinitialiser()


@pytest.fixture
def engine():
    # StaticPool : une seule connexion, partagée par les threads du client de test.
    moteur = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(moteur)
    yield moteur
    moteur.dispose()


@pytest.fixture
def base_de_test(engine):
    def session_de_test():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_de_test
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def anonyme(base_de_test):
    with TestClient(app) as client:
        yield client


@pytest.fixture
def creer_compte(engine):
    """Crée un compte directement en base et renvoie son identifiant."""
    def creer(role="administrateur", email=None, actif=True, mot_de_passe=MOT_DE_PASSE):
        with Session(engine) as session:
            compte = Utilisateur(email=email or f"{role}@mini-erp.example", nom=f"Compte {role}",
                                 role=role, actif=actif,
                                 mot_de_passe_hache=securite.hacher_mot_de_passe(mot_de_passe))
            session.add(compte)
            session.commit()
            return compte.id
    return creer


@pytest.fixture
def connecter(anonyme, creer_compte):
    numeros = count(1)

    def connexion(role: str) -> dict[str, str]:
        email = f"{role}.{next(numeros)}@mini-erp.example"
        creer_compte(role, email)
        reponse = anonyme.post("/api/auth/connexion", json={"email": email, "mot_de_passe": MOT_DE_PASSE})
        assert reponse.status_code == 200, reponse.text
        return {"Authorization": f"Bearer {reponse.json()['access_token']}"}
    return connexion


@pytest.fixture
def api(base_de_test, connecter):
    entetes = connecter("administrateur")
    with TestClient(app) as client:
        client.headers.update(entetes)
        yield client


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
