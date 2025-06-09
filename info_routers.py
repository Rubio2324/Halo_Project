# info_routes.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/developer-info", tags=["Información"])
def developer_info():
    return {
        "nombre": "Luis David Rubio Ramirez",
        "correo": "ldrubio31@ucarolica.edu.co",
        "carrera": "Ingeniería de Sistemas",
        "universidad": "Universidad Catolica de Colombia",
        "semestre": "5",
        "github": "https://github.com/Rubio2324"
    }

@router.get("/project-objective", tags=["Información"])
def project_objective():
    return {
        "objetivo": "Desarrollar un sistema de gestión para jugadores y equipos de Halo eSports, incluyendo control de historial, imágenes, filtros, validaciones y estadísticas, con una arquitectura limpia y desplegado en la web con conexión a una base de datos en línea."
                    "resuelve:" "Permite administrar información detallada de competencias de Halo con estadísticas reales, visualización ordenada y control de cambios. Útil para ligas, torneos y fanáticos."
    "tecnologias:"
        "Python + FastAPI"
        "SQLModel + PostgreSQL"
        "Render (deploy backend y base de datos)"
        "GitHub (control de versiones)"
        "Supabase (almacenamiento de imágenes)"
        "pytest (testing backend)"
    }


@router.get("/planning-info", tags=["Documentación"])
def planning_info():
    return {
        "objetivos": [
            "Gestionar jugadores y equipos profesionales de Halo eSports.",
            "Permitir registro, consulta, edición y eliminación lógica de datos.",
            "Visualizar estadísticas clave de jugadores y equipos."
        ],
        "fuente_datos_reales": [
            "https://liquipedia.net/halo/Halo_Championship_Series/2024/Charlotte",
            "https://www.halodatahive.com/",
            "https://twitter.com/HCS"
        ],
        "modelo_datos": "El modelo incluye campos como nombre, gamertag, kills, deaths, equipo y URL de imagen.",
        "casos_uso": [
            "Registrar jugadores con sus estadísticas.",
            "Consultar jugadores por nombre o equipo.",
            "Registrar equipos y asociarlos a jugadores.",
            "Actualizar información de jugadores y equipos.",
            "Eliminar lógicamente jugadores y equipos manteniendo historial."
        ],
        "imagen_casos_uso_url": "https://ufhpjqntmtiyxplisbkg.supabase.co/storage/v1/object/sign/halo-imagenes/diagrama_casos_uso.png?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV80NTYyYWRmMi05NzRhLTQ5N2ItYTkwYS1kZDdhNjAxNjIxMzkiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJoYWxvLWltYWdlbmVzL2RpYWdyYW1hX2Nhc29zX3Vzby5wbmciLCJpYXQiOjE3NDk0NTU4MTYsImV4cCI6MTc4MDk5MTgxNn0.iJfl42NWhh8G14paxWS1nbjprmTv7LW2GM0ptgmxpJQ"
    }

@router.get("/design-info", tags=["Documentación"])
def design_info():
    return {
        "diagrama_clases": "Representa las relaciones entre Player, Team, DeletedPlayer, DeletedTeam.",
        "mapa_endpoints": "Incluye rutas para CRUD de jugadores y equipos, búsqueda, historial, planificación y diseño.",
        "mockups": "Los wireframes se presentarán en la fase frontend.",
        "imagen_diagrama_clases_url": "https://ufhpjqntmtiyxplisbkg.supabase.co/storage/v1/object/sign/halo-imagenes/Diagrama%20de%20Clases%20Proyecto.png?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV80NTYyYWRmMi05NzRhLTQ5N2ItYTkwYS1kZDdhNjAxNjIxMzkiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJoYWxvLWltYWdlbmVzL0RpYWdyYW1hIGRlIENsYXNlcyBQcm95ZWN0by5wbmciLCJpYXQiOjE3NDk0NTU4NTUsImV4cCI6MTc4MDk5MTg1NX0.3ZeoRLUu9oIMWaZ9_cduvY2JF9BpAIlQIve2T93pho0"
    }
