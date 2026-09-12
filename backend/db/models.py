"""
backend/db/models.py
SQLAlchemy ORM models for SPECTRA-UPI
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    full_name     = Column(String(100), nullable=False)
    email         = Column(String(120), unique=True, index=True, nullable=False)
    phone         = Column(String(20), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    transactions  = relationship("Transaction", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<User {self.email}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Transaction fields (what the user submits)
    amount          = Column(Float, nullable=False)
    platform        = Column(String(50), nullable=False)
    tx_date         = Column(String(20), nullable=False)   # DD/MM/YYYY
    tx_time         = Column(String(10), nullable=False)   # HH:MM

    # ML feature inputs
    location_change = Column(Boolean, default=False)
    new_recipient   = Column(Boolean, default=True)
    failed_attempts = Column(Integer, default=0)
    device_count    = Column(Integer, default=1)

    # ML output
    is_fraud        = Column(Boolean, nullable=False)
    fraud_score     = Column(Float, nullable=False)        # 0.0–1.0 confidence

    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.id} ₹{self.amount} {'FRAUD' if self.is_fraud else 'SAFE'}>"
