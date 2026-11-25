"""Tests des routes /api/produits (épisode 8)."""
from decimal import Decimal


def test_creer_produit(api):
    reponse = api.post("/api/produits", json={
        "reference": " p-0042 ", "nom": "Écran 27 pouces", "categorie": "Écrans", "prix_ht": "249.90",
    })
    assert reponse.status_code == 201
    produit = reponse.json()
    assert produit["reference"] == "P-0042"
    assert Decimal(produit["prix_ht"]) == Decimal("249.90")
    assert Decimal(produit["taux_tva"]) == Decimal("20.00")
    assert produit["stock_actuel"] == 0
    assert produit["sous_le_seuil"] is True


def test_prix_negatif_refuse(api):
    reponse = api.post("/api/produits", json={"reference": "X", "nom": "A", "categorie": "B", "prix_ht": "-1"})
    assert reponse.status_code == 422


def test_prix_avec_trois_decimales_refuse(api):
    reponse = api.post("/api/produits", json={"reference": "X", "nom": "A", "categorie": "B", "prix_ht": "1.999"})
    assert reponse.status_code == 422


def test_stock_ne_se_saisit_pas(api):
    reponse = api.post("/api/produits", json={"reference": "X", "nom": "A", "categorie": "B", "prix_ht": "1", "stock_actuel": 50})
    assert reponse.status_code == 422


def test_reference_en_double_refusee(api, nouveau_produit):
    nouveau_produit(reference="P-0042")
    reponse = api.post("/api/produits", json={"reference": "p-0042", "nom": "Autre", "categorie": "B", "prix_ht": "1"})
    assert reponse.status_code == 409


def test_produit_introuvable(api):
    assert api.get("/api/produits/999").status_code == 404


def test_modifier_prix(api, nouveau_produit):
    produit = nouveau_produit()
    reponse = api.patch(f"/api/produits/{produit['id']}", json={"prix_ht": "239.90"})
    assert reponse.status_code == 200
    assert Decimal(reponse.json()["prix_ht"]) == Decimal("239.90")


def test_supprimer_archive_le_produit(api, nouveau_produit):
    produit = nouveau_produit()
    assert api.delete(f"/api/produits/{produit['id']}").status_code == 204

    assert api.get(f"/api/produits/{produit['id']}").json()["actif"] is False
    assert api.get("/api/produits").json()["total"] == 0
    assert api.get("/api/produits", params={"inclure_archives": True}).json()["total"] == 1


def test_filtre_sous_le_seuil(api, nouveau_produit):
    nouveau_produit(reference="P-A", seuil_alerte=5)   # stock 0 < 5
    nouveau_produit(reference="P-B", seuil_alerte=0)   # stock 0 >= 0
    a_commander = api.get("/api/produits", params={"sous_le_seuil": True}).json()
    assert [p["reference"] for p in a_commander["items"]] == ["P-A"]
