# operations_player.py
from sqlmodel import Session, select
from typing import List, Optional
from models_player import Player, UpdatedPlayer,PlayerCreate
from db import get_session
from fastapi import HTTPException
from models_team import Team
from operations_team import get_all_teams


# Obtener todos los jugadores
def read_all_players(session: Session) -> List[Player]:
    return session.exec(select(Player)).all()

# Obtener jugador por ID
def read_player_by_id(player_id: int, session: Session) -> Optional[Player]:
    return session.get(Player, player_id)

# Crear nuevo jugador
def create_player(player: PlayerCreate):
    # Obtener todos los equipos disponibles
    teams = get_all_teams()

    # Verificar si el team_name existe
    if player.team_name not in [team.name for team in teams]:
        raise HTTPException(status_code=400, detail="El equipo no existe")

    # Guardar jugador si todo está bien
    with get_session() as session:
        db_player = Player.from_orm(player)
        session.add(db_player)
        session.commit()
        session.refresh(db_player)
        return db_player

# Modificar jugador
def modify_player(player_id: int, update: UpdatedPlayer, session: Session) -> Optional[Player]:
    db_player = session.get(Player, player_id)
    if not db_player:
        return None

    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_player, key, value)

    session.add(db_player)
    session.commit()
    session.refresh(db_player)
    return db_player

# Eliminar jugador
def delete_player(player_id: int, session: Session) -> Optional[Player]:
    player = session.get(Player, player_id)
    if not player:
        return None

    session.delete(player)
    session.commit()
    return player
