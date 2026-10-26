def test_lookup_verified_demo_entity(client):
    response = client.get("/api/lookup", params={"q": "demo.kyc-alert@exampleupi"})
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "HIGH_RISK"
    assert body["query"]["normalized_value"] == "demo.kyc-alert@exampleupi"
    assert body["report_summary"]["verified_count"] == 3
    assert body["demo_data"] is True
    assert len(body["laws"]) > 0
    assert len(body["helplines"]) > 0
    assert body["timeline"]
    # Reporter identity is never exposed.
    assert all("reporter" not in item for item in body["timeline"])
    assert "SAFE" not in body["verdict_label"].upper()


def test_pending_only_entity_is_suspicious_not_high(client):
    response = client.get("/api/lookup", params={"q": "demo.collect@exampleupi"})
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "SUSPICIOUS"
    assert body["report_summary"]["verified_count"] == 0
    assert body["report_summary"]["pending_count"] == 1
    assert body["timeline"] == []


def test_unknown_entity_is_no_reports_found(client):
    response = client.get("/api/lookup", params={"q": "nobody-here@okaxis"})
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "NO_REPORTS"
    assert body["verdict_label"] == "NO REPORTS FOUND"
    assert body["safety_note"] == "This does not guarantee safety. Verify before paying."


def test_url_heuristic_flags_shortener(client):
    response = client.get("/api/lookup", params={"q": "https://bit.ly/kyc-update"})
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "SUSPICIOUS"
    assert any(signal["code"] == "url:shortener" for signal in body["signals"])


def test_qr_payload_maps_to_payee(client):
    response = client.get(
        "/api/lookup",
        params={"q": "upi://pay?pa=demo.qr@exampleupi&pn=Demo%20Store", "type": "auto"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["query"]["detected_type"] == "upi_id"
    assert body["query"]["normalized_value"] == "demo.qr@exampleupi"


def test_invalid_value_returns_400(client):
    response = client.get("/api/lookup", params={"q": "not a valid value"})
    assert response.status_code == 400
