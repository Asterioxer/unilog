import os
import json
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture
def mock_metrics():
    return {
        "error_metrics": {"error_rate": 0.08},
        "performance": {"top_slow_endpoints": [["/checkout", 1500]]},
        "security": {
            "injection_metrics": {"sql_injection_count": 2, "xss_injection_count": 0},
            "scanner_metrics": {"scanner_hits_count": 5},
            "brute_force": {"lockout_candidates_count": 1},
            "bot_metrics": {"headless_fingerprints_count": 0}
        }
    }

@pytest.fixture
def mock_insights():
    return [
        {
            "id": "sec-inj-04",
            "category": "security",
            "severity": "critical",
            "confidence": 0.95,
            "description": "SQL Injection attempted on /api/v1/users",
            "recommendation": "Use parameterized queries",
            "evidence": {}
        }
    ]

def test_ai_explain_fallback_mock(mock_metrics, mock_insights):
    """Test that the AI endpoint falls back to a high-quality local mock when no key is set."""
    # Ensure GEMINI_API_KEY is unset
    with patch.dict(os.environ, {}, clear=True):
        resp = client.post(
            "/api/v1/ai/explain",
            json={"metrics": mock_metrics, "insights": mock_insights}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "explanation" in data
        assert len(data["remediations"]) > 0
        assert data["remediations"][0]["title"] == "Enforce Input Sanitization / WAF Rules"
        assert data["remediations"][0]["language"] == "nginx"

@patch("httpx.AsyncClient.post")
def test_ai_explain_gemini_api(mock_post, mock_metrics, mock_insights):
    """Test that the AI endpoint successfully makes HTTP requests to Gemini when key is present."""
    gemini_resp = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "summary": "Gemini Summary Analysis",
                                "explanation": "Gemini Detailed Explanation",
                                "remediations": [
                                    {
                                        "title": "Gemini Mitigation Rule",
                                        "description": "How to fix using Gemini recommendations",
                                        "code": "deny 1.2.3.4;",
                                        "language": "nginx"
                                    }
                                ]
                            })
                        }
                    ]
                }
            }
        ]
    }
    
    mock_post.return_value = AsyncMock(status_code=200, json=lambda: gemini_resp)

    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-gemini-key"}):
        resp = client.post(
            "/api/v1/ai/explain",
            json={"metrics": mock_metrics, "insights": mock_insights}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"] == "Gemini Summary Analysis"
        assert data["explanation"] == "Gemini Detailed Explanation"
        assert data["remediations"][0]["title"] == "Gemini Mitigation Rule"
