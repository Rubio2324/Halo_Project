from sqlmodel import SQLModel, Field
from typing import Optional

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    gamertag: str
    kills: int
    deaths: int
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

class UpdatedPlayer(SQLModel):
    name: Optional[str] = None
    gamertag: Optional[str] = None
    kills: Optional[int] = None
    deaths: Optional[int] = None
    team_id: Optional[int] = None
