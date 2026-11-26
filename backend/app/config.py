"""Configuration lue dans les variables d'environnement (fichier .env via Docker Compose)."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    jwt_secret: str  # signe les jetons de connexion (épisode 10) : jamais dans le code
    # Émetteur des factures (épisode 11). Adresse : lignes séparées par « | ».
    entreprise_nom: str = "Mini-ERP Analytics (démo)"
    entreprise_adresse: str = ""
    entreprise_tva: str = ""
    entreprise_siret: str = ""


def get_settings() -> Settings:
    return Settings(
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "1433")),
        db_name=os.getenv("DB_NAME", "MiniERP"),
        db_user=os.getenv("DB_USER", "sa"),
        db_password=os.getenv("MSSQL_SA_PASSWORD", ""),
        jwt_secret=os.getenv("JWT_SECRET", ""),
        entreprise_nom=os.getenv("ENTREPRISE_NOM", "Mini-ERP Analytics (démo)"),
        entreprise_adresse=os.getenv("ENTREPRISE_ADRESSE", ""),
        entreprise_tva=os.getenv("ENTREPRISE_TVA", ""),
        entreprise_siret=os.getenv("ENTREPRISE_SIRET", ""),
    )
