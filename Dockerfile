# Multi-stage Dockerfile
# Stage 1: build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
COPY frontend/tsconfig.json frontend/vite.config.ts ./
COPY frontend/src ./src
COPY frontend/index.html ./
RUN npm ci --silent && npm run build

# Stage 2: build backend image and copy frontend build into backend/static
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System deps for spaCy model installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY backend/ ./backend
# Copy frontend static build into backend/static
COPY --from=frontend-build /app/frontend/dist ./backend/static

# Create venv and install requirements
RUN python -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"
RUN pip install --upgrade pip
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install -r backend/requirements.txt

# Install spaCy model. Using en_core_web_sm as lightweight model.
RUN python -m spacy download en_core_web_sm

WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
