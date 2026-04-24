# Medialib v2

A Booru-like media library designed for storing, categorizing, and managing content.

The system is primarily oriented toward local image collections, but it also supports video and looped animations (including GIFs). Tag-based indexing and a custom Domain Specific Language (DSL) implementation allow for content searching as fast as Booru-style imageboards, far exceeding traditional tree-like folder hierarchies.

## Key Features

- **Network Access**: Access your collection from any device within your local network.
- **Access Control**: Manage content access using filtering mechanisms and user groups (e.g., the `nsfw` group).
- **Automated Import**: Upload content manually or automatically using the Derpibooru-Dl loader, which imports tags directly from the source.
- **Compatibility Adaptability**: Automatic processing of uploaded content to create a set of representations based on device compatibility levels.
- **Smart Rendering**: Displays content optimized for the compatibility level of the current device.
- **AI-Powered Tagging**: Simplifies routine tagging tasks with an AI tagger and tag implication mechanisms (automatically pulling abstract tags based on specific ones).
- **Hybrid Deduplication**: A combination of SHA256 and LAB-based perceptual hashing (phash) prevents duplicate uploads and identifies visually similar images.
- **Modern Compression**: Utilization of **WEBP** and **AVIF** formats reduces total collection size by approximately 50%. The `pyvips` library enables high-quality 10-bit AVIF representations with low RAM usage even for massive source files.

## Technology Stack

- **Backend**: Django 6.x, PostgreSQL.
- **Task Queue**: Celery + Redis (for heavy media processing).
- **Media Tools**: FFmpeg (video), pyvips (images), ImageHash (analytics), and Pillow.
- **Frontend**: Vanilla JS, Web Components, and CSS Variables (for easy theme switching).

## Project Architecture

- `media_receiving`: File ingestion, validation, and task management.
- `image_processing`: Core engine for representation processing, analysis, hash generation, and comparison.
- `medialib`: UI logic, collections, albums, and tags.
- `base`: Shared enums, functions, and base classes.

## Compatibility Levels (CL) Concept

The Compatibility Level concept is adapted from the earlier ACLMMP project. In Medialib v2, the level numbering order is determined by the formula $4 - X$ from initial ACLMMP definition. Detailed specifications can be found in `image_processing.core.specification`.

### Level Overview

1. **CL1**: The minimum level supported by Medialib v2. Supports **WEBP** images, H.264 looped animations (60fps), or VP9 720p 30fps video in **WebM**.
2. **CL2**: Modern low-power devices. Capable of decoding **AVIF** (up to 2048x2048 at 10-bit), VP9 1080p (8-bit), or AV1 720p.
3. **CL3**: Mid-range PC level. Supports AVIF 4096x4096, native **SVG** rendering, AV1 1080p 60fps, or VP9 up to 4K.
4. **CL4**: High-performance devices capable of decoding **AV1 in 4K** at 60fps.

_Note: CL0 is reserved for legacy devices (PNG/JPEG up to 1024x1024) and is not currently targeted by this project._

## Building

> [!IMPORTANT]
> **Security Note:** Regardless of the deployment method, never use the default `django-insecure-` keys in production.
> 
> Always generate a fresh, unique key for each environment and keep it out of version control (Git).

### Environment Configuration
Before proceeding, Copy and rename `.env.example` to `.env` (required) and `.env.docker.example` to `.env.docker` (for Docker). 
You can generate a secure, production-ready key using this command:
```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(50))'
```

### With Docker (Recommended)

This is the fastest way to get the production-ready environment up and running with all dependencies (libvips, AVIF/HEIF support, PostgreSQL, Redis) pre-configured.

Step 1. **Prepare environment files**:

Copy and rename `.env.example` to `.env` (required) and `.env.docker.example` to `.env.docker` (for Docker), based on the provided examples. Ensure `USE_X_ACCEL=1` is set in `.env.docker` for optimal performance.

Step 2. **Configure SELinux** (if applicable):

If you are running on a system with SELinux (e.g., Fedora, RHEL), the project is already configured to disable MCS labeling via `security_opt` to allow shared access between Web and Celery containers.


Ensure your storage directory has the correct context:

```
sudo chcon -R -t container_file_t /path/to/your/medialib_storage
```

Also add this option to your `.env` config: `VOLUME_FLAGS=:z`

Step 3. **Launch the stack**:

```
docker compose up -d --build
```

This command builds the Python 3.14 image, sets up the Nginx reverse proxy with `X-Accel-Redirect` support, and starts the Celery worker.

Step 4. **Initialize Database**:

```
docker compose exec web python manage.py migrate
```

### Manual (Local Development)

Use this method if you want to run the server directly on your host machine for debugging purposes.

Step 1. **Install System Dependencies**:

You need libvips with HEIF/AVIF support.

- Debian/Ubuntu:

    ```
    sudo apt install libvips-dev libheif-plugin-aomenc libheif-plugin-dav1d
    ```

- MacOS:
`brew install vips`

And also ffmpeg with libx264, libvpx, libopus.

Step 2. **Setup Python Environment**:

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Step 3. **Configure Environment**:

Set `USE_X_ACCEL=0` in your local `.env` file. In this mode, Django will handle file redirects via standard 302 Found response.

Step 4. **Run Services**:

You will need to run PostgreSQL and Redis separately (or keep them in Docker), then start the dev server in your preferred way:

`python manage.py runserver`

or

`gunicorn medialib_v2.wsgi:application --bind 0.0.0.0:12925 --workers 4 --access-logfile - --error-logfile -`

And the Celery worker:

`celery -A medialib_v2 worker --loglevel=info`

### Configuration (Environment Variables)

#### Base seting (Django)

| Variable            | Default value         | Description                                                      |
| ------------------- | --------------------- | ---------------------------------------------------------------- |
| `DJANGO_SECRET_KEY` | (required)            | Django secret key for cryphographic signs.                       |
| `DEBUG`             | `0`                   | Debug mode in Django (1 — enabled, 0 — disabled).                |
| `ALLOWED_HOSTS`     | `localhost,127.0.0.1` | The list of hosts/domains, which application allowed to work on. |
| `TIME_ZONE`         | `UTC`                 | Application time zone (may affect on date filends of models).    |

#### Date base (PostgreSQL)

| Variable       | Default value      | Description                          |
| -------------- | ------------------ | ------------------------------------ |
| `DB_NAME`      | `medialib_db`      | Main data base name.                 |
| `TEST_DB_NAME` | `test_medialib_db` | Name of data base for tests running. |
| `DB_USER`      | `postgres`         | Data base user name.                 |
| `DB_PASSWORD`  | (required)         | Data base user password.             |
| `DB_HOST`      | `localhost`        | Data base host name.                 |
| `DB_PORT`      | `5432`             | The port of data base.               |

#### Storage and static files

| Variable                | Default value | Description                                                            |
| ----------------------- | ------------- | ---------------------------------------------------------------------- |
| `MEDIALIB_STORAGE_PATH` | `./media`     | The path on the hosh machine, where files should be stored.            |
| `MEDIALIB_ROOT`         | `/app/media`  | Path to media directory inside container (sync with с Docker volumes). |
| `USE_X_ACCEL`           | `0`           | Enable `X-Accel-Redirect` to speed up file sharing with Nginx.         |
| `VOLUME_FLAGS`          | (empty)       | Volume mount flags. Use `:z` on SELinux systems.                       |

#### Infrastructure

| Variable           | Default value | Описание                                                                 |
| ------------------ | ------------- | ------------------------------------------------------------------------ |
| `GUNICORN_WORKERS` | `4`           | Worker count in Gunicorn.                                                |
| `CELERY_WORKERS`   | `2`           | Parralel processes count in Celery worker.                               |
| `HOST_PORT`        | `8829`        | Port numner which Nginx will be accesible outside of Docker environment. |
  

## License  
  
This project is licensed under the [MIT License](LICENSE).