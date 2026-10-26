from db.models import ApiKey, User
from api.auth import hash_password


def _register(client, email="user@example.com", phone="9876501111", password="secret123"):
    response = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Test User", "email": email, "phone": phone, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _make_role(db_session, email, role):
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    db_session.commit()
    return user


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_anonymous_and_normal_user_cannot_reach_admin(client, db_session):
    anonymous = client.get("/api/admin/reports")
    assert anonymous.status_code in {401, 403}

    data = _register(client)
    normal = client.get("/api/admin/reports", headers=_auth_header(data["access_token"]))
    assert normal.status_code == 403


def test_moderator_can_verify_report_and_verdict_becomes_high_risk(client, db_session):
    data = _register(client, email="mod@example.com", phone="9876502222")
    _make_role(db_session, "mod@example.com", "moderator")

    created = client.post(
        "/api/reports",
        json={
            "entity_value": "moderation.case@exampleupi",
            "scam_type_code": "FP-006",
            "amount_lost": 7500,
            "description": "Fake KYC call asked me to install remote support.",
        },
    )
    assert created.status_code == 201
    report_id = created.json()["id"]

    queue = client.get("/api/admin/reports?status=pending", headers=_auth_header(data["access_token"]))
    assert queue.status_code == 200
    assert any(row["id"] == report_id for row in queue.json())

    updated = client.patch(
        f"/api/admin/reports/{report_id}",
        json={"action": "verify", "note": "Caller recording reviewed."},
        headers=_auth_header(data["access_token"]),
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["status"] == "verified"
    assert body["entity_status"] == "reported"

    lookup = client.get("/api/lookup", params={"q": "moderation.case@exampleupi"}).json()
    assert lookup["verdict"] == "HIGH_RISK"
    assert lookup["report_summary"]["verified_count"] == 1
    assert lookup["timeline"]


def test_rejecting_pending_report_returns_entity_to_clean(client):
    data = _register(client, email="mod2@example.com", phone="9876503333")
    from db.database import SessionLocal

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "mod2@example.com").first()
        user.role = "admin"
        db.commit()
    finally:
        db.close()

    created = client.post(
        "/api/reports",
        json={
            "entity_value": "reject.case@exampleupi",
            "scam_type_code": "FP-007",
            "description": "Said I won a lottery and needed a processing fee.",
        },
    )
    report_id = created.json()["id"]
    before = client.get("/api/lookup", params={"q": "reject.case@exampleupi"}).json()
    assert before["verdict"] == "SUSPICIOUS"

    updated = client.patch(
        f"/api/admin/reports/{report_id}",
        json={"action": "reject", "note": "No evidence supplied."},
        headers=_auth_header(data["access_token"]),
    )
    assert updated.status_code == 200
    after = client.get("/api/lookup", params={"q": "reject.case@exampleupi"}).json()
    assert after["verdict"] == "NO_REPORTS"


def test_dispute_admin_flow(client):
    data = _register(client, email="mod3@example.com", phone="9876504444")
    from db.database import SessionLocal

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "mod3@example.com").first()
        user.role = "moderator"
        db.commit()
    finally:
        db.close()

    created = client.post(
        "/api/disputes",
        json={"entity_value": "wrong.listing@exampleupi", "reason": "This identifier belongs to my shop, not a fraudster."},
    )
    assert created.status_code == 201
    dispute_id = created.json()["id"]

    rows = client.get("/api/admin/disputes", headers=_auth_header(data["access_token"]))
    assert rows.status_code == 200
    assert any(row["id"] == dispute_id for row in rows.json())

    resolved = client.patch(
        f"/api/admin/disputes/{dispute_id}",
        json={"status": "resolved"},
        headers=_auth_header(data["access_token"]),
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"


def test_api_key_lifecycle_and_developer_lookup(client, db_session):
    data = _register(client, email="dev@example.com", phone="9876505555")
    headers = _auth_header(data["access_token"])

    created = client.post("/api/keys", json={"name": "My script"}, headers=headers)
    assert created.status_code == 201, created.text
    raw_key = created.json()["key"]
    key_id = created.json()["id"]
    assert raw_key.startswith("spk_")

    stored = db_session.query(ApiKey).filter(ApiKey.id == key_id).first()
    assert stored.key_hash != raw_key

    listed = client.get("/api/keys", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "My script"
    assert "key" not in listed.json()[0]

    public = client.get("/api/v1/lookup", params={"q": "demo.kyc-alert@exampleupi"})
    assert public.status_code in {401, 403}

    lookup = client.get(
        "/api/v1/lookup",
        params={"q": "demo.kyc-alert@exampleupi"},
        headers={"X-API-Key": raw_key},
    )
    assert lookup.status_code == 200, lookup.text
    assert lookup.json()["verdict"] == "HIGH_RISK"

    revoked = client.delete(f"/api/keys/{key_id}", headers=headers)
    assert revoked.status_code == 204
    denied = client.get(
        "/api/v1/lookup",
        params={"q": "demo.kyc-alert@exampleupi"},
        headers={"X-API-Key": raw_key},
    )
    assert denied.status_code == 401
