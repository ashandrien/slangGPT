Deployment guide

This repository includes a multi-stage Dockerfile that builds the frontend and
serves the built static assets from the Python/FastAPI backend.

Build image (local):

```bash
# From repository root (where Dockerfile lives)
docker build -t slanggpt:latest .
```

Run locally:

```bash
docker run --rm -p 8000:8000 slanggpt:latest
```

Or with docker-compose:

```bash
docker-compose up --build -d
```

Notes:
- The backend serves static files from `/static` if the frontend build is
  present. The Dockerfile copies the Vite `dist/` into `backend/static` so the
  site will be available at http://localhost:8000/ when the container runs.
- The Dockerfile installs `en_core_web_sm` spaCy model. For production you may
  want to select a different model or reduce image size by using a custom
  model artifact deployment.
