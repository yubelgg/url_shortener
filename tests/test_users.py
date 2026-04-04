import uuid


def unique(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_create_user(client):
    name = unique("user")
    response = client.post("/users", json={
        "username": name,
        "email": f"{name}@example.com"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["username"] == name


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
    name = unique("dupe")
    client.post("/users", json={
        "username": name,
        "email": f"{name}@example.com"
    })
    response = client.post("/users", json={
        "username": name,
        "email": f"{name}@example.com"
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
    name = unique("getme")
    create = client.post("/users", json={
        "username": name,
        "email": f"{name}@example.com"
    })
    assert create.status_code == 201
    user_id = create.get_json()["id"]

    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.get_json()["username"] == name


def test_get_user_not_found(client):
    response = client.get("/users/999999")
    assert response.status_code == 404


def test_update_user(client):
    name = unique("update")
    create = client.post("/users", json={
        "username": name,
        "email": f"{name}@example.com"
    })
    assert create.status_code == 201
    user_id = create.get_json()["id"]

    new_name = unique("updated")
    response = client.put(f"/users/{user_id}", json={
        "username": new_name
    })
    assert response.status_code == 200
    assert response.get_json()["username"] == new_name


def test_update_user_not_found(client):
    response = client.put("/users/999999", json={
        "username": "nope"
    })
    assert response.status_code == 404