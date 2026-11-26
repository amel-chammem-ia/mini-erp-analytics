"""Dates et fuseaux horaires (épisode 9).

La base enregistre les dates en UTC (SYSUTCDATETIME). C'est la bonne pratique : une seule
heure de référence, quel que soit le serveur. Mais tout ce qui est « métier » (le mois d'un
chiffre d'affaires, une date affichée) se lit en heure de Paris.

Le bug corrigé à l'épisode 9 : le chiffre d'affaires était regroupé par mois UTC.
Une vente du 1er décembre à 0 h 30 (heure de Paris) est enregistrée le 30 novembre à
23 h 30 UTC : elle était comptée en novembre.
"""
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

FUSEAU_METIER = ZoneInfo("Europe/Paris")


def en_utc(moment: datetime) -> datetime:
    """Une date lue en base (sans fuseau, mais en UTC) devient une date UTC explicite."""
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def heure_metier(moment: datetime) -> datetime:
    """La même date, vue depuis Paris (heure d'hiver ou d'été selon la saison)."""
    return en_utc(moment).astimezone(FUSEAU_METIER)


def mois_metier(moment: datetime) -> str:
    """Le mois comptable « AAAA-MM » d'une date enregistrée en UTC."""
    return heure_metier(moment).strftime("%Y-%m")
