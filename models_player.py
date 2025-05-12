from sqlmodel import SQLModel, Field
from typing import Optional

# === MODELOS JUGADOR ===
class PlayerCreate(SQLModel):
    name: str
    nickname: str
    team_id: Optional[int] = None

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    gamertag: str
    team: str
    kills: int
    deaths: int

class UpdatedPlayer(SQLModel):
    name: Optional[str] = None
    gamertag: Optional[str] = None
    team: Optional[str] = None
    kills: Optional[int] = None
    deaths: Optional[int] = None