def test_list_events(client):
    response = client.get("/events")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_event_created_on_url_creation(client):
    user = client.post("/users", json={
        "username": "eventuser",
        "email": "eventuser@example.com"
    })
    user_id = user.get_json()["id"]

    client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://eventtest.com"
    })

    response = client.get("/events")
    events = response.get_json()
    created_events = [e for e in events if e["event_type"] == "created"]
    assert len(created_events) > 0