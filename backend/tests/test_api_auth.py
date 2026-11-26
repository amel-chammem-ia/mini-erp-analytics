"""Tests de la connexion et des droits par l'API (épisode 10).

À lancer dans le conteneur :  docker compose exec api pytest
"""
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.creer_admin import creer_administrateur
from app.models import Utilisateur
from app.securite import creer_jeton, verifier_mot_de_passe

from .conftest import MOT_DE_PASSE, SECRET_DE_TEST

MESSAGE = "E-mail ou mot de passe incorrect"


def se_connecter(client, email, mot_de_passe=MOT_DE_PASSE):
    return client.post("/api/auth/connexion", json={"email": email, "mot_de_passe": mot_de_passe})


def entete(jeton):
    return {"Authorization": f"Bearer {jeton}"}


def modifier_compte(engine, compte_id, **champs):
    with Session(engine) as session:
        compte = session.get(Utilisateur, compte_id)
        for champ, valeur in champs.items():
            setattr(compte, champ, valeur)
        session.commit()


# Connexion -------------------------------------------------------------------
def test_connexion_reussie_puis_moi(anonyme, creer_compte):
    creer_compte("vendeur", "lea@exemple.fr")
    reponse = se_connecter(anonyme, "lea@exemple.fr")
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["token_type"] == "bearer" and corps["expire_dans"] == 1800

    moi = anonyme.get("/api/auth/moi", headers=entete(corps["access_token"])).json()
    assert moi["email"] == "lea@exemple.fr" and moi["role"] == "vendeur"
    assert "ventes:valider" in moi["droits"] and "utilisateurs:gerer" not in moi["droits"]
    assert "mot_de_passe_hache" not in moi


def test_email_insensible_a_la_casse(anonyme, creer_compte):
    creer_compte("vendeur", "lea@exemple.fr")
    assert se_connecter(anonyme, "  Lea@Exemple.FR ").status_code == 200


def test_mauvais_mot_de_passe_et_email_inconnu_meme_reponse(anonyme, creer_compte):
    creer_compte("vendeur", "lea@exemple.fr")
    mauvais = se_connecter(anonyme, "lea@exemple.fr", "pas-le-bon-mot-de-passe")
    inconnu = se_connecter(anonyme, "personne@exemple.fr")
    assert mauvais.status_code == inconnu.status_code == 401
    assert mauvais.json() == inconnu.json() == {"detail": MESSAGE}


def test_compte_desactive_ne_peut_pas_se_connecter(anonyme, creer_compte):
    creer_compte("vendeur", "lea@exemple.fr", actif=False)
    reponse = se_connecter(anonyme, "lea@exemple.fr")
    assert reponse.status_code == 401 and reponse.json() == {"detail": MESSAGE}


def test_trop_de_tentatives(anonyme, creer_compte):
    creer_compte("vendeur", "lea@exemple.fr")
    for _ in range(5):
        assert se_connecter(anonyme, "lea@exemple.fr", "essai-au-hasard").status_code == 401
    # Même avec le bon mot de passe : le compte est bloqué pendant 15 minutes.
    assert se_connecter(anonyme, "lea@exemple.fr").status_code == 429


# Jeton -------------------------------------------------------------------------
def test_sans_jeton_401(anonyme):
    reponse = anonyme.get("/api/clients")
    assert reponse.status_code == 401
    assert reponse.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("jeton", ["abc", "a.b.c", creer_jeton(1, "un-autre-secret-de-plus-de-32-caracteres")])
def test_jeton_invalide_401(anonyme, creer_compte, jeton):
    creer_compte("administrateur")
    assert anonyme.get("/api/clients", headers=entete(jeton)).status_code == 401


def test_jeton_expire_401(anonyme, creer_compte):
    compte_id = creer_compte("administrateur")
    jeton = creer_jeton(compte_id, SECRET_DE_TEST, maintenant=datetime.now(timezone.utc) - timedelta(hours=1))
    assert anonyme.get("/api/clients", headers=entete(jeton)).status_code == 401


def test_desactivation_immediate(anonyme, engine, creer_compte):
    compte_id = creer_compte("commercial", "paul@exemple.fr")
    jeton = se_connecter(anonyme, "paul@exemple.fr").json()["access_token"]
    assert anonyme.get("/api/clients", headers=entete(jeton)).status_code == 200
    modifier_compte(engine, compte_id, actif=False)
    assert anonyme.get("/api/clients", headers=entete(jeton)).status_code == 401


def test_changement_de_role_immediat(anonyme, engine, creer_compte):
    compte_id = creer_compte("commercial", "paul@exemple.fr")
    jeton = se_connecter(anonyme, "paul@exemple.fr").json()["access_token"]
    assert anonyme.get("/api/clients", headers=entete(jeton)).status_code == 200
    modifier_compte(engine, compte_id, role="magasinier")
    assert anonyme.get("/api/clients", headers=entete(jeton)).status_code == 403


# Droits par rôle ---------------------------------------------------------------
NOUVEAU_CLIENT = {"nom": "Atelier Test", "email": "test@atelier.example", "numero_tva": "FR00000000001"}
NOUVEAU_PRODUIT = {"reference": "P-TEST", "nom": "Clavier", "categorie": "Accessoires", "prix_ht": "39.90"}


@pytest.mark.parametrize(("role", "methode", "url", "corps", "attendu"), [
    ("commercial", "post", "/api/clients", NOUVEAU_CLIENT, 201),
    ("vendeur", "post", "/api/clients", NOUVEAU_CLIENT, 403),
    ("magasinier", "get", "/api/clients", None, 403),
    ("vendeur", "get", "/api/produits", None, 200),
    ("vendeur", "post", "/api/produits", NOUVEAU_PRODUIT, 403),
    ("magasinier", "post", "/api/produits", NOUVEAU_PRODUIT, 201),
    ("commercial", "get", "/api/statistiques/ca-par-mois", None, 403),
    ("manager", "get", "/api/statistiques/ca-par-mois", None, 200),
    ("dirigeant", "get", "/api/utilisateurs", None, 403),
])
def test_droits_par_role(anonyme, connecter, role, methode, url, corps, attendu):
    reponse = anonyme.request(methode, url, json=corps, headers=connecter(role))
    assert reponse.status_code == attendu, reponse.text
    if attendu == 403:
        assert reponse.json() == {"detail": "Votre rôle ne permet pas cette action"}


def test_seul_l_administrateur_supprime_un_client(anonyme, api, connecter, nouveau_client):
    client = nouveau_client()
    assert anonyme.delete(f"/api/clients/{client['id']}", headers=connecter("commercial")).status_code == 403
    assert api.delete(f"/api/clients/{client['id']}").status_code == 204


# Gestion des comptes -----------------------------------------------------------
def test_creer_un_compte_puis_se_connecter(api, anonyme):
    reponse = api.post("/api/utilisateurs", json={"email": "Nina@Exemple.fr", "nom": "Nina Martin",
                                                  "role": "magasinier", "mot_de_passe": "Hiver-au-depot-2026"})
    assert reponse.status_code == 201
    assert reponse.json()["email"] == "nina@exemple.fr"
    assert "mot_de_passe" not in reponse.text  # ni le mot de passe, ni son empreinte
    assert se_connecter(anonyme, "nina@exemple.fr", "Hiver-au-depot-2026").status_code == 200


def test_mot_de_passe_trop_court_refuse(api):
    reponse = api.post("/api/utilisateurs", json={"email": "nina@exemple.fr", "nom": "Nina",
                                                  "role": "magasinier", "mot_de_passe": "court"})
    assert reponse.status_code == 422


def test_role_inconnu_refuse(api):
    reponse = api.post("/api/utilisateurs", json={"email": "nina@exemple.fr", "nom": "Nina",
                                                  "role": "stagiaire", "mot_de_passe": "Hiver-au-depot-2026"})
    assert reponse.status_code == 422


def test_email_de_compte_en_double(api, creer_compte):
    creer_compte("vendeur", "lea@exemple.fr")
    reponse = api.post("/api/utilisateurs", json={"email": "lea@exemple.fr", "nom": "Léa",
                                                  "role": "vendeur", "mot_de_passe": "Hiver-au-depot-2026"})
    assert reponse.status_code == 409


def test_changer_le_mot_de_passe(api, anonyme, engine, creer_compte):
    compte_id = creer_compte("vendeur", "lea@exemple.fr")
    reponse = api.patch(f"/api/utilisateurs/{compte_id}", json={"mot_de_passe": "Nouveau-mot-de-passe-2026"})
    assert reponse.status_code == 200
    assert se_connecter(anonyme, "lea@exemple.fr").status_code == 401
    assert se_connecter(anonyme, "lea@exemple.fr", "Nouveau-mot-de-passe-2026").status_code == 200
    with Session(engine) as session:
        assert verifier_mot_de_passe("Nouveau-mot-de-passe-2026", session.get(Utilisateur, compte_id).mot_de_passe_hache)


def test_l_administrateur_ne_peut_pas_se_retirer_ses_droits(api):
    moi = api.get("/api/auth/moi").json()
    for changement in ({"role": "vendeur"}, {"actif": False}):
        assert api.patch(f"/api/utilisateurs/{moi['id']}", json=changement).status_code == 409


def test_lister_les_comptes(api, creer_compte):
    creer_compte("vendeur", "lea@exemple.fr")
    corps = api.get("/api/utilisateurs").json()
    assert corps["total"] == 2
    assert all("mot_de_passe_hache" not in compte for compte in corps["items"])


# Premier administrateur (python -m app.creer_admin) ----------------------------
def test_creer_le_premier_administrateur(engine):
    with Session(engine) as session:
        admin = creer_administrateur(session, "Admin@Entreprise.example", "Amel", "Un-mot-de-passe-solide")
        assert admin.role == "administrateur" and admin.email == "admin@entreprise.example"
        assert verifier_mot_de_passe("Un-mot-de-passe-solide", admin.mot_de_passe_hache)
        with pytest.raises(ValueError, match="déjà"):
            creer_administrateur(session, "admin@entreprise.example", "Amel", "Un-mot-de-passe-solide")
        with pytest.raises(ValidationError):
            creer_administrateur(session, "autre@entreprise.example", "Amel", "court")
