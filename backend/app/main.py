"""Point d'entrée de l'API Mini-ERP Analytics."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import database

app = FastAPI(title="Mini-ERP Analytics", version="0.1.0")


@app.get("/api/health")
def health() -> JSONResponse:
    """Route de santé : l'API répond, et indique si la base est joignable."""
    if database.check_database():
        return JSONResponse({"api": "ok", "database": "ok"})
    return JSONResponse({"api": "ok", "database": "indisponible"}, status_code=503)
