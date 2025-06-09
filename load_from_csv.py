import csv
from sqlmodel import Session, select
from utils.db import engine
from data.models_team import Team
from data.models_player import Player

def load_teams(session: Session, csv_path: str):
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Validar si el equipo ya existe por nombre
            existing_team = session.exec(select(Team).where(Team.name == row["name"])).first()
            if existing_team:
                print(f"Equipo '{row['name']}' ya existe. Saltando.")
                continue

            team = Team(
                name=row["name"],
                region=row["region"],
                championships=int(row["championships"]),
                image_url=row.get("image_url")
            )
            session.add(team)
        session.commit()

def load_players(session: Session, csv_path: str):
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Validar si el jugador ya existe por gamertag
            existing_player = session.exec(select(Player).where(Player.gamertag == row["gamertag"])).first()
            if existing_player:
                print(f"Jugador '{row['gamertag']}' ya existe. Saltando.")
                continue

            # Buscar ID del equipo por nombre
            team = session.exec(select(Team).where(Team.name == row["team_name"])).first()
            if not team:
                print(f"Equipo '{row['team_name']}' no encontrado. Saltando jugador '{row['gamertag']}'.")
                continue

            player = Player(
                name=row["name"],
                gamertag=row["gamertag"],
                kills=int(row["kills"]),
                deaths=int(row["deaths"]),
                team_id=team.id,
                image_url=row.get("image_url")
            )
            session.add(player)
        session.commit()

def main():
    csv_teams = "teams_real.csv"
    csv_players = "players_real.csv"

    with Session(engine) as session:
        load_teams(session, csv_teams)
        load_players(session, csv_players)

if __name__ == "__main__":
    main()
