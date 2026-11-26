"""Calcul des montants d'une vente : HT, TVA par taux, TTC (épisode 11).

Les règles, décidées avant d'écrire le moindre prompt (voir docs/factures.md) :

1. Les montants sont des Decimal, jamais des float : en float, 0.1 + 0.2 vaut 0.30000000000000004.
2. Montant HT d'une ligne = quantité × prix unitaire HT, arrondi au centime.
3. La TVA se calcule par taux, sur le total HT de ce taux, puis s'arrondit au centime.
   (Arrondir la TVA ligne par ligne, puis additionner, peut donner un centime de plus.)
4. Arrondi commercial : 0,005 € et plus s'arrondit au centime supérieur (ROUND_HALF_UP).
5. TTC = total HT + total TVA. Les trois totaux sont donc toujours cohérents.

Ce module ne dépend ni de FastAPI ni de la base : il se teste seul.
"""
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENTIME = Decimal("0.01")
ZERO = Decimal("0.00")
CENT = Decimal("100")


def arrondir(montant: Decimal) -> Decimal:
    """Arrondi commercial au centime. Refuse les float : l'erreur serait déjà dans le nombre."""
    if not isinstance(montant, Decimal):
        raise TypeError(f"Montant attendu en Decimal, reçu {type(montant).__name__}")
    return montant.quantize(CENTIME, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class LigneMontant:
    quantite: int
    prix_unitaire_ht: Decimal
    taux_tva: Decimal

    def __post_init__(self):
        if isinstance(self.quantite, bool) or not isinstance(self.quantite, int) or self.quantite <= 0:
            raise ValueError("La quantité doit être un entier supérieur à 0")
        for nom in ("prix_unitaire_ht", "taux_tva"):
            if not isinstance(getattr(self, nom), Decimal):
                raise TypeError(f"{nom} doit être un Decimal")
        if self.prix_unitaire_ht < 0:
            raise ValueError("Le prix unitaire ne peut pas être négatif")
        if not ZERO <= self.taux_tva <= CENT:
            raise ValueError("Le taux de TVA doit être compris entre 0 et 100")

    @property
    def montant_ht(self) -> Decimal:
        return arrondir(self.prix_unitaire_ht * self.quantite)


@dataclass(frozen=True)
class LigneTva:
    taux: Decimal
    base_ht: Decimal
    montant_tva: Decimal


@dataclass(frozen=True)
class Totaux:
    total_ht: Decimal
    tva_par_taux: tuple[LigneTva, ...]
    total_tva: Decimal
    total_ttc: Decimal


def calculer_totaux(lignes: Iterable[LigneMontant]) -> Totaux:
    lignes = list(lignes)
    if not lignes:
        raise ValueError("Une vente contient au moins une ligne")
    bases: dict[Decimal, Decimal] = defaultdict(lambda: ZERO)
    for ligne in lignes:
        bases[ligne.taux_tva] += ligne.montant_ht       # Decimal("20") et Decimal("20.00") : même taux
    tva = tuple(LigneTva(taux, base, arrondir(base * taux / CENT)) for taux, base in sorted(bases.items()))
    total_ht = sum((t.base_ht for t in tva), ZERO)
    total_tva = sum((t.montant_tva for t in tva), ZERO)
    return Totaux(total_ht=total_ht, tva_par_taux=tva, total_tva=total_tva, total_ttc=total_ht + total_tva)


def format_euros(montant: Decimal) -> str:
    """1234.5 → « 1 234,50 € » (espaces insécables, pour l'affichage et la facture PDF)."""
    signe = "-" if montant < 0 else ""
    entier, decimales = f"{abs(arrondir(montant)):.2f}".split(".")
    groupes = []
    while len(entier) > 3:
        groupes.insert(0, entier[-3:])
        entier = entier[:-3]
    groupes.insert(0, entier)
    return f"{signe}{chr(0xA0).join(groupes)},{decimales}{chr(0xA0)}€"


def format_numero_facture(annee: int, rang: int) -> str:
    """Numéro unique et chronologique, sans trou, recommencé chaque année : FAC-2026-00001."""
    if rang < 1 or rang > 99_999:
        raise ValueError("Rang de facture hors limites")
    return f"FAC-{annee}-{rang:05d}"
