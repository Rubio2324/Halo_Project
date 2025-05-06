from typing import List

from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse

from models_player import Player, PlayerWithID, UpdatedPlayer
from models_player import Team, TeamWithID, UpdatedTeam
from operations_player import (
    read_all_players,
    read_player_by_id,
    new_player,
    modify_player,
    delete_player
)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API de jugadores Halo eSports"}

# Crear jugador
@app.post("/player", response_model=PlayerWithID)
async def create_player(player: Player):
    return new_player(player)

# Obtener todos los jugadores
@app.get("/player", response_model=List[PlayerWithID])
async def get_all_players():
    return read_all_players()

# Obtener un jugador por ID
@app.get("/player/{player_id}", response_model=PlayerWithID)
async def get_player(player_id: int):
    player = read_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player

# Modificar un jugador
@app.put("/player/{player_id}", response_model=PlayerWithID)
async def update_player(player_id: int, update: UpdatedPlayer):
    updated = modify_player(player_id, update)
    if not updated:
        raise HTTPException(status_code=417, detail="No se pudo actualizar el jugador")
    return updated

# Eliminar un jugador
@app.delete("/player/{player_id}", response_model=PlayerWithID)
async def remove_player(player_id: int):
    deleted = delete_player(player_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Jugador no encontrado para eliminar")
    return deleted

# Filtrar jugadores por equipo
@app.get("/player/filter/{team}", response_model=List[PlayerWithID])
async def filter_players_by_team(team: str):
    players = [p for p in read_all_players() if p.team.lower() == team.lower()]
    if not players:
        raise HTTPException(status_code=404, detail=f"No se encontraron jugadores en el equipo '{team}'")
    return players

# Buscar jugador por gamertag
@app.get("/player/search/{gamertag}", response_model=PlayerWithID)
async def search_by_gamertag(gamertag: str):
    for p in read_all_players():
        if p.gamertag.lower() == gamertag.lower():
            return p
    raise HTTPException(status_code=404, detail="Gamertag no encontrado")

# Manejo de errores HTTP
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

# Ruta para lanzar una excepción a propósito (para pruebas)
@app.get("/error")
async def raise_exception():
    raise HTTPException(status_code=400, detail="Esto es un error simulado")
from operations_team import (
    read_all_teams,
    read_team_by_id,
    new_team,
    modify_team,
    delete_team,
    filter_teams_by_region,
    search_team_by_name
)

# === ENDPOINTS PARA TEAM ===

@app.post("/team", response_model=TeamWithID)
async def create_team(team: Team):
    return new_team(team)

@app.get("/team", response_model=List[TeamWithID])
async def get_all_teams():
    return read_all_teams()

@app.get("/team/{team_id}", response_model=TeamWithID)
async def get_team(team_id: int):
    team = read_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return team

@app.put("/team/{team_id}", response_model=TeamWithID)
async def update_team(team_id: int, update: UpdatedTeam):
    updated = modify_team(team_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="No se pudo actualizar el equipo")
    return updated

@app.delete("/team/{team_id}", response_model=TeamWithID)
async def remove_team(team_id: int):
    deleted = delete_team(team_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Equipo no encontrado para eliminar")
    return deleted

@app.get("/team/filter/{region}", response_model=List[TeamWithID])
async def filter_teams(region: str):
    teams = filter_teams_by_region(region)
    if not teams:
        raise HTTPException(status_code=404, detail=f"No hay equipos en la región '{region}'")
    return teams

@app.get("/team/search/{name}", response_model=TeamWithID)
async def search_team(name: str):
    team = search_team_by_name(name)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado con ese nombre")
    return team