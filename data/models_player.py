from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import validator
from sqlalchemy import Column, BIGINT, ForeignKey

MAX_BIGINT = 9223372036854775807

# --- MODELO PRINCIPAL (TABLA) ---
class Player(SQLModel, table=True):
    id: Optional[int] = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    name: str
    gamertag: str
    kills: int = Field(sa_column=Column(BIGINT))
    deaths: int = Field(sa_column=Column(BIGINT))
    team_id: Optional[int] = Field(sa_column=Column(BIGINT, ForeignKey("team.id"), nullable=True))
    image_url: Optional[str] = None

# --- CREAR PLAYER ---
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

# --- ACTUALIZAR PLAYER ---
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

# --- ELIMINADO (HISTORIAL) ---
class DeletedPlayer(SQLModel, table=True):
    id: Optional[int] = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    name: str
    gamertag: str
    kills: int = Field(sa_column=Column(BIGINT))
    deaths: int = Field(sa_column=Column(BIGINT))
    team_id: Optional[int] = Field(sa_column=Column(BIGINT, ForeignKey("team.id"), nullable=True))
    image_url: Optional[str] = None
