"""Tests des modèles sur une base SQLite en mémoire : aucune base SQL Server n'est nécessaire."""
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Client, LigneVente, Produit, Vente


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def client_test(email="contact@exemple.example", tva="FR00000000001"):
    return Client(nom="Atelier Test", email=email, numero_tva=tva, ville="Lyon")


def produit_test(reference="P-TEST", prix="899.00"):
    return Produit(reference=reference, nom="Ordinateur portable", categorie="Ordinateurs",
                   prix_ht=Decimal(prix), stock_actuel=3, seuil_alerte=5)


def test_vente_avec_lignes(session):
    client, produit = client_test(), produit_test()
    vente = Vente(numero="V-TEST-0001", client=client, statut="validee")
    vente.lignes.append(LigneVente(produit=produit, quantite=3, prix_unitaire_ht=produit.prix_ht, taux_tva=Decimal("20.00")))
    session.add(vente)
    session.commit()

    relue = session.get(Vente, vente.id)
    assert relue.client.nom == "Atelier Test"
    assert relue.lignes[0].produit.reference == "P-TEST"
    assert relue.lignes[0].montant_ht == Decimal("2697.00")


def test_produit_sous_le_seuil():
    assert produit_test().sous_le_seuil is True


def test_quantite_negative_refusee(session):
    vente = Vente(numero="V-TEST-0002", client=client_test())
    vente.lignes.append(LigneVente(produit=produit_test(), quantite=-1, prix_unitaire_ht=Decimal("10"), taux_tva=Decimal("20")))
    session.add(vente)
    with pytest.raises(IntegrityError):
        session.commit()


def test_email_client_unique(session):
    session.add_all([client_test(tva="FR00000000001"), client_test(tva="FR00000000002")])
    with pytest.raises(IntegrityError):
        session.commit()
