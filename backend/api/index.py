"""Vercel serverless entry point for QueryNova backend.

Normalizes request paths from Vercel's Python runtime and rewrite proxy headers
(e.g., HTTP_X_MATCHED_PATH, HTTP_X_FORWARDED_PATH) so that Flask routes matching /api/*
function reliably across all serverless invocations.
"""
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import app as _flask_app


class VercelPathResolver:
    """WSGI middleware to extract original request path from Vercel proxy headers."""

    __slots__ = ("_app",)

    def __init__(self, wsgi_app):
        self._app = wsgi_app

    def __call__(self, environ, start_response):
        # Vercel rewrites store the original request path in these headers
        headers_to_check = [
            "HTTP_X_MATCHED_PATH",
            "HTTP_X_FORWARDED_PATH",
            "HTTP_X_INITIAL_PATH",
            "HTTP_X_INVOKE_PATH",
            "HTTP_X_ORIGINAL_URI",
            "HTTP_X_REWRITE_URL",
        ]

        path = None
        for header_name in headers_to_check:
            val = environ.get(header_name, "").strip()
            if val and not val.endswith("index.py"):
                path = val
                break

        if not path:
            script = environ.get("SCRIPT_NAME", "")
            path_info = environ.get("PATH_INFO", "")
            path = f"{script}{path_info}"

        # Clean Vercel artifacts
        path = re.sub(r"^/api/index(\.py)?", "", path)
        path = re.sub(r"^(?:/api)+", "/api", path)

        if not path.startswith("/api"):
            path = "/api" + (path if path.startswith("/") else "/" + path)

        environ["PATH_INFO"] = path
        environ["SCRIPT_NAME"] = ""
        return self._app(environ, start_response)


# Vercel detects and executes this module-level `app` object.
app = VercelPathResolver(_flask_app)
