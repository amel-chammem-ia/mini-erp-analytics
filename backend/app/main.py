"""Point d'entrée de l'API Mini-ERP Analytics.

Documentation interactive générée par FastAPI : http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import database
from .config import get_settings
from .routers import auth, clients, produits, statistiques, utilisateurs
from .securite import verifier_secret


@asynccontextmanager
async def demarrage(_app: FastAPI):
    # Sans secret solide dans le .env, l'API refuse de démarrer plutôt que de signer des jetons faibles.
    verifier_secret(get_settings().jwt_secret)
    yield


app = FastAPI(
    title="Mini-ERP Analytics",
    version="0.4.0",
    description="API du projet Mini-ERP Analytics (saison 2 de Formation Prompt Engineering).",
    lifespan=demarrage,
)
app.include_router(auth.router)
app.include_router(utilisateurs.router)
app.include_router(clients.router)
app.include_router(produits.router)
app.include_router(statistiques.router)


@app.get("/api/health", tags=["Santé"])
def health() -> JSONResponse:
    """Route de santé : l'API répond, et indique si la base est joignable."""
    if database.check_database():
        return JSONResponse({"api": "ok", "database": "ok"})
    return JSONResponse({"api": "ok", "database": "indisponible"}, status_code=503)
