"""Tests des ventes et des factures par l'API (épisode 11).

À lancer dans le conteneur :  docker compose exec api pytest
"""
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CompteurFacture, MouvementStock, Produit
from app.routers.ventes import maintenant_utc
from app.temps import heure_metier


def stock(engine, produit_id, quantite=None):
    """Lit le stock d'un produit, ou le fixe si une quantité est donnée."""
    with Session(engine) as session:
        produit = session.get(Produit, produit_id)
        if quantite is not None:
            produit.stock_actuel = quantite
            session.commit()
        return produit.stock_actuel


@pytest.fixture
def catalogue(nouveau_produit, engine):
    ecran = nouveau_produit(reference="P-ECRAN", nom="Écran 27 pouces", prix_ht="0.99", seuil_alerte=2)
    clavier = nouveau_produit(reference="P-CLAVIER", nom="Clavier", categorie="Accessoires", prix_ht="49.90")
    stock(engine, ecran["id"], 10)
    stock(engine, clavier["id"], 3)
    return {"ecran": ecran, "clavier": clavier}


@pytest.fixture
def commande(api, nouveau_client, catalogue):
    client = nouveau_client()

    def creer(lignes=None, client_id=None):
        lignes = [(catalogue["ecran"]["id"], 3)] if lignes is None else lignes
        corps = {"client_id": client_id or client["id"],
                 "lignes": [{"produit_id": p, "quantite": q} for p, q in lignes]}
        return api.post("/api/ventes", json=corps)
    return creer


# Création et totaux ----------------------------------------------------------
def test_creer_une_commande_calcule_les_totaux(commande):
    reponse = commande()
    assert reponse.status_code == 201
    vente = reponse.json()
    assert vente["statut"] == "brouillon" and vente["numero_facture"] is None
    assert vente["numero"].startswith("V-")
    # 3 × 0,99 € : TVA calculée sur le total HT (0,594 → 0,59 €), pas ligne par ligne (0,60 €).
    assert Decimal(vente["total_ht"]) == Decimal("2.97")
    assert Decimal(vente["total_tva"]) == Decimal("0.59")
    assert Decimal(vente["total_ttc"]) == Decimal("3.56")
    assert vente["lignes"][0]["reference"] == "P-ECRAN"


def test_le_prix_vient_du_catalogue_pas_du_client(api, nouveau_client, catalogue):
    corps = {"client_id": nouveau_client()["id"],
             "lignes": [{"produit_id": catalogue["ecran"]["id"], "quantite": 1, "prix_unitaire_ht": "0.01"}]}
    assert api.post("/api/ventes", json=corps).status_code == 422


@pytest.mark.parametrize("lignes", [[], [(1, 0)], [(1, -2)]])
def test_commande_invalide(commande, lignes):
    assert commande(lignes=lignes).status_code == 422


def test_produit_en_double_refuse(commande, catalogue):
    ecran = catalogue["ecran"]["id"]
    reponse = commande(lignes=[(ecran, 1), (ecran, 2)])
    assert reponse.status_code == 422


def test_produit_ou_client_inconnu(commande):
    assert commande(lignes=[(9999, 1)]).status_code == 404
    assert commande(client_id=9999).status_code == 404


def test_produit_archive_invendable(api, commande, catalogue):
    api.delete(f"/api/produits/{catalogue['clavier']['id']}")
    assert commande(lignes=[(catalogue["clavier"]["id"], 1)]).status_code == 409


def test_modifier_un_brouillon(api, commande, catalogue):
    vente = commande().json()
    corps = {"client_id": vente["client_id"],
             "lignes": [{"produit_id": catalogue["ecran"]["id"], "quantite": 1},
                        {"produit_id": catalogue["clavier"]["id"], "quantite": 2}]}
    reponse = api.put(f"/api/ventes/{vente['id']}", json=corps)
    assert reponse.status_code == 200
    assert len(reponse.json()["lignes"]) == 2
    assert Decimal(reponse.json()["total_ht"]) == Decimal("100.79")


# Validation et facture ---------------------------------------------------------
def test_valider_sort_le_stock_et_attribue_un_numero(api, engine, commande, catalogue):
    vente = commande().json()
    reponse = api.post(f"/api/ventes/{vente['id']}/valider")
    assert reponse.status_code == 200
    validee = reponse.json()
    annee = heure_metier(maintenant_utc()).year
    assert validee["statut"] == "validee"
    assert validee["numero_facture"] == f"FAC-{annee}-00001"
    assert validee["facturee_le"].endswith("Z")
    assert stock(engine, catalogue["ecran"]["id"]) == 7
    with Session(engine) as session:
        sorties = session.scalars(select(MouvementStock).where(MouvementStock.vente_id == vente["id"])).all()
        assert [(m.type_mouvement, m.quantite) for m in sorties] == [("sortie", 3)]


def test_numeros_continus_sans_trou(api, engine, commande, catalogue):
    annee = heure_metier(maintenant_utc()).year
    premiere = commande().json()
    en_rupture = commande(lignes=[(catalogue["clavier"]["id"], 50)]).json()
    seconde = commande().json()
    assert api.post(f"/api/ventes/{premiere['id']}/valider").json()["numero_facture"] == f"FAC-{annee}-00001"
    assert api.post(f"/api/ventes/{en_rupture['id']}/valider").status_code == 409   # échec : aucun numéro consommé
    assert api.post(f"/api/ventes/{seconde['id']}/valider").json()["numero_facture"] == f"FAC-{annee}-00002"
    with Session(engine) as session:
        assert session.get(CompteurFacture, annee).dernier_numero == 2


def test_stock_insuffisant_rien_ne_bouge(api, engine, commande, catalogue):
    vente = commande(lignes=[(catalogue["ecran"]["id"], 2), (catalogue["clavier"]["id"], 5)]).json()
    reponse = api.post(f"/api/ventes/{vente['id']}/valider")
    assert reponse.status_code == 409
    assert "P-CLAVIER (demandé 5, disponible 3)" in reponse.json()["detail"]
    assert stock(engine, catalogue["ecran"]["id"]) == 10          # la sortie de l'écran est annulée aussi
    assert api.get(f"/api/ventes/{vente['id']}").json()["statut"] == "brouillon"


def test_une_vente_validee_est_figee(api, commande, catalogue):
    vente = commande().json()
    api.post(f"/api/ventes/{vente['id']}/valider")
    corps = {"client_id": vente["client_id"], "lignes": [{"produit_id": catalogue["ecran"]["id"], "quantite": 1}]}
    assert api.put(f"/api/ventes/{vente['id']}", json=corps).status_code == 409
    assert api.post(f"/api/ventes/{vente['id']}/valider").status_code == 409
    assert api.post(f"/api/ventes/{vente['id']}/annuler").status_code == 409


def test_le_prix_de_la_facture_ne_change_plus(api, commande, catalogue):
    vente = commande().json()
    api.post(f"/api/ventes/{vente['id']}/valider")
    api.patch(f"/api/produits/{catalogue['ecran']['id']}", json={"prix_ht": "5.00"})
    assert Decimal(api.get(f"/api/ventes/{vente['id']}").json()["total_ht"]) == Decimal("2.97")


def test_annuler_un_brouillon(api, commande):
    vente = commande().json()
    assert api.post(f"/api/ventes/{vente['id']}/annuler").json()["statut"] == "annulee"
    assert api.post(f"/api/ventes/{vente['id']}/valider").status_code == 409


def test_facture_pdf(api, commande):
    vente = commande().json()
    assert api.get(f"/api/ventes/{vente['id']}/facture.pdf").status_code == 409    # pas encore validée
    numero = api.post(f"/api/ventes/{vente['id']}/valider").json()["numero_facture"]
    reponse = api.get(f"/api/ventes/{vente['id']}/facture.pdf")
    assert reponse.status_code == 200
    assert reponse.headers["content-type"] == "application/pdf"
    assert numero in reponse.headers["content-disposition"]
    assert reponse.content.startswith(b"%PDF-") and numero.encode() in reponse.content


def test_lister_et_filtrer(api, commande):
    premiere = commande().json()
    commande()
    api.post(f"/api/ventes/{premiere['id']}/valider")
    assert api.get("/api/ventes").json()["total"] == 2
    validees = api.get("/api/ventes", params={"statut": "validee"}).json()
    assert [v["id"] for v in validees["items"]] == [premiere["id"]]


# Droits (matrice de l'épisode 10) ----------------------------------------------
def test_le_vendeur_cree_et_valide(anonyme, connecter, commande):
    vente = commande().json()
    vendeur = connecter("vendeur")
    assert anonyme.post(f"/api/ventes/{vente['id']}/valider", headers=vendeur).status_code == 200
    assert anonyme.get(f"/api/ventes/{vente['id']}/facture.pdf", headers=vendeur).status_code == 200


@pytest.mark.parametrize(("role", "attendu"), [("commercial", 200), ("magasinier", 403)])
def test_qui_peut_lire_les_ventes(anonyme, connecter, role, attendu):
    assert anonyme.get("/api/ventes", headers=connecter(role)).status_code == attendu


def test_le_commercial_ne_valide_pas(anonyme, connecter, commande):
    vente = commande().json()
    assert anonyme.post(f"/api/ventes/{vente['id']}/valider", headers=connecter("commercial")).status_code == 403
