import csv
from typing import Optional, List
from models_player import Team, TeamWithID, UpdatedTeam

FILENAME = "team.csv"
DELETED_FILENAME = "deleted_teams.csv"
FIELDS = ["id", "name", "region", "championships"]

def read_all_teams() -> List[TeamWithID]:
    with open(FILENAME) as f:
        reader = csv.DictReader(f)
        return [TeamWithID(**row) for row in reader]

def read_team_by_id(team_id: int) -> Optional[TeamWithID]:
    for team in read_all_teams():
        if team.id == team_id:
            return team

def get_next_id() -> int:
    try:
        teams = read_all_teams()
        return max(t.id for t in teams) + 1
    except:
        return 1

def write_team(team: TeamWithID):
    with open(FILENAME, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow(team.model_dump())

def new_team(team: Team) -> TeamWithID:
    id = get_next_id()
    team_with_id = TeamWithID(id=id, **team.model_dump())
    write_team(team_with_id)
    return team_with_id

def modify_team(team_id: int, update: UpdatedTeam) -> Optional[TeamWithID]:
    teams = read_all_teams()
    updated = None

    for i, t in enumerate(teams):
        if t.id == team_id:
            updated_data = t.model_dump()
            for field, value in update.model_dump(exclude_none=True).items():
                updated_data[field] = value
            updated = TeamWithID(**updated_data)
            teams[i] = updated
            break

    if updated:
        with open(FILENAME, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for t in teams:
                writer.writerow(t.model_dump())
        return updated

def delete_team(team_id: int) -> Optional[TeamWithID]:
    teams = read_all_teams()
    deleted = None
    with open(FILENAME, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for t in teams:
            if t.id == team_id:
                deleted = t
                continue
            writer.writerow(t.model_dump())

    if deleted:
        # Guardar el eliminado para trazabilidad
        with open(DELETED_FILENAME, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writerow(deleted.model_dump())

    return deleted

#  Buscar por nombre exacto
def search_team_by_name(name: str) -> Optional[TeamWithID]:
    for t in read_all_teams():
        if t.name.lower() == name.lower():
            return t

#  Filtrar por región
def filter_teams_by_region(region: str) -> List[TeamWithID]:
    return [t for t in read_all_teams() if t.region.lower() == region.lower()]

