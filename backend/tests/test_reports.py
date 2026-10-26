from datetime import date

from db.models import Report


def _report_payload(**overrides):
    payload = {
        "entity_value": "fresh.report@exampleupi",
        "entity_type": "auto",
        "scam_type_code": "FP-002",
        "amount_lost": 1200,
        "incident_date": date.today().isoformat(),
        "description": "Sent a fake collect request and asked me to approve it.",
        "captcha_token": None,
    }
    payload.update(overrides)
    return payload


def test_report_is_pending_and_never_verified_automatically(client):
    response = client.post("/api/reports", json=_report_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert "pending review" in body["message"]
    assert "****" in body["masked_value"]

    lookup = client.get("/api/lookup", params={"q": "fresh.report@exampleupi"}).json()
    assert lookup["verdict"] == "SUSPICIOUS"
    assert lookup["report_summary"]["verified_count"] == 0
    assert lookup["report_summary"]["pending_count"] == 1
    assert lookup["timeline"] == []


def test_duplicate_report_within_24h_is_rejected(client):
    assert client.post("/api/reports", json=_report_payload()).status_code == 201
    second = client.post(
        "/api/reports",
        json=_report_payload(description="A different description for the same entity."),
    )
    assert second.status_code == 409
    assert "already reported" in second.json()["detail"]


def test_invalid_evidence_url_rejected(client):
    response = client.post(
        "/api/reports",
        json=_report_payload(entity_value="evidence.test@exampleupi", evidence_url="javascript:alert(1)"),
    )
    assert response.status_code == 400


def test_captcha_failure_blocks_report(client, monkeypatch):
    import api.public as public_module

    monkeypatch.setattr(public_module, "verify_turnstile", lambda token, ip: (False, "CAPTCHA failed"))
    response = client.post("/api/reports", json=_report_payload(entity_value="captcha.test@exampleupi"))
    assert response.status_code == 400
    assert "CAPTCHA" in response.json()["detail"]


def test_logged_in_report_gets_priority(client):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test Reporter",
            "email": "reporter@example.com",
            "phone": "9876501234",
            "password": "secret123",
        },
    )
    assert register.status_code == 201
    token = register.json()["access_token"]

    response = client.post(
        "/api/reports",
        json=_report_payload(entity_value="priority.test@exampleupi"),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_evidence_link_gets_priority_flag(client, db_session):
    response = client.post(
        "/api/reports",
        json=_report_payload(
            entity_value="evidence.priority@exampleupi",
            evidence_url="https://example.com/receipt/123",
        ),
    )
    assert response.status_code == 201
    report = db_session.query(Report).filter(Report.id == response.json()["id"]).first()
    assert report.priority_flag is True


def test_dispute_flow(client):
    payload = {
        "entity_value": "dispute.me@exampleupi",
        "reason": "This listing is about my business and the reports are not mine.",
    }
    first = client.post("/api/disputes", json=payload)
    assert first.status_code == 201
    assert first.json()["status"] == "open"
    second = client.post("/api/disputes", json=payload)
    assert second.status_code == 201
    third = client.post("/api/disputes", json=payload)
    assert third.status_code == 409


def test_public_stats_never_include_identifiers(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_verified_reports"] >= 4
    assert "demo.kyc-alert@exampleupi" not in str(body)
    assert isinstance(body["top_scam_types_this_month"], list)


def test_awareness_includes_laws_and_helplines(client):
    response = client.get("/api/awareness")
    assert response.status_code == 200
    body = response.json()
    assert len(body["patterns"]) == 8
    assert any(item["number"] == "1930" for item in body["helplines"])
    assert body["laws"]
