from typing import List
from fastapi import FastAPI, HTTPException, Depends
from starlette.responses import JSONResponse
from sqlmodel import Session, select
from sqlalchemy import text

from data.models_team import Team, TeamCreate, UpdatedTeam
from data.models_player import Player, PlayerCreate, UpdatedPlayer
from utils.db import create_db_and_tables, get_session

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

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/", tags=["General"])
async def root():
    return {"message": "API de jugadores Halo eSports"}

# ==== ENDPOINTS PLAYER ==== (igual que antes)

@app.post("/player", response_model=Player, tags=["Players"])
def create_player(player: PlayerCreate, session: Session = Depends(get_session)):
    if player.team_id is not None:
        team = session.get(Team, player.team_id)
        if not team:
            raise HTTPException(status_code=400, detail=f"El team_id {player.team_id} no existe")
    db_player = Player.from_orm(player)
    session.add(db_player)
    session.commit()
    session.refresh(db_player)
    return db_player

@app.get("/players", response_model=List[Player], tags=["Players"])
def get_players(session: Session = Depends(get_session)):
    players = session.exec(select(Player)).all()
    return players

@app.get("/player/{player_id}", response_model=Player, tags=["Players"])
def get_player(player_id: int, session: Session = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player

@app.put("/player/{player_id}", response_model=Player, tags=["Players"])
def update_player(player_id: int, updated_data: UpdatedPlayer, session: Session = Depends(get_session)):
    db_player = session.get(Player, player_id)
    if not db_player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    updated_fields = updated_data.dict(exclude_unset=True)
    for key, value in updated_fields.items():
        setattr(db_player, key, value)
    session.add(db_player)
    session.commit()
    session.refresh(db_player)
    return db_player

@app.delete("/player/{player_id}", tags=["Players"])
def delete_player(player_id: int, session: Session = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    session.delete(player)
    session.commit()
    return {"message": "Jugador eliminado"}

# ==== ENDPOINTS TEAM ====

@app.post("/team", response_model=Team, tags=["Teams"])
def create_team(team: TeamCreate, session: Session = Depends(get_session)):
    db_team = Team.from_orm(team)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team

@app.get("/teams", response_model=List[Team], tags=["Teams"])
def get_teams(session: Session = Depends(get_session)):
    teams = session.exec(select(Team)).all()
    return teams

@app.get("/team/{team_id}", response_model=Team, tags=["Teams"])
def get_team(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team no encontrado")
    return team

@app.put("/team/{team_id}", response_model=Team, tags=["Teams"])
def update_team(team_id: int, updated_data: UpdatedTeam, session: Session = Depends(get_session)):
    db_team = session.get(Team, team_id)
    if not db_team:
        raise HTTPException(status_code=404, detail="Team no encontrado")
    updated_fields = updated_data.dict(exclude_unset=True)
    for key, value in updated_fields.items():
        setattr(db_team, key, value)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team

@app.delete("/team/{team_id}", tags=["Teams"])
def delete_team(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team no encontrado")
    session.delete(team)
    session.commit()
    return {"message": "Team eliminado"}

# === NUEVO ENDPOINT: Enumerar IDs de equipos ===

@app.get("/team-ids", tags=["Teams"])
def get_team_ids(session: Session = Depends(get_session)):
    team_ids = session.exec(select(Team.id)).all()
    if not team_ids:
        return {"message": "No hay equipos registrados."}
    return {"team_ids": team_ids}

# ==== ENDPOINT PARA RESETEAR JUGADORES Y EQUIPOS ====

@app.delete("/reset-all", tags=["General"])
def reset_all(session: Session = Depends(get_session)):
    session.exec(text("DELETE FROM player"))
    session.exec(text("DELETE FROM team"))
    # Reiniciar secuencias para IDs (PostgreSQL)
    session.execute(text("SELECT setval(pg_get_serial_sequence('player', 'id'), 1, false)"))
    session.execute(text("SELECT setval(pg_get_serial_sequence('team', 'id'), 1, false)"))
    session.commit()
    return {"message": "Todos los jugadores y equipos eliminados, secuencias reiniciadas"}

# ==== MANEJO DE ERRORES ====

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "msg": "¡Llorelo! Algo salió mal...",
            "detail": exc.detail,
            "path": str(request.url)
        },
    )

@app.get("/error", tags=["General"])
async def raise_exception():
    raise HTTPException(status_code=400, detail="Esto es un error simulado")

