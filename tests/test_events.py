import uuid


def unique(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_list_events(client):
    response = client.get("/events")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_event_created_on_url_creation(client):
    name = unique("eventuser")
    user = client.post("/users", json={
        "username": name,
        "email": f"{name}@example.com"
    })
    assert user.status_code == 201
    user_id = user.get_json()["id"]

    client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://eventtest.com"
    })

    response = client.get("/events")
    events = response.get_json()
    created_events = [e for e in events if e["event_type"] == "created"]
    assert len(created_events) > 0