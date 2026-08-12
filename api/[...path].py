"""Catch-all Vercel function for /api/* routes.

Using Vercel's filesystem router avoids a rewrite that changes the path Flask
receives (for example, from /api/health to /api/index.py).
"""
from backend.app import app
