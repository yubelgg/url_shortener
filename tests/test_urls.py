def test_create_url(client):
    # Create a user first
    user = client.post("/users", json={
        "username": "urluser",
        "email": "urluser@example.com"
    })
    user_id = user.get_json()["id"]

    response = client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
        "title": "Example"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["original_url"] == "https://example.com"
    assert data["short_code"] is not None


def test_create_url_missing_fields(client):
    response = client.post("/urls", json={
        "user_id": 1
    })
    assert response.status_code == 400


def test_create_url_user_not_found(client):
    response = client.post("/urls", json={
        "user_id": 999999,
        "original_url": "https://example.com"
    })
    assert response.status_code == 404


def test_list_urls(client):
    response = client.get("/urls")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_list_urls_filter_by_user(client):
    user = client.post("/users", json={
        "username": "filteruser",
        "email": "filteruser@example.com"
    })
    user_id = user.get_json()["id"]

    client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://filtered.com"
    })

    response = client.get(f"/urls?user_id={user_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert all(u["user_id"] == user_id for u in data)


def test_get_url(client):
    user = client.post("/users", json={
        "username": "geturluser",
        "email": "geturluser@example.com"
    })
    user_id = user.get_json()["id"]

    create = client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://getme.com"
    })
    url_id = create.get_json()["id"]

    response = client.get(f"/urls/{url_id}")
    assert response.status_code == 200
    assert response.get_json()["original_url"] == "https://getme.com"


def test_get_url_not_found(client):
    response = client.get("/urls/999999")
    assert response.status_code == 404


def test_update_url(client):
    user = client.post("/users", json={
        "username": "updateurluser",
        "email": "updateurluser@example.com"
    })
    user_id = user.get_json()["id"]

    create = client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://old.com"
    })
    url_id = create.get_json()["id"]

    response = client.put(f"/urls/{url_id}", json={
        "title": "New Title",
        "is_active": False
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "New Title"
    assert data["is_active"] is False


def test_update_url_not_found(client):
    response = client.put("/urls/999999", json={
        "title": "nope"
    })
    assert response.status_code == 404