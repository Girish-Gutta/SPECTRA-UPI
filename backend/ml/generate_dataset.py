"""
generate_dataset.py
Generates a realistic synthetic UPI transaction dataset with fraud labels.
Outputs: ../data/upi_transactions.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ── Reproducibility ────────────────────────────────────────────────────────
np.random.seed(42)
random.seed(42)

# ── Config ─────────────────────────────────────────────────────────────────
N_TOTAL     = 50_000   # total transactions
FRAUD_RATIO = 0.07     # 7% fraud (realistic for UPI)
N_FRAUD     = int(N_TOTAL * FRAUD_RATIO)
N_LEGIT     = N_TOTAL - N_FRAUD

PLATFORMS   = ["Google Pay", "PhonePe", "Paytm", "BHIM"]
PLATFORM_W  = [0.40,         0.32,      0.20,    0.08]   # market share weights

START_DATE  = datetime(2024, 1, 1)
END_DATE    = datetime(2026, 9, 1)
DATE_RANGE  = (END_DATE - START_DATE).days


def random_datetime(fraud=False):
    """Legitimate txns cluster 9am–9pm; fraud spikes 1am–5am."""
    day = START_DATE + timedelta(days=random.randint(0, DATE_RANGE))
    if fraud:
        # Fraud more likely at odd hours
        hour = random.choices(range(24), weights=[
            6,6,6,6,4,2,1,1,1,1,1,1,1,1,1,1,2,2,2,2,3,4,5,5
        ])[0]
    else:
        hour = random.choices(range(24), weights=[
            1,1,1,1,1,1,2,4,6,8,8,8,7,7,8,8,8,7,6,5,4,3,2,2
        ])[0]
    minute = random.randint(0, 59)
    return day.replace(hour=hour, minute=minute)


def generate_legit(n):
    records = []
    for _ in range(n):
        dt = random_datetime(fraud=False)
        amount = round(np.random.lognormal(mean=6.5, sigma=1.2), 2)  # ₹50–₹5k typical
        amount = min(amount, 99_999)  # UPI per-txn limit
        platform = random.choices(PLATFORMS, weights=PLATFORM_W)[0]
        # Devices: most users have 1–2 devices
        device_count = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
        # Location: mostly same city
        location_change = random.choices([0, 1], weights=[0.92, 0.08])[0]
        # Failed attempts before this txn: almost never for legit
        failed_attempts = random.choices([0, 1, 2], weights=[0.95, 0.04, 0.01])[0]
        # Recipient seen before?
        new_recipient = random.choices([0, 1], weights=[0.80, 0.20])[0]
        # Txn frequency in last hour
        txn_freq_1h = random.choices(range(6), weights=[0.55, 0.30, 0.10, 0.03, 0.015, 0.005])[0]

        records.append({
            "amount": amount,
            "hour": dt.hour,
            "day_of_week": dt.weekday(),       # 0=Mon, 6=Sun
            "is_weekend": int(dt.weekday() >= 5),
            "platform": platform,
            "device_count": device_count,
            "location_change": location_change,
            "failed_attempts": failed_attempts,
            "new_recipient": new_recipient,
            "txn_freq_1h": txn_freq_1h,
            "is_fraud": 0,
        })
    return records


def generate_fraud(n):
    records = []
    for _ in range(n):
        dt = random_datetime(fraud=True)
        # Fraud: large round amounts OR micro-test then large
        fraud_type = random.choices(["large", "round_large", "micro"], weights=[0.5, 0.3, 0.2])[0]
        if fraud_type == "large":
            amount = round(random.uniform(20_000, 99_999), 2)
        elif fraud_type == "round_large":
            amount = float(random.choice([5000, 10000, 25000, 50000, 99000]))
        else:
            amount = round(random.uniform(1, 50), 2)  # test transaction

        platform = random.choices(PLATFORMS, weights=PLATFORM_W)[0]
        device_count = random.choices([1, 2, 3, 4], weights=[0.3, 0.3, 0.25, 0.15])[0]
        location_change = random.choices([0, 1], weights=[0.35, 0.65])[0]   # often new location
        failed_attempts = random.choices([0, 1, 2, 3], weights=[0.4, 0.3, 0.2, 0.1])[0]
        new_recipient = random.choices([0, 1], weights=[0.2, 0.8])[0]       # almost always new
        txn_freq_1h = random.choices(range(8), weights=[0.2, 0.2, 0.2, 0.15, 0.1, 0.07, 0.05, 0.03])[0]

        records.append({
            "amount": amount,
            "hour": dt.hour,
            "day_of_week": dt.weekday(),
            "is_weekend": int(dt.weekday() >= 5),
            "platform": platform,
            "device_count": device_count,
            "location_change": location_change,
            "failed_attempts": failed_attempts,
            "new_recipient": new_recipient,
            "txn_freq_1h": txn_freq_1h,
            "is_fraud": 1,
        })
    return records


if __name__ == "__main__":
    print(f"Generating {N_LEGIT:,} legitimate + {N_FRAUD:,} fraudulent transactions...")

    legit = generate_legit(N_LEGIT)
    fraud = generate_fraud(N_FRAUD)
    all_records = legit + fraud

    df = pd.DataFrame(all_records)

    # One-hot encode platform
    df = pd.get_dummies(df, columns=["platform"], prefix="plat")

    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    out_path = "../data/upi_transactions.csv"
    df.to_csv(out_path, index=False)

    print(f"✅ Dataset saved to {out_path}")
    print(f"   Shape  : {df.shape}")
    print(f"   Fraud  : {df['is_fraud'].sum():,}  ({df['is_fraud'].mean()*100:.1f}%)")
    print(f"   Legit  : {(df['is_fraud']==0).sum():,}")
    print(f"\nFeatures: {[c for c in df.columns if c != 'is_fraud']}")
