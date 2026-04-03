# =====================================================
# AZURE APP SERVICE STARTUP CONFIGURATION
# =====================================================
# This script starts the application for Azure App Service
# Azure will execute: python startup_azure.py

import os
import subprocess
import sys

# Ensure .env is loaded
from dotenv import load_dotenv
load_dotenv()

# Get configuration
workers = os.getenv("GUNICORN_WORKERS", "4")
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "sync")
timeout = os.getenv("GUNICORN_TIMEOUT", "120")
bind_address = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# Log startup information
print("🚀 Starting Mango Market Platform on Azure App Service...")
print(f"   Workers: {workers}")
print(f"   Worker Class: {worker_class}")
print(f"   Bind Address: {bind_address}")
print(f"   Timeout: {timeout}s")
print()

# Command to start Gunicorn
cmd = [
    sys.executable,
    "-m",
    "gunicorn",
    f"--workers={workers}",
    f"--worker-class={worker_class}",
    f"--bind={bind_address}",
    f"--timeout={timeout}",
    "--access-logfile=-",  # Log to stdout
    "--error-logfile=-",   # Log to stderr
    "app:app"
]

# Execute Gunicorn
try:
    subprocess.run(cmd, check=True)
except KeyboardInterrupt:
    print("\n✋ Shutdown requested")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
