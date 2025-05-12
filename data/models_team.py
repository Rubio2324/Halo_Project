from sqlmodel import SQLModel, Field
from typing import Optional

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    region: str
    championships: int

class UpdatedTeam(SQLModel):
    name: Optional[str] = None
    region: Optional[str] = None
    championships: Optional[int] = None
