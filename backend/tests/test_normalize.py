import pytest

from services.normalize import (
    NormalizationError,
    mask_value,
    normalize,
    normalize_phone,
    normalize_upi,
    normalize_url,
    parse_upi_payload,
)


def test_upi_is_lowercased_and_trimmed():
    result = normalize("  Ravi.Kumar@OKAxis  ")
    assert result.type == "upi_id"
    assert result.value == "ravi.kumar@okaxis"


@pytest.mark.parametrize("bad", ["ravi", "ravi@@okaxis", "@okaxis", "ravi@", "ravi kumar@okaxis"])
def test_invalid_upi_rejected(bad):
    with pytest.raises(NormalizationError):
        normalize_upi(bad)


def test_url_normalization_strips_tracking_and_fragment():
    result = normalize_url("HTTPS://Example.COM:443/Path/?utm_source=x&b=2&a=1#frag")
    assert result.value == "https://example.com/Path/?a=1&b=2"
    assert result.details["host"] == "example.com"


def test_url_rejects_non_http_scheme():
    with pytest.raises(NormalizationError):
        normalize_url("javascript:alert(1)")


def test_upi_payload_parsing_and_entity_collapse():
    payload = "upi://pay?pa=Ravi@OKAxis&pn=Ravi%20Shop&am=250.00&cu=INR"
    parsed = parse_upi_payload(payload)
    assert parsed == {"pa": "ravi@okaxis", "pn": "Ravi Shop", "am": "250.00"}
    normalized = normalize(payload)
    assert normalized.type == "upi_id"
    assert normalized.value == "ravi@okaxis"
    assert normalized.details["qr"] is True
    assert normalized.details["payee_name"] == "Ravi Shop"


def test_non_upi_qr_text_is_qr_payload():
    from services.normalize import normalize_qr

    result = normalize_qr("PAYLOAD:not-a-upi-intent")
    assert result.type == "qr_payload"
    assert result.value == "PAYLOAD:not-a-upi-intent"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("9876543210", "+919876543210"),
        ("+91 98765 43210", "+919876543210"),
        ("09876543210", "+919876543210"),
        ("919876543210", "+919876543210"),
    ],
)
def test_phone_normalization(raw, expected):
    assert normalize_phone(raw).value == expected


def test_auto_detection():
    assert normalize("ravi@okaxis").type == "upi_id"
    assert normalize("9876543210").type == "phone"
    assert normalize("example.com/kyc").type == "url"
    assert normalize("upi://pay?pa=ravi@okaxis").type == "upi_id"


def test_mask_value_hides_most_of_the_identifier():
    assert mask_value("ravi@okaxis", "upi_id") == "ra****@okaxis"
    assert mask_value("+919876543210", "phone").endswith("3210")
    assert "ravi@okaxis" not in mask_value("https://ravi@okaxis.example/x", "url")
