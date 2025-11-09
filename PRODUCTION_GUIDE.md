# Production Deployment Guide

## What is a WSGI Server?

**WSGI (Web Server Gateway Interface)** is a standard interface between web servers and Python web applications. Flask's built-in development server is **not suitable for production** because it:
- Can only handle one request at a time
- Lacks security features
- Has poor performance under load
- Is not designed for stability

**Production WSGI servers** like Gunicorn or Waitress are designed to:
- Handle multiple concurrent requests
- Provide better security
- Offer superior performance
- Include process management and recovery

## Available Production Servers

### 1. **Gunicorn** (Recommended for Linux/Unix/Mac)
- Most popular WSGI server
- Easy to configure
- Great performance
- Multi-worker support

### 2. **Waitress** (Recommended for Windows)
- Pure Python (no C dependencies)
- Cross-platform
- Good for Windows production

### 3. **uWSGI** (Advanced)
- Very configurable
- Excellent performance
- Steeper learning curve

---

## Quick Start

### Install Production Dependencies

```bash
pip install -r requirements.txt
```

### Running on Windows (with Waitress)

```bash
# Simple command
waitress-serve --host=0.0.0.0 --port=8080 --threads=4 app:app

# Or use the provided script
start_production.bat
```

### Running on Linux/Unix/Mac (with Gunicorn)

```bash
# Simple command
gunicorn --bind 0.0.0.0:8080 --workers 4 app:app

# With custom config
gunicorn --config gunicorn_config.py app:app

# Or use the provided script
chmod +x start_production.sh
./start_production.sh
```

---

## Configuration Options

### Gunicorn Configuration (`gunicorn_config.py`)

Key settings you can adjust:

```python
# Number of worker processes (CPU cores * 2 + 1 is recommended)
workers = 4

# Port to bind to
bind = "0.0.0.0:8080"

# Request timeout in seconds
timeout = 30

# Log level (debug, info, warning, error, critical)
loglevel = "info"
```

### Environment Variables

Create a `.env` file in the server directory:

```env
# Database
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/notes_db

# Server
PORT=8080
DEBUG=false

# CORS (comma-separated origins or "*")
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Gunicorn
GUNICORN_WORKERS=4
LOG_LEVEL=info
```

---

## Production Deployment Options

### 1. **Traditional VPS/Server (DigitalOcean, Linode, AWS EC2)**

#### Setup with Nginx + Gunicorn

1. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx postgresql
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Nginx** (`/etc/nginx/sites-available/todoapp`):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **Create systemd service** (`/etc/systemd/system/todoapp.service`):
   ```ini
   [Unit]
   Description=Todo App Gunicorn Service
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/todolist/server
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/gunicorn --config gunicorn_config.py app:app

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start services:**
   ```bash
   sudo systemctl enable todoapp
   sudo systemctl start todoapp
   sudo systemctl enable nginx
   sudo systemctl start nginx
   ```

---

### 2. **Render.com (Easy Cloud Deployment)**

1. Create a `render.yaml` file:
   ```yaml
   services:
     - type: web
       name: todo-app
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: gunicorn --config gunicorn_config.py app:app
       envVars:
         - key: DATABASE_URL
           fromDatabase:
             name: todo-db
             property: connectionString
         - key: PYTHON_VERSION
           value: 3.11
   
   databases:
     - name: todo-db
       databaseName: notes_db
       user: notes_user
   ```

2. Push to GitHub and connect to Render

---

### 3. **Heroku**

1. Create `Procfile`:
   ```
   web: gunicorn --config gunicorn_config.py app:app
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   heroku addons:create heroku-postgresql:mini
   git push heroku main
   ```

---

### 4. **Docker Deployment**

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run with Gunicorn
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/notes_db
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=notes_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run:
```bash
docker-compose up -d
```

---

### 5. **Railway.app (Easiest)**

1. Push your code to GitHub
2. Connect Railway to your repo
3. Add PostgreSQL database
4. Railway auto-detects Flask and uses Gunicorn

---

## Performance Tuning

### Worker Calculation
```
workers = (2 × CPU cores) + 1
```

For a 2-core server: `workers = 5`

### For High Traffic
```python
# In gunicorn_config.py
workers = 8
worker_class = "gevent"  # Async workers
worker_connections = 1000
```

Install gevent:
```bash
pip install gevent
```

---

## Monitoring & Logging

### View Logs (systemd)
```bash
sudo journalctl -u todoapp -f
```

### Application Monitoring
Consider using:
- **Sentry** - Error tracking
- **New Relic** - APM
- **Datadog** - Infrastructure monitoring

---

## Security Checklist

- [ ] Set `DEBUG=false` in production
- [ ] Use strong database passwords
- [ ] Configure proper CORS origins (not "*")
- [ ] Use HTTPS (SSL/TLS certificates)
- [ ] Set up firewall rules
- [ ] Keep dependencies updated
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting (use Flask-Limiter)
- [ ] Set up backup strategy for database

---

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Find process
   sudo lsof -i :8080
   # Kill process
   sudo kill -9 <PID>
   ```

2. **Database connection errors:**
   - Check DATABASE_URL is correct
   - Ensure PostgreSQL is running
   - Verify network access to database

3. **Workers dying:**
   - Increase timeout value
   - Check memory usage
   - Review error logs

---

## Next Steps

1. ✅ Install production dependencies
2. ✅ Test with Waitress/Gunicorn locally
3. Choose deployment platform
4. Set up database in production
5. Configure environment variables
6. Deploy application
7. Set up domain and SSL
8. Configure monitoring
9. Set up automated backups

---

## Support Resources

- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Waitress Documentation](https://docs.pylonsproject.org/projects/waitress/)
- [Flask Deployment Options](https://flask.palletsprojects.com/en/latest/deploying/)
- [Nginx Configuration](https://nginx.org/en/docs/)
