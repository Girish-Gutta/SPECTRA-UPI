def test_public_lookup_returns_429_after_limit(client):
    """Exercise the real slowapi limiter wired into the public endpoint."""
    from services.ratelimit import limiter

    limiter.reset()
    limiter.enabled = True
    try:
        statuses = [
            client.get("/api/lookup", params={"q": "demo.qr@exampleupi"}).status_code
            for _ in range(61)
        ]
    finally:
        limiter.enabled = False
        limiter.reset()

    assert statuses[0] == 200
    assert statuses[-1] == 429
    assert 200 in statuses


def test_report_endpoint_is_limited_per_reporter(client):
    from services.ratelimit import limiter

    limiter.reset()
    limiter.enabled = True
    payload = {
        "entity_value": "rage.report@exampleupi",
        "scam_type_code": "FP-002",
        "description": "Repeated automated submission test for rate limiting.",
    }
    try:
        statuses = [client.post("/api/reports", json=payload).status_code for _ in range(7)]
    finally:
        limiter.enabled = False
        limiter.reset()

    # 201 for the first successful reports, 409 for duplicates, 429 once the
    # per-reporter limit is exceeded. The last request must be throttled.
    assert statuses[-1] == 429
    assert 201 in statuses
