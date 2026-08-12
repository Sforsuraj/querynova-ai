"""Vercel serverless entry point.

Vercel's Python runtime may set SCRIPT_NAME based on the function's
directory (e.g. SCRIPT_NAME="/api" for files under api/).  Flask
matches routes against PATH_INFO only, so /api/* routes will 404 if
the /api prefix is absorbed by SCRIPT_NAME.

The _VercelPathFix middleware merges SCRIPT_NAME back into PATH_INFO
so that Flask's url_map sees the full original request path.
"""
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import app as _flask_app


class _VercelPathFix:
    """WSGI middleware: merge SCRIPT_NAME into PATH_INFO for Flask."""

    __slots__ = ("_app",)

    def __init__(self, wsgi_app):
        self._app = wsgi_app

    def __call__(self, environ, start_response):
        script = environ.get("SCRIPT_NAME", "")
        if script:
            environ["PATH_INFO"] = script + environ.get("PATH_INFO", "")
            environ["SCRIPT_NAME"] = ""
        return self._app(environ, start_response)


# Vercel discovers this module-level `app` variable.
app = _VercelPathFix(_flask_app)
