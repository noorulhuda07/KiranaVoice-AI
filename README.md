# KiranaVoice AI

## Run locally (Windows PowerShell)

The backend uses FastAPI, SQLite, and the dependencies pinned in
`backend/requirements.txt`. From the project root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

If creating a local environment from scratch, run `python -m venv .venv` from
the project root, then use `.\.venv\Scripts\python.exe` in place of
`..\.venv\Scripts\python.exe` after changing to `backend`. The backend reads
`backend\.env`; set `GNANI_API_KEY` there to your own key to enable Gnani voice
services. Keep it blank to run the inventory and text-command workflows without
Gnani. Speech transcription also requires FFmpeg on `PATH`.

Run backend tests from `backend` with:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
```

In a second PowerShell window, from the project root:

```powershell
Set-Location frontend
npm install
npm run dev
```

The frontend reads `frontend\.env` (`VITE_API_URL=http://127.0.0.1:8000`).
The API health endpoint is `http://127.0.0.1:8000/api/health`; the Vite app is
`http://localhost:5173`.

## Status
- Done: product CRUD, add/sell/check/low-stock, alias matching, clarification, unit/stock validation,
  large-change confirmation, undo as compensating transaction, transaction history, decimal quantities.
- Gnani Prisma v2.5 STT + Timbre v2.5 TTS wired per docs.gnani.ai (backend/app/gnani.py). NOT yet tested with a real key.
- Not built: stock reconciliation, settings page, auth, deployment config.
