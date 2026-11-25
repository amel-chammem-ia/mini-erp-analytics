"""Connexion à SQL Server avec SQLAlchemy et le pilote ODBC 18."""
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings


@lru_cache
def get_engine() -> Engine:
    s = get_settings()
    url = URL.create(
        "mssql+pyodbc",
        username=s.db_user,
        password=s.db_password,
        host=s.db_host,
        port=s.db_port,
        database=s.db_name,
        query={"driver": "ODBC Driver 18 for SQL Server", "TrustServerCertificate": "yes"},
    )
    return create_engine(url, pool_pre_ping=True)


def check_database() -> bool:
    """Renvoie True si la base répond à un SELECT 1."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
