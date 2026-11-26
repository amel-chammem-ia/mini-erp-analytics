"""Contrôle d'accès des routes : qui est connecté, et a-t-il le droit (épisode 10).

- 401 Unauthorized : on ne sait pas qui vous êtes (pas de jeton, jeton expiré ou falsifié).
- 403 Forbidden : on sait qui vous êtes, mais votre rôle ne permet pas cette action.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings
from .droits import a_le_droit, verifier_droit
from .models import Utilisateur
from .routers.commun import SessionDep
from .securite import JetonInvalide, lire_jeton

# auto_error=False : on renvoie nous-mêmes un 401 propre quand l'en-tête manque.
porteur = HTTPBearer(auto_error=False, description="Jeton obtenu sur POST /api/auth/connexion")


def non_authentifie(detail: str = "Connexion requise") -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"})


def utilisateur_courant(
    session: SessionDep,
    identifiants: Annotated[HTTPAuthorizationCredentials | None, Depends(porteur)],
) -> Utilisateur:
    if identifiants is None:
        raise non_authentifie()
    try:
        utilisateur_id = lire_jeton(identifiants.credentials, get_settings().jwt_secret)
    except JetonInvalide:
        raise non_authentifie("Session expirée ou invalide : reconnectez-vous") from None
    # Le rôle et le statut sont relus en base : une désactivation s'applique tout de suite.
    utilisateur = session.get(Utilisateur, utilisateur_id)
    if utilisateur is None or not utilisateur.actif:
        raise non_authentifie("Session expirée ou invalide : reconnectez-vous")
    return utilisateur


UtilisateurCourant = Annotated[Utilisateur, Depends(utilisateur_courant)]


def autoriser(droit: str):
    """Dépendance à poser sur une route : dependencies=[autoriser("clients:ecrire")]."""
    verifier_droit(droit)  # nom de droit inconnu : erreur dès l'import du module

    def controler(utilisateur: UtilisateurCourant) -> Utilisateur:
        if not a_le_droit(utilisateur.role, droit):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Votre rôle ne permet pas cette action")
        return utilisateur

    return Depends(controler)
