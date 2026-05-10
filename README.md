# AI-Based Expense Categorization & Smart Budget Planner

Production-style full-stack app using:
- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL
- Frontend: React + TypeScript + Vite
- ML: scikit-learn TF-IDF + Logistic Regression / Naive Bayes

This repository now includes:
- AI category prediction endpoint + retraining endpoint
- Budget CRUD with usage/remaining/overspending metrics
- Advanced analytics endpoints with optimized aggregation queries
- Anomaly flagging (`current > 2x` rolling 3-month category average)
- Expense forecasting with confidence interval
- Savings goal tracking with progress and ETA
- Notification system (budget threshold, anomaly, savings milestone)
- Optional JWT route protection + AI endpoint rate limiting

## Assumptions

- Existing project is FastAPI-based (not Node/Express), so implementation follows Python architecture.
- Existing data model has no users table; features requiring `user_id` use JWT `sub` if enabled, otherwise `DEFAULT_USER_ID` (default `1`).
- Backward compatibility is preserved for existing endpoints (`/api/upload`, `/api/transactions`, `/api/analytics/summary`, `/api/forecast`, etc.).

## 1. Teammate Setup After Pull

### 1.1 Pull latest changes
```powershell
git pull origin <your-branch>
```

### 1.2 Create env files
```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

### 1.3 Configure ports globally (optional)

| Service | Variable | Default |
|---|---|---|
| PostgreSQL | `DB_PORT` | `5432` |
| Backend | `BACKEND_PORT` | `8001` |
| Frontend | `FRONTEND_PORT` | `5173` |

If you change one, update corresponding URLs:
- `VITE_API_BASE_URL`
- `CORS_ORIGINS`
- `CORS_ORIGIN_REGEX`

## 2. Run with Docker (Recommended Team Flow)

```powershell
docker compose up --build
```

Default URLs:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8001/api`
- PostgreSQL: `localhost:5432`

Stop:
```powershell
docker compose down
```

Reset containers + DB volume:
```powershell
docker compose down -v
```

## 3. Run Without Docker

### 3.1 Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python app/ml/train_model.py
$env:BACKEND_PORT = "8001"
uvicorn app.main:app --reload --host 0.0.0.0 --port $env:BACKEND_PORT
```

Optional LSTM retraining:
```powershell
pip install torch
```
Without `torch`, the app still runs normally, but selecting the `lstm` retraining algorithm will return a clear backend error.

### 3.2 Frontend
Open another terminal:
```powershell
cd frontend
npm install
$env:FRONTEND_PORT = "5173"
npm run dev
```

## 4. Migration Steps

If DB already exists from older version:
```powershell
cd backend
alembic upgrade head
```

New migration applied:
- `20260301_02_advanced_features.py`

Schema additions:
- `transactions.anomaly_flag`
- `budgets` table
- `savings_goals` table
- `notifications` table
- additional performance indexes on transactions and new tables

## 5. Important Environment Variables

Backend:
- `DATABASE_URL`
- `CORS_ORIGINS`
- `MODEL_PATH`
- `ENVIRONMENT` (`development` or `production`)
- `AUTH_REQUIRED` (`false` by default for non-breaking local dev)
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `DEFAULT_USER_ID`
- `AI_RATE_LIMIT_PER_MINUTE`

Frontend:
- `VITE_API_BASE_URL`
- `FRONTEND_PORT`

## 6. API Endpoints

### Existing + maintained
- `POST /api/upload`
- `POST /api/transactions`
- `GET /api/transactions?limit=&offset=`
- `PATCH /api/transactions/{id}/override`
- `GET /api/analytics/summary`
- `GET /api/analytics/categories`
- `GET /api/analytics/monthly-trend`
- `GET /api/alerts`
- `GET /api/budget/recommendations`
- `GET /api/forecast`
- `GET /api/financial-health-score`
- `GET /api/ai-summary`

### New AI
- `POST /api/ai/predict-category`
- `POST /api/ai/retrain-model`

### New Budget CRUD
- `POST /api/budgets`
- `GET /api/budgets`
- `GET /api/budgets/{id}`
- `PATCH /api/budgets/{id}`
- `DELETE /api/budgets/{id}`

### New Analytics
- `GET /api/analytics/monthly-summary`
- `GET /api/analytics/category-distribution`
- `GET /api/analytics/income-vs-expense`
- `GET /api/analytics/savings-rate`
- `GET /api/analytics/forecast`

### Savings Goals
- `POST /api/savings-goals`
- `GET /api/savings-goals`
- `PATCH /api/savings-goals/{id}/progress`
- `DELETE /api/savings-goals/{id}`

### Notifications
- `GET /api/notifications`
- `PATCH /api/notifications/{id}`

## 7. Security Notes

- Route-level JWT dependency is implemented with optional enforcement.
- Enable strict auth by setting:
  - `AUTH_REQUIRED=true`
  - secure `JWT_SECRET_KEY`
- AI endpoints have in-memory rate limiting by client IP.
- SQLAlchemy ORM is used for query safety.
- In production mode (`ENVIRONMENT=production`), generic 500 error messages are returned.

## 8. Frontend Integration Added

- Dashboard:
  - AI quick category prediction
  - live notifications panel (mark read)
- Budget page:
  - budget CRUD creation flow + utilization view
  - savings goal creation + progress updates
  - advanced forecast with confidence interval
- Upload page:
  - model retraining action
  - anomaly flag visibility in upload result

## 9. Notes

- `sample_transactions.csv` can be used for quick testing.
- If scikit-learn is unavailable (common on Python 3.14), retraining now falls back to a built-in Naive Bayes text model and still works.
- For best model quality, Python 3.12/3.13 with scikit-learn is still recommended.
