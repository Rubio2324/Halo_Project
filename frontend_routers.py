from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from utils.db import get_session
from data.models_player import Player
from data.models_team import Team

templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter(prefix="/frontend", tags=["Frontend"])

print("✅ frontend_routers.py cargado correctamente")

@router.get("/players/view", response_class=HTMLResponse)
def show_players(request: Request, session: Session = Depends(get_session)):
    players = session.exec(select(Player)).all()
    return templates.TemplateResponse("players.html", {"request": request, "players": players})

@router.get("/teams/view", response_class=HTMLResponse)
def show_teams(request: Request, session: Session = Depends(get_session)):
    teams = session.exec(select(Team)).all()
    return templates.TemplateResponse("teams.html", {"request": request, "teams": teams})
