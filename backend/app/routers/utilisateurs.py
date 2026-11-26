"""Routes /api/utilisateurs : l'administrateur gère les comptes et les rôles (épisode 10, US-09)."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from ..acces import autoriser
from ..models import Utilisateur
from ..schemas import Page, UtilisateurCreation, UtilisateurLecture, UtilisateurModification
from ..securite import hacher_mot_de_passe
from .commun import TAILLE_MAX, TAILLE_PAR_DEFAUT, SessionDep, enregistrer, paginer

# Toutes les routes de ce fichier exigent le droit utilisateurs:gerer.
router = APIRouter(prefix="/api/utilisateurs", tags=["Utilisateurs"],
                   dependencies=[autoriser("utilisateurs:gerer")])

Administrateur = Annotated[Utilisateur, autoriser("utilisateurs:gerer")]


@router.get("", response_model=Page[UtilisateurLecture], summary="Lister les comptes")
def lister_utilisateurs(
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    taille: Annotated[int, Query(ge=1, le=TAILLE_MAX)] = TAILLE_PAR_DEFAUT,
):
    requete = select(Utilisateur).order_by(Utilisateur.nom, Utilisateur.id)
    items, total = paginer(session, requete, page, taille)
    return {"items": items, "total": total, "page": page, "taille": taille}


@router.post("", response_model=UtilisateurLecture, status_code=status.HTTP_201_CREATED,
             summary="Créer un compte")
def creer_utilisateur(donnees: UtilisateurCreation, session: SessionDep):
    if session.scalar(select(Utilisateur.id).where(Utilisateur.email == donnees.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Un compte utilise déjà cette adresse e-mail")
    utilisateur = Utilisateur(email=donnees.email, nom=donnees.nom, role=donnees.role,
                              mot_de_passe_hache=hacher_mot_de_passe(donnees.mot_de_passe))
    session.add(utilisateur)
    enregistrer(session, utilisateur)
    return utilisateur


@router.patch("/{utilisateur_id}", response_model=UtilisateurLecture, summary="Modifier un compte")
def modifier_utilisateur(utilisateur_id: int, donnees: UtilisateurModification,
                         session: SessionDep, admin: Administrateur):
    utilisateur = session.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compte introuvable")
    changements = donnees.model_dump(exclude_unset=True)

    # Garde-fou : un administrateur ne peut pas se retirer ses propres droits ni se désactiver,
    # sinon l'application pourrait se retrouver sans aucun administrateur.
    if utilisateur.id == admin.id and (
        changements.get("actif") is False or changements.get("role", "administrateur") != "administrateur"
    ):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Vous ne pouvez pas retirer vos propres droits d'administrateur")

    if "mot_de_passe" in changements:
        utilisateur.mot_de_passe_hache = hacher_mot_de_passe(changements.pop("mot_de_passe"))
    for champ, valeur in changements.items():
        setattr(utilisateur, champ, valeur)
    enregistrer(session, utilisateur)
    return utilisateur
