from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlmodel import Session

from utils.db import create_db_and_tables, get_session
from routers import router  # Importa el router con endpoints de players y teams

app = FastAPI(
    title="API de Halo eSports",
    description="""
Esta API permite la gestión de **jugadores** y **equipos** del universo de Halo en el contexto de eSports.

Puedes:

- Crear, actualizar, eliminar y buscar jugadores.
- Registrar y administrar equipos.
""",
    version="1.0.0"
)

app.include_router(router)  # Incluye los endpoints de players y teams

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/", tags=["General"])
async def root():
    return {"message": "API de jugadores Halo eSports"}

@app.delete("/reset-all", tags=["General"])
def reset_all(session: Session = Depends(get_session)):
    # Eliminar registros de todas las tablas (incluyendo historial)
    session.exec(text("DELETE FROM player"))
    session.exec(text("DELETE FROM team"))
    session.exec(text("DELETE FROM deletedplayer"))
    session.exec(text("DELETE FROM deletedteam"))

    # Reiniciar secuencias para IDs (PostgreSQL)
    session.execute(text("SELECT setval(pg_get_serial_sequence('player', 'id'), 1, false)"))
    session.execute(text("SELECT setval(pg_get_serial_sequence('team', 'id'), 1, false)"))
    session.execute(text("SELECT setval(pg_get_serial_sequence('deletedplayer', 'id'), 1, false)"))
    session.execute(text("SELECT setval(pg_get_serial_sequence('deletedteam', 'id'), 1, false)"))

    session.commit()
    return {"message": "Todos los jugadores, equipos y registros históricos eliminados. Secuencias reiniciadas."}

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "msg": "¡Llórelo! Algo salió mal...",
            "detail": exc.detail,
            "path": str(request.url)
        },
    )

@app.get("/error", tags=["General"])
async def raise_exception():
    raise HTTPException(status_code=400, detail="Esto es un error simulado")

