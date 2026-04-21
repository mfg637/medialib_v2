FROM python:3.14-slim-trixie

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libmagic1 \
    libheif-plugin-dav1d \
    libheif-plugin-aomenc \
    libvips-dev \
    libjxl-tools \
    ffmpeg \
    libx264-dev \
    libvpx-dev \
    libopus-dev \
    libdav1d-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir whitenoise

COPY . .

ARG MEDIALIB_ROOT=/app/media
ENV MEDIALIB_ROOT=${MEDIALIB_ROOT}

RUN python manage.py collectstatic --noinput

ENV GUNICORN_WORKERS=4
ENV DJANGO_SETTINGS_MODULE=medialib_v2.settings

EXPOSE 8000

CMD gunicorn --bind 0.0.0.0:8000 \
             --workers $GUNICORN_WORKERS \
             medialib_v2.wsgi:application
