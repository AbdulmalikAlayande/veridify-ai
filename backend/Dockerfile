FROM python:3.11-slim

WORKDIR /app

# OpenCV runtime deps (libGL etc.) — opencv-python-headless still needs glib/libgomp.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Cache the dependency layer separately from app source.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# App source. .dockerignore prunes .venv / .env / __pycache__ etc.
COPY . .

# Privacy contract: temp images land here and get deleted immediately after inference.
RUN mkdir -p /tmp/veridifi

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# $PORT is honoured for Render/Fly/Heroku; falls back to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
