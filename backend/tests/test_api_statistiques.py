"""Tests de /api/statistiques et du format des dates de l'API (épisode 9)."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Vente


def ajouter_vente(engine, client_id, numero, date_utc, statut, total_ht):
    with Session(engine) as session:
        session.add(Vente(numero=numero, client_id=client_id, date_vente=date_utc,
                          statut=statut, total_ht=Decimal(total_ht)))
        session.commit()


def test_ca_par_mois_en_heure_de_paris(api, engine, nouveau_client):
    client = nouveau_client()
    ajouter_vente(engine, client["id"], "V-1", datetime(2026, 11, 13, 9, 50), "validee", "5212.00")
    ajouter_vente(engine, client["id"], "V-2", datetime(2026, 11, 30, 23, 30), "validee", "899.00")
    ajouter_vente(engine, client["id"], "V-3", datetime(2026, 11, 20, 16, 35), "brouillon", "179.60")
    ajouter_vente(engine, client["id"], "V-4", datetime(2026, 11, 21, 10, 0), "annulee", "649.00")

    reponse = api.get("/api/statistiques/ca-par-mois")
    assert reponse.status_code == 200
    mois = {m["mois"]: m for m in reponse.json()}
    assert set(mois) == {"2026-11", "2026-12"}
    assert mois["2026-11"]["nb_ventes"] == 1
    assert Decimal(mois["2026-11"]["ca_ht"]) == Decimal("5212.00")
    assert Decimal(mois["2026-12"]["ca_ht"]) == Decimal("899.00")


def test_ca_par_mois_sans_vente(api):
    assert api.get("/api/statistiques/ca-par-mois").json() == []


def test_les_dates_de_l_api_indiquent_leur_fuseau(nouveau_client):
    client = nouveau_client()
    assert client["cree_le"].endswith("Z")
