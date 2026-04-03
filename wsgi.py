"""
WSGI Entry Point for Gunicorn / Azure Web App
Used by: gunicorn wsgi:app
"""

import os
import sys
from dotenv import load_dotenv

# =====================================================
# LOAD ENV VARIABLES (optional - works without .env)
# =====================================================
load_dotenv()

# =====================================================
# ADD ROOT PATH (so 'backend' module is found)
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# =====================================================
# IMPORT FLASK APP
# =====================================================
from backend.app import app

# =====================================================
# OPTIONAL: LOCAL TESTING ONLY (NOT USED IN AZURE)
# =====================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Azure uses PORT
    app.run(host="0.0.0.0", port=port)