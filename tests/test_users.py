import json


def test_create_user(client):
    response = client.post("/users", json={
        "username": "testuser123",
        "email": "testuser123@example.com"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["username"] == "testuser123"
    assert data["email"] == "testuser123@example.com"


def test_create_user_missing_fields(client):
    response = client.post("/users", json={})
    assert response.status_code == 400


def test_create_user_invalid_types(client):
    response = client.post("/users", json={
        "username": 123,
        "email": "test@example.com"
    })
    assert response.status_code == 400


def test_create_duplicate_user(client):
    client.post("/users", json={
        "username": "dupeuser",
        "email": "dupeuser@example.com"
    })
    response = client.post("/users", json={
        "username": "dupeuser",
        "email": "dupeuser@example.com"
    })
    assert response.status_code == 400


def test_list_users(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_list_users_pagination(client):
    response = client.get("/users?page=1&per_page=5")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) <= 5


def test_get_user(client):
    # Create a user first
    create = client.post("/users", json={
        "username": "getme",
        "email": "getme@example.com"
    })
    user_id = create.get_json()["id"]

    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.get_json()["username"] == "getme"


def test_get_user_not_found(client):
    response = client.get("/users/999999")
    assert response.status_code == 404


def test_update_user(client):
    create = client.post("/users", json={
        "username": "updateme",
        "email": "updateme@example.com"
    })
    user_id = create.get_json()["id"]

    response = client.put(f"/users/{user_id}", json={
        "username": "updated_name"
    })
    assert response.status_code == 200
    assert response.get_json()["username"] == "updated_name"


def test_update_user_not_found(client):
    response = client.put("/users/999999", json={
        "username": "nope"
    })
    assert response.status_code == 404