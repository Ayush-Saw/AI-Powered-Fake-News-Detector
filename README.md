# AI-Powered Fake News Detection and Verification Platform

## Setup (Windows PowerShell)
1. Put your existing `fake_news.csv` in `backend/dataset/fake_news.csv`.
2. Open PowerShell in this project folder:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m backend.train_model
python run.py
```
Open http://127.0.0.1:5000.

Expected dataset columns: `title`, `text`, `label`. Optional: `date`, `source`, `author`, `category`. Labels can be `fake`/`real` or `0`/`1`. The training script computes metrics from its own held-out test split and writes `backend/model/model_info.json`. Never invent or manually alter reported scores.

## Existing model compatibility
The app looks for `backend/model/fake_news_model.pkl` and `tfidf_vectorizer.pkl`. Compatible artifacts can be reused. If unavailable, retrain with the command above. Only load trusted pickle/joblib files.

## Login, roles, and dashboards
- `/register`: public user registration (passwords are stored as hashes).
- `/login` and `/logout`: session-based authentication.
- `/dashboard`: signed-in user's own analyses.
- `/admin/dashboard`: administrator overview, registered users, platform-wide analysis totals, and recent analyses.
- Admin-only pages are protected by a role check; registering through the public form always creates a regular user.
- On first run, a development administrator is created using `admin@truthlens.local` / `Admin@123` unless `ADMIN_EMAIL` and `ADMIN_PASSWORD` environment variables are set. Change these credentials and set `TRUTHLENS_SECRET_KEY` before any public deployment. The default credentials are for local development only.

## Pages
Home, login, registration, user dashboard, admin dashboard, detection, result, explainable AI, evidence search, source analysis, analytics, history, duplicate/similarity search, model performance, awareness quiz, about.

## Important limits
The model detects patterns learned from its dataset; it does not independently establish truth. The existing model previously reported by the project owner scored about 51.08% accuracy and should be treated as a weak baseline until reevaluated. Hindi input is optionally translated to English; translation can change meaning and an English-trained model is not validated for Hindi. Evidence search retrieves related Wikipedia pages as investigation leads, not proof. Similarity is not truth.

## Testing
- Visit `/api/health`.
- Submit a text at `/detect`; open result and explanation.
- Check `/history`, `/analytics`, `/model-performance`.
- Try `/verify?q=...` and `/duplicate`.
- Download a result PDF.
- Test empty text, long text, and Hindi text.
