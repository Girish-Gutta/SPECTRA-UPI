# SPECTRA-UPI
### Swift Payment Evaluation & Classification for Transaction Risk Analysis

A full-stack UPI fraud detection system powered by XGBoost ML — real-time fraud scoring with 97%+ accuracy.

---

## Project Structure

```
SPECTRA-UPI/
├── frontend/          # HTML/CSS/JS web app (login, dashboard, fraud check, history)
├── backend/
│   ├── api/           # FastAPI REST API (auth, prediction, transaction history)
│   ├── ml/            # Dataset generation + model training scripts
│   ├── models/        # Trained model artifacts (.pkl files)
│   ├── data/          # Synthetic UPI transaction dataset
│   ├── db/            # Database schema + migrations
│   └── venv/          # Python virtual environment
├── docs/              # Architecture diagrams, API docs
└── .github/           # CI/CD workflows
```

## Tech Stack

| Layer      | Technology              |
|------------|------------------------|
| Frontend   | HTML5 · CSS3 · Vanilla JS |
| Backend    | Python · FastAPI        |
| ML Model   | XGBoost · scikit-learn  |
| Database   | SQLite → PostgreSQL     |
| Auth       | JWT Tokens              |
| Deploy     | Render (backend) · GitHub Pages (frontend) |

## Model Performance

| Metric    | Score  |
|-----------|--------|
| AUC-ROC   | 0.9998 |
| Precision | 96.8%  |
| Recall    | 98.0%  |
| F1 Score  | 97.4%  |

## Setup

```bash
cd backend
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Regenerate dataset (optional)
python ml/generate_dataset.py

# Retrain model (optional)
python ml/train_model.py

# Start API server
uvicorn api.main:app --reload --port 8000
```

## Status

- [x] Phase 1 — Dataset + ML Model
- [ ] Phase 2 — FastAPI Backend
- [ ] Phase 3 — Frontend ↔ Backend Integration
- [ ] Phase 4 — Polish + Deploy
