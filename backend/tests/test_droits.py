"""Tests de la matrice des droits (épisode 10) : chaque ligne du tableau docs/droits.md."""
import pytest

from app.droits import DROITS, ROLES, a_le_droit, droits_du_role

# (rôle, droit, autorisé ?) : les cas qui comptent le plus pour le métier.
CAS = [
    ("commercial", "clients:ecrire", True),
    ("commercial", "clients:supprimer", False),
    ("commercial", "statistiques:lire", False),
    ("vendeur", "clients:lire", True),
    ("vendeur", "clients:ecrire", False),
    ("vendeur", "ventes:valider", True),
    ("magasinier", "produits:ecrire", True),
    ("magasinier", "clients:lire", False),
    ("manager", "statistiques:lire", True),
    ("manager", "produits:ecrire", False),
    ("dirigeant", "statistiques:lire", True),
    ("dirigeant", "clients:ecrire", False),
    ("administrateur", "utilisateurs:gerer", True),
    ("dirigeant", "utilisateurs:gerer", False),
]


@pytest.mark.parametrize(("role", "droit", "attendu"), CAS)
def test_matrice(role, droit, attendu):
    assert a_le_droit(role, droit) is attendu


def test_chaque_droit_ne_cite_que_des_roles_connus():
    for droit, roles in DROITS.items():
        assert roles <= set(ROLES), droit


def test_seul_l_administrateur_gere_les_comptes():
    assert DROITS["utilisateurs:gerer"] == {"administrateur"}


def test_le_dirigeant_lit_tout():
    lectures = [droit for droit in DROITS if droit.endswith(":lire")]
    assert all(a_le_droit("dirigeant", droit) for droit in lectures)


def test_tout_le_monde_consulte_les_produits():
    assert all(a_le_droit(role, "produits:lire") for role in ROLES)


def test_droit_inconnu_refuse_bruyamment():
    with pytest.raises(KeyError):
        a_le_droit("administrateur", "client:ecrire")  # faute de frappe : « client » sans s


def test_role_inconnu_n_a_aucun_droit():
    assert droits_du_role("stagiaire") == []
    assert not a_le_droit("stagiaire", "produits:lire")
