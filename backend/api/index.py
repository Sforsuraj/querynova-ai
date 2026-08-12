"""Vercel serverless entry point for QueryNova backend.

Normalizes SCRIPT_NAME and PATH_INFO variations from Vercel's Python runtime
so that Flask routes matching /api/* function reliably across all serverless invokers.
"""
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import app as _flask_app


class PathNormalizer:
    """WSGI middleware to normalize request paths for Flask routing."""

    __slots__ = ("_app",)

    def __init__(self, wsgi_app):
        self._app = wsgi_app

    def __call__(self, environ, start_response):
        script = environ.get("SCRIPT_NAME", "")
        path = environ.get("PATH_INFO", "")

        # Combine script name and path info
        combined = f"{script}{path}"

        # Strip any leading Vercel entrypoint artifacts like /api/index.py or /api/index
        combined = re.sub(r"^/api/index(\.py)?", "", combined)

        # Collapse duplicate /api prefixes (e.g., /api/api/health -> /api/health)
        combined = re.sub(r"^(?:/api)+", "/api", combined)

        # Ensure path starts with /api
        if not combined.startswith("/api"):
            combined = "/api" + (combined if combined.startswith("/") else "/" + combined)

        environ["PATH_INFO"] = combined
        environ["SCRIPT_NAME"] = ""
        return self._app(environ, start_response)


# Vercel detects and executes this module-level `app` object.
app = PathNormalizer(_flask_app)
