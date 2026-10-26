"""User-managed developer API keys (JWT required)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

try:  # pragma: no cover
    from ..db import get_db
    from ..db.models import ApiKey
    from ..services.security import generate_api_key, hash_api_key
    from .auth import get_current_user
    from .admin_schemas import ApiKeyCreate, ApiKeyCreated, ApiKeyOut
except (ImportError, ValueError):  # pragma: no cover
    from db import get_db
    from db.models import ApiKey
    from services.security import generate_api_key, hash_api_key
    from api.auth import get_current_user
    from api.admin_schemas import ApiKeyCreate, ApiKeyCreated, ApiKeyOut

router = APIRouter(prefix="/keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyCreated, status_code=201)
def create_key(
    body: ApiKeyCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    active = (
        db.query(ApiKey)
        .filter(ApiKey.user_id == current_user.id, ApiKey.revoked.is_(False))
        .count()
    )
    if active >= 10:
        raise HTTPException(status_code=400, detail="You already have 10 active API keys")

    raw = generate_api_key()
    row = ApiKey(
        user_id=current_user.id,
        key_hash=hash_api_key(raw),
        name=body.name,
        created_at=datetime.now(timezone.utc),
        revoked=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ApiKeyCreated(
        id=row.id,
        name=row.name,
        prefix=raw[:12] + "…",
        created_at=row.created_at,
        revoked=row.revoked,
        key=raw,
        message="Copy this key now. It is stored only as a hash and cannot be shown again.",
    )


@router.get("", response_model=list[ApiKeyOut])
def list_keys(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ApiKey)
        .filter(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )
    return [
        ApiKeyOut(
            id=row.id,
            name=row.name,
            # The raw key is never recoverable after creation.
            prefix="spk_…",
            created_at=row.created_at,
            revoked=row.revoked,
        )
        for row in rows
    ]


@router.delete("/{key_id}", status_code=204)
def revoke_key(
    key_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="API key not found")
    row.revoked = True
    db.commit()
    return Response(status_code=204)
