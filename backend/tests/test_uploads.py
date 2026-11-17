import io
import os

import pytest
from PIL import Image

from app.core.config import settings
from app.models import UserRole


@pytest.fixture(autouse=True)
def tmp_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


def make_image(fmt="PNG", size=(400, 300), exif_make=None, noise=False) -> bytes:
    if noise:
        img = Image.frombytes("RGB", size, os.urandom(size[0] * size[1] * 3))
    else:
        img = Image.new("RGB", size, (190, 120, 100))
    kwargs = {}
    if exif_make:
        exif = Image.Exif()
        exif[0x010F] = exif_make  # "Make" tag
        kwargs["exif"] = exif
    buf = io.BytesIO()
    img.save(buf, fmt, **kwargs)
    return buf.getvalue()


def upload(client, headers, data, name="photo.png", ctype="image/png"):
    return client.post("/api/uploads/images", files={"file": (name, data, ctype)}, headers=headers)


@pytest.fixture
def patient(make_user, auth_headers):
    make_user(email="pat@example.com")
    return auth_headers("pat@example.com")


def test_upload_png_stored_as_jpeg(client, patient, tmp_uploads):
    r = upload(client, patient, make_image())
    assert r.status_code == 201, r.text
    body = r.json()
    saved = tmp_uploads / body["path"]
    assert saved.is_file()
    assert Image.open(saved).format == "JPEG"
    assert body["url"] == f"/api/uploads/images/{body['path']}"


def test_exif_metadata_is_stripped(client, patient, tmp_uploads):
    data = make_image("JPEG", exif_make="SecretPhoneModel")
    assert 0x010F in Image.open(io.BytesIO(data)).getexif()  # sanity: input has EXIF
    r = upload(client, patient, data, name="p.jpg", ctype="image/jpeg")
    saved = tmp_uploads / r.json()["path"]
    assert 0x010F not in Image.open(saved).getexif()


def test_large_image_is_downscaled(client, patient):
    body = upload(client, patient, make_image(size=(3000, 2000))).json()
    assert max(body["width"], body["height"]) == 1024


def test_not_an_image_rejected(client, patient):
    r = upload(client, patient, b"definitely not an image", name="x.png")
    assert r.status_code == 400


def test_gif_rejected(client, patient):
    r = upload(client, patient, make_image("GIF"), name="x.gif", ctype="image/gif")
    assert r.status_code == 415


def test_tiny_image_rejected(client, patient):
    r = upload(client, patient, make_image(size=(50, 50)))
    assert r.status_code == 400


def test_oversize_rejected(client, patient, monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 1000)
    r = upload(client, patient, make_image(noise=True))
    assert r.status_code == 413


def test_login_required(client):
    assert upload(client, {}, make_image()).status_code == 401


def test_doctor_cannot_upload(client, make_user, auth_headers):
    make_user(email="doc@example.com", role=UserRole.doctor)
    assert upload(client, auth_headers("doc@example.com"), make_image()).status_code == 403


def test_image_access_rules(client, patient, make_user, auth_headers):
    path = upload(client, patient, make_image()).json()["path"]
    url = f"/api/uploads/images/{path}"

    r = client.get(url, headers=patient)
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"

    make_user(email="other@example.com")
    assert client.get(url, headers=auth_headers("other@example.com")).status_code == 404

    make_user(email="admin@example.com", role=UserRole.admin)
    assert client.get(url, headers=auth_headers("admin@example.com")).status_code == 200


def test_path_traversal_blocked(client, patient):
    r = client.get("/api/uploads/images/1/..%2F..%2F.env", headers=patient)
    assert r.status_code == 404
