from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import validator

MAX_BIGINT = 9223372036854775807

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    gamertag: str
    kills: int
    deaths: int
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    image_url: Optional[str] = None  # Nueva columna

class PlayerCreate(SQLModel):
    name: str
    gamertag: str
    kills: int
    deaths: int
    team_id: Optional[int] = None
    image_url: Optional[str] = None

    @validator('kills', 'deaths')
    def check_bigint_range(cls, v):
        if v < 0:
            raise ValueError("No se permiten valores negativos.")
        if v > MAX_BIGINT:
            raise ValueError(f"El valor no puede ser mayor a {MAX_BIGINT}.")
        return v

class UpdatedPlayer(SQLModel):
    name: Optional[str] = None
    gamertag: Optional[str] = None
    kills: Optional[int] = None
    deaths: Optional[int] = None
    team_id: Optional[int] = None
    image_url: Optional[str] = None

    @validator('kills', 'deaths')
    def check_bigint_range(cls, v):
        if v is None:
            return v
        if v < 0:
            raise ValueError("No se permiten valores negativos.")
        if v > MAX_BIGINT:
            raise ValueError(f"El valor no puede ser mayor a {MAX_BIGINT}.")
        return v

class DeletedPlayer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    gamertag: str
    kills: int
    deaths: int
    team_id: Optional[int] = None
    image_url: Optional[str] = None
