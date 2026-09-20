import io

import pytest
from PIL import Image

from civicai.uploads import MAX_IMAGE_BYTES


def picture(format="PNG"):
    stream = io.BytesIO()
    Image.new("RGB", (12, 12), "green").save(stream, format=format)
    return stream.getvalue()


def submit(client, content, mime="image/png", name="../../attack.png"):
    return client.post("/api/v1/complaints", files={
        "description": (None, "Photo evidence"),
        "image": (name, content, mime),
    })


@pytest.mark.parametrize("format,mime", [("PNG", "image/png"), ("JPEG", "image/jpeg")])
def test_image_persists_and_is_served(client, format, mime):
    result = submit(client, picture(format), mime)
    assert result.status_code == 201
    body = result.json()
    assert body["image_ref"].startswith("/api/v1/complaint-images/")
    assert "attack" not in body["image_ref"] and ".." not in body["image_ref"]
    assert client.get("/api/v1/complaints/" + body["complaint_id"]).json() == body
    assert client.get("/api/v1/complaints").json()[0]["image_ref"] == body["image_ref"]
    image = client.get(body["image_ref"])
    assert image.status_code == 200
    assert image.headers["content-type"] == mime
    assert image.headers["x-content-type-options"] == "nosniff"
    Image.open(io.BytesIO(image.content)).verify()


@pytest.mark.parametrize("content,mime", [
    (b"<svg/>", "image/svg+xml"), (b"not an image", "image/png"),
    (picture("PNG"), "image/jpeg"), (b"video", "video/mp4"),
])
def test_invalid_images(client, content, mime):
    assert submit(client, content, mime).status_code == 422
    assert client.get("/api/v1/complaints").json() == []


def test_oversized_image(client):
    assert submit(client, b"x" * (MAX_IMAGE_BYTES + 1)).status_code == 413
    assert client.get("/api/v1/complaints").json() == []


def test_image_reference_cannot_be_supplied(client):
    response = client.post("/api/v1/complaints", files={
        "description": (None, "Issue"), "image_ref": (None, "/etc/passwd")})
    assert response.status_code == 422


def test_image_path_is_restricted(client):
    assert client.get("/api/v1/complaint-images/secret.txt").status_code == 404


def test_duplicate_fields_rejected(client):
    assert client.post("/api/v1/complaints", files=[
        ("description", (None, "One")), ("description", (None, "Two"))
    ]).status_code == 422


def test_json_contract_has_clear_error(client):
    assert client.post("/api/v1/complaints", json={"description": "Old client"}).status_code == 415


def test_storage_failure_is_clear(client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OSError("private filesystem detail")
    monkeypatch.setattr("civicai.routes.save_image", unavailable)
    response = submit(client, picture())
    assert response.status_code == 503
    assert response.json()["message"] == "Image storage is temporarily unavailable."
    assert client.get("/api/v1/complaints").json() == []


def test_database_failure_cleans_up_image(client, monkeypatch):
    from sqlalchemy.exc import OperationalError
    def unavailable(*args, **kwargs):
        raise OperationalError("insert", {}, Exception("offline"))
    monkeypatch.setattr("civicai.service.create_complaint", unavailable)
    assert submit(client, picture()).status_code == 503
    assert list(client.app.state.upload_directory.iterdir()) == []


def test_whole_request_is_bounded(client):
    response = client.post("/api/v1/complaints", content=b"x" * (MAX_IMAGE_BYTES + 256 * 1024 + 1),
                           headers={"Content-Type": "multipart/form-data; boundary=test"})
    assert response.status_code == 413


def test_metadata_is_removed(client):
    from PIL.PngImagePlugin import PngInfo
    stream = io.BytesIO()
    metadata = PngInfo()
    metadata.add_text("private_note", "Must not survive")
    Image.new("RGB", (10, 10)).save(stream, format="PNG", pnginfo=metadata)
    response = submit(client, stream.getvalue())
    image = client.get(response.json()["image_ref"])
    assert "private_note" not in Image.open(io.BytesIO(image.content)).info
