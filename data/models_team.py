from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import validator
from sqlalchemy import Column, BIGINT

MAX_BIGINT = 9223372036854775807

# --- MODELO PRINCIPAL (TABLA) ---
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, sa_column=Column(BIGINT, primary_key=True))
    name: str
    region: str
    championships: int = Field(sa_column=Column(BIGINT))
    image_url: Optional[str] = None


# --- CREAR TEAM ---
class TeamCreate(SQLModel):
    name: str
    region: str
    championships: int
    image_url: Optional[str] = None

    @validator('championships')
    def check_bigint_range(cls, v):
        if v < 0:
            raise ValueError("No se permiten valores negativos.")
        if v > MAX_BIGINT:
            raise ValueError(f"El valor no puede ser mayor a {MAX_BIGINT}.")
        return v


# --- ACTUALIZAR TEAM ---
class UpdatedTeam(SQLModel):
    name: Optional[str] = None
    region: Optional[str] = None
    championships: Optional[int] = None
    image_url: Optional[str] = None

    @validator('championships')
    def check_bigint_range(cls, v):
        if v is None:
            return v
        if v < 0:
            raise ValueError("No se permiten valores negativos.")
        if v > MAX_BIGINT:
            raise ValueError(f"El valor no puede ser mayor a {MAX_BIGINT}.")
        return v


# --- ELIMINADO (HISTORIAL) ---
class DeletedTeam(SQLModel, table=True):
    id: Optional[int] = Field(default=None, sa_column=Column(BIGINT, primary_key=True))
    name: str
    region: str
    championships: int = Field(sa_column=Column(BIGINT))
    image_url: Optional[str] = None
