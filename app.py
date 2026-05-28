#!/usr/bin/env python
"""
TaskApp - Main Entry Point
Deprecated: Use run.py instead

This file now uses the proper factory pattern.
All routes, models, and views are in the app/ folder.

To run:
    python run.py    (RECOMMENDED)
    python app.py    (Also works)
"""
from app import create_app

if __name__ == '__main__':
    app = create_app()
    #
    app.run(host='0.0.0.0', port=7001, debug=True)