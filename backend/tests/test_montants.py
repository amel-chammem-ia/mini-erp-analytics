"""Tests du calcul des montants (épisode 11) : centimes, arrondis, TVA par taux.

Sans serveur ni base : ces tests tournent en une fraction de seconde.
"""
from decimal import Decimal as D

import pytest

from app.montants import (LigneMontant, arrondir, calculer_totaux, format_euros,
                          format_numero_facture)


def ligne(quantite, prix, taux="20.00"):
    return LigneMontant(quantite, D(prix), D(taux))


# Pourquoi pas de float -----------------------------------------------------
def test_le_float_se_trompe_deja_sur_dix_centimes():
    assert 0.1 + 0.2 != 0.3                       # 0.30000000000000004
    assert D("0.10") + D("0.20") == D("0.30")


def test_un_float_est_refuse():
    with pytest.raises(TypeError):
        arrondir(19.99)
    with pytest.raises(TypeError):
        LigneMontant(1, 19.99, D("20"))


# Arrondis ------------------------------------------------------------------
@pytest.mark.parametrize(("montant", "attendu"), [
    ("1.004", "1.00"), ("1.005", "1.01"), ("2.675", "2.68"), ("0.055", "0.06"), ("10", "10.00"),
])
def test_arrondi_commercial_au_centime(montant, attendu):
    assert arrondir(D(montant)) == D(attendu)


def test_le_round_de_python_n_est_pas_l_arrondi_commercial():
    assert round(2.675, 2) == 2.67                # 2.675 n'existe pas en float : 2.67499999…
    assert arrondir(D("2.675")) == D("2.68")


# Le centime qui change tout --------------------------------------------------
def test_tva_par_taux_et_non_ligne_par_ligne():
    # Trois lignes à 0,99 € HT, TVA 20 %.
    # Ligne par ligne : 0,198 → 0,20, trois fois = 0,60 €.
    # Par taux, sur le total HT : 2,97 × 20 % = 0,594 → 0,59 €. C'est la règle retenue.
    totaux = calculer_totaux([ligne(1, "0.99"), ligne(1, "0.99"), ligne(1, "0.99")])
    assert totaux.total_ht == D("2.97")
    assert totaux.total_tva == D("0.59")
    assert totaux.total_ttc == D("3.56")


def test_plusieurs_taux_de_tva():
    totaux = calculer_totaux([ligne(2, "899.00"), ligne(3, "49.90"), ligne(1, "24.90", "5.50")])
    assert [(t.taux, t.base_ht, t.montant_tva) for t in totaux.tva_par_taux] == [
        (D("5.50"), D("24.90"), D("1.37")),       # 1,3695 → 1,37
        (D("20.00"), D("1947.70"), D("389.54")),
    ]
    assert totaux.total_ht == D("1972.60")
    assert totaux.total_tva == D("390.91")
    assert totaux.total_ttc == D("2363.51")


def test_meme_taux_ecrit_differemment():
    totaux = calculer_totaux([ligne(1, "10.00", "20"), ligne(1, "10.00", "20.00")])
    assert len(totaux.tva_par_taux) == 1


def test_ttc_egale_toujours_ht_plus_tva():
    totaux = calculer_totaux([ligne(q, p) for q, p in [(3, "0.33"), (7, "1.17"), (13, "19.99"), (1, "0.01")]])
    assert totaux.total_ttc == totaux.total_ht + totaux.total_tva


def test_taux_zero():
    totaux = calculer_totaux([ligne(4, "12.50", "0")])
    assert (totaux.total_ht, totaux.total_tva, totaux.total_ttc) == (D("50.00"), D("0.00"), D("50.00"))


# Données refusées ------------------------------------------------------------
def test_vente_sans_ligne():
    with pytest.raises(ValueError):
        calculer_totaux([])


@pytest.mark.parametrize(("quantite", "prix", "taux"), [
    (0, "10", "20"), (-1, "10", "20"), (True, "10", "20"), (1, "-0.01", "20"), (1, "10", "100.01"), (1, "10", "-1"),
])
def test_ligne_invalide(quantite, prix, taux):
    with pytest.raises(ValueError):
        LigneMontant(quantite, D(prix), D(taux))


# Affichage et numérotation ---------------------------------------------------
def test_format_euros():
    assert format_euros(D("1234.5")) == "1 234,50 €"
    assert format_euros(D("0")) == "0,00 €"
    assert format_euros(D("1234567.891")) == "1 234 567,89 €"


def test_numero_de_facture():
    assert format_numero_facture(2026, 1) == "FAC-2026-00001"
    assert format_numero_facture(2026, 12345) == "FAC-2026-12345"
    with pytest.raises(ValueError):
        format_numero_facture(2026, 0)
