"""Point d'entrée de l'API Mini-ERP Analytics.

Documentation interactive générée par FastAPI : http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import database
from .routers import clients, produits

app = FastAPI(
    title="Mini-ERP Analytics",
    version="0.2.0",
    description="API du projet Mini-ERP Analytics (saison 2 de Formation Prompt Engineering).",
)
app.include_router(clients.router)
app.include_router(produits.router)


@app.get("/api/health", tags=["Santé"])
def health() -> JSONResponse:
    """Route de santé : l'API répond, et indique si la base est joignable."""
    if database.check_database():
        return JSONResponse({"api": "ok", "database": "ok"})
    return JSONResponse({"api": "ok", "database": "indisponible"}, status_code=503)
