from typing import List
from fastapi import FastAPI, HTTPException, Depends
from starlette.responses import JSONResponse
from sqlmodel import Session, select

from data.models_team import Team, UpdatedTeam
from data.models_player import Player, UpdatedPlayer
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

# ==== ENDPOINTS PLAYER ====

@app.post("/player", response_model=Player, tags=["Players"])
def create_player(player: Player, session: Session = Depends(get_session)):
    if player.team_id is not None:
        team = session.get(Team, player.team_id)
        if not team:
            raise HTTPException(status_code=400, detail=f"El team_id {player.team_id} no existe")
    session.add(player)
    session.commit()
    session.refresh(player)
    return player

@app.get("/player", response_model=List[Player], tags=["Players"])
def get_all_players(session: Session = Depends(get_session)):
    return session.exec(select(Player)).all()

@app.get("/player/{player_id}", response_model=Player, tags=["Players"])
def get_player(player_id: int, session: Session = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player

@app.put("/player/{player_id}", response_model=Player, tags=["Players"])
def update_player(player_id: int, update: UpdatedPlayer, session: Session = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    for key, value in update.dict(exclude_unset=True).items():
        setattr(player, key, value)

    session.add(player)
    session.commit()
    session.refresh(player)
    return player

@app.delete("/player/{player_id}", response_model=Player, tags=["Players"])
def delete_player(player_id: int, session: Session = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    session.delete(player)
    session.commit()
    return player

@app.get("/player/filter/{team_id}", response_model=List[Player], tags=["Players"])
def filter_players_by_team(team_id: int, session: Session = Depends(get_session)):
    players = session.exec(select(Player).where(Player.team_id == team_id)).all()
    if not players:
        raise HTTPException(status_code=404, detail=f"No hay jugadores en el equipo con ID {team_id}")
    return players

@app.get("/player/search/{gamertag}", response_model=Player, tags=["Players"])
def search_by_gamertag(gamertag: str, session: Session = Depends(get_session)):
    player = session.exec(select(Player).where(Player.gamertag.ilike(gamertag))).first()
    if not player:
        raise HTTPException(status_code=404, detail="Gamertag no encontrado")
    return player

# ==== ENDPOINTS TEAM ====

@app.post("/team", response_model=Team, tags=["Teams"])
def create_team(team: Team, session: Session = Depends(get_session)):
    session.add(team)
    session.commit()
    session.refresh(team)
    return team

@app.get("/team", response_model=List[Team], tags=["Teams"])
def get_all_teams(session: Session = Depends(get_session)):
    return session.exec(select(Team)).all()

@app.get("/team/{team_id}", response_model=Team, tags=["Teams"])
def get_team(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return team

@app.put("/team/{team_id}", response_model=Team, tags=["Teams"])
def update_team(team_id: int, update: UpdatedTeam, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    for key, value in update.dict(exclude_unset=True).items():
        setattr(team, key, value)

    session.add(team)
    session.commit()
    session.refresh(team)
    return team

@app.delete("/team/{team_id}", response_model=Team, tags=["Teams"])
def delete_team(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    session.delete(team)
    session.commit()
    return team

@app.get("/team/filter/{region}", response_model=List[Team], tags=["Teams"])
def filter_teams_by_region(region: str, session: Session = Depends(get_session)):
    teams = session.exec(select(Team).where(Team.region.ilike(region))).all()
    if not teams:
        raise HTTPException(status_code=404, detail=f"No hay equipos en la región '{region}'")
    return teams

@app.get("/team/search/{name}", response_model=Team, tags=["Teams"])
def search_team_by_name(name: str, session: Session = Depends(get_session)):
    team = session.exec(select(Team).where(Team.name.ilike(name))).first()
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return team

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
