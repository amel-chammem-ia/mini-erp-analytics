"""Modèles SQLAlchemy : le reflet Python des tables de database/01_schema.sql (épisode 7)."""
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Unicode, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

CENTIME = Decimal("0.01")


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(Unicode(120))
    email: Mapped[str] = mapped_column(Unicode(254), unique=True)
    numero_tva: Mapped[str] = mapped_column(Unicode(20), unique=True)
    ville: Mapped[str | None] = mapped_column(Unicode(80))
    cree_le: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())

    ventes: Mapped[list["Vente"]] = relationship(back_populates="client")


class Produit(Base):
    __tablename__ = "produits"
    __table_args__ = (
        CheckConstraint("prix_ht >= 0", name="ck_produits_prix"),
        CheckConstraint("taux_tva BETWEEN 0 AND 100", name="ck_produits_tva"),
        CheckConstraint("stock_actuel >= 0", name="ck_produits_stock"),
        CheckConstraint("seuil_alerte >= 0", name="ck_produits_seuil"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(Unicode(30), unique=True)
    nom: Mapped[str] = mapped_column(Unicode(150))
    categorie: Mapped[str] = mapped_column(Unicode(60))
    prix_ht: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    taux_tva: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("20.00"))
    stock_actuel: Mapped[int] = mapped_column(default=0)
    seuil_alerte: Mapped[int] = mapped_column(default=5)
    actif: Mapped[bool] = mapped_column(default=True)

    @property
    def sous_le_seuil(self) -> bool:
        return self.stock_actuel < self.seuil_alerte


class Vente(Base):
    __tablename__ = "ventes"
    __table_args__ = (
        CheckConstraint("statut IN ('brouillon', 'validee', 'annulee')", name="ck_ventes_statut"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(Unicode(20), unique=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    date_vente: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    statut: Mapped[str] = mapped_column(Unicode(12), default="brouillon")
    total_ht: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    total_tva: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    total_ttc: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))

    client: Mapped[Client] = relationship(back_populates="ventes")
    lignes: Mapped[list["LigneVente"]] = relationship(back_populates="vente", cascade="all, delete-orphan")


class LigneVente(Base):
    __tablename__ = "lignes_vente"
    __table_args__ = (
        CheckConstraint("quantite > 0", name="ck_lignes_vente_quantite"),
        CheckConstraint("prix_unitaire_ht >= 0", name="ck_lignes_vente_prix"),
        UniqueConstraint("vente_id", "produit_id", name="uq_lignes_vente_produit"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vente_id: Mapped[int] = mapped_column(ForeignKey("ventes.id", ondelete="CASCADE"))
    produit_id: Mapped[int] = mapped_column(ForeignKey("produits.id"))
    quantite: Mapped[int]
    prix_unitaire_ht: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    taux_tva: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    vente: Mapped[Vente] = relationship(back_populates="lignes")
    produit: Mapped[Produit] = relationship()

    @property
    def montant_ht(self) -> Decimal:
        """Quantité × prix unitaire, arrondi au centime."""
        return (self.prix_unitaire_ht * self.quantite).quantize(CENTIME, rounding=ROUND_HALF_UP)


class MouvementStock(Base):
    __tablename__ = "mouvements_stock"
    __table_args__ = (
        CheckConstraint("type_mouvement IN ('entree', 'sortie')", name="ck_mouvements_type"),
        CheckConstraint("quantite > 0", name="ck_mouvements_quantite"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    produit_id: Mapped[int] = mapped_column(ForeignKey("produits.id"))
    type_mouvement: Mapped[str] = mapped_column(Unicode(10))
    quantite: Mapped[int]
    date_mouvement: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    vente_id: Mapped[int | None] = mapped_column(ForeignKey("ventes.id"))
    commentaire: Mapped[str | None] = mapped_column(Unicode(200))

    produit: Mapped[Produit] = relationship()


class Utilisateur(Base):
    """Un compte de connexion (épisode 10). Le mot de passe n'est jamais stocké, seulement son empreinte."""
    __tablename__ = "utilisateurs"
    __table_args__ = (
        CheckConstraint(
            "role IN ('commercial', 'vendeur', 'magasinier', 'manager', 'dirigeant', 'administrateur')",
            name="ck_utilisateurs_role",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(Unicode(254), unique=True)
    nom: Mapped[str] = mapped_column(Unicode(120))
    mot_de_passe_hache: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(Unicode(20))
    actif: Mapped[bool] = mapped_column(default=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
