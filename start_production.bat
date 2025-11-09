@echo off
REM Production startup script using Waitress (for Windows)

echo Starting Flask application with Waitress...
waitress-serve --host=0.0.0.0 --port=8080 --threads=4 app:app
