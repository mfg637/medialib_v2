# ==============================================================================
# Stage 1: Builder 
# ==============================================================================
FROM python:3.14-slim-trixie AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libvips-dev \
    libopus-dev \
    libdav1d-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt


# ==============================================================================
# Stage 2: Final
# ==============================================================================
FROM python:3.14-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    DJANGO_SETTINGS_MODULE=medialib_v2.settings

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    libvips42t64 \
    ffmpeg \
    libheif-plugin-dav1d \
    libheif-plugin-aomenc \
    libjxl-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ARG MEDIALIB_ROOT=/app/media
ENV MEDIALIB_ROOT=${MEDIALIB_ROOT}

ENV GUNICORN_WORKERS=4

COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD gunicorn --bind 0.0.0.0:8000 \
             --workers $GUNICORN_WORKERS \
             medialib_v2.wsgi:application
