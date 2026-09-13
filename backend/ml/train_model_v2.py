"""
train_model_v2.py
Beast-mode: trains on 15-feature behavioral dataset, saves model + scaler + features.
"""

import pandas as pd
import numpy as np
import joblib
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, precision_score, recall_score, f1_score
)
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

BASE_DIR    = Path(__file__).resolve().parent.parent
DATA_PATH   = BASE_DIR / "data" / "upi_transactions_v2.csv"
MODELS_DIR  = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

MODEL_PATH    = MODELS_DIR / "fraud_model_v2.pkl"
SCALER_PATH   = MODELS_DIR / "scaler_v2.pkl"
FEATURES_PATH = MODELS_DIR / "feature_columns_v2.pkl"

print("Loading v2 dataset...")
df = pd.read_csv(DATA_PATH)
print(f"  Shape: {df.shape}  |  Fraud: {df['is_fraud'].mean()*100:.1f}%")

TARGET   = "is_fraud"
FEATURES = [c for c in df.columns if c != TARGET]
print(f"  Features ({len(FEATURES)}): {FEATURES}")

X = df[FEATURES].values
y = df[TARGET].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain: {len(X_train):,}  |  Test: {len(X_test):,}")

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

print("\nApplying SMOTE...")
sm = SMOTE(random_state=42)
X_bal, y_bal = sm.fit_resample(X_train_sc, y_train)
print(f"  After SMOTE: Legit={( y_bal==0).sum():,}  Fraud={(y_bal==1).sum():,}")

print("\nTraining XGBoost v2...")
model = XGBClassifier(
    n_estimators=300,
    max_depth=7,
    learning_rate=0.08,
    subsample=0.85,
    colsample_bytree=0.85,
    min_child_weight=3,
    gamma=0.1,
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42,
    verbosity=0,
)
model.fit(X_bal, y_bal)

y_pred  = model.predict(X_test_sc)
y_proba = model.predict_proba(X_test_sc)[:, 1]

print("\n" + "="*55)
print("V2 MODEL PERFORMANCE")
print("="*55)
print(f"  AUC-ROC   : {roc_auc_score(y_test, y_proba):.4f}")
print(f"  Precision : {precision_score(y_test, y_pred):.4f}")
print(f"  Recall    : {recall_score(y_test, y_pred):.4f}")
print(f"  F1 Score  : {f1_score(y_test, y_pred):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))

cm = confusion_matrix(y_test, y_pred)
print(f"  True Negatives  : {cm[0][0]:,}")
print(f"  False Positives : {cm[0][1]:,}")
print(f"  False Negatives : {cm[1][0]:,}")
print(f"  True Positives  : {cm[1][1]:,}")

print("\nTop Feature Importances:")
feat_imp = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: x[1], reverse=True)
for feat, imp in feat_imp[:12]:
    bar = "=" * int(imp * 150)
    print(f"  {feat:<35} {imp:.4f}  {bar}")

joblib.dump(model,    MODEL_PATH)
joblib.dump(scaler,   SCALER_PATH)
joblib.dump(FEATURES, FEATURES_PATH)

print(f"\n[OK] Model v2 saved   -> {MODEL_PATH}")
print(f"[OK] Scaler v2 saved  -> {SCALER_PATH}")
print(f"[OK] Features saved   -> {FEATURES_PATH}")
