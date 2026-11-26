"""Routes /api/ventes : commandes, validation et facture PDF (épisode 11, US-04 et US-05).

Cycle de vie d'une vente :
    brouillon ──valider──▶ validée (stock sorti, numéro de facture attribué, plus modifiable)
        └─────annuler──▶ annulée
Une vente validée ne s'annule pas : il faudrait une facture d'avoir (non couvert ici).
"""
import secrets
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from ..acces import autoriser
from ..config import get_settings
from ..facture_pdf import FactureDocument, LigneFacture, Partie, generer_facture_pdf
from ..models import Client, CompteurFacture, LigneVente, MouvementStock, Produit, Vente
from ..montants import LigneMontant, calculer_totaux, format_numero_facture
from ..schemas import Page, StatutVente, VenteCreation, VenteDetail, VenteResume
from ..temps import heure_metier
from .commun import TAILLE_MAX, TAILLE_PAR_DEFAUT, SessionDep, paginer

router = APIRouter(prefix="/api/ventes", tags=["Ventes"])


def maintenant_utc() -> datetime:
    """La base enregistre des dates UTC sans fuseau (épisode 9)."""
    return datetime.now(UTC).replace(tzinfo=None)


def charger(session, vente_id: int) -> Vente:
    vente = session.scalar(select(Vente).where(Vente.id == vente_id)
                           .options(selectinload(Vente.lignes).selectinload(LigneVente.produit),
                                    selectinload(Vente.client)))
    if vente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vente introuvable")
    return vente


def lignes_triees(vente: Vente) -> list[LigneVente]:
    return sorted(vente.lignes, key=lambda ligne: ligne.id or 0)


def montants(vente: Vente) -> list[LigneMontant]:
    return [LigneMontant(ligne.quantite, ligne.prix_unitaire_ht, ligne.taux_tva) for ligne in lignes_triees(vente)]


def appliquer_totaux(vente: Vente) -> None:
    totaux = calculer_totaux(montants(vente))
    vente.total_ht, vente.total_tva, vente.total_ttc = totaux.total_ht, totaux.total_tva, totaux.total_ttc


def en_detail(vente: Vente) -> dict:
    totaux = calculer_totaux(montants(vente))
    lignes = [{"produit_id": ligne.produit_id, "reference": ligne.produit.reference, "designation": ligne.produit.nom,
               "quantite": ligne.quantite, "prix_unitaire_ht": ligne.prix_unitaire_ht, "taux_tva": ligne.taux_tva,
               "montant_ht": montant.montant_ht}
              for ligne, montant in zip(lignes_triees(vente), montants(vente), strict=True)]
    return {**VenteResume.model_validate(vente).model_dump(), "client_nom": vente.client.nom, "lignes": lignes,
            "tva_par_taux": [{"taux": t.taux, "base_ht": t.base_ht, "montant_tva": t.montant_tva}
                             for t in totaux.tva_par_taux]}


def verifier_client(session, client_id: int) -> None:
    if session.get(Client, client_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client introuvable")


def construire_lignes(session, donnees: VenteCreation) -> list[LigneVente]:
    """Prix et taux de TVA copiés depuis le catalogue : la vente garde le prix du jour de la commande."""
    ids = [ligne.produit_id for ligne in donnees.lignes]
    produits = {p.id: p for p in session.scalars(select(Produit).where(Produit.id.in_(ids)))}
    inconnus = [str(i) for i in ids if i not in produits]
    if inconnus:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Produit introuvable : {', '.join(inconnus)}")
    archives = [produits[i].reference for i in ids if not produits[i].actif]
    if archives:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Produit archivé, impossible à vendre : {', '.join(archives)}")
    return [LigneVente(produit_id=ligne.produit_id, quantite=ligne.quantite,
                       prix_unitaire_ht=produits[ligne.produit_id].prix_ht,
                       taux_tva=produits[ligne.produit_id].taux_tva) for ligne in donnees.lignes]


def exiger_brouillon(vente: Vente) -> None:
    if vente.statut == "validee":
        raise HTTPException(status.HTTP_409_CONFLICT, "Une vente validée n'est plus modifiable")
    if vente.statut == "annulee":
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette vente est annulée")


@router.get("", response_model=Page[VenteResume], summary="Lister les ventes",
            dependencies=[autoriser("ventes:lire")])
def lister_ventes(
    session: SessionDep,
    statut: StatutVente | None = None,
    client_id: Annotated[int | None, Query(ge=1)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    taille: Annotated[int, Query(ge=1, le=TAILLE_MAX)] = TAILLE_PAR_DEFAUT,
):
    requete = select(Vente).order_by(Vente.date_vente.desc(), Vente.id.desc())
    if statut:
        requete = requete.where(Vente.statut == statut)
    if client_id:
        requete = requete.where(Vente.client_id == client_id)
    items, total = paginer(session, requete, page, taille)
    return {"items": items, "total": total, "page": page, "taille": taille}


@router.get("/{vente_id}", response_model=VenteDetail, summary="Détail d'une vente",
            dependencies=[autoriser("ventes:lire")])
def lire_vente(vente_id: int, session: SessionDep):
    return en_detail(charger(session, vente_id))


@router.post("", response_model=VenteDetail, status_code=status.HTTP_201_CREATED,
             summary="Enregistrer une commande (brouillon)", dependencies=[autoriser("ventes:ecrire")])
def creer_vente(donnees: VenteCreation, session: SessionDep):
    verifier_client(session, donnees.client_id)
    maintenant = maintenant_utc()
    vente = Vente(numero=f"TMP-{secrets.token_hex(6)}", client_id=donnees.client_id, date_vente=maintenant,
                  statut="brouillon", lignes=construire_lignes(session, donnees))
    appliquer_totaux(vente)
    session.add(vente)
    session.flush()  # attribue l'identifiant, qui donne le numéro de commande
    vente.numero = f"V-{heure_metier(maintenant).year}-{vente.id:04d}"
    session.commit()
    return en_detail(charger(session, vente.id))


@router.put("/{vente_id}", response_model=VenteDetail, summary="Modifier un brouillon",
            dependencies=[autoriser("ventes:ecrire")])
def modifier_vente(vente_id: int, donnees: VenteCreation, session: SessionDep):
    vente = charger(session, vente_id)
    exiger_brouillon(vente)
    verifier_client(session, donnees.client_id)
    nouvelles = construire_lignes(session, donnees)
    vente.client_id = donnees.client_id
    vente.lignes.clear()
    session.flush()  # supprime les anciennes lignes avant d'insérer les nouvelles (unicité vente + produit)
    vente.lignes.extend(nouvelles)
    appliquer_totaux(vente)
    session.commit()
    session.expire_all()
    return en_detail(charger(session, vente_id))


@router.post("/{vente_id}/valider", response_model=VenteDetail, summary="Valider et facturer",
             dependencies=[autoriser("ventes:valider")])
def valider_vente(vente_id: int, session: SessionDep):
    """En une seule transaction : sortie du stock, numéro de facture, statut validé.
    Si une étape échoue, rien n'est enregistré, et aucun numéro de facture n'est consommé."""
    vente = charger(session, vente_id)
    exiger_brouillon(vente)

    # 1. Le stock : chaque sortie n'a lieu que si le stock suffit (UPDATE conditionnel, sûr à plusieurs).
    ruptures = []
    for ligne in lignes_triees(vente):
        resultat = session.execute(
            update(Produit)
            .where(Produit.id == ligne.produit_id, Produit.stock_actuel >= ligne.quantite)
            .values(stock_actuel=Produit.stock_actuel - ligne.quantite)
            .execution_options(synchronize_session=False))
        if resultat.rowcount != 1:
            ruptures.append(ligne)
    if ruptures:
        session.rollback()
        details = ", ".join(f"{r.produit.reference} (demandé {r.quantite}, disponible {r.produit.stock_actuel})"
                            for r in ruptures)
        raise HTTPException(status.HTTP_409_CONFLICT, f"Stock insuffisant : {details}")

    # 2. Le numéro de facture : compteur de l'année verrouillé jusqu'à la fin de la transaction.
    maintenant = maintenant_utc()
    annee = heure_metier(maintenant).year
    compteur = session.get(CompteurFacture, annee, with_for_update=True)
    if compteur is None:
        compteur = CompteurFacture(annee=annee, dernier_numero=0)
        session.add(compteur)
    compteur.dernier_numero += 1

    # 3. La vente est figée.
    vente.numero_facture = format_numero_facture(annee, compteur.dernier_numero)
    vente.facturee_le = maintenant
    vente.statut = "validee"
    appliquer_totaux(vente)
    for ligne in lignes_triees(vente):
        session.add(MouvementStock(produit_id=ligne.produit_id, type_mouvement="sortie", quantite=ligne.quantite,
                                   date_mouvement=maintenant, vente_id=vente.id,
                                   commentaire=f"Facture {vente.numero_facture}"))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Une autre validation est en cours : réessayez dans un instant") from None
    session.expire_all()
    return en_detail(charger(session, vente_id))


@router.post("/{vente_id}/annuler", response_model=VenteDetail, summary="Annuler un brouillon",
             dependencies=[autoriser("ventes:ecrire")])
def annuler_vente(vente_id: int, session: SessionDep):
    vente = charger(session, vente_id)
    if vente.statut == "validee":
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Une facture validée ne s'annule pas : il faut émettre une facture d'avoir")
    exiger_brouillon(vente)
    vente.statut = "annulee"
    session.commit()
    return en_detail(charger(session, vente_id))


@router.get("/{vente_id}/facture.pdf", summary="Télécharger la facture PDF",
            response_class=Response, responses={200: {"content": {"application/pdf": {}}}},
            dependencies=[autoriser("ventes:lire")])
def facture_pdf(vente_id: int, session: SessionDep):
    vente = charger(session, vente_id)
    if vente.statut != "validee" or vente.numero_facture is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "La facture n'existe qu'une fois la vente validée")
    reglages = get_settings()
    client = vente.client
    document = FactureDocument(
        numero=vente.numero_facture,
        date_emission=heure_metier(vente.facturee_le).date(),
        numero_commande=vente.numero,
        emetteur=Partie(reglages.entreprise_nom,
                        tuple(x.strip() for x in reglages.entreprise_adresse.split("|") if x.strip()),
                        reglages.entreprise_tva or None, reglages.entreprise_siret or None),
        client=Partie(client.nom, (client.ville,) if client.ville else (), client.numero_tva, email=client.email),
        lignes=tuple(LigneFacture(ligne.produit.reference, ligne.produit.nom, ligne.quantite,
                                  ligne.prix_unitaire_ht, ligne.taux_tva, montant.montant_ht)
                     for ligne, montant in zip(lignes_triees(vente), montants(vente), strict=True)),
        totaux=calculer_totaux(montants(vente)),
    )
    return Response(generer_facture_pdf(document), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{vente.numero_facture}.pdf"'})
