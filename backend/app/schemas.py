"""Schémas Pydantic : ce que l'API accepte en entrée et renvoie en sortie (épisode 8).

Règle : on ne fait jamais confiance aux données reçues. Chaque champ est typé et borné ;
une donnée invalide est refusée avec le code 422 avant même de toucher la base.
"""
from datetime import datetime
from decimal import Decimal
from typing import Annotated, ClassVar, Generic, Literal, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, model_validator

from .temps import en_utc

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
# Une date qui sort de l'API dit toujours son fuseau : "2026-11-30T23:30:00Z" (épisode 9).
HorodatageUTC = Annotated[datetime, AfterValidator(en_utc)]


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
    cree_le: HorodatageUTC | None


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


# Statistiques ---------------------------------------------------------------
class CaMois(BaseModel):
    """Chiffre d'affaires HT d'un mois, en heure de Paris (épisode 9)."""
    mois: Annotated[str, Field(pattern=r"^\d{4}-\d{2}$", examples=["2026-12"])]
    nb_ventes: int
    ca_ht: Decimal


# Connexion et comptes (épisode 10) -------------------------------------------
Role = Literal["commercial", "vendeur", "magasinier", "manager", "dirigeant", "administrateur"]
# 12 caractères minimum (recommandation de l'ANSSI pour un mot de passe seul) ;
# 128 maximum pour qu'un texte énorme ne coûte pas un calcul de hachage démesuré.
MotDePasse = Annotated[str, StringConstraints(min_length=12, max_length=128)]


class Connexion(BaseModel):
    """À la connexion, on ne valide pas le format de l'e-mail : la réponse doit rester la même
    qu'il existe ou non. On borne seulement les longueurs."""
    email: Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=254)]
    mot_de_passe: Annotated[str, StringConstraints(max_length=128)]


class Jeton(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expire_dans: int  # secondes


class UtilisateurCreation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Email
    nom: Annotated[Texte, StringConstraints(max_length=120)]
    role: Role
    mot_de_passe: MotDePasse


class UtilisateurModification(Modification):
    OBLIGATOIRES = ("nom", "role", "actif", "mot_de_passe")

    nom: Annotated[Texte, StringConstraints(max_length=120)] | None = None
    role: Role | None = None
    actif: bool | None = None
    mot_de_passe: MotDePasse | None = None


class UtilisateurLecture(BaseModel):
    """Jamais d'empreinte de mot de passe dans une réponse."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nom: str
    role: Role
    actif: bool
    cree_le: HorodatageUTC | None = None


class Moi(UtilisateurLecture):
    droits: list[str]


# Ventes et factures (épisode 11) ---------------------------------------------
StatutVente = Literal["brouillon", "validee", "annulee"]


class LigneCommande(BaseModel):
    """Le prix et le taux de TVA ne viennent jamais du client de l'API : ils sont lus dans le catalogue."""
    model_config = ConfigDict(extra="forbid")

    produit_id: Annotated[int, Field(ge=1)]
    quantite: Annotated[int, Field(ge=1, le=10_000)]


class VenteCreation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: Annotated[int, Field(ge=1)]
    lignes: Annotated[list[LigneCommande], Field(min_length=1, max_length=100)]

    @model_validator(mode="after")
    def produits_distincts(self):
        produits = [ligne.produit_id for ligne in self.lignes]
        if len(produits) != len(set(produits)):
            raise ValueError("Un produit ne peut apparaître qu'une fois : augmentez sa quantité")
        return self


class LigneVenteLecture(BaseModel):
    produit_id: int
    reference: str
    designation: str
    quantite: int
    prix_unitaire_ht: Decimal
    taux_tva: Decimal
    montant_ht: Decimal


class TvaLecture(BaseModel):
    taux: Decimal
    base_ht: Decimal
    montant_tva: Decimal


class VenteResume(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    client_id: int
    statut: StatutVente
    date_vente: HorodatageUTC
    numero_facture: str | None = None
    facturee_le: HorodatageUTC | None = None
    total_ht: Decimal
    total_tva: Decimal
    total_ttc: Decimal


class VenteDetail(VenteResume):
    client_nom: str
    lignes: list[LigneVenteLecture]
    tva_par_taux: list[TvaLecture]
