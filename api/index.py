"""
Vercel Serverless Entrypoint for Flight Disruption Platform.
Exposes the ASGI FastAPI application 'app' to the @vercel/python runtime.
"""
import sys
import os

# Ensure the root project directory is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.api.main import app

# Vercel serverless ASGI handler
