from pathlib import Path

import httpx
import pytest

from civicai.config import EmailSettings
from civicai.emailing import BrevoEmailService, OutboundEmail
from civicai.evidence import LocalEvidenceStorage, validate_key


def test_local_evidence_round_trip_is_private_and_deletable(tmp_path: Path):
    storage = LocalEvidenceStorage(tmp_path)
    key = "a" * 32 + ".png"
    storage.put(key, b"clean-image", "image/png")
    assert storage.get(key) == (b"clean-image", "image/png")
    storage.delete(key)
    with pytest.raises(FileNotFoundError):
        storage.get(key)


def test_evidence_key_rejects_path_traversal():
    with pytest.raises(FileNotFoundError):
        validate_key("../private.png")


def brevo_settings(api_key: str = "secret") -> EmailSettings:
    return EmailSettings("brevo", "verified@example.com", Path("tmp"), "", 587, "", "", True, api_key, "https://api.brevo.com/v3/smtp/email")


def test_brevo_sends_expected_https_payload(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self): return None

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return Response()

    monkeypatch.setattr("civicai.emailing.httpx.post", fake_post)
    BrevoEmailService(brevo_settings()).send(OutboundEmail("person@example.com", "Verify", "safe link"))
    assert captured["headers"]["api-key"] == "secret"
    assert captured["json"]["to"] == [{"email": "person@example.com"}]
    assert captured["timeout"] == 10


def test_brevo_failure_does_not_leak_provider_response(monkeypatch):
    def fail(*args, **kwargs):
        raise httpx.HTTPError("provider body contains token")

    monkeypatch.setattr("civicai.emailing.httpx.post", fail)
    with pytest.raises(RuntimeError, match="Transactional email delivery failed") as exc:
        BrevoEmailService(brevo_settings()).send(OutboundEmail("person@example.com", "Reset", "secret-link"))
    assert "token" not in str(exc.value)
