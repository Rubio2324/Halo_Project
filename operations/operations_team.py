# operations_team.py
from sqlmodel import Session, select
from typing import List, Optional
from fastapi import HTTPException
from data.models_team import Team, UpdatedTeam, DeletedTeam
from data.models_player import DeletedPlayer, Player

# Obtener todos los equipos
def get_all_teams(session: Session) -> List[Team]:
    return session.exec(select(Team)).all()

# Obtener equipo por ID
def read_team_by_id(team_id: int, session: Session) -> Optional[Team]:
    return session.get(Team, team_id)

# Crear nuevo equipo
def new_team(team: Team, session: Session) -> Team:
    session.add(team)
    session.commit()
    session.refresh(team)
    return team

# Modificar equipo
def modify_team(team_id: int, update: UpdatedTeam, session: Session) -> Optional[Team]:
    db_team = session.get(Team, team_id)
    if not db_team:
        return None

    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_team, key, value)

    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team

# Eliminar equipo
def delete_team(team_id: int, session: Session) -> Optional[Team]:
    team = session.get(Team, team_id)
    if not team:
        return None

    session.delete(team)
    session.commit()
    return team

# Buscar por nombre exacto
def search_team_by_name(name: str, session: Session) -> Optional[Team]:
    return session.exec(select(Team).where(Team.name.ilike(name))).first()

# Filtrar por región
def filter_teams_by_region(region: str, session: Session) -> List[Team]:
    return session.exec(select(Team).where(Team.region.ilike(region))).all()

#Teams eliminados y mandarlos al histrial
def delete_team(team_id: int, session: Session):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    # Guardar el team en DeletedTeam
    deleted_team = DeletedTeam(**team.dict())
    session.add(deleted_team)

    # Buscar jugadores del equipo
    players = session.exec(select(Player).where(Player.team_id == team_id)).all()

    for player in players:
        deleted_player = DeletedPlayer(**player.dict())
        session.add(deleted_player)
        session.delete(player)

    session.delete(team)
    session.commit()
    return {"message": f"Equipo '{team.name}' y sus jugadores han sido eliminados con historial."}


#Mostrar Historial
def get_deleted_teams(session: Session) -> List[DeletedTeam]:
    teams = session.exec(select(DeletedTeam)).all()
    return teams

#Restaurar Teams y Jugadores de ese Team
def restore_team(team_id: int, session: Session):
    deleted_team = session.get(DeletedTeam, team_id)
    if not deleted_team:
        raise HTTPException(status_code=404, detail="Equipo eliminado no encontrado")

    restored_team = Team(**deleted_team.dict())
    session.add(restored_team)

    # Restaurar los jugadores con ese team_id
    deleted_players = session.exec(select(DeletedPlayer).where(DeletedPlayer.team_id == team_id)).all()
    for deleted_player in deleted_players:
        restored_player = Player(**deleted_player.dict())
        session.add(restored_player)
        session.delete(deleted_player)

    session.delete(deleted_team)
    session.commit()
    return {"message": f"Equipo '{restored_team.name}' y sus jugadores han sido restaurados."}