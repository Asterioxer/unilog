# Deployment & Operations Guide

This guide covers deploying `unilog` into production environments using Docker, Docker Compose, Nginx Reverse Proxy, and HTTPS/WebSocket configurations.

---

## 🐳 Option 1: Quickstart with Docker Compose

`unilog` includes a production multi-stage `Dockerfile` and `docker-compose.yml` for unified stack deployment.

### 1. Launch Stack

```bash
docker-compose up -d --build
```

### 2. Verify Services

- **Frontend Dashboard**: `http://localhost:5173` (or `http://localhost`)
- **Backend REST API**: `http://localhost:8002`
- **FastAPI OpenAPI Swagger**: `http://localhost:8002/docs`
- **WebSocket Streaming**: `ws://localhost:8002/api/v1/ws/live`

---

## 📦 Option 2: Docker Single-Container Deployment

### 1. Build Docker Image

```bash
docker build -t unilog:latest .
```

### 2. Run Container

```bash
docker run -d \
  --name unilog \
  -p 8002:8002 \
  -e GEMINI_API_KEY="your_api_key_here" \
  unilog:latest
```

---

## 🌐 Option 3: Production Nginx Reverse Proxy & SSL Setup

Below is a production-tested Nginx virtual host configuration supporting static frontend asset serving, REST API proxying, and WebSocket upgrading.

```nginx
server {
    listen 80;
    server_name unilog.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name unilog.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/unilog.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/unilog.yourdomain.com/privkey.pem;

    # Frontend Static SPA Assets
    location / {
        root /var/www/unilog/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend REST API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Real-Time WebSocket Streaming Proxy
    location /api/v1/ws/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

---

## 🔑 Environment Variables Reference

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | `""` | Google Gemini API key for AI SRE Assistant features. |
| `PORT` | `8002` | API HTTP bind port. |
| `HOST` | `0.0.0.0` | API bind address. |
| `LOG_LEVEL` | `INFO` | Backend logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `CORS_ORIGINS` | `"*"` | Allowed CORS origins for API requests. |
