from pydantic import BaseModel
from typing import Optional

# === MODELO EQUIPO ===
class Team(BaseModel):
    name: str
    region: str
    championships: int

class TeamWithID(Team):
    id: int

class UpdatedTeam(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    championships: Optional[int] = None
