"""Routes /api/auth : se connecter et savoir qui l'on est (épisode 10)."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..acces import UtilisateurCourant
from ..config import get_settings
from ..droits import droits_du_role
from ..models import Utilisateur
from ..schemas import Connexion, Jeton, Moi, UtilisateurLecture
from ..securite import (DUREE_JETON, LimiteurTentatives, creer_jeton, simuler_verification,
                        verifier_mot_de_passe)
from .commun import SessionDep

router = APIRouter(prefix="/api/auth", tags=["Connexion"])

# Même message que l'e-mail existe ou non : on ne révèle pas quels comptes existent.
IDENTIFIANTS_INCORRECTS = "E-mail ou mot de passe incorrect"

limiteur = LimiteurTentatives(max_echecs=5, fenetre_secondes=15 * 60)


@router.post("/connexion", response_model=Jeton, summary="Se connecter")
def se_connecter(donnees: Connexion, session: SessionDep):
    """E-mail et mot de passe en échange d'un jeton valable 30 minutes."""
    if limiteur.est_bloque(donnees.email):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "Trop de tentatives : réessayez dans quelques minutes")

    utilisateur = session.scalar(select(Utilisateur).where(Utilisateur.email == donnees.email))
    if utilisateur is None:
        simuler_verification()  # même durée de calcul qu'avec un vrai compte
        valide = False
    else:
        valide = verifier_mot_de_passe(donnees.mot_de_passe, utilisateur.mot_de_passe_hache)

    if not valide or not utilisateur.actif:
        limiteur.noter_echec(donnees.email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, IDENTIFIANTS_INCORRECTS,
                            headers={"WWW-Authenticate": "Bearer"})

    limiteur.reinitialiser(donnees.email)
    jeton = creer_jeton(utilisateur.id, get_settings().jwt_secret)
    return {"access_token": jeton, "expire_dans": int(DUREE_JETON.total_seconds())}


@router.get("/moi", response_model=Moi, summary="Mon compte et mes droits")
def moi(utilisateur: UtilisateurCourant):
    """L'interface s'en sert pour n'afficher que les écrans autorisés (épisode 13)."""
    compte = UtilisateurLecture.model_validate(utilisateur).model_dump()
    return {**compte, "droits": droits_du_role(utilisateur.role)}
