"""WSGI entrypoint.

Local development:
    python wsgi.py

Production (Cloud Run / container):
    gunicorn --bind 0.0.0.0:${PORT} wsgi:app
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Local-only runner. Production should use Gunicorn via Dockerfile.
    app.run(host="0.0.0.0", port=app.config.get("PORT", 8080))
