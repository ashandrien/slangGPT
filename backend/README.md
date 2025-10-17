````markdown
# Backend (FastAPI + spaCy)

Run the FastAPI backend which exposes a POST /chat endpoint. It uses spaCy to do simple NLP processing and returns a mocked assistant reply.

Quickstart (macOS / zsh):

# Backend (FastAPI + spaCy)

Run the FastAPI backend which exposes a POST /chat endpoint. It uses spaCy to do simple NLP processing and returns a mocked assistant reply.

Quickstart (macOS / zsh):

```bash
# create venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Endpoint:
- POST /chat  {"message": "..."} -> {"reply": "...", "meta": {...}}

Development CORS & proxy
------------------------

During local development the frontend uses Vite. The project includes a Vite dev proxy (see `frontend/vite.config.ts`) which forwards requests for `/slang` and `/chat` to the backend at `http://127.0.0.1:8000`.

Recommendation for local development:

- Use the Vite dev server (`cd frontend && npm run dev`) and keep the backend running at `127.0.0.1:8000`. The dev proxy makes API calls same-origin so CORS is not required.
- Backend CORS is intentionally restricted to a small set of local dev origins in `main.py`. If you add new dev ports, update the `allow_origins` list or use an environment-driven configuration.

To restart the backend after changing CORS:

```bash
cd backend
source .venv/bin/activate
# restart uvicorn (example)
pkill -f 'uvicorn main:app' || true
uvicorn main:app --host 127.0.0.1 --port 8000 &
```

Environment-controlled allowed origins
--------------------------------------

You can control allowed CORS origins at runtime using the `ALLOWED_ORIGINS` environment variable (comma-separated). Example (zsh/bash):

```bash
# allow 5173 and 5178
export ALLOWED_ORIGINS="http://127.0.0.1:5173,http://127.0.0.1:5178"
uvicorn main:app --host 127.0.0.1 --port 8000

# revert to default behavior
unset ALLOWED_ORIGINS
uvicorn main:app --host 127.0.0.1 --port 8000
```

