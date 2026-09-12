"""
backend/api/routes.py
All API route handlers — auth + transactions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from ..db import get_db, User, Transaction
except (ImportError, ValueError):
    from db import get_db, User, Transaction
from .auth import hash_password, verify_password, create_access_token, get_current_user
from .schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
    TransactionRequest, FraudPredictionResponse, TransactionHistoryItem,
)
from .predictor import predict

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user. Returns a JWT token immediately."""
    # Check email uniqueness
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    # Check phone uniqueness
    if db.query(User).filter(User.phone == body.phone).first():
        raise HTTPException(status_code=409, detail="Phone number already registered")

    user = User(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Login with email or phone + password. Returns a JWT token."""
    # Try email first, then phone
    user = db.query(User).filter(User.email == body.identifier).first()
    if not user:
        user = db.query(User).filter(User.phone == body.identifier).first()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
    )


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently logged-in user's profile."""
    return current_user


# ─────────────────────────────────────────────────────────────────────────────
# TRANSACTION ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/transactions/check", response_model=FraudPredictionResponse, status_code=201)
def check_transaction(
    body: TransactionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run ML fraud prediction on a transaction and save the result."""
    result = predict(
        amount=body.amount,
        platform=body.platform,
        tx_date=body.tx_date,
        tx_time=body.tx_time,
        location_change=body.location_change,
        new_recipient=body.new_recipient,
        failed_attempts=body.failed_attempts,
        device_count=body.device_count,
    )

    # Persist to DB
    tx = Transaction(
        user_id=current_user.id,
        amount=body.amount,
        platform=body.platform,
        tx_date=body.tx_date,
        tx_time=body.tx_time,
        location_change=body.location_change,
        new_recipient=body.new_recipient,
        failed_attempts=body.failed_attempts,
        device_count=body.device_count,
        is_fraud=result.is_fraud,
        fraud_score=result.fraud_score,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    return FraudPredictionResponse(
        transaction_id=tx.id,
        is_fraud=result.is_fraud,
        fraud_score=result.fraud_score,
        confidence_pct=result.confidence_pct,
        verdict=result.verdict,
        top_risk_factors=result.top_risk_factors,
        amount=body.amount,
        platform=body.platform,
    )


@router.get("/transactions", response_model=list[TransactionHistoryItem])
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Fetch the logged-in user's transaction history, newest first."""
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = []
    for tx in txs:
        verdict = "FRAUD" if tx.fraud_score >= 0.65 else ("SUSPICIOUS" if tx.fraud_score >= 0.35 else "SAFE")
        result.append(TransactionHistoryItem(
            id=tx.id,
            amount=tx.amount,
            platform=tx.platform,
            tx_date=tx.tx_date,
            tx_time=tx.tx_time,
            is_fraud=tx.is_fraud,
            fraud_score=tx.fraud_score,
            verdict=verdict,
            created_at=tx.created_at,
        ))
    return result


@router.delete("/transactions/{tx_id}", status_code=204)
def delete_transaction(
    tx_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a transaction (only owner can delete their own)."""
    tx = db.query(Transaction).filter(
        Transaction.id == tx_id,
        Transaction.user_id == current_user.id
    ).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(tx)
    db.commit()
