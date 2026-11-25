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


def get_settings() -> Settings:
    return Settings(
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "1433")),
        db_name=os.getenv("DB_NAME", "master"),
        db_user=os.getenv("DB_USER", "sa"),
        db_password=os.getenv("MSSQL_SA_PASSWORD", ""),
    )
