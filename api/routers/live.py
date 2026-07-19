import asyncio
import json
import random
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("unilog-api")
router = APIRouter(tags=["Live"])

# Malicious scanner targets, bot user agents, and typical login endpoints to trigger security rules in real-time
IP_POOL = ["192.168.1.10", "10.0.0.15", "185.220.101.47", "127.0.0.1", "192.168.0.85", "8.8.8.8"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Playwright/1.39.0 (headless)",
    "Nikto/2.1.6",
    "Go-http-client/2.0"
]
PATHS = ["/index.html", "/products", "/cart", "/checkout", "/wp-admin", "/.env", "/api/v1/auth/login"]
METHODS = ["GET", "POST", "PUT", "DELETE"]
STATUS_CODES = [200, 200, 200, 302, 404, 401, 500]

def generate_live_nginx_record() -> dict:
    ip = random.choice(IP_POOL)
    path = random.choice(PATHS)
    method = random.choice(METHODS)
    status_code = random.choice(STATUS_CODES)
    ua = random.choice(USER_AGENTS)
    
    # Custom rule modifiers
    if path == "/api/v1/auth/login":
        method = "POST"
        if random.random() > 0.3:
            status_code = 401 # Simulate login failures for brute force rules
    elif path in ["/wp-admin", "/.env"]:
        method = "GET"
        status_code = 404 # Scanner probe simulation
        
    size = random.randint(100, 1500) if status_code == 200 else random.randint(20, 300)
    ts = datetime.now(timezone.utc).strftime("%d/%b/%Y:%H:%M:%S +0000")
    
    # Reconstruct raw line as it would appear in web logs
    raw = f'{ip} - - [{ts}] "{method} {path} HTTP/1.1" {status_code} {size} "-" "{ua}"'
    
    # Map to standard parsed schema
    level = "INFO"
    if status_code >= 500:
        level = "ERROR"
    elif status_code >= 400:
        level = "WARN"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "level": level,
        "source_ip": ip,
        "method": method,
        "path": path,
        "status_code": status_code,
        "size": size,
        "user_agent": ua,
        "raw": raw
    }

@router.websocket("/ws/live")
async def live_stream_websocket(websocket: WebSocket):
    await websocket.accept()
    logger.info("Live stream WebSocket connection established")
    
    streaming = True
    delay = 0.5 # send logs every 500ms by default
    
    # Task to read incoming client control messages
    async def receive_messages():
        nonlocal streaming, delay
        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                action = msg.get("action")
                if action == "pause":
                    streaming = False
                    logger.info("Live stream paused by client")
                elif action == "resume":
                    streaming = True
                    logger.info("Live stream resumed by client")
                elif action == "rate":
                    delay = max(0.1, min(5.0, float(msg.get("value", 0.5))))
                    logger.info(f"Live stream delay updated to {delay}s")
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"Error in websocket receive: {e}")

    # Start the receiver task
    receive_task = asyncio.create_task(receive_messages())

    try:
        while True:
            if streaming:
                record = generate_live_nginx_record()
                await websocket.send_json(record)
            await asyncio.sleep(delay)
    except WebSocketDisconnect:
        logger.info("Live stream WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Error in websocket send stream: {e}")
    finally:
        receive_task.cancel()
        try:
            await websocket.close()
        except Exception:
            pass
