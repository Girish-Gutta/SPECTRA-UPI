"""
train_model.py
Trains an XGBoost fraud detection model on the generated dataset.
Outputs: ../models/fraud_model.pkl  +  ../models/feature_columns.pkl
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, precision_score, recall_score, f1_score
)
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

# ── Paths ──────────────────────────────────────────────────────────────────
DATA_PATH   = Path("../data/upi_transactions.csv")
MODELS_DIR  = Path("../models")
MODELS_DIR.mkdir(exist_ok=True)

MODEL_PATH    = MODELS_DIR / "fraud_model.pkl"
SCALER_PATH   = MODELS_DIR / "scaler.pkl"
FEATURES_PATH = MODELS_DIR / "feature_columns.pkl"

# ── Load Data ──────────────────────────────────────────────────────────────
print("Loading dataset...")
df = pd.read_csv(DATA_PATH)
print(f"  Shape: {df.shape}  |  Fraud rate: {df['is_fraud'].mean()*100:.1f}%")

# ── Features / Target ──────────────────────────────────────────────────────
TARGET = "is_fraud"
FEATURES = [c for c in df.columns if c != TARGET]

X = df[FEATURES].values
y = df[TARGET].values

# ── Train/Test Split ───────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain: {len(X_train):,}  |  Test: {len(X_test):,}")

# ── Scale ──────────────────────────────────────────────────────────────────
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

# ── Handle Class Imbalance with SMOTE ─────────────────────────────────────
print("\nApplying SMOTE to balance training data...")
sm = SMOTE(random_state=42)
X_train_bal, y_train_bal = sm.fit_resample(X_train_sc, y_train)
print(f"  After SMOTE — Legit: {(y_train_bal==0).sum():,}  Fraud: {(y_train_bal==1).sum():,}")

# ── Train XGBoost ──────────────────────────────────────────────────────────
print("\nTraining XGBoost model...")
model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=1,          # balanced by SMOTE already
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42,
    verbosity=0,
)
model.fit(X_train_bal, y_train_bal)
print("  Done.")

# ── Evaluate ───────────────────────────────────────────────────────────────
y_pred  = model.predict(X_test_sc)
y_proba = model.predict_proba(X_test_sc)[:, 1]

print("\n" + "="*50)
print("MODEL PERFORMANCE ON TEST SET")
print("="*50)
print(f"  AUC-ROC   : {roc_auc_score(y_test, y_proba):.4f}")
print(f"  Precision : {precision_score(y_test, y_pred):.4f}")
print(f"  Recall    : {recall_score(y_test, y_pred):.4f}")
print(f"  F1 Score  : {f1_score(y_test, y_pred):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))

cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:")
print(f"  True Negatives  (legit correctly flagged safe) : {cm[0][0]:,}")
print(f"  False Positives (legit flagged as fraud)       : {cm[0][1]:,}")
print(f"  False Negatives (fraud missed)                 : {cm[1][0]:,}")
print(f"  True Positives  (fraud correctly caught)       : {cm[1][1]:,}")

# ── Feature Importance ─────────────────────────────────────────────────────
print("\nTop Feature Importances:")
importances = model.feature_importances_
feat_imp = sorted(zip(FEATURES, importances), key=lambda x: x[1], reverse=True)
for feat, imp in feat_imp[:10]:
    bar = "█" * int(imp * 200)
    print(f"  {feat:<30} {imp:.4f}  {bar}")

# ── Save Model ─────────────────────────────────────────────────────────────
joblib.dump(model,    MODEL_PATH)
joblib.dump(scaler,   SCALER_PATH)
joblib.dump(FEATURES, FEATURES_PATH)

print(f"\n✅ Model saved    → {MODEL_PATH}")
print(f"✅ Scaler saved   → {SCALER_PATH}")
print(f"✅ Features saved → {FEATURES_PATH}")
print("\nPhase 1 complete. Ready for Phase 2 (FastAPI backend).")
