def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok"}


def test_register_login_me(client):
    r = client.post(
        "/api/auth/register",
        json={"name": "Asha", "email": "Asha@Example.com", "password": "secret123"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "asha@example.com"
    assert body["role"] == "patient"
    assert "password" not in body and "password_hash" not in body

    r = client.post("/api/auth/login", json={"email": "asha@example.com", "password": "secret123"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["name"] == "Asha"


def test_register_duplicate_email(client, make_user):
    make_user(email="dup@example.com")
    r = client.post(
        "/api/auth/register",
        json={"name": "X", "email": "dup@example.com", "password": "secret123"},
    )
    assert r.status_code == 409


def test_register_cannot_choose_role(client):
    r = client.post(
        "/api/auth/register",
        json={"name": "Sneaky", "email": "s@example.com", "password": "secret123", "role": "admin"},
    )
    assert r.status_code == 201
    assert r.json()["role"] == "patient"


def test_short_password_rejected(client):
    r = client.post(
        "/api/auth/register",
        json={"name": "X", "email": "x@example.com", "password": "short"},
    )
    assert r.status_code == 422


def test_wrong_password(client, make_user):
    make_user(email="p@example.com")
    r = client.post("/api/auth/login", json={"email": "p@example.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/users/me").status_code == 401


def test_bad_token(client):
    r = client.get("/api/users/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_logout(client, make_user, auth_headers):
    make_user(email="out@example.com")
    r = client.post("/api/auth/logout", headers=auth_headers("out@example.com"))
    assert r.status_code == 204


def test_inactive_user_cannot_login(client, make_user, db):
    user = make_user(email="off@example.com")
    user.is_active = False
    db.commit()
    r = client.post("/api/auth/login", json={"email": "off@example.com", "password": "secret123"})
    assert r.status_code == 403
