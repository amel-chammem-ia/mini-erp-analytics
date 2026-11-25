"""Tests des routes /api/clients (épisode 8)."""
from sqlalchemy.orm import Session

from app.models import Vente


def test_creer_client_normalise_les_donnees(api):
    reponse = api.post("/api/clients", json={
        "nom": "  Atelier Dupont ", "email": " Contact@Dupont.Example ", "numero_tva": "fr12345678901", "ville": "Lyon",
    })
    assert reponse.status_code == 201
    client = reponse.json()
    assert client["id"] > 0
    assert client["nom"] == "Atelier Dupont"
    assert client["email"] == "contact@dupont.example"
    assert client["numero_tva"] == "FR12345678901"


def test_email_invalide_refuse(api):
    reponse = api.post("/api/clients", json={"nom": "A", "email": "pas-un-mail", "numero_tva": "FR123"})
    assert reponse.status_code == 422


def test_champ_inconnu_refuse(api):
    reponse = api.post("/api/clients", json={"nom": "A", "email": "a@b.example", "numero_tva": "FR123", "role": "admin"})
    assert reponse.status_code == 422


def test_email_en_double_refuse(api, nouveau_client):
    nouveau_client(email="contact@dupont.example")
    r = api.post("/api/clients", json={
        "nom": "Autre",
        "email": "CONTACT@dupont.example",
        "numero_tva": "FR22222222222"})
    assert r.status_code == 409
    assert "e-mail" in r.json()["detail"]


def test_client_introuvable(api):
    assert api.get("/api/clients/999").status_code == 404


def test_recherche_paginee(api, nouveau_client):
    for i in range(25):
        ville = "Lyon" if i % 2 == 0 else "Nantes"
        nouveau_client(nom=f"Atelier {i:02d}", email=f"atelier{i}@test.example", numero_tva=f"FR{i:011d}", ville=ville)

    page1 = api.get("/api/clients", params={"recherche": "lyon", "taille": 10}).json()
    assert page1["total"] == 13
    assert len(page1["items"]) == 10
    page2 = api.get("/api/clients", params={"recherche": "lyon", "taille": 10, "page": 2}).json()
    assert len(page2["items"]) == 3
    assert api.get("/api/clients").json()["taille"] == 20


def test_recherche_avec_caractere_joker(api, nouveau_client):
    nouveau_client(nom="Atelier 100% Bio", email="bio@test.example", numero_tva="FR00000000001")
    nouveau_client(nom="Atelier 100 Pro", email="pro@test.example", numero_tva="FR00000000002")
    resultat = api.get("/api/clients", params={"recherche": "100%"}).json()
    assert [c["nom"] for c in resultat["items"]] == ["Atelier 100% Bio"]


def test_modifier_client(api, nouveau_client):
    client = nouveau_client()
    reponse = api.patch(f"/api/clients/{client['id']}", json={"ville": "Bordeaux"})
    assert reponse.status_code == 200
    assert reponse.json()["ville"] == "Bordeaux"
    assert reponse.json()["nom"] == client["nom"]


def test_modifier_client_nom_vide_refuse(api, nouveau_client):
    client = nouveau_client()
    assert api.patch(f"/api/clients/{client['id']}", json={"nom": None}).status_code == 422


def test_supprimer_client_sans_vente(api, nouveau_client):
    client = nouveau_client()
    assert api.delete(f"/api/clients/{client['id']}").status_code == 204
    assert api.get(f"/api/clients/{client['id']}").status_code == 404


def test_supprimer_client_avec_ventes_refuse(api, engine, nouveau_client):
    client = nouveau_client()
    with Session(engine) as session:
        session.add(Vente(numero="V-2026-0001", client_id=client["id"], statut="validee"))
        session.commit()
    reponse = api.delete(f"/api/clients/{client['id']}")
    assert reponse.status_code == 409
    assert api.get(f"/api/clients/{client['id']}").status_code == 200
