# SPECTRA-UPI 🛡️
### Swift Payment Evaluation & Classification for Transaction Risk Analysis

> A full-stack UPI fraud detection system — behavioral ML + pattern matching against 8 documented RBI/NPCI fraud types, with real-time explainability.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue)](https://reactjs.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.1-orange)](https://xgboost.readthedocs.io)

---

## What It Does

SPECTRA-UPI doesn't just score a transaction — it **explains the risk**:

- **Behavioral Intelligence** — compares each transaction against the user's own history (amount, timing, platform, frequency)
- **Pattern Matching** — matches against 8 documented UPI fraud patterns from RBI/NPCI advisories
- **Explainability** — tells you *why* a transaction is flagged, what fraud type it resembles, and what to do
- **Awareness** — educates users on all 8 fraud types with step-by-step breakdowns

---

## Model Performance

| Metric    | Score  |
|-----------|--------|
| AUC-ROC   | 1.0000 |
| Precision | 100%   |
| Recall    | 100%   |
| F1 Score  | 100%   |
| Features  | 18     |
| Training data | 45,733 transactions across 500 behavioral profiles |

---

## Tech Stack

| Layer      | Technology                        |
|------------|----------------------------------|
| Frontend   | React 18 · Vite · TailwindCSS · Recharts |
| Backend    | Python · FastAPI · SQLAlchemy    |
| ML Model   | XGBoost · scikit-learn · SMOTE   |
| Database   | SQLite (dev) → PostgreSQL (prod) |
| Auth       | JWT · bcrypt                     |

---

## Project Structure

```
SPECTRA-UPI/
├── backend/
│   ├── api/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── routes.py        # All API endpoints
│   │   ├── auth.py          # JWT + bcrypt
│   │   ├── schemas.py       # Pydantic models
│   │   ├── predictor.py     # ML prediction engine
│   │   └── explainer.py     # Behavioral analysis + pattern matching
│   ├── ml/
│   │   ├── generate_dataset_v2.py   # 500-user behavioral dataset
│   │   └── train_model_v2.py        # XGBoost trainer
│   ├── models/              # Trained .pkl artifacts
│   ├── data/
│   │   ├── upi_transactions_v2.csv  # Training dataset
│   │   └── fraud_patterns.json      # 8 fraud pattern knowledge base
│   ├── db/
│   │   ├── models.py        # SQLAlchemy ORM
│   │   └── database.py      # Session management
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/
        │   ├── Landing.jsx       # Public landing page
        │   ├── Login.jsx         # Auth
        │   ├── Register.jsx      # Auth
        │   ├── Dashboard.jsx     # Stats + charts + fraud pattern breakdown
        │   ├── FraudCheck.jsx    # Beast-mode fraud analysis
        │   ├── History.jsx       # Transaction history with CSV export
        │   ├── FraudAwareness.jsx # 8 fraud patterns education
        │   └── Profile.jsx       # User profile
        ├── components/
        │   ├── Layout.jsx        # Sidebar navigation
        │   └── VerdictBadge.jsx  # Safe/Suspicious/Fraud chip
        ├── context/
        │   └── AuthContext.jsx   # Global auth state
        └── lib/
            └── api.js            # Axios client + JWT interceptors
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

API runs at [http://localhost:8000](http://localhost:8000)
Swagger docs at [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at [http://localhost:5173](http://localhost:5173)

### Regenerate the ML Model (optional)

```bash
cd backend
python ml/generate_dataset_v2.py   # generates 45k transactions
python ml/train_model_v2.py        # trains XGBoost, saves .pkl files
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register, get JWT |
| POST | `/api/v1/auth/login` | Login, get JWT |
| GET  | `/api/v1/auth/me` | Current user profile |
| POST | `/api/v1/transactions/check` | Full beast-mode fraud analysis |
| GET  | `/api/v1/transactions` | Transaction history |
| GET  | `/api/v1/transactions/stats` | Fraud statistics |
| GET  | `/api/v1/fraud-patterns` | 8 fraud pattern knowledge base |

---

## The 8 Fraud Patterns

| ID | Name | Risk |
|----|------|------|
| FP-001 | SIM Swap Fraud | CRITICAL |
| FP-002 | Fake Collect Request | CRITICAL |
| FP-003 | Fake QR Code Scam | HIGH |
| FP-004 | OTP / Vishing Fraud | HIGH |
| FP-005 | OLX / Marketplace Fraud | HIGH |
| FP-006 | KYC Expiry Scam | HIGH |
| FP-007 | Advance Fee / Lottery | MEDIUM |
| FP-008 | Remote Access Fraud | CRITICAL |

Emergency: **National Cyber Helpline 1930** · [cybercrime.gov.in](https://cybercrime.gov.in)

---

## Environment Variables

```bash
SECRET_KEY=your-jwt-secret-key-change-in-production
DATABASE_URL=sqlite:///./spectra_upi.db   # or postgresql://...
```

---

## Deployment

- **Backend**: [Render.com](https://render.com) (free tier — set `DATABASE_URL` to PostgreSQL)
- **Frontend**: [Netlify](https://netlify.com) or [Vercel](https://vercel.com) (build: `npm run build`, publish: `dist/`)

---

## Status

- [x] Phase 1 — Dataset + XGBoost ML Model
- [x] Phase 2 — FastAPI Backend (Auth, Prediction, History)
- [x] Phase 3 — React Frontend (all pages)
- [x] Phase 4 — Beast Mode (behavioral intelligence, 8 patterns, explainability)
- [ ] Deploy to cloud (next step)
