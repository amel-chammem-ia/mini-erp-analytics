"""Schémas Pydantic : ce que l'API accepte en entrée et renvoie en sortie (épisode 8).

Règle : on ne fait jamais confiance aux données reçues. Chaque champ est typé et borné ;
une donnée invalide est refusée avec le code 422 avant même de toucher la base.
"""
from datetime import datetime
from decimal import Decimal
from typing import Annotated, ClassVar, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

T = TypeVar("T")

# Types réutilisables -------------------------------------------------------
Texte = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Email = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, max_length=254,
                      pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]
NumeroTva = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z]{2}[0-9A-Za-z]{2,13}$"),
]
Montant = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
TauxTva = Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]


class Page(BaseModel, Generic[T]):
    """Une page de résultats : les éléments, le nombre total et la position."""
    items: list[T]
    total: int
    page: int
    taille: int


class Modification(BaseModel):
    """Base des PATCH : un champ absent ne change pas, un champ obligatoire ne peut pas valoir null."""
    model_config = ConfigDict(extra="forbid")
    OBLIGATOIRES: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def refuser_null_sur_champ_obligatoire(self):
        for champ in self.OBLIGATOIRES:
            if champ in self.model_fields_set and getattr(self, champ) is None:
                raise ValueError(f"Le champ {champ} ne peut pas être vide")
        return self


# Clients -------------------------------------------------------------------
class ClientCreation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom: Annotated[Texte, StringConstraints(max_length=120)]
    email: Email
    numero_tva: NumeroTva
    ville: Annotated[Texte, StringConstraints(max_length=80)] | None = None


class ClientModification(Modification):
    """Tous les champs sont facultatifs : on ne modifie que ce qui est envoyé (PATCH)."""
    OBLIGATOIRES = ("nom", "email", "numero_tva")

    nom: Annotated[Texte, StringConstraints(max_length=120)] | None = None
    email: Email | None = None
    numero_tva: NumeroTva | None = None
    ville: Annotated[Texte, StringConstraints(max_length=80)] | None = None


class ClientLecture(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    email: str
    numero_tva: str
    ville: str | None
    cree_le: datetime | None


# Produits ------------------------------------------------------------------
class ProduitCreation(BaseModel):
    """Le stock n'est pas saisi ici : il ne bouge que par des mouvements de stock (épisode 12)."""
    model_config = ConfigDict(extra="forbid")

    reference: Annotated[Texte, StringConstraints(max_length=30, to_upper=True)]
    nom: Annotated[Texte, StringConstraints(max_length=150)]
    categorie: Annotated[Texte, StringConstraints(max_length=60)]
    prix_ht: Montant
    taux_tva: TauxTva = Decimal("20.00")
    seuil_alerte: Annotated[int, Field(ge=0)] = 5


class ProduitModification(Modification):
    """La référence ne change jamais : elle identifie le produit sur les factures."""
    OBLIGATOIRES = ("nom", "categorie", "prix_ht", "taux_tva", "seuil_alerte", "actif")

    nom: Annotated[Texte, StringConstraints(max_length=150)] | None = None
    categorie: Annotated[Texte, StringConstraints(max_length=60)] | None = None
    prix_ht: Montant | None = None
    taux_tva: TauxTva | None = None
    seuil_alerte: Annotated[int, Field(ge=0)] | None = None
    actif: bool | None = None


class ProduitLecture(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    nom: str
    categorie: str
    prix_ht: Decimal
    taux_tva: Decimal
    stock_actuel: int
    seuil_alerte: int
    actif: bool
    sous_le_seuil: bool
