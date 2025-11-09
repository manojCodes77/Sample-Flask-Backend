#!/bin/bash
# Production startup script using Gunicorn (for Linux/Unix/Mac)

echo "Starting Flask application with Gunicorn..."
exec gunicorn --config gunicorn_config.py app:app
