from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from info_routers import router as info_router

from utils.db import get_session
from data.models_player import Player, PlayerCreate, UpdatedPlayer, DeletedPlayer
from data.models_team import Team, TeamCreate, UpdatedTeam
from data.models_team import DeletedTeam
from operations.operations_team import get_deleted_teams,restore_team, delete_team

router = APIRouter()
router.include_router(info_router)

# ---------------------- PLAYERS ----------------------

@router.post("/players/", response_model=Player, tags=["Players"])
def create_player(player: PlayerCreate, session: Session = Depends(get_session)):
    if player.team_id is not None:
        team = session.get(Team, player.team_id)
        if not team:
            raise HTTPException(status_code=400, detail=f"El team_id {player.team_id} no existe")
    db_player = Player(
        name=player.name,
        gamertag=player.gamertag,
        kills=player.kills,
        deaths=player.deaths,
        team_id=player.team_id,
        image_url=player.image_url,
    )
    session.add(db_player)
    session.commit()
    session.refresh(db_player)
    return db_player

# Obtener todos los jugadores
@router.get("/players", tags=["Players"])
def get_all_players(session: Session = Depends(get_session)):
    players = session.exec(select(Player)).all()
    if not players:
        raise HTTPException(status_code=404, detail="No hay jugadores registrados.")
    return players

@router.get("/players/{player_id}", response_model=Player, tags=["Players"])
def get_player_by_id(player_id: int, session: Session = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player

@router.put("/players/{player_id}", response_model=Player, tags=["Players"])
def update_player(player_id: int, update_data: UpdatedPlayer, session: Session = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    update_dict = update_data.dict(exclude_unset=True)

    # Validar que el team_id existe si viene en los datos
    if "team_id" in update_dict and update_dict["team_id"] is not None:
        team = session.get(Team, update_dict["team_id"])
        if not team:
            raise HTTPException(status_code=400, detail=f"El team_id {update_dict['team_id']} no existe")

    for key, value in update_dict.items():
        setattr(player, key, value)

    session.add(player)
    session.commit()
    session.refresh(player)
    return player


#Eliminar Jugador y Pasarlo al Historial
@router.delete("/players/{player_id}", response_model=dict, tags=["Players"])
def delete_player(player_id: int, session: Session = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    deleted_player = DeletedPlayer(
        id=player.id,
        name=player.name,
        gamertag=player.gamertag,
        kills=player.kills,
        deaths=player.deaths,
        team_id=player.team_id,
        image_url=player.image_url
    )
    session.add(deleted_player)
    session.delete(player)
    session.commit()
    return {"message": "Jugador eliminado y movido al historial"}

#Mostrar Historial
@router.get("/deleted-players", tags=["Players"])
def get_deleted_players(session: Session = Depends(get_session)):
    deleted_players = session.exec(select(DeletedPlayer)).all()
    if not deleted_players:
        raise HTTPException(status_code=404, detail="No hay jugadores eliminados.")
    return deleted_players

#Restaurar Jugador eliminado
@router.post("/players/restore/{player_id}", response_model=Player, tags=["Players"])
def restore_player(player_id: int, session: Session = Depends(get_session)):
    deleted_player = session.get(DeletedPlayer, player_id)
    if not deleted_player:
        raise HTTPException(status_code=404, detail="Jugador eliminado no encontrado")

    # Validar si el team_id sigue existiendo (modo estricto)
    if deleted_player.team_id is not None:
        team = session.get(Team, deleted_player.team_id)
        if not team:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede restaurar el jugador porque el equipo con ID {deleted_player.team_id} no existe"
            )

    restored_player = Player(
        id=deleted_player.id,
        name=deleted_player.name,
        gamertag=deleted_player.gamertag,
        kills=deleted_player.kills,
        deaths=deleted_player.deaths,
        team_id=deleted_player.team_id,
        image_url=deleted_player.image_url
    )

    session.add(restored_player)
    session.delete(deleted_player)
    session.commit()
    session.refresh(restored_player)
    return restored_player


# Filtrar jugadores por nombre
@router.get("/players/by-name/{name}", tags=["Players"])
def get_player_by_name(name: str, session: Session = Depends(get_session)):
    players = session.exec(select(Player).where(Player.name.ilike(f"%{name}%"))).all()
    if not players:
        raise HTTPException(status_code=404, detail=f"No se encontraron jugadores con el nombre '{name}'.")
    return players

# Filtrar jugadores por equipo
@router.get("/players/by-team/{team_id}", tags=["Players"])
def get_players_by_team(team_id: int, session: Session = Depends(get_session)):
    players = session.exec(select(Player).where(Player.team_id == team_id)).all()
    if not players:
        raise HTTPException(status_code=404, detail=f"No se encontraron jugadores para el equipo con ID {team_id}.")
    return players

# ---------------------- TEAMS ----------------------

@router.post("/teams/", response_model=Team, tags=["Teams"])
def create_team(team: TeamCreate, session: Session = Depends(get_session)):
    db_team = Team.from_orm(team)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team

# Obtener todos los equipos
@router.get("/teams", tags=["Teams"])
def get_all_teams(session: Session = Depends(get_session)):
    teams = session.exec(select(Team)).all()
    if not teams:
        raise HTTPException(status_code=404, detail="No hay equipos registrados.")
    return teams

@router.get("/teams/{team_id}", response_model=Team, tags=["Teams"])
def get_team(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return team

@router.put("/teams/{team_id}", response_model=Team, tags=["Teams"])
def update_team(team_id: int, update_data: UpdatedTeam, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(team, key, value)
    session.add(team)
    session.commit()
    session.refresh(team)
    return team

#Eliminar Teams y mandarlos al historial
@router.delete("/teams/{team_id}", tags=["Teams"])
def delete_teams (team_id: int, session: Session = Depends(get_session)):
    return delete_team(team_id, session)

#Mostrar Teams Eliminados
@router.get("/deleted-teams", tags=["Teams"])
def get_deleted_teams(session: Session = Depends(get_session)):
    deleted_teams = session.exec(select(DeletedTeam)).all()
    if not deleted_teams:
        raise HTTPException(status_code=404, detail="No hay equipos eliminados.")
    return deleted_teams

#Restaurar Teams
@router.post("/teams/restore/{team_id}", tags=["Teams"])
def restore_team_endpoint (team_id: int, session: Session = Depends(get_session)):
    return restore_team(team_id, session)

# Filtrar equipos por nombre
@router.get("/teams/by-name/{name}", tags=["Teams"])
def get_teams_by_name(name: str, session: Session = Depends(get_session)):
    teams = session.exec(select(Team).where(Team.name.ilike(f"%{name}%"))).all()
    if not teams:
        raise HTTPException(status_code=404, detail=f"No se encontraron equipos con el nombre '{name}'.")
    return teams

# Filtrar equipos por cantidad de campeonatos
@router.get("/teams/by-championship/{championship}", tags=["Teams"])
def get_teams_by_championship(championship: int, session: Session = Depends(get_session)):
    teams = session.exec(select(Team).where(Team.championships == championship)).all()
    if not teams:
        raise HTTPException(status_code=404, detail=f"No se encontraron equipos con {championship} campeonatos ganados.")
    return teams
