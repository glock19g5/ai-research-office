# AIO-1.1 Backend (Phase 1 foundation)

FastAPI service, separated from the existing Streamlit UI (`app.py` on `main`).
Phase 1 pre-flight (WB-0.3): health endpoint + test scaffold only — **no AI, no DB**.

## Run locally
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # no real secrets required
uvicorn app.main:app --reload
# -> http://127.0.0.1:8000/health
```

## Test
```bash
cd backend
pip install -r requirements.txt
pytest -q
```

## Layout
- `app/main.py` — FastAPI app + `/health`
- `app/config.py` — settings via pydantic-settings (no secrets in code, D-014)
- `tests/` — pytest scaffold
