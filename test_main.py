from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_reset_all():
    response = client.delete("/reset-all")
    assert response.status_code == 200
    assert "eliminados" in response.json()["message"]


def test_create_team():
    response = client.post("/teams/", json={
        "name": "Team Test",
        "championships": 3
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Team Test"


def test_create_player():
    # Asegúrate de que el equipo exista primero
    team_response = client.post("/teams/", json={
        "name": "Team Player Test",
        "championships": 1
    })
    team_id = team_response.json()["id"]

    response = client.post("/players/", json={
        "name": "Player Test",
        "gamertag": "PlayerX",
        "kills": 10,
        "deaths": 5,
        "team_id": team_id,
        "image_url": "http://example.com/image.jpg"
    })

    assert response.status_code == 200
    assert response.json()["name"] == "Player Test"


def test_get_all_players():
    response = client.get("/players/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_invalid_team_id():
    response = client.post("/players/", json={
        "name": "Invalid Team Player",
        "gamertag": "FailX",
        "kills": 1,
        "deaths": 1,
        "team_id": 9999
    })
    assert response.status_code == 400
    assert "no existe" in response.json()["detail"]


def test_update_team():
    # Crear equipo
    team_response = client.post("/teams/", json={
        "name": "Old Team Name",
        "championships": 1
    })
    team_id = team_response.json()["id"]

    # Actualizar equipo
    update_response = client.put(f"/teams/{team_id}", json={
        "name": "New Team Name",
        "championships": 5
    })

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "New Team Name"
    assert update_response.json()["championships"] == 5


def test_delete_team():
    # Crear equipo
    team_response = client.post("/teams/", json={
        "name": "Team to Delete",
        "championships": 0
    })
    team_id = team_response.json()["id"]

    # Eliminar equipo
    delete_response = client.delete(f"/teams/{team_id}")
    assert delete_response.status_code == 200
    assert "eliminado" in delete_response.json()["message"].lower()

    # Intentar obtener el equipo eliminado (debería dar error 404)
    get_response = client.get(f"/teams/{team_id}")
    assert get_response.status_code == 404


def test_update_player():
    # Crear equipo
    team_response = client.post("/teams/", json={
        "name": "Team for Player Update",
        "championships": 2
    })
    team_id = team_response.json()["id"]

    # Crear jugador
    player_response = client.post("/players/", json={
        "name": "Player Update",
        "gamertag": "PUX",
        "kills": 3,
        "deaths": 2,
        "team_id": team_id,
        "image_url": None
    })
    player_id = player_response.json()["id"]

    # Actualizar jugador
    update_response = client.put(f"/players/{player_id}", json={
        "kills": 15,
        "deaths": 7
    })

    assert update_response.status_code == 200
    assert update_response.json()["kills"] == 15
    assert update_response.json()["deaths"] == 7


def test_delete_player():
    # Crear equipo
    team_response = client.post("/teams/", json={
        "name": "Team for Player Delete",
        "championships": 0
    })
    team_id = team_response.json()["id"]

    # Crear jugador
    player_response = client.post("/players/", json={
        "name": "Player to Delete",
        "gamertag": "DelX",
        "kills": 1,
        "deaths": 1,
        "team_id": team_id,
        "image_url": None
    })
    player_id = player_response.json()["id"]

    # Eliminar jugador
    delete_response = client.delete(f"/players/{player_id}")
    assert delete_response.status_code == 200
    assert "eliminado" in delete_response.json()["message"].lower()

    # Intentar obtener el jugador eliminado (debería dar error 404)
    get_response = client.get(f"/players/{player_id}")
    assert get_response.status_code == 404
