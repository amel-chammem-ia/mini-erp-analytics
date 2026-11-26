"""Tests des dates et du chiffre d'affaires par mois (épisode 9).

Le premier test est le test de non-régression du bug du fuseau horaire :
une vente du 1er décembre à 0 h 30 (Paris) est enregistrée le 30 novembre à 23 h 30 UTC.
"""
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

from app.statistiques import ca_par_mois
from app.temps import en_utc, mois_metier


def test_vente_du_1er_decembre_a_0h30_comptee_en_decembre():
    assert mois_metier(datetime(2026, 11, 30, 23, 30)) == "2026-12"


def test_heure_d_ete_deux_heures_d_avance():
    # 31 juillet 22 h 30 UTC = 1er août 0 h 30 à Paris (UTC+2)
    assert mois_metier(datetime(2026, 7, 31, 22, 30)) == "2026-08"


def test_juste_avant_minuit_a_paris_reste_dans_le_mois():
    # 30 novembre 22 h 59 UTC = 23 h 59 à Paris
    assert mois_metier(datetime(2026, 11, 30, 22, 59)) == "2026-11"


def test_milieu_de_mois():
    assert mois_metier(datetime(2026, 11, 13, 9, 50)) == "2026-11"


def test_date_avec_fuseau_explicite():
    new_york = timezone(timedelta(hours=-5))
    # 30 novembre 19 h à New York = 1er décembre 1 h à Paris
    assert mois_metier(datetime(2026, 11, 30, 19, 0, tzinfo=new_york)) == "2026-12"


def test_en_utc_ajoute_le_fuseau_sans_changer_l_heure():
    assert en_utc(datetime(2026, 11, 30, 23, 30)) == datetime(2026, 11, 30, 23, 30, tzinfo=UTC)


def test_ca_par_mois_regroupe_en_heure_de_paris():
    ventes = [
        (datetime(2026, 11, 13, 9, 50), Decimal("5212.00")),
        (datetime(2026, 11, 30, 23, 30), Decimal("899.00")),   # 1er décembre, 0 h 30 à Paris
        (datetime(2026, 12, 2, 10, 0), Decimal("159.00")),
    ]
    assert ca_par_mois(ventes) == [
        {"mois": "2026-11", "nb_ventes": 1, "ca_ht": Decimal("5212.00")},
        {"mois": "2026-12", "nb_ventes": 2, "ca_ht": Decimal("1058.00")},
    ]


def test_ca_par_mois_sans_vente():
    assert ca_par_mois([]) == []
