from pydantic import BaseModel
from typing import Optional

class Player(BaseModel):
    name: str
    gamertag: str
    team: str
    kills: int
    deaths: int

class PlayerWithID(Player):
    id: int

class Team(BaseModel):
    name: str
    region: str
    championships: int

class TeamWithID(Team):
    id: int

class UpdatedPlayer(BaseModel):
    name: Optional[str] = None
    gamertag: Optional[str] = None
    team: Optional[str] = None
    kills: Optional[int] = None
    deaths: Optional[int] = None

class UpdatedTeam(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    championships: Optional[int] = None
