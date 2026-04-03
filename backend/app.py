"""
Mango Market Platform - Entry Point (Production-Ready for Azure)
Imports create_app from consolidated main.py
Handles all three systems: Farmer, Broker, and Host

⚠️ PRODUCTION NOTE:
This module creates the Flask app for GUNICORN. DO NOT use app.run() in production.
<<<<<<< HEAD
Run with: gunicorn app:app
=======
For Azure App Service, deploy with Gunicorn:
  - Use requirements.txt with: gunicorn>=20.1.0
  - Azure startup command: gunicorn --workers 4 --worker-class sync --bind 0.0.0.0:8000 app:app
>>>>>>> 8413c5c (Updated project for Azure deployment (wsgi + config fixes))
"""

import sys
import os
import logging
from dotenv import load_dotenv

# =====================================================
# LOAD ENVIRONMENT VARIABLES EARLY
# =====================================================
load_dotenv()

# =====================================================
# CONFIGURE LOGGING (For Azure monitoring)
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================
# ADD CURRENT DIRECTORY TO PATH
# =====================================================
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# =====================================================
# IMPORT FLASK APP FACTORY
# =====================================================
try:
    from main import create_app
except ImportError as e:
    logger.error(f"Failed to import create_app from main.py: {e}")
    sys.exit(1)

<<<<<<< HEAD
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

=======
# =====================================================
# CREATE FLASK APP INSTANCE
# =====================================================
try:
    app = create_app()
    logger.info("✅ Flask app created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create Flask app: {e}")
    sys.exit(1)

# =====================================================
# HEALTH CHECK / DIAGNOSTIC ROUTES
# =====================================================
@app.route("/", methods=["GET"])
def home():
    """Health check endpoint for Azure App Service"""
    return {
        "status": "success",
        "message": "Mango Market Platform Backend is running 🚀",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }, 200


# =====================================================
# ERROR HANDLERS (For Azure App Service)
# =====================================================
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 - Resource not found: {error}")
    return {"error": "Resource not found"}, 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 - Internal server error: {error}")
    return {"error": "Internal server error"}, 500


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    logger.warning(f"403 - Access forbidden: {error}")
    return {"error": "Access forbidden"}, 403


# =====================================================
# SECURITY HEADERS (For production)
# =====================================================
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


# =====================================================
# WSGI APPLICATION (For Gunicorn/Azure)
# =====================================================
# This is the entry point for Gunicorn:
# gunicorn --workers 4 --bind 0.0.0.0:8000 app:app
if __name__ != "__main__":
    logger.info("Running under WSGI server (Gunicorn)")


# =====================================================
# DEVELOPMENT SERVER (Local testing only)
# =====================================================
if __name__ == "__main__":
    logger.warning("⚠️ Running in development mode (Flask development server)")
    logger.warning("⚠️ DO NOT use this in production. Use Gunicorn instead.")
    logger.info("For Azure deployment, use:")
    logger.info("  gunicorn --workers 4 --bind 0.0.0.0:8000 app:app")

    # Get configuration from environment variables
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1")
    host = os.getenv("FLASK_HOST", "0.0.0.0")  # Listen on all interfaces
    port = int(os.getenv("FLASK_PORT", "5000"))

    # Start development server
>>>>>>> 8413c5c (Updated project for Azure deployment (wsgi + config fixes))
    app.run(
        debug=debug_mode,
        host=host,
        port=port,
        use_reloader=debug_mode,
        threaded=True
    )
