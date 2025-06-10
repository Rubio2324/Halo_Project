from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import text
from sqlmodel import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from utils.db import create_db_and_tables, get_session

# Define BASE_DIR lo antes posible
BASE_DIR = Path(__file__).resolve().parent

# Define templates aquí también para uso de main.py y por si algún router lo necesita directamente
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))

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

# Monta los archivos estáticos
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# IMPORTANTE: Importar los routers *después* de que 'app', 'templates' y 'BASE_DIR'
# estén definidos para evitar la importación circular.
# Asegúrate de que 'routers.py' no intente importar nada de 'main.py'
# y que 'frontend_routers.py' ya no importe 'templates' y 'BASE_DIR' de aquí.
from routers import router # Este es tu router de la API pura
from frontend_routers import router as frontend_router # Este es el router de las vistas HTML

# Incluir routers
app.include_router(frontend_router)
app.include_router(router)

@app.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.delete("/reset-all", tags=["General"])
def reset_all(session: Session = Depends(get_session)):
    session.exec(text("DELETE FROM player"))
    session.exec(text("DELETE FROM team"))
    session.exec(text("DELETE FROM deletedplayer"))
    session.exec(text("DELETE FROM deletedteam"))

    # Reiniciar secuencias de IDs en PostgreSQL
    # Las comillas dobles son necesarias si los nombres de tabla/columna no son minúsculas
    session.execute(text("SELECT setval('player_id_seq', 1, false)"))
    session.execute(text("SELECT setval('team_id_seq', 1, false)"))
    session.execute(text("SELECT setval('deletedplayer_id_seq', 1, false)"))
    session.execute(text("SELECT setval('deletedteam_id_seq', 1, false)"))


    session.commit()
    return {"message": "Todos los jugadores, equipos y registros históricos eliminados. Secuencias reiniciadas."}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
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