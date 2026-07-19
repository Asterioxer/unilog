import json
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app, raise_server_exceptions=False)

def test_websocket_live_stream():
    """Verify that the live streaming WebSocket endpoint accepts connections, sends records, and responds to controls."""
    with client.websocket_connect("/api/v1/ws/live") as websocket:
        # 1. Receive initial stream data
        data = websocket.receive_json()
        assert "timestamp" in data
        assert "level" in data
        assert "source_ip" in data
        assert "raw" in data
        assert "status_code" in data
        
        # 2. Update rate delay control
        websocket.send_text(json.dumps({"action": "rate", "value": 0.1}))
        
        # 3. Receive another record
        data2 = websocket.receive_json()
        assert "raw" in data2
