"""
generate_dataset_v2.py
Beast-mode dataset: per-user behavioral baselines + 15 features + 8 known fraud patterns.
Outputs: ../data/upi_transactions_v2.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

np.random.seed(42)
random.seed(42)

# ── Config ─────────────────────────────────────────────────────────────────
N_USERS     = 500
TXN_PER_USER = (30, 150)   # each user has 30–150 transactions
FRAUD_RATIO  = 0.07
PLATFORMS    = ["Google Pay", "PhonePe", "Paytm", "BHIM"]
PLATFORM_W   = [0.40, 0.32, 0.20, 0.08]
START_DATE   = datetime(2024, 1, 1)
END_DATE     = datetime(2026, 9, 1)
DATE_RANGE   = (END_DATE - START_DATE).days


# ── Build per-user behavioral profiles ────────────────────────────────────
def build_user_profile(user_id):
    """Each user has their own spending habits."""
    preferred_platform = random.choices(PLATFORMS, weights=PLATFORM_W)[0]
    avg_amount  = np.random.lognormal(mean=random.uniform(5.5, 7.5), sigma=0.5)
    std_amount  = avg_amount * random.uniform(0.3, 0.8)
    active_hours = sorted(random.sample(range(8, 23), random.randint(3, 6)))
    usual_devices = random.randint(1, 2)
    known_recipients = [f"recip_{user_id}_{i}" for i in range(random.randint(3, 15))]
    return {
        "user_id": user_id,
        "preferred_platform": preferred_platform,
        "avg_amount": avg_amount,
        "std_amount": std_amount,
        "active_hours": active_hours,
        "usual_devices": usual_devices,
        "known_recipients": known_recipients,
    }


def random_dt(fraud=False, active_hours=None):
    day = START_DATE + timedelta(days=random.randint(0, DATE_RANGE))
    if fraud:
        hour = random.choices(range(24), weights=[
            6,6,6,6,4,2,1,1,1,1,1,1,1,1,1,1,2,2,2,2,3,4,5,5
        ])[0]
    elif active_hours:
        hour = random.choice(active_hours)
    else:
        hour = random.choices(range(24), weights=[
            1,1,1,1,1,1,2,4,6,8,8,8,7,7,8,8,8,7,6,5,4,3,2,2
        ])[0]
    return day.replace(hour=hour, minute=random.randint(0, 59))


def amount_z_score(amount, avg, std):
    """How many standard deviations is this amount from the user's typical?"""
    if std < 1: return 0.0
    return round((amount - avg) / std, 3)


def generate_legit_for_user(profile, recent_txns):
    """Generate a legitimate transaction consistent with user behavior."""
    dt = random_dt(fraud=False, active_hours=profile["active_hours"])
    # Amount close to their usual
    amount = max(1, round(np.random.normal(profile["avg_amount"], profile["std_amount"]), 2))
    amount = min(amount, 99999)
    platform = random.choices(
        PLATFORMS,
        weights=[0.6 if p == profile["preferred_platform"] else 0.13 for p in PLATFORMS]
    )[0]
    recipient = random.choice(profile["known_recipients"])
    new_recipient = 0
    location_change = random.choices([0, 1], weights=[0.93, 0.07])[0]
    failed_attempts = random.choices([0, 1, 2], weights=[0.95, 0.04, 0.01])[0]
    device_count = random.choices(
        [profile["usual_devices"], profile["usual_devices"] + 1],
        weights=[0.90, 0.10]
    )[0]

    # Behavioral features
    last_hour_txns = [t for t in recent_txns if (dt - t["dt"]).total_seconds() < 3600]
    txn_freq_1h = len(last_hour_txns)
    last_24h_txns = [t for t in recent_txns if (dt - t["dt"]).total_seconds() < 86400]
    txn_freq_24h = len(last_24h_txns)
    recent_amounts = [t["amount"] for t in last_24h_txns[-5:]]
    avg_recent_amount = np.mean(recent_amounts) if recent_amounts else profile["avg_amount"]
    amount_vs_recent = abs(amount - avg_recent_amount) / (avg_recent_amount + 1)

    return {
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
        "txn_freq_24h": txn_freq_24h,
        "amount_z_score": amount_z_score(amount, profile["avg_amount"], profile["std_amount"]),
        "amount_vs_recent_ratio": round(amount_vs_recent, 3),
        "is_preferred_platform": int(platform == profile["preferred_platform"]),
        "amount_round": int(amount % 100 == 0 and amount >= 1000),
        "is_fraud": 0,
        "fraud_pattern": "NONE",
        "_dt": dt,
        "_recipient": recipient,
    }


def generate_fraud_for_user(profile, recent_txns):
    """Generate a fraudulent transaction based on one of the 8 known patterns."""
    # Pick a fraud pattern
    pattern = random.choice([
        "FP-001", "FP-002", "FP-003", "FP-004",
        "FP-005", "FP-006", "FP-007", "FP-008"
    ])

    dt = random_dt(fraud=True)

    # Pattern-specific characteristics
    if pattern == "FP-001":  # SIM Swap
        amount = random.uniform(20000, 99999)
        new_recipient = 1; location_change = 1; device_count = 3
        failed_attempts = random.randint(0, 1); txn_freq_1h = random.randint(2, 5)
        platform = random.choice(PLATFORMS)

    elif pattern == "FP-002":  # Fake Collect
        amount = random.uniform(500, 50000)
        new_recipient = 1; location_change = 0; device_count = profile["usual_devices"]
        failed_attempts = 0; txn_freq_1h = random.randint(1, 3)
        platform = random.choice(PLATFORMS)

    elif pattern == "FP-003":  # Fake QR
        amount = float(random.choice([100, 200, 500, 1000, 2000, 5000]))
        new_recipient = 1; location_change = random.randint(0, 1)
        device_count = profile["usual_devices"]; failed_attempts = 0
        txn_freq_1h = random.randint(0, 2)
        platform = random.choice(PLATFORMS)

    elif pattern == "FP-004":  # OTP/Vishing
        amount = random.uniform(5000, 99999)
        new_recipient = 1; location_change = 0
        device_count = random.randint(2, 3)
        failed_attempts = random.randint(1, 3); txn_freq_1h = random.randint(1, 4)
        platform = random.choice(PLATFORMS)

    elif pattern == "FP-005":  # OLX Marketplace
        amount = float(random.choice([5000, 10000, 15000, 20000, 25000, 30000]))
        new_recipient = 1; location_change = random.randint(0, 1)
        device_count = profile["usual_devices"]; failed_attempts = 0
        txn_freq_1h = random.randint(0, 1)
        platform = random.choice(PLATFORMS)

    elif pattern == "FP-006":  # KYC Scam
        amount = float(random.choice([1, 10, 50, 100, 499, 999]))  # small test amounts
        new_recipient = 1; location_change = 0
        device_count = random.randint(1, 2)
        failed_attempts = random.randint(2, 4); txn_freq_1h = random.randint(1, 3)
        platform = random.choice(PLATFORMS)

    elif pattern == "FP-007":  # Advance Fee
        amount = float(random.choice([99, 199, 299, 499, 999, 1999]))
        new_recipient = 1; location_change = 0
        device_count = profile["usual_devices"]; failed_attempts = 0
        txn_freq_1h = random.randint(0, 2)
        platform = random.choice(PLATFORMS)

    else:  # FP-008 Remote Access
        amount = random.uniform(10000, 99999)
        new_recipient = 1; location_change = 1
        device_count = random.randint(3, 4)
        failed_attempts = random.randint(0, 1); txn_freq_1h = random.randint(3, 6)
        platform = random.choice(PLATFORMS)

    # Behavioral deviation
    last_24h = [t for t in recent_txns if (dt - t["dt"]).total_seconds() < 86400]
    recent_amounts = [t["amount"] for t in last_24h[-5:]]
    avg_recent = np.mean(recent_amounts) if recent_amounts else profile["avg_amount"]
    amount_vs_recent = abs(amount - avg_recent) / (avg_recent + 1)

    return {
        "amount": round(amount, 2),
        "hour": dt.hour,
        "day_of_week": dt.weekday(),
        "is_weekend": int(dt.weekday() >= 5),
        "platform": platform,
        "device_count": device_count,
        "location_change": location_change,
        "failed_attempts": failed_attempts,
        "new_recipient": new_recipient,
        "txn_freq_1h": txn_freq_1h,
        "txn_freq_24h": random.randint(0, 5),
        "amount_z_score": amount_z_score(amount, profile["avg_amount"], profile["std_amount"]),
        "amount_vs_recent_ratio": round(amount_vs_recent, 3),
        "is_preferred_platform": int(platform == profile["preferred_platform"]),
        "amount_round": int(amount % 100 == 0 and amount >= 1000),
        "is_fraud": 1,
        "fraud_pattern": pattern,
        "_dt": dt,
        "_recipient": f"unknown_{random.randint(1000,9999)}",
    }


if __name__ == "__main__":
    print("Generating beast-mode dataset with per-user behavioral profiles...")
    all_records = []

    for user_id in range(N_USERS):
        profile = build_user_profile(user_id)
        n_txns = random.randint(*TXN_PER_USER)
        n_fraud = max(1, int(n_txns * FRAUD_RATIO))
        n_legit = n_txns - n_fraud

        fraud_indices = set(random.sample(range(n_txns), n_fraud))
        recent_txns = []

        for i in range(n_txns):
            if i in fraud_indices:
                row = generate_fraud_for_user(profile, recent_txns)
            else:
                row = generate_legit_for_user(profile, recent_txns)

            row["user_id"] = user_id
            recent_txns.append({"dt": row["_dt"], "amount": row["amount"]})
            if len(recent_txns) > 50:
                recent_txns.pop(0)

            # Remove internal fields
            row.pop("_dt"); row.pop("_recipient")
            all_records.append(row)

        if user_id % 100 == 0:
            print(f"  Users processed: {user_id}/{N_USERS}")

    df = pd.DataFrame(all_records)

    # One-hot encode platform
    df = pd.get_dummies(df, columns=["platform"], prefix="plat")

    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    out_path = data_dir / "upi_transactions_v2.csv"

    # Save training data (drop user_id and fraud_pattern — not features)
    train_df = df.drop(columns=["user_id", "fraud_pattern"])
    train_df.to_csv(out_path, index=False)

    print(f"\n[OK] Dataset saved to {out_path}")
    print(f"   Shape      : {train_df.shape}")
    print(f"   Users      : {N_USERS}")
    print(f"   Total Txns : {len(df):,}")
    print(f"   Fraud      : {df['is_fraud'].sum():,}  ({df['is_fraud'].mean()*100:.1f}%)")
    print(f"   Features   : {[c for c in train_df.columns if c != 'is_fraud']}")
    print(f"\n   Fraud by pattern:")
    for p, cnt in df[df['is_fraud']==1]['fraud_pattern'].value_counts().items():
        print(f"     {p}: {cnt}")
