from services import linkcheck
from services.normalize import normalize


def _clear_external_config(monkeypatch):
    monkeypatch.setattr(linkcheck, "SAFE_BROWSING_KEY", "")
    monkeypatch.setattr(linkcheck, "VIRUSTOTAL_KEY", "")
    monkeypatch.setattr(linkcheck, "OPENPHISH_FEED_URL", "")
    monkeypatch.setattr(linkcheck, "PHISHTANK_FEED_URL", "")
    monkeypatch.setattr(linkcheck, "EXTERNAL_CHECKS_ENABLED", True)


def test_all_external_sources_missing_is_a_silent_noop(monkeypatch):
    _clear_external_config(monkeypatch)

    def fail(*args, **kwargs):
        raise AssertionError("no external request should be made without keys")

    monkeypatch.setattr(linkcheck.urllib.request, "urlopen", fail)

    assert linkcheck._enabled_sources() == []
    assert linkcheck.check_url_signals(normalize("https://fresh.example/pay")) == []


def test_non_url_values_never_call_external_services(monkeypatch):
    _clear_external_config(monkeypatch)
    monkeypatch.setattr(linkcheck, "SAFE_BROWSING_KEY", "configured-but-unused")

    assert linkcheck.check_url_signals(normalize("demo.kyc-alert@exampleupi")) == []
    assert linkcheck.check_url_signals(normalize("+919876543210")) == []


def test_public_lookup_works_with_all_external_keys_missing(client, monkeypatch):
    _clear_external_config(monkeypatch)

    response = client.get("/api/lookup", params={"q": "https://never-checked.example/pay"})
    assert response.status_code == 200, response.text
    assert response.json()["verdict"] in {"HIGH_RISK", "SUSPICIOUS", "NO_REPORTS"}
