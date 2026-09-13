"""
backend/api/routes.py  (v2 — beast mode)
"""

import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from collections import Counter

try:
    from ..db import get_db, User, Transaction
except (ImportError, ValueError):
    from db import get_db, User, Transaction

from .auth import hash_password, verify_password, create_access_token, get_current_user
from .schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
    TransactionRequest, FullFraudAnalysis, TransactionHistoryItem,
    FraudStatsResponse, AnomalyReason,
)
from .predictor import predict

router = APIRouter()

# Load fraud patterns for the /patterns endpoint
_KB_PATH = Path(__file__).resolve().parent.parent / "data" / "fraud_patterns.json"
with open(_KB_PATH, encoding="utf-8") as f:
    _FRAUD_KB = json.load(f)


# ── AUTH ──────────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(409, "Email already registered")
    if db.query(User).filter(User.phone == body.phone).first():
        raise HTTPException(409, "Phone already registered")
    user = User(
        full_name=body.full_name, email=body.email,
        phone=body.phone, hashed_password=hash_password(body.password),
    )
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user_id=user.id,
                         full_name=user.full_name, email=user.email)


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.identifier).first()
    if not user:
        user = db.query(User).filter(User.phone == body.identifier).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user_id=user.id,
                         full_name=user.full_name, email=user.email)


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ── TRANSACTIONS ──────────────────────────────────────────────────────────

@router.post("/transactions/check", response_model=FullFraudAnalysis, status_code=201)
def check_transaction(
    body: TransactionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = predict(
        amount=body.amount, platform=body.platform,
        tx_date=body.tx_date, tx_time=body.tx_time,
        location_change=body.location_change, new_recipient=body.new_recipient,
        failed_attempts=body.failed_attempts, device_count=body.device_count,
        txn_freq_1h=body.txn_freq_1h, txn_freq_24h=body.txn_freq_24h,
        amount_z_score=body.amount_z_score, amount_vs_recent=body.amount_vs_recent,
        is_preferred_platform=body.is_preferred_platform,
    )

    tx = Transaction(
        user_id=current_user.id, amount=body.amount, platform=body.platform,
        tx_date=body.tx_date, tx_time=body.tx_time,
        location_change=body.location_change, new_recipient=body.new_recipient,
        failed_attempts=body.failed_attempts, device_count=body.device_count,
        is_fraud=result.is_fraud, fraud_score=result.fraud_score,
        matched_pattern_id=result.matched_pattern_id,
        matched_pattern_name=result.matched_pattern_name,
    )
    db.add(tx); db.commit(); db.refresh(tx)

    return FullFraudAnalysis(
        transaction_id=tx.id, amount=body.amount, platform=body.platform,
        is_fraud=result.is_fraud, fraud_score=result.fraud_score,
        confidence_pct=result.confidence_pct, verdict=result.verdict,
        risk_level=result.risk_level, behavior_flags=result.behavior_flags,
        anomaly_reasons=[AnomalyReason(**r) for r in result.anomaly_reasons],
        feature_contributions=result.feature_contributions,
        matched_pattern_id=result.matched_pattern_id,
        matched_pattern_name=result.matched_pattern_name,
        pattern_similarity=result.pattern_similarity,
        fraud_how_it_works=result.fraud_how_it_works,
        fraud_warning_signs=result.fraud_warning_signs,
        immediate_action=result.immediate_action,
        prevention_tip=result.prevention_tip,
        report_to=result.report_to,
        helplines=result.helplines,
    )


@router.get("/transactions", response_model=list[TransactionHistoryItem])
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50, offset: int = 0,
):
    txs = (db.query(Transaction)
           .filter(Transaction.user_id == current_user.id)
           .order_by(Transaction.created_at.desc())
           .offset(offset).limit(limit).all())

    result = []
    for tx in txs:
        v = "FRAUD" if tx.fraud_score >= 0.65 else ("SUSPICIOUS" if tx.fraud_score >= 0.35 else "SAFE")
        result.append(TransactionHistoryItem(
            id=tx.id, amount=tx.amount, platform=tx.platform,
            tx_date=tx.tx_date, tx_time=tx.tx_time,
            is_fraud=tx.is_fraud, fraud_score=tx.fraud_score, verdict=v,
            matched_pattern_id=getattr(tx, "matched_pattern_id", None),
            matched_pattern_name=getattr(tx, "matched_pattern_name", None),
            created_at=tx.created_at,
        ))
    return result


@router.get("/transactions/stats", response_model=FraudStatsResponse)
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txs = db.query(Transaction).filter(Transaction.user_id == current_user.id).all()
    fraud_txs  = [t for t in txs if t.fraud_score >= 0.65]
    safe_txs   = [t for t in txs if t.fraud_score < 0.35]
    susp_txs   = [t for t in txs if 0.35 <= t.fraud_score < 0.65]

    pattern_ids = [t.matched_pattern_id for t in fraud_txs if getattr(t, "matched_pattern_id", None)]
    pattern_counts = Counter(pattern_ids)
    top_patterns = [
        {"id": pid, "count": cnt, "name": next(
            (p["name"] for p in _FRAUD_KB["patterns"] if p["id"] == pid), pid
        )}
        for pid, cnt in pattern_counts.most_common(3)
    ]

    recent_fraud_types = list(dict.fromkeys(
        t.matched_pattern_name for t in sorted(fraud_txs, key=lambda x: x.created_at, reverse=True)
        if getattr(t, "matched_pattern_name", None)
    ))[:3]

    return FraudStatsResponse(
        total_transactions=len(txs),
        fraud_count=len(fraud_txs),
        safe_count=len(safe_txs),
        suspicious_count=len(susp_txs),
        fraud_rate_pct=round(len(fraud_txs) / len(txs) * 100, 1) if txs else 0.0,
        total_amount_at_risk=round(sum(t.amount for t in fraud_txs), 2),
        top_fraud_patterns=top_patterns,
        recent_fraud_types=recent_fraud_types,
    )


@router.delete("/transactions/{tx_id}", status_code=204)
def delete_transaction(
    tx_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tx = db.query(Transaction).filter(
        Transaction.id == tx_id, Transaction.user_id == current_user.id
    ).first()
    if not tx:
        raise HTTPException(404, "Transaction not found")
    db.delete(tx); db.commit()


# ── FRAUD KNOWLEDGE BASE ──────────────────────────────────────────────────

@router.get("/fraud-patterns")
def get_fraud_patterns():
    """Return the 8 known UPI fraud patterns for the awareness page."""
    return _FRAUD_KB
