"""Routes /api/clients : rechercher, lire, créer, modifier, supprimer (épisode 8)."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import Client, Vente
from ..schemas import ClientCreation, ClientLecture, ClientModification, Page
from .commun import (ECHAPPEMENT, TAILLE_MAX, TAILLE_PAR_DEFAUT, SessionDep, enregistrer,
                     motif_recherche, paginer)

router = APIRouter(prefix="/api/clients", tags=["Clients"])


def client_ou_404(session: Session, client_id: int) -> Client:
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client introuvable")
    return client


def verifier_unicite(session: Session, email: str | None, numero_tva: str | None,
                     sauf_id: int | None = None) -> None:
    """409 si l'e-mail ou le numéro de TVA appartient déjà à un autre client."""
    controles = (
        (Client.email, email, "Un client utilise déjà cette adresse e-mail"),
        (Client.numero_tva, numero_tva, "Un client utilise déjà ce numéro de TVA"),
    )
    for colonne, valeur, message in controles:
        if valeur is None:
            continue
        requete = select(Client.id).where(colonne == valeur)
        if sauf_id is not None:
            requete = requete.where(Client.id != sauf_id)
        if session.scalar(requete) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, message)


@router.get("", response_model=Page[ClientLecture], summary="Rechercher des clients")
def lister_clients(
    session: SessionDep,
    recherche: Annotated[str | None, Query(max_length=100, description="Nom, e-mail ou ville")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    taille: Annotated[int, Query(ge=1, le=TAILLE_MAX)] = TAILLE_PAR_DEFAUT,
):
    requete = select(Client).order_by(Client.nom, Client.id)
    if recherche and recherche.strip():
        motif = motif_recherche(recherche)
        requete = requete.where(or_(
            Client.nom.ilike(motif, escape=ECHAPPEMENT),
            Client.email.ilike(motif, escape=ECHAPPEMENT),
            Client.ville.ilike(motif, escape=ECHAPPEMENT),
        ))
    items, total = paginer(session, requete, page, taille)
    return {"items": items, "total": total, "page": page, "taille": taille}


@router.get("/{client_id}", response_model=ClientLecture, summary="Lire un client")
def lire_client(client_id: int, session: SessionDep):
    return client_ou_404(session, client_id)


@router.post("", response_model=ClientLecture, status_code=status.HTTP_201_CREATED, summary="Créer un client")
def creer_client(donnees: ClientCreation, session: SessionDep):
    verifier_unicite(session, donnees.email, donnees.numero_tva)
    client = Client(**donnees.model_dump())
    session.add(client)
    enregistrer(session, client)
    return client


@router.patch("/{client_id}", response_model=ClientLecture, summary="Modifier un client")
def modifier_client(client_id: int, donnees: ClientModification, session: SessionDep):
    client = client_ou_404(session, client_id)
    changements = donnees.model_dump(exclude_unset=True)
    verifier_unicite(session, changements.get("email"), changements.get("numero_tva"), sauf_id=client_id)
    for champ, valeur in changements.items():
        setattr(client, champ, valeur)
    enregistrer(session, client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer un client")
def supprimer_client(client_id: int, session: SessionDep) -> Response:
    """Un client qui a des ventes ne se supprime pas : ses factures doivent rester lisibles."""
    client = client_ou_404(session, client_id)
    if session.scalar(select(Vente.id).where(Vente.client_id == client_id).limit(1)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ce client a des ventes : il ne peut pas être supprimé")
    session.delete(client)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
