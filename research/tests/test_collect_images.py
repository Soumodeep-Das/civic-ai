import hashlib
import io
import json

import httpx
from PIL import Image
import pytest

from research.civicai_research import collect_images as collect


@pytest.mark.parametrize("url", ["http://zenodo.org/file", "https://zenodo.org.evil.invalid/file",
                                     "https://user:pass@zenodo.org/file", "https://zenodo.org:8443/file",
                                     "file:///private/file"])
def test_rejects_unapproved_download_locations(url):
    with pytest.raises(ValueError):
        collect.check_url(url)


@pytest.mark.parametrize("name", ["../file", "..", "C:secret", "dir/file", "dir\\file",
                                     "NUL.txt", "COM1", "file.", "file ", "file\x00"])
def test_rejects_unsafe_windows_filenames(name):
    with pytest.raises(ValueError):
        collect.safe_name(name)


def test_download_verifies_bytes_and_cannot_overwrite(tmp_path):
    data = b"synthetic source bytes"
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=data))) as client:
        target = tmp_path / "source"
        result = collect.download(client, "https://zenodo.org/file", target, 100,
                                  expected_size=len(data), expected_md5=hashlib.md5(data).hexdigest(),
                                  expected_sha256=hashlib.sha256(data).hexdigest())
        assert result["bytes"] == len(data)
        assert target.read_bytes() == data
        with pytest.raises(FileExistsError):
            collect.download(client, "https://zenodo.org/file", target, 100)


@pytest.mark.parametrize("kwargs", [{"limit": 2}, {"expected_size": 99},
                                       {"expected_md5": "0" * 32}, {"expected_sha256": "0" * 64}])
def test_failed_integrity_never_completes_snapshot(tmp_path, kwargs):
    output = tmp_path / "snapshot"
    collect.begin(output)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"fixture"))) as client:
        with pytest.raises(ValueError):
            collect.download(client, "https://zenodo.org/file", output / "source", **{"limit": 100, **kwargs})
    assert (output / "INCOMPLETE").exists()
    assert not (output / "COMPLETE").exists()


def test_redirect_checked_before_second_request_even_if_client_follows(tmp_path):
    calls = []
    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://unapproved.invalid/file"})
    with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True) as client:
        with pytest.raises(ValueError, match="Unexpected download"):
            collect.download(client, "https://zenodo.org/file", tmp_path / "source", 100)
    assert calls == ["https://zenodo.org/file"]


def test_bounded_publisher_redirect(tmp_path):
    calls = []
    def handler(request):
        calls.append(str(request.url))
        if request.url.host == "data.mendeley.com":
            return httpx.Response(302, headers={"location": "https://prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com/file"})
        return httpx.Response(200, content=b"fixture")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = collect.download(client, "https://data.mendeley.com/file", tmp_path / "source", 100)
    assert len(calls) == 2
    assert result["sha256"] == hashlib.sha256(b"fixture").hexdigest()


def page(identity=1, description="Synthetic Kolkata test fixture", license_name="CC BY-SA 4.0"):
    return {"pageid": identity, "title": "File:Fixture.png", "imageinfo": [{
        "url": "https://upload.wikimedia.org/fixture.png", "descriptionurl": "https://commons.wikimedia.org/wiki/File:Fixture.png",
        "sha1": "fixture-content-hash", "size": 80, "mime": "image/png", "extmetadata": {
            "LicenseShortName": {"value": license_name}, "ImageDescription": {"value": description},
            "Artist": {"value": "Synthetic fixture author"}}}]}


def test_query_or_uploader_is_not_indian_provenance():
    foreign = page(description="Berlin", license_name="CC BY 4.0")
    foreign["query"] = "India garbage"
    foreign["imageinfo"][0]["extmetadata"]["Artist"]["value"] = "India Photographer"
    assert not collect.eligible(foreign)
    assert not collect.eligible(page(license_name="All rights reserved"))
    assert not collect.eligible(page(license_name="CC BY-NC-ND 4.0"))
    assert collect.eligible(page())


def test_commons_preserves_rights_and_leaves_labels_pending(tmp_path, monkeypatch):
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4)).save(buffer, format="PNG")
    body = buffer.getvalue()
    first, duplicate = page(), page(identity=2)
    first["imageinfo"][0]["size"] = duplicate["imageinfo"][0]["size"] = len(body)
    def handler(request):
        if request.url.host == "commons.wikimedia.org":
            return httpx.Response(200, json={"query": {"pages": {"1": first, "2": duplicate}}})
        return httpx.Response(200, content=body)
    monkeypatch.setattr(collect, "TOPICS", {"garbage_waste": ["India fixture"]})
    output = tmp_path / "snapshot"
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        collect.commons(client, output)
    records = json.loads((output / "candidates.json").read_text())
    report = json.loads((output / "acquisition.json").read_text())
    assert len(records) == 1
    record = records[0]
    assert record["source_metadata"]["Artist"]["value"] == "Synthetic fixture author"
    assert record["category_label"] is None and record["severity_label"] is None
    assert record["split"] == "unassigned" and record["annotation_status"] == "pending"
    assert record["privacy_review"] == "pending"
    assert not report["training_approved"]
    assert report["rejected"] == 1
    assert (output / "COMPLETE").exists() and not (output / "INCOMPLETE").exists()
    with pytest.raises(FileExistsError):
        collect.begin(output)


def test_footpath_license_change_blocks_download(tmp_path):
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={
            "metadata": {"license": {"id": "unknown"}}, "files": []}))) as client:
        with pytest.raises(ValueError, match="license changed"):
            collect.footpath(client, tmp_path / "snapshot", True)
    assert (tmp_path / "snapshot/INCOMPLETE").exists()


def test_footpath_defaults_to_metadata_not_large_archive(tmp_path):
    body = b"synthetic license fixture"
    calls = []
    def handler(request):
        calls.append(str(request.url))
        if "/api/" in request.url.path:
            return httpx.Response(200, json={"metadata": {"license": {"id": "cc-by-4.0"}}, "files": [
                {"key": "LICENSE.txt", "size": len(body), "checksum": "md5:" + hashlib.md5(body).hexdigest(),
                 "links": {"self": "https://zenodo.org/license"}},
                {"key": "images.zip", "size": 4_500_000_000, "checksum": "md5:" + "0" * 32,
                 "links": {"self": "https://zenodo.org/archive"}}]})
        assert request.url.path == "/license"
        return httpx.Response(200, content=body)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        collect.footpath(client, tmp_path / "snapshot")
    report = json.loads((tmp_path / "snapshot/acquisition.json").read_text())
    assert len(calls) == 2
    assert not report["archive_downloaded"] and not report["training_approved"]


def test_dwsd_pin_change_blocks_archive(tmp_path):
    calls = []
    def handler(request):
        calls.append(str(request.url))
        if "snapshot" in request.url.path:
            return httpx.Response(200, json={"licence": {"short_name": "CC BY 4.0"}, "version": 1})
        return httpx.Response(200, json=[{"filename": "DSWD.zip", "content_details": {
            "sha256_hash": "0" * 64, "size": 252719363}}])
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="pinned archive changed"):
            collect.dwsd(client, tmp_path / "snapshot")
    assert len(calls) == 2
    assert not (tmp_path / "snapshot/COMPLETE").exists()
