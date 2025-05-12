# operations_team.py
from sqlmodel import Session, select
from typing import List, Optional
from models_team import Team, UpdatedTeam

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
