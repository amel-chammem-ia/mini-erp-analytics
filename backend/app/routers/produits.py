"""Routes /api/produits : rechercher, lire, créer, modifier, archiver (épisode 8)."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import or_, select, true
from sqlalchemy.orm import Session

from ..models import Produit
from ..schemas import Page, ProduitCreation, ProduitLecture, ProduitModification
from .commun import (ECHAPPEMENT, TAILLE_MAX, TAILLE_PAR_DEFAUT, SessionDep, enregistrer,
                     motif_recherche, paginer)

router = APIRouter(prefix="/api/produits", tags=["Produits"])


def produit_ou_404(session: Session, produit_id: int) -> Produit:
    produit = session.get(Produit, produit_id)
    if produit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produit introuvable")
    return produit


@router.get("", response_model=Page[ProduitLecture], summary="Rechercher des produits")
def lister_produits(
    session: SessionDep,
    recherche: Annotated[str | None, Query(max_length=100, description="Référence ou nom")] = None,
    categorie: Annotated[str | None, Query(max_length=60)] = None,
    sous_le_seuil: Annotated[bool | None, Query(description="true : seulement les produits à réapprovisionner")] = None,
    inclure_archives: bool = False,
    page: Annotated[int, Query(ge=1)] = 1,
    taille: Annotated[int, Query(ge=1, le=TAILLE_MAX)] = TAILLE_PAR_DEFAUT,
):
    requete = select(Produit).order_by(Produit.reference, Produit.id)
    if not inclure_archives:
        requete = requete.where(Produit.actif == true())
    if recherche and recherche.strip():
        motif = motif_recherche(recherche)
        requete = requete.where(or_(
            Produit.reference.ilike(motif, escape=ECHAPPEMENT),
            Produit.nom.ilike(motif, escape=ECHAPPEMENT),
        ))
    if categorie:
        requete = requete.where(Produit.categorie == categorie.strip())
    if sous_le_seuil is True:
        requete = requete.where(Produit.stock_actuel < Produit.seuil_alerte)
    elif sous_le_seuil is False:
        requete = requete.where(Produit.stock_actuel >= Produit.seuil_alerte)
    items, total = paginer(session, requete, page, taille)
    return {"items": items, "total": total, "page": page, "taille": taille}


@router.get("/{produit_id}", response_model=ProduitLecture, summary="Lire un produit")
def lire_produit(produit_id: int, session: SessionDep):
    return produit_ou_404(session, produit_id)


@router.post("", response_model=ProduitLecture, status_code=status.HTTP_201_CREATED, summary="Créer un produit")
def creer_produit(donnees: ProduitCreation, session: SessionDep):
    if session.scalar(select(Produit.id).where(Produit.reference == donnees.reference)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Un produit utilise déjà cette référence")
    produit = Produit(**donnees.model_dump(), stock_actuel=0, actif=True)
    session.add(produit)
    enregistrer(session, produit)
    return produit


@router.patch("/{produit_id}", response_model=ProduitLecture, summary="Modifier un produit")
def modifier_produit(produit_id: int, donnees: ProduitModification, session: SessionDep):
    produit = produit_ou_404(session, produit_id)
    for champ, valeur in donnees.model_dump(exclude_unset=True).items():
        setattr(produit, champ, valeur)
    enregistrer(session, produit)
    return produit


@router.delete("/{produit_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Archiver un produit")
def archiver_produit(produit_id: int, session: SessionDep) -> Response:
    """Un produit ne disparaît jamais : il figure peut-être sur des factures. On l'archive."""
    produit = produit_ou_404(session, produit_id)
    produit.actif = False
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
