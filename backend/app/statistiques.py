"""Indicateurs calculés à partir des ventes (épisode 9 : chiffre d'affaires par mois)."""
from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal

from .temps import mois_metier


def ca_par_mois(ventes: Iterable[tuple[datetime, Decimal]]) -> list[dict]:
    """Regroupe des ventes (date UTC, total HT) par mois, en heure de Paris.

    Renvoie une ligne par mois, triée : {"mois": "2026-12", "nb_ventes": 3, "ca_ht": Decimal}.
    """
    totaux: dict[str, list] = {}
    for date_vente, total_ht in ventes:
        ligne = totaux.setdefault(mois_metier(date_vente), [0, Decimal("0.00")])
        ligne[0] += 1
        ligne[1] += total_ht
    return [{"mois": mois, "nb_ventes": nb, "ca_ht": ca} for mois, (nb, ca) in sorted(totaux.items())]
