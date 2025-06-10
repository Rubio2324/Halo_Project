from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from typing import Optional, Union, List # Asegúrate de que 'Union' y 'List' estén aquí
import shutil
import os
from pathlib import Path

from sqlalchemy import func # <-- ¡Añade esta línea para funciones de agregación!
from sqlalchemy.orm import selectinload # <-- ¡Añade esta línea para cargar relaciones!

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

# NOTA: Si este router tiene un prefix="/frontend", entonces la ruta "/" interna
# de este router se traduce a "/frontend/". Si tu index está en la raíz del dominio,
# esta función debería estar en main.py sin prefijo o usar url_for con 'name' definido en main.py.
# Para propósitos de este archivo, la dejamos aquí asumiendo que /frontend/ es el inicio del frontend.
@router.get("/", response_class=HTMLResponse, tags=["Público"])
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


#---------------------------- PLAYERS --------------------------------------------------------------------------
@router.get("/players/view", response_class=HTMLResponse, tags=["Frontend Player"])
def show_players(request: Request, session: Session = Depends(get_session)):
    # ¡IMPORTANTE! Cargar la relación 'team' para poder mostrar el nombre del equipo
    players = session.exec(select(Player).options(selectinload(Player.team))).all()
    teams = session.exec(select(Team)).all() # Necesario para el dropdown del formulario
    return templates.TemplateResponse("players.html", {"request": request, "players": players, "teams": teams})

@router.get("/players/search", response_class=HTMLResponse, tags=["Frontend Player"])
def search_players(
    request: Request,
    name: Optional[str] = None,
    team_id: Optional[Union[int, str]] = None,
    session: Session = Depends(get_session)
):
    # ¡IMPORTANTE! Cargar la relación 'team' para poder mostrar el nombre del equipo en los resultados
    query = select(Player).options(selectinload(Player.team))

    if name:
        query = query.where(Player.name.ilike(f"%{name}%"))

    # Convertir "" a None para team_id
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
    teams = session.exec(select(Team)).all()  # Para el formulario
    return templates.TemplateResponse("players.html", {"request": request, "players": players, "teams": teams})

@router.get("/deleted-players/view", response_class=HTMLResponse, tags=["Frontend Player"])
def show_deleted_players(request: Request, session: Session = Depends(get_session)):
    # También es una buena práctica cargar la relación del equipo aquí si la tabla deleted_players tiene team_id
    # players = session.exec(select(DeletedPlayer).options(selectinload(DeletedPlayer.team))).all()
    # (Asumiendo que DeletedPlayer tiene una relación a Team si team_id se mantiene)
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
    try: # Inicia el bloque try
        validar_extension_jpg(image)

        static_dir = project_root_dir / "static"
        os.makedirs(static_dir, exist_ok=True)  # Crea la carpeta si no existe

        image_path = static_dir / image.filename
        # Asegúrate de que el nombre del archivo no cause problemas (ej. caracteres especiales, duplicados)
        # Podrías generar un nombre único si es necesario, pero por ahora usamos el original
        with open(image_path, "wb") as buffer:
            buffer.write(await image.read())

        image_url = f"/static/{image.filename}" # La URL para el navegador

        team = None
        if team_id is not None: # Solo intenta buscar el equipo si se proporcionó un team_id
            team = session.get(Team, team_id)
            if not team:
                raise HTTPException(status_code=400, detail=f"El team_id {team_id} no existe")

        db_player = Player(
            name=name,
            gamertag=gamertag,
            kills=kills,
            deaths=deaths,
            team_id=team_id, # Esto puede ser None si no se seleccionó un equipo
            image_url=image_url
        )

        session.add(db_player)
        session.commit()
        session.refresh(db_player)

        # Log para depuración
        print(f"DEBUG: Jugador '{db_player.name}' (ID: {db_player.id}) creado exitosamente. Redirigiendo...")

        return RedirectResponse("/frontend/players/view", status_code=303)

    except HTTPException as e:
        # Esto captura las excepciones lanzadas por validar_extension_jpg o por la no existencia del team_id
        session.rollback() # Asegúrate de hacer rollback si algo falla antes del commit final
        print(f"ERROR: HTTPException al crear jugador: {e.detail}")
        raise e # Re-lanza la excepción para que FastAPI la maneje y muestre al usuario

    except Exception as e:
        # Esto capturará cualquier otro error inesperado (ej. problemas de DB, escritura de archivo)
        session.rollback() # Importante: si hay un error, haz rollback
        print(f"ERROR: Error inesperado al crear jugador: {e}")
        # Puedes redirigir a una página de error o mostrar un mensaje genérico
        # Para depuración, es mejor lanzar una HTTPException 500
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
    try: # Inicia el bloque try
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

    # Convertir "" a None para championships
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
    try: # Inicia el bloque try
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


# ÚNICA FUNCIÓN delete_team_frontend - la duplicada ha sido eliminada.
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
        team = session.get(DeletedTeam, team_id) # Busca en DeletedTeam
        if not team:
            raise HTTPException(status_code=404, detail="Equipo eliminado no encontrado.")

        # Opcional: Validar si el equipo ya existe en la tabla de Team principal con el mismo ID
        # Esto es importante si el ID no es auto-generado al restaurar o si hay UNIQUE constraints por nombre
        # Si el ID es una PK y se reutiliza, y SQLModel maneja bien los IDs, esta parte puede ser omitida.
        # current_team = session.get(Team, team_id)
        # if current_team:
        #     raise HTTPException(status_code=400, detail=f"El equipo con ID {team_id} ya existe en la tabla principal.")

        restored_team = Team( # Crea una nueva instancia del modelo Team
            id=team.id,
            name=team.name,
            region=team.region,
            championships=team.championships,
            image_url=team.image_url
        )

        session.add(restored_team) # Añade a la tabla Team
        session.delete(team) # Elimina de la tabla DeletedTeam
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
    try: # Inicia el bloque try
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