from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from typing import Optional
import shutil
import os
from pathlib import Path

from utils.db import get_session
from data.models_player import Player,DeletedPlayer
from data.models_team import Team, DeletedTeam
from fastapi.templating import Jinja2Templates
from urllib.parse import urlencode

def validar_extension_jpg(archivo: UploadFile):
    ext = os.path.splitext(archivo.filename)[1].lower()
    if ext != ".jpg":
        raise HTTPException(status_code=400, detail="Solo se permiten archivos con extensión .jpg")


templates = Jinja2Templates(directory="frontend/templates")

router = APIRouter(prefix="/frontend")

print("✅ frontend_routers.py cargado correctamente")

#---------------------------- PLAYERS --------------------------------------------------------------------------
@router.get("/players/view", response_class=HTMLResponse, tags=["Frontend Player"])
def show_players(request: Request, session: Session = Depends(get_session)):
    players = session.exec(select(Player)).all()
    teams = session.exec(select(Team)).all()
    return templates.TemplateResponse("players.html", {"request": request, "players": players, "teams": teams})

@router.get("/players/search", response_class=HTMLResponse, tags=["Frontend Player"])
def search_players(
    request: Request,
    name: Optional[str] = None,
    team_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    query = select(Player)

    if name:
        query = query.where(Player.name.ilike(f"%{name}%"))
    if team_id is not None:
        query = query.where(Player.team_id == team_id)

    players = session.exec(query).all()
    teams = session.exec(select(Team)).all()  # Para el formulario

    return templates.TemplateResponse("players.html", {"request": request, "players": players, "teams": teams})

@router.get("/deleted-players/view", response_class=HTMLResponse, tags=["Frontend Player"])
def show_deleted_players(request: Request, session: Session = Depends(get_session)):
    players = session.exec(select(DeletedPlayer)).all()
    return templates.TemplateResponse("deleted_players.html", {"request": request, "players": players})

@router.get("/form/players", response_class=HTMLResponse, tags=["Frontend Player"])
def form_create_player(request: Request, session: Session = Depends(get_session)):
    teams = session.exec(select(Team)).all()
    if not teams:
        raise HTTPException(status_code=400, detail="No hay equipos registrados.")
    return templates.TemplateResponse("player_form.html", {"request": request, "teams": teams})

@router.post("/players-form", tags=["Frontend Player"])
async def create_player_form(
    request: Request,
    session: Session = Depends(get_session),
    name: str = Form(...),
    gamertag: str = Form(...),
    kills: int = Form(...),
    deaths: int = Form(...),
    team_id: Optional[int] = Form(None),
    image: UploadFile = File(...)
):
    validar_extension_jpg(image)

    os.makedirs("static", exist_ok=True)

    image_path = f"static/{image.filename}"
    with open(image_path, "wb") as buffer:
        buffer.write(await image.read())

    image_url = f"/static/{image.filename}"

    if team_id:
        team = session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=400, detail=f"El team_id {team_id} no existe")

    db_player = Player(
        name=name,
        gamertag=gamertag,
        kills=kills,
        deaths=deaths,
        team_id=team_id,
        image_url=image_url
    )

    session.add(db_player)
    session.commit()
    session.refresh(db_player)
    return RedirectResponse("/frontend/players/view", status_code=303)

@router.post("/players/delete/{player_id}", tags=["Frontend Player"])
def delete_player_frontend(player_id: int, session: Session = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado.")

    deleted_player = DeletedPlayer(
        id=player.id,
        name=player.name,
        gamertag=player.gamertag,
        kills=player.kills,
        deaths=player.deaths,
        team_id=player.team_id,
        image_url=player.image_url
    )

    session.add(deleted_player)
    session.delete(player)
    session.commit()

    return RedirectResponse(url="/frontend/players/view", status_code=303)

@router.post("/players/restore/{player_id}", tags=["Frontend Player"])
def restore_deleted_player(player_id: int, session: Session = Depends(get_session)):
    player = session.get(DeletedPlayer, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador eliminado no encontrado")

    # Validar si el equipo existe antes de restaurar (modo estricto)
    if player.team_id:
        team = session.get(Team, player.team_id)
        if not team:
            raise HTTPException(status_code=400, detail=f"El equipo con ID {player.team_id} no existe")

    restored = Player(
        id=player.id,
        name=player.name,
        gamertag=player.gamertag,
        kills=player.kills,
        deaths=player.deaths,
        team_id=player.team_id,
        image_url=player.image_url
    )

    session.add(restored)
    session.delete(player)
    session.commit()
    return RedirectResponse(url="/frontend/players/view", status_code=303)

@router.post("/deleted-players/delete/{player_id}", tags=["Frontend Player"])
def delete_player_permanently(player_id: int, session: Session = Depends(get_session)):
    player = session.get(DeletedPlayer, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador eliminado no encontrado")
    session.delete(player)
    session.commit()
    return RedirectResponse("/frontend/deleted-players/view", status_code=303)

@router.get("/players/edit/{player_id}", response_class=HTMLResponse, tags=["Frontend Player"])
def edit_player_form(player_id: int, request: Request, session: Session = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado.")

    teams = session.exec(select(Team)).all()
    return templates.TemplateResponse("edit_player.html", {"request": request, "player": player, "teams": teams})


@router.post("/players/update/{player_id}", tags=["Frontend Player"])
async def update_player_form(
    player_id: int,
    name: str = Form(...),
    gamertag: str = Form(...),
    kills: int = Form(...),
    deaths: int = Form(...),
    team_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado.")

    if team_id:
        team = session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=400, detail="Equipo no válido.")

    player.name = name
    player.gamertag = gamertag
    player.kills = kills
    player.deaths = deaths
    player.team_id = team_id

    if image:
        validar_extension_jpg(image)
        os.makedirs("static", exist_ok=True)
        image_path = f"static/{image.filename}"
        with open(image_path, "wb") as buffer:
            buffer.write(await image.read())
        player.image_url = f"/static/{image.filename}"

    session.add(player)
    session.commit()
    session.refresh(player)

    return RedirectResponse(url="/frontend/players/view", status_code=303)




#----------------------------- TEAMS ----------------------------------------------------------------------------
@router.get("/teams/view", response_class=HTMLResponse , tags=["Frontend Teams"])
def show_teams(request: Request, session: Session = Depends(get_session)):
    teams = session.exec(select(Team)).all()
    return templates.TemplateResponse("teams.html", {"request": request, "teams": teams})

@router.get("/teams/search", response_class=HTMLResponse, tags=["Frontend Teams"])
def search_teams(
    request: Request,
    name: Optional[str] = None,
    championships: Optional[int] = None,
    session: Session = Depends(get_session)
):
    query = select(Team)
    if name:
        query = query.where(Team.name.ilike(f"%{name}%"))
    if championships is not None:
        query = query.where(Team.championships == championships)
    teams = session.exec(query).all()
    return templates.TemplateResponse("teams.html", {"request": request, "teams": teams})

@router.get("/teams/deleted/view", response_class=HTMLResponse, tags=["Frontend Teams"])
def view_deleted_teams(request: Request, session: Session = Depends(get_session)):
    teams = session.exec(select(DeletedTeam)).all()
    return templates.TemplateResponse("deleted_teams.html", {"request": request, "teams": teams})

@router.get("/teams-form", response_class=HTMLResponse, tags=["Frontend Teams"])
def form_team(request: Request):
    return templates.TemplateResponse("create_team.html", {"request": request})

@router.post("/teams-form", tags=["Frontend Teams"])
async def create_team_form(
    name: str = Form(...),
    region: str = Form(...),
    championships: int = Form(...),
    image: UploadFile = File(...),
    session: Session = Depends(get_session)  # ✅ CORRECTO
):
    validar_extension_jpg(image)

    # Crear carpeta si no existe
    if not os.path.exists("static"):
        os.makedirs("static")

    image_path = f"static/{image.filename}"
    with open(image_path, "wb") as buffer:
        buffer.write(await image.read())

    image_url = f"/static/{image.filename}"

    db_team = Team(
        name=name,
        region=region,
        championships=championships,
        image_url=image_url
    )

    session.add(db_team)
    session.commit()
    session.refresh(db_team)

    return RedirectResponse(url="/frontend/teams/view", status_code=303)

@router.post("/teams/delete/{team_id}", tags=["Frontend Teams"])
def delete_team_frontend(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")

    players = session.exec(select(Player).where(Player.team_id == team_id)).all()
    if players:
        raise HTTPException(status_code=400, detail="No se puede eliminar el equipo porque tiene jugadores asignados.")

    deleted_team = DeletedTeam(
        id=team.id,
        name=team.name,
        region=team.region,
        championships=team.championships,
        image_url=team.image_url
    )

    session.add(deleted_team)
    session.delete(team)
    session.commit()

    return RedirectResponse(url="/frontend/teams/view", status_code=303)


@router.post("/teams/delete/{team_id}", tags=["Frontend Teams"])
def delete_team_frontend(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        return RedirectResponse(url="/frontend/teams/view?error=Equipo%20no%20encontrado", status_code=303)

    players = session.exec(select(Player).where(Player.team_id == team_id)).all()
    if players:
        # Redirige con mensaje de error si hay jugadores asignados
        message = urlencode({"error": "No se puede eliminar el equipo porque tiene jugadores asignados."})
        return RedirectResponse(url=f"/frontend/teams/view?{message}", status_code=303)

    deleted_team = DeletedTeam(
        id=team.id,
        name=team.name,
        region=team.region,
        championships=team.championships,
        image_url=team.image_url
    )

    session.add(deleted_team)
    session.delete(team)
    session.commit()

    return RedirectResponse(url="/frontend/teams/view", status_code=303)


@router.post("/teams/delete-permanent/{team_id}", tags=["Frontend Teams"])
def delete_team_permanently(team_id: int, session: Session = Depends(get_session)):
    team = session.get(DeletedTeam, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo eliminado no encontrado.")

    session.delete(team)
    session.commit()
    return RedirectResponse(url="/frontend/teams/deleted/view", status_code=303)

from fastapi import UploadFile, File

# GET: Mostrar formulario de edición
@router.get("/teams/edit/{team_id}", response_class=HTMLResponse, tags=["Frontend Teams"])
def edit_team_form(team_id: int, request: Request, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse("edit_team.html", {"request": request, "team": team})


# POST: Procesar formulario de edición
@router.post("/teams/edit/{team_id}", tags=["Frontend Teams"])
async def update_team_form(
    team_id: int,
    name: str = Form(...),
    region: str = Form(...),
    championships: int = Form(...),
    image: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    team.name = name
    team.region = region
    team.championships = championships

    if image:
        validar_extension_jpg(image)
        os.makedirs("static", exist_ok=True)
        image_path = f"static/{image.filename}"
        with open(image_path, "wb") as buffer:
            buffer.write(await image.read())
        team.image_url = f"/static/{image.filename}"

    session.add(team)
    session.commit()
    return RedirectResponse(url="/frontend/teams/view", status_code=303)

# ---------------- INFORMACIÓN Y DOCUMENTACIÓN ------------------------

@router.get("/info/developer", response_class=HTMLResponse, tags=["Informativo"])
def developer_info(request: Request):
    return templates.TemplateResponse("developer_info.html", {"request": request})

@router.get("/info/objective", response_class=HTMLResponse, tags=["Informativo"])
def project_objective(request: Request):
    return templates.TemplateResponse("project_objective.html", {"request": request})

@router.get("/docs/planning", response_class=HTMLResponse, tags=["Documentación"])
def planning_info(request: Request):
    return templates.TemplateResponse("planning_info.html", {"request": request})

@router.get("/docs/design", response_class=HTMLResponse, tags=["Documentación"])
def design_info(request: Request):
    return templates.TemplateResponse("design_info.html", {"request": request})

