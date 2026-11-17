from app.models import UserRole


def test_patient_cannot_access_admin(client, make_user, auth_headers):
    make_user(email="pat@example.com", role=UserRole.patient)
    r = client.get("/api/admin/users", headers=auth_headers("pat@example.com"))
    assert r.status_code == 403


def test_doctor_cannot_access_admin(client, make_user, auth_headers):
    make_user(email="doc@example.com", role=UserRole.doctor)
    r = client.get("/api/admin/users", headers=auth_headers("doc@example.com"))
    assert r.status_code == 403


def test_admin_can_list_users(client, make_user, auth_headers):
    make_user(email="admin@example.com", role=UserRole.admin)
    make_user(email="pat@example.com")
    r = client.get("/api/admin/users", headers=auth_headers("admin@example.com"))
    assert r.status_code == 200
    assert {u["email"] for u in r.json()} == {"admin@example.com", "pat@example.com"}


def test_admin_can_promote_user(client, make_user, auth_headers):
    make_user(email="admin@example.com", role=UserRole.admin)
    pat = make_user(email="pat@example.com")
    r = client.patch(
        f"/api/admin/users/{pat.id}",
        json={"role": "doctor"},
        headers=auth_headers("admin@example.com"),
    )
    assert r.status_code == 200
    assert r.json()["role"] == "doctor"


def test_admin_cannot_demote_self(client, make_user, auth_headers):
    admin = make_user(email="admin@example.com", role=UserRole.admin)
    r = client.patch(
        f"/api/admin/users/{admin.id}",
        json={"role": "patient"},
        headers=auth_headers("admin@example.com"),
    )
    assert r.status_code == 400


def test_admin_stats(client, make_user, auth_headers):
    make_user(email="admin@example.com", role=UserRole.admin)
    make_user(email="pat@example.com")
    r = client.get("/api/admin/stats", headers=auth_headers("admin@example.com"))
    assert r.status_code == 200
    body = r.json()
    assert body["users_by_role"] == {"patient": 1, "doctor": 0, "admin": 1}
    assert body["appointments_by_status"]["booked"] == 0


def test_patient_cannot_see_stats(client, make_user, auth_headers):
    make_user(email="pat@example.com")
    r = client.get("/api/admin/stats", headers=auth_headers("pat@example.com"))
    assert r.status_code == 403
