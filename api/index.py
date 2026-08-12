"""Vercel Python serverless entry point for the QueryNova Flask API."""
from backend.app import app

# Vercel imports this WSGI application directly. Do not call app.run() here.
