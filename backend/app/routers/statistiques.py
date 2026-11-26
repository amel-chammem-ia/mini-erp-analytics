"""Routes /api/statistiques : les premiers indicateurs (épisode 9, droits : épisode 10)."""
from fastapi import APIRouter
from sqlalchemy import select

from ..acces import autoriser
from ..models import Vente
from ..schemas import CaMois
from ..statistiques import ca_par_mois
from .commun import SessionDep

router = APIRouter(prefix="/api/statistiques", tags=["Statistiques"])


@router.get("/ca-par-mois", response_model=list[CaMois], summary="Chiffre d'affaires HT par mois",
            dependencies=[autoriser("statistiques:lire")])
def lire_ca_par_mois(session: SessionDep):
    """Ventes validées uniquement, regroupées par mois en heure de Paris."""
    ventes = session.execute(
        select(Vente.date_vente, Vente.total_ht).where(Vente.statut == "validee")
    ).all()
    return ca_par_mois(ventes)
