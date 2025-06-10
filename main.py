from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import text
from sqlmodel import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from utils.db import create_db_and_tables, get_session
from routers import router
from frontend_routers import router as frontend_router


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "frontend" / "templates")

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

@app.get("/", response_class=HTMLResponse, name="index") # <--- Colócalo justo aquí, después de response_class=HTMLResponse
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(frontend_router)
app.include_router(router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.delete("/reset-all", tags=["General"])
def reset_all(session: Session = Depends(get_session)):
    session.exec(text("DELETE FROM player"))
    session.exec(text("DELETE FROM team"))
    session.exec(text("DELETE FROM deletedplayer"))
    session.exec(text("DELETE FROM deletedteam"))

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