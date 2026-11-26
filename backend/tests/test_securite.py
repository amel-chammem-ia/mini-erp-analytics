"""Tests du module securite : hachage, jetons, limite de tentatives (épisode 10).

Aucun serveur ni aucune base : ces tests tournent en une seconde.
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app import securite
from app.securite import (DUREE_JETON, JetonInvalide, LimiteurTentatives, creer_jeton,
                          hacher_mot_de_passe, lire_jeton, verifier_mot_de_passe)

SECRET = "secret-de-test-assez-long-pour-hs256-0123456789"


@pytest.fixture(autouse=True)
def scrypt_rapide(monkeypatch):
    """Paramètres allégés pour les tests ; ils sont lus dans l'empreinte, la vérification suit."""
    monkeypatch.setattr(securite, "SCRYPT_N", 2**10)


# Mots de passe -------------------------------------------------------------
def test_le_mot_de_passe_n_apparait_pas_dans_l_empreinte():
    empreinte = hacher_mot_de_passe("Printemps-2026!")
    assert "Printemps" not in empreinte
    assert empreinte.startswith("scrypt$1024$8$1$")


def test_bon_et_mauvais_mot_de_passe():
    empreinte = hacher_mot_de_passe("Printemps-2026!")
    assert verifier_mot_de_passe("Printemps-2026!", empreinte)
    assert not verifier_mot_de_passe("printemps-2026!", empreinte)
    assert not verifier_mot_de_passe("", empreinte)


def test_deux_comptes_meme_mot_de_passe_empreintes_differentes():
    # Le sel aléatoire empêche de repérer les mots de passe identiques dans la base.
    assert hacher_mot_de_passe("Printemps-2026!") != hacher_mot_de_passe("Printemps-2026!")


def test_les_parametres_sont_lus_dans_l_empreinte(monkeypatch):
    ancienne = hacher_mot_de_passe("Printemps-2026!")
    monkeypatch.setattr(securite, "SCRYPT_N", 2**11)  # on durcit les paramètres
    assert verifier_mot_de_passe("Printemps-2026!", ancienne)  # les anciens comptes marchent encore


@pytest.mark.parametrize("empreinte", ["", "texte-en-clair", "bcrypt$x$y$z$a$b", "scrypt$abc$8$1$AA$AA"])
def test_empreinte_illisible_ne_correspond_jamais(empreinte):
    assert not verifier_mot_de_passe("texte-en-clair", empreinte)


# Jetons ----------------------------------------------------------------------
def test_jeton_aller_retour():
    assert lire_jeton(creer_jeton(42, SECRET), SECRET) == 42


def test_jeton_expire():
    il_y_a_une_heure = datetime.now(timezone.utc) - timedelta(hours=1)
    jeton = creer_jeton(42, SECRET, maintenant=il_y_a_une_heure)
    with pytest.raises(JetonInvalide):
        lire_jeton(jeton, SECRET)


def test_jeton_valable_trente_minutes():
    maintenant = datetime.now(timezone.utc)
    charge = jwt.decode(creer_jeton(42, SECRET, maintenant), SECRET, algorithms=["HS256"])
    assert charge["exp"] - charge["iat"] == DUREE_JETON.total_seconds() == 1800


def test_jeton_signe_avec_un_autre_secret():
    jeton = creer_jeton(42, "un-autre-secret-tout-aussi-long-0123456789")
    with pytest.raises(JetonInvalide):
        lire_jeton(jeton, SECRET)


def test_jeton_modifie_a_la_main():
    # Quelqu'un remplace l'identifiant 42 par 1 (l'administrateur) sans connaître le secret.
    entete, _, signature = creer_jeton(42, SECRET).split(".")
    faux = jwt.encode({"sub": "1", "iat": 0, "exp": 9999999999}, "cle-devinee-par-l-attaquant-0123456789", algorithm="HS256")
    falsifie = ".".join([entete, faux.split(".")[1], signature])
    with pytest.raises(JetonInvalide):
        lire_jeton(falsifie, SECRET)


def test_jeton_sans_signature_refuse():
    # L'attaque "alg: none" : un jeton non signé ne doit jamais être accepté.
    non_signe = jwt.encode({"sub": "1", "iat": 0, "exp": 9999999999}, key=None, algorithm="none")
    with pytest.raises(JetonInvalide):
        lire_jeton(non_signe, SECRET)


@pytest.mark.parametrize("jeton", ["", "abc", "a.b.c"])
def test_jeton_mal_forme(jeton):
    with pytest.raises(JetonInvalide):
        lire_jeton(jeton, SECRET)


@pytest.mark.parametrize("secret", ["", "court", "x" * 31])
def test_secret_absent_ou_trop_court(secret):
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        creer_jeton(42, secret)


# Limite des tentatives -------------------------------------------------------
def test_blocage_apres_cinq_echecs_puis_deblocage():
    limiteur = LimiteurTentatives(max_echecs=5, fenetre_secondes=900)
    for seconde in range(5):
        assert not limiteur.est_bloque("lea@exemple.fr", maintenant=seconde)
        limiteur.noter_echec("lea@exemple.fr", maintenant=seconde)
    assert limiteur.est_bloque("lea@exemple.fr", maintenant=10)
    assert not limiteur.est_bloque("paul@exemple.fr", maintenant=10)  # les autres comptes ne sont pas touchés
    assert not limiteur.est_bloque("lea@exemple.fr", maintenant=905)  # 15 minutes plus tard


def test_une_connexion_reussie_remet_le_compteur_a_zero():
    limiteur = LimiteurTentatives(max_echecs=2, fenetre_secondes=900)
    limiteur.noter_echec("lea@exemple.fr", maintenant=0)
    limiteur.reinitialiser("lea@exemple.fr")
    limiteur.noter_echec("lea@exemple.fr", maintenant=1)
    assert not limiteur.est_bloque("lea@exemple.fr", maintenant=2)
