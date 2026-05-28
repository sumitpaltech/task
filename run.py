#!/usr/bin/env python
"""
Application Entry Point.

Local dev:   python run.py
Production:  gunicorn --bind 0.0.0.0:5000 run:app
"""
from app import create_app

# Module-level `app` is required for gunicorn (run:app)
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
