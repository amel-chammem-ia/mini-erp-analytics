"""Outils partagés par les routes : pagination, recherche et enregistrement."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_session

SessionDep = Annotated[Session, Depends(get_session)]

TAILLE_PAR_DEFAUT = 20  # le cahier des charges (US-02) demande des résultats paginés par 20
TAILLE_MAX = 100
ECHAPPEMENT = "\\"


def motif_recherche(texte: str) -> str:
    """Transforme la saisie en motif LIKE '%texte%' : %, _ et [ tapés par l'utilisateur restent des caractères."""
    echappe = texte.strip()
    for caractere in (ECHAPPEMENT, "%", "_", "["):
        echappe = echappe.replace(caractere, ECHAPPEMENT + caractere)
    return f"%{echappe}%"


def paginer(session: Session, requete: Select, page: int, taille: int) -> tuple[list, int]:
    """Renvoie les éléments de la page demandée et le nombre total de résultats.

    La requête doit être triée (ORDER BY) : SQL Server l'exige pour OFFSET / FETCH.
    """
    total = session.scalar(select(func.count()).select_from(requete.order_by(None).subquery()))
    items = session.scalars(requete.offset((page - 1) * taille).limit(taille)).all()
    return list(items), total or 0


def enregistrer(session: Session, objet) -> None:
    """Valide la transaction ; une contrainte UNIQUE violée devient une erreur 409 claire."""
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette donnée existe déjà") from None
    session.refresh(objet)
