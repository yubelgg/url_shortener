import uuid


def unique(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _create_user_and_url(client):
    name = unique("redir")
    u = client.post("/users", json={"username": name, "email": f"{name}@example.com"})
    assert u.status_code == 201
    uid = u.get_json()["id"]
    r = client.post(
        "/urls",
        json={"user_id": uid, "original_url": "https://redirect-target.example/path"},
    )
    assert r.status_code == 201
    return r.get_json()


def test_redirect_active_returns_302_and_logs_click(client):
    data = _create_user_and_url(client)
    code = data["short_code"]

    before = client.get("/events").get_json()
    click_count = sum(1 for e in before if e.get("event_type") == "clicked")

    resp = client.get(f"/r/{code}", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers.get("Location") == "https://redirect-target.example/path"

    after = client.get("/events").get_json()
    assert sum(1 for e in after if e.get("event_type") == "clicked") == click_count + 1


def test_redirect_unknown_code_404(client):
    resp = client.get("/r/n0pexx", follow_redirects=False)
    assert resp.status_code == 404
    assert "error" in resp.get_json()


def test_redirect_code_too_long_400(client):
    resp = client.get("/r/abcdefghijklmnop", follow_redirects=False)
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_redirect_inactive_url_404(client):
    data = _create_user_and_url(client)
    url_id = data["id"]
    code = data["short_code"]
    client.put(f"/urls/{url_id}", json={"is_active": False})

    resp = client.get(f"/r/{code}", follow_redirects=False)
    assert resp.status_code == 404


def test_create_url_rejects_non_integer_user_id(client):
    r = client.post(
        "/urls",
        json={"user_id": "1", "original_url": "https://a.com"},
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400
    assert "user_id" in r.get_json().get("error", "").lower()


def test_create_url_rejects_wrong_content_type(client):
    r = client.post(
        "/urls",
        data="user_id=1&original_url=https://a.com",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 400
