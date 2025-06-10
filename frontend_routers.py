from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from typing import Optional, Union, List # Añadido List para consistencia, aunque no se usa directamente en este snippet
import shutil
import os
from pathlib import Path

# --- NUEVAS IMPORTACIONES PARA ESTADÍSTICAS Y RELACIONES ---
from sqlalchemy import func # Para funciones de agregación como count, sum, avg
from sqlalchemy.orm import selectinload # Para cargar relaciones en las consultas de jugadores
# ------------------------------------------------------------

from fastapi.templating import Jinja2Templates

from utils.db import get_session
from data.models_player import Player, DeletedPlayer
from data.models_team import Team, DeletedTeam
from urllib.parse import urlencode

def validar_extension_jpg(archivo: UploadFile):
    ext = os.path.splitext(archivo.filename)[1].lower()
    if ext != ".jpg":
        # Se lanza una HTTPException si la extensión no es .jpg
        raise HTTPException(status_code=400, detail="Solo se permiten archivos con extensión .jpg")

# Definir la ruta base para este módulo.
# Asumiendo que frontend_routers.py está en la raíz de 'src' (project_root_dir)
# y que 'static' y 'frontend/templates' están directamente bajo 'src'.
project_root_dir = Path(__file__).resolve().parent

# Inicializar templates para este router. La carpeta de plantillas es 'frontend/templates' relativa a project_root_dir
templates = Jinja2Templates(directory=str(project_root_dir / "frontend" / "templates"))

router = APIRouter(prefix="/frontend")

print("✅ frontend_routers.py cargado correctamente")

# ---------------- RUTAS PÚBLICAS (ACCESO DESDE main.py) ------------------------
# Mantengo tu ruta de índice aquí, aunque es común que esté en main.py sin prefijo.
@router.get("/", response_class=HTMLResponse, tags=["Público"])
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#---------------------------- PLAYERS --------------------------------------------------------------------------
@router.get("/players/view", response_class=HTMLResponse, tags=["Frontend Player"])
def show_players(request: Request, session: Session = Depends(get_session)):
    # ACTUALIZADO: Cargar la relación 'team' para poder mostrar el nombre del equipo en la vista
    players = session.exec(select(Player).options(selectinload(Player.team))).all()
    teams = session.exec(select(Team)).all()
    return templates.TemplateResponse("players.html", {"request": request, "players": players, "teams": teams})

@router.get("/players/search", response_class=HTMLResponse, tags=["Frontend Player"])
def search_players(
    request: Request,
    name: Optional[str] = None,
    team_id: Optional[Union[int, str]] = None,
    session: Session = Depends(get_session)
):
    # ACTUALIZADO: Cargar la relación 'team' también en la búsqueda para consistencia
    query = select(Player).options(selectinload(Player.team))

    if name:
        query = query.where(Player.name.ilike(f"%{name}%"))

    if isinstance(team_id, str) and team_id == "":
        team_id = None
    elif isinstance(team_id, str):
        try:
            team_id = int(team_id)
        except ValueError:
            team_id = None

    if team_id is not None:
        query = query.where(Player.team_id == team_id)

    players = session.exec(query).all()
    teams = session.exec(select(Team)).all()
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
    try:
        validar_extension_jpg(image)

        static_dir = project_root_dir / "static"
        os.makedirs(static_dir, exist_ok=True)

        image_path = static_dir / image.filename
        with open(image_path, "wb") as buffer:
            buffer.write(await image.read())

        image_url = f"/static/{image.filename}"

        team = None
        if team_id is not None:
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

        print(f"DEBUG: Jugador '{db_player.name}' (ID: {db_player.id}) creado exitosamente. Redirigiendo...")

        return RedirectResponse("/frontend/players/view", status_code=303)

    except HTTPException as e:
        session.rollback()
        print(f"ERROR: HTTPException al crear jugador: {e.detail}")
        raise e

    except Exception as e:
        session.rollback()
        print(f"ERROR: Error inesperado al crear jugador: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al crear jugador: {e}")


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
    try:
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
            static_dir = project_root_dir / "static"
            os.makedirs(static_dir, exist_ok=True)
            image_path = static_dir / image.filename
            with open(image_path, "wb") as buffer:
                buffer.write(await image.read())
            player.image_url = f"/static/{image.filename}"

        session.add(player)
        session.commit()
        session.refresh(player)

        print(f"DEBUG: Jugador '{player.name}' (ID: {player.id}) actualizado exitosamente.")

        return RedirectResponse(url="/frontend/players/view", status_code=303)

    except HTTPException as e:
        session.rollback()
        print(f"ERROR: HTTPException al actualizar jugador: {e.detail}")
        raise e
    except Exception as e:
        session.rollback()
        print(f"ERROR: Error inesperado al actualizar jugador: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {e}")


#----------------------------- TEAMS ----------------------------------------------------------------------------
@router.get("/teams/view", response_class=HTMLResponse , tags=["Frontend Teams"])
def show_teams(request: Request, session: Session = Depends(get_session)):
    teams = session.exec(select(Team)).all()
    return templates.TemplateResponse("teams.html", {"request": request, "teams": teams})

@router.get("/teams/search", response_class=HTMLResponse, tags=["Frontend Teams"])
def search_teams(
    request: Request,
    name: Optional[str] = None,
    championships: Optional[Union[int, str]] = None,
    session: Session = Depends(get_session)
):
    query = select(Team)
    if name:
        query = query.where(Team.name.ilike(f"%{name}%"))

    if isinstance(championships, str) and championships == "":
        championships = None
    elif isinstance(championships, str):
        try:
            championships = int(championships)
        except ValueError:
            championships = None

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
    return templates.TemplateResponse("team_form.html", {"request": request})

@router.post("/teams-form", tags=["Frontend Teams"])
async def create_team_form(
    name: str = Form(...),
    region: str = Form(...),
    championships: int = Form(...),
    image: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    try:
        validar_extension_jpg(image)

        static_dir = project_root_dir / "static"
        os.makedirs(static_dir, exist_ok=True)

        image_path = static_dir / image.filename
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

        print(f"DEBUG: Equipo '{db_team.name}' (ID: {db_team.id}) creado exitosamente. Redirigiendo...")

        return RedirectResponse(url="/frontend/teams/view", status_code=303)

    except HTTPException as e:
        session.rollback()
        print(f"ERROR: HTTPException al crear equipo: {e.detail}")
        raise e
    except Exception as e:
        session.rollback()
        print(f"ERROR: Error inesperado al crear equipo: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {e}")


@router.post("/teams/delete/{team_id}", tags=["Frontend Teams"])
def delete_team_frontend(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        return RedirectResponse(url="/frontend/teams/view?error=Equipo%20no%20encontrado", status_code=303)

    players = session.exec(select(Player).where(Player.team_id == team_id)).all()
    if players:
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

@router.post("/teams/restore/{team_id}", tags=["Frontend Teams"])
def restore_deleted_team(team_id: int, session: Session = Depends(get_session)):
    try:
        team = session.get(DeletedTeam, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Equipo eliminado no encontrado.")

        restored_team = Team(
            id=team.id,
            name=team.name,
            region=team.region,
            championships=team.championships,
            image_url=team.image_url
        )

        session.add(restored_team)
        session.delete(team)
        session.commit()
        print(f"DEBUG: Equipo '{restored_team.name}' (ID: {restored_team.id}) restaurado exitosamente.")
        return RedirectResponse(url="/frontend/teams/view", status_code=303)

    except HTTPException as e:
        session.rollback()
        print(f"ERROR: HTTPException al restaurar equipo: {e.detail}")
        raise e
    except Exception as e:
        session.rollback()
        print(f"ERROR: Error inesperado al restaurar equipo: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al restaurar equipo: {e}")


@router.post("/teams/delete-permanent/{team_id}", tags=["Frontend Teams"])
def delete_team_permanently(team_id: int, session: Session = Depends(get_session)):
    team = session.get(DeletedTeam, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo eliminado no encontrado.")

    session.delete(team)
    session.commit()
    return RedirectResponse(url="/frontend/teams/deleted/view", status_code=303)

@router.get("/teams/edit/{team_id}", response_class=HTMLResponse, tags=["Frontend Teams"])
def edit_team_form(team_id: int, request: Request, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse("edit_team.html", {"request": request, "team": team})

@router.post("/teams/edit/{team_id}", tags=["Frontend Teams"])
async def update_team_form(
    team_id: int,
    name: str = Form(...),
    region: str = Form(...),
    championships: int = Form(...),
    image: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    try:
        team = session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")

        team.name = name
        team.region = region
        team.championships = championships

        if image:
            validar_extension_jpg(image)
            static_dir = project_root_dir / "static"
            os.makedirs(static_dir, exist_ok=True)
            image_path = static_dir / image.filename
            with open(image_path, "wb") as buffer:
                buffer.write(await image.read())
            team.image_url = f"/static/{image.filename}"

        session.add(team)
        session.commit()
        print(f"DEBUG: Equipo '{team.name}' (ID: {team.id}) actualizado exitosamente.")
        return RedirectResponse(url="/frontend/teams/view", status_code=303)

    except HTTPException as e:
        session.rollback()
        print(f"ERROR: HTTPException al actualizar equipo: {e.detail}")
        raise e
    except Exception as e:
        session.rollback()
        print(f"ERROR: Error inesperado al actualizar equipo: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {e}")


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

# ---------------- APARTADO DE ESTADÍSTICAS ------------------------
@router.get("/estadisticas", response_class=HTMLResponse, tags=["Estadísticas"])
def show_statistics(request: Request, session: Session = Depends(get_session)):
    stats = {}

    # 1. Total de jugadores
    # Usar .one() para obtener el valor escalar directamente de la función de agregación
    stats['total_jugadores'] = session.exec(select(func.count(Player.id))).one()

    # 2. Total de equipos
    stats['total_equipos'] = session.exec(select(func.count(Team.id))).one()

    # 3. Jugador con más kills (manejo de caso sin jugadores)
    top_player_kills = session.exec(select(Player).order_by(Player.kills.desc()).limit(1)).first()
    stats['jugador_mas_kills_nombre'] = top_player_kills.name if top_player_kills else "N/A"
    stats['jugador_mas_kills_valor'] = top_player_kills.kills if top_player_kills else 0

    # 4. Jugador con más muertes (manejo de caso sin jugadores)
    top_player_deaths = session.exec(select(Player).order_by(Player.deaths.desc()).limit(1)).first()
    stats['jugador_mas_deaths_nombre'] = top_player_deaths.name if top_player_deaths else "N/A"
    stats['jugador_mas_deaths_valor'] = top_player_deaths.deaths if top_player_deaths else 0

    # 5. Equipo con más campeonatos (manejo de caso sin equipos)
    top_team_championships = session.exec(select(Team).order_by(Team.championships.desc()).limit(1)).first()
    stats['equipo_mas_campeonatos_nombre'] = top_team_championships.name if top_team_championships else "N/A"
    stats['equipo_mas_campeonatos_valor'] = top_team_championships.championships if top_team_championships else 0

    # 6. Promedio de Kills por jugador
    # .scalar_one_or_none() aquí es apropiado para SUM si el resultado podría ser None (no hay filas)
    total_kills = session.exec(select(func.sum(Player.kills))).scalar_one_or_none() or 0
    total_players_for_avg = stats['total_jugadores'] # Reutilizamos el total de jugadores ya calculado
    stats['promedio_kills_por_jugador'] = round(total_kills / total_players_for_avg, 2) if total_players_for_avg > 0 else 0.0

    # 7. Promedio de Deaths por jugador
    total_deaths = session.exec(select(func.sum(Player.deaths))).scalar_one_or_none() or 0
    stats['promedio_deaths_por_jugador'] = round(total_deaths / total_players_for_avg, 2) if total_players_for_avg > 0 else 0.0

    # 8. K/D Ratio promedio de todos los jugadores
    if total_deaths > 0:
        stats['promedio_kd_ratio'] = round(total_kills / total_deaths, 2)
    else:
        stats['promedio_kd_ratio'] = "∞" # Infinito si no hay muertes (o no hay jugadores con muertes)

    return templates.TemplateResponse("estadisticas.html", {"request": request, "stats": stats})