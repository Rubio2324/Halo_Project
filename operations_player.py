import csv
from models_player import Player, PlayerWithID, UpdatedPlayer
from typing import Optional

FILENAME = "player.csv"
FIELDS = ["id", "name", "gamertag", "team", "kills", "deaths"]

def read_all_players():
    with open(FILENAME) as f:
        reader = csv.DictReader(f)
        return [PlayerWithID(**row) for row in reader]

def read_player_by_id(player_id: int):
    for player in read_all_players():
        if player.id == player_id:
            return player

def get_next_id():
    try:
        players = read_all_players()
        return max(p.id for p in players) + 1
    except:
        return 1

def write_player(player: PlayerWithID):
    with open(FILENAME, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow(player.model_dump())

def new_player(player: Player):
    id = get_next_id()
    player_with_id = PlayerWithID(id=id, **player.model_dump())
    write_player(player_with_id)
    return player_with_id

def modify_player(player_id: int, update: UpdatedPlayer):
    players = read_all_players()
    updated = None

    for i, p in enumerate(players):
        if p.id == player_id:
            updated_data = p.model_dump()
            for field, value in update.model_dump(exclude_none=True).items():
                updated_data[field] = value
            updated = PlayerWithID(**updated_data)
            players[i] = updated
            break

    if updated:
        with open(FILENAME, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for p in players:
                writer.writerow(p.model_dump())
        return updated

def delete_player(player_id: int):
    players = read_all_players()
    deleted = None
    with open(FILENAME, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for p in players:
            if p.id == player_id:
                deleted = p
                continue
            writer.writerow(p.model_dump())
    return deleted

