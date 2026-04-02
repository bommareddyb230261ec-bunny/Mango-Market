"""
Mango Market Platform - Entry Point
Imports create_app from consolidated main.py
Handles all three systems: Farmer, Broker, and Host

⚠️ PRODUCTION NOTE:
This module creates the Flask app for GUNICORN. DO NOT use app.run() in production.
Run with: gunicorn app:app
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env before any imports
load_dotenv()

# Add current directory to sys.path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import create_app

# Create the Flask app instance
app = create_app()

# ✅ ADD THIS ROUTE (IMPORTANT FIX)
@app.route("/")
def home():
    return "Backend is running 🚀"

# ---------------------------------------------------
# Development server (DO NOT use in production)
# ---------------------------------------------------
if __name__ == '__main__':
    import logging

    logging.info("Starting Mango Market Platform (Development Mode)...")
    logging.info("For production, use: gunicorn app:app")

    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1')
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))

    app.run(
        debug=debug_mode,
        host=host,
        port=port,
        use_reloader=debug_mode,
        threaded=True
    )
