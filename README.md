# FSI Application

## Overview
This repository follows the **Freight Services Inc. (FSI) Application Architecture Standard** using Flask + SQLAlchemy and Cloud Run for runtime hosting.

## Local Development
### Prerequisites
- Python 3.10+
- PostgreSQL (or a compatible reachable database)

### Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a local `.env` file (or export vars in your shell):
```env
APP_ENV=local
FSI_PRODUCTION=false
DEBUG=true
SECRET_KEY=dev-only-change-me
DATABASE_URL=postgresql+psycopg://localhost/fsi_app
PORT=8080
```

Run locally with Flask's dev server:
```bash
python wsgi.py
```

## Production Runtime (Cloud Run)
Production serving uses Gunicorn, not Flask's development server.

### Container
Build and run using the included `Dockerfile`:
- WSGI server: `gunicorn`
- App module: `wsgi:app`
- Bind: `0.0.0.0:$PORT`

### Cloud Build + Cloud Run Deploy
Use the included `cloudbuild.yaml`:
```bash
gcloud builds submit --config cloudbuild.yaml .
```

The pipeline:
1. Builds the container image.
2. Pushes image to Artifact Registry.
3. Deploys to Cloud Run with required env + secrets wiring.

## Required Runtime Environment Variables
These values are read by `app/config.py`.

| Variable | Required in Production | Description | Source |
|---|---:|---|---|
| `APP_ENV` | Yes | Set to `production` in Cloud Run deploy. | Cloud Run env var |
| `FSI_PRODUCTION` | Yes | Safety switch enabling strict env validation. | Cloud Run env var |
| `SECRET_KEY` | Yes | Flask secret key for signing sessions/CSRF. | Secret Manager (`fsi-secret-key`) |
| `DATABASE_URL` | Yes | SQLAlchemy DB URL (`postgresql+psycopg://...`). | Secret Manager (`fsi-database-url`) |
| `PORT` | Auto | HTTP listen port injected by Cloud Run. | Cloud Run runtime |
| `DEBUG` | No | Keep `false` in production. | Cloud Run env var |
| `SESSION_COOKIE_SECURE` | No | Defaults to `true` when production mode is enabled. | Optional env var |
| `REMEMBER_COOKIE_SECURE` | No | Defaults to `true` when production mode is enabled. | Optional env var |

## Secret Manager Names
`cloudbuild.yaml` expects these secret names by default:
- `fsi-secret-key` → mounted as `SECRET_KEY`
- `fsi-database-url` → mounted as `DATABASE_URL`

Adjust via Cloud Build substitutions if your organization uses different naming.

## Entrypoint Guidance
- **Local development:** `python wsgi.py`
- **Production/container:** `gunicorn --bind 0.0.0.0:${PORT} wsgi:app`

The `wsgi.py` file keeps local bootstrap behavior while production execution is handled by the Docker `CMD`.
