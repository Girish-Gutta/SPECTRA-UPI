"""Developer lookup API (`GET /api/v1/lookup`) with X-API-Key auth."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

try:  # pragma: no cover
    from ..db import get_db
    from ..db.models import ApiKey, User
    from ..services.lookup_service import perform_lookup
    from ..services.normalize import NormalizationError
    from ..services.ratelimit import API_KEY_LIMIT, api_key, limiter
    from ..services.security import api_key_rate_key, hash_api_key
    from .public_schemas import LookupResponse
except (ImportError, ValueError):  # pragma: no cover
    from db import get_db
    from db.models import ApiKey, User
    from services.lookup_service import perform_lookup
    from services.normalize import NormalizationError
    from services.ratelimit import API_KEY_LIMIT, api_key, limiter
    from services.security import api_key_rate_key, hash_api_key
    from api.public_schemas import LookupResponse

router = APIRouter(tags=["developer"])
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key_owner(
    raw_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db),
) -> User:
    if not raw_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    row = (
        db.query(ApiKey)
        .filter(ApiKey.key_hash == hash_api_key(raw_key), ApiKey.revoked.is_(False))
        .first()
    )
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    user = db.query(User).filter(User.id == row.user_id, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="API key owner is inactive")
    return user


@router.get("/lookup", response_model=LookupResponse)
@limiter.limit(API_KEY_LIMIT, key_func=api_key_rate_key)
def developer_lookup(
    request: Request,
    response: Response,
    q: str = Query(..., min_length=2, max_length=2048),
    entity_type: str = Query("auto", alias="type", pattern="^(auto|upi_id|url|qr_payload|phone)$"),
    db: Session = Depends(get_db),
    owner: User = Depends(get_api_key_owner),
    amount: Optional[float] = Query(None, ge=0, le=200000),
    platform: Optional[str] = Query(None, max_length=50),
    tx_date: Optional[str] = Query(None, max_length=20),
    tx_time: Optional[str] = Query(None, max_length=10),
    location_change: bool = False,
    new_recipient: bool = True,
    failed_attempts: int = Query(0, ge=0, le=20),
    device_count: int = Query(1, ge=1, le=20),
    txn_freq_1h: int = Query(0, ge=0, le=100),
    txn_freq_24h: int = Query(0, ge=0, le=500),
    amount_z_score: float = Query(0.0, ge=0, le=100),
    amount_vs_recent: float = Query(0.0, ge=0, le=100),
    is_preferred_platform: bool = True,
):
    transaction = None
    if amount is not None and platform:
        transaction = {
            "amount": amount,
            "platform": platform,
            "tx_date": tx_date or "",
            "tx_time": tx_time or "",
            "location_change": location_change,
            "new_recipient": new_recipient,
            "failed_attempts": failed_attempts,
            "device_count": device_count,
            "txn_freq_1h": txn_freq_1h,
            "txn_freq_24h": txn_freq_24h,
            "amount_z_score": amount_z_score,
            "amount_vs_recent": amount_vs_recent,
            "is_preferred_platform": is_preferred_platform,
        }
    try:
        return perform_lookup(db, q, entity_type, transaction)
    except NormalizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
