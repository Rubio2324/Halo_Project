from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional

from utils.db import get_session
from data.models_player import Player, PlayerCreate, UpdatedPlayer
from data.models_team import Team, TeamCreate, UpdatedTeam

router = APIRouter()

# ---------------------- PLAYERS ----------------------

@router.post("/players/", response_model=Player, tags=["Players"])
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

@router.get("/players/", response_model=List[Player], tags=["Players"])
def get_all_players(session: Session = Depends(get_session)):
    return session.exec(select(Player)).all()

@router.get("/players/{player_id}", response_model=Player, tags=["Players"])
def get_player(player_id: int, session: Session = Depends(get_session)):
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
    for key, value in update_dict.items():
        setattr(player, key, value)
    session.add(player)
    session.commit()
    session.refresh(player)
    return player

@router.delete("/players/{player_id}", tags=["Players"])
def delete_player(player_id: int, session: Session = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    session.delete(player)
    session.commit()
    return {"message": "Jugador eliminado exitosamente"}

# Obtener todos los jugadores
@router.get("/players/", response_model=List[Player])
def get_all_players(session: Session = Depends(get_session)):
    return session.exec(select(Player)).all()

# Filtrar jugadores por nombre
@router.get("/players/by-name/", response_model=List[Player])
def get_players_by_name(name: str, session: Session = Depends(get_session)):
    return session.exec(select(Player).where(Player.name.ilike(f"%{name}%"))).all()

# Filtrar jugadores por equipo
@router.get("/players/by-team/", response_model=List[Player])
def get_players_by_team(team_id: int, session: Session = Depends(get_session)):
    return session.exec(select(Player).where(Player.team_id == team_id)).all()

# ---------------------- TEAMS ----------------------

@router.post("/teams/", response_model=Team, tags=["Teams"])
def create_team(team: TeamCreate, session: Session = Depends(get_session)):
    db_team = Team.from_orm(team)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team

@router.get("/teams/", response_model=List[Team], tags=["Teams"])
def get_all_teams(session: Session = Depends(get_session)):
    return session.exec(select(Team)).all()

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

@router.delete("/teams/{team_id}", tags=["Teams"])
def delete_team(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    session.delete(team)
    session.commit()
    return {"message": "Equipo eliminado exitosamente"}

# Obtener todos los equipos
@router.get("/teams/", response_model=List[Team])
def get_all_teams(session: Session = Depends(get_session)):
    return session.exec(select(Team)).all()

# Filtrar equipos por nombre
@router.get("/teams/by-name/", response_model=List[Team])
def get_teams_by_name(name: str, session: Session = Depends(get_session)):
    return session.exec(select(Team).where(Team.name.ilike(f"%{name}%"))).all()

# Filtrar equipos por cantidad de campeonatos
@router.get("/teams/by-championships/", response_model=List[Team])
def get_teams_by_championships(championships: int, session: Session = Depends(get_session)):
    return session.exec(select(Team).where(Team.championships == championships)).all()