import json
import os
import time
import urllib.request
import urllib.error
from typing import Any
from .base import BaseLLMClient  # type: ignore

class GeminiClient(BaseLLMClient):
    """Gemini API Client implementation with timeout protection and retries."""
    
    def __init__(self, api_key: str = "", timeout: float = 60.0, retries: int = 1):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.timeout = timeout
        self.retries = retries
        
    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing.")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        
        # Build payload
        payload: dict[str, Any] = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }
            
        # Standard configuration forcing JSON structure
        payload["generationConfig"] = {
            "responseMimeType": "application/json"
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        attempt = 0
        backoff = 2.0
        
        while True:
            try:
                # Execute HTTP POST request with configured timeout
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    res_body = response.read().decode("utf-8")
                    res_json = json.loads(res_body)
                    
                    candidates = res_json.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                    raise ValueError(f"Invalid Gemini response schema: {res_body}")
            except (urllib.error.URLError, urllib.error.HTTPError) as e:
                attempt += 1
                if attempt > self.retries:
                    raise RuntimeError(f"Gemini API request failed after {self.retries} retries: {e}")
                time.sleep(backoff)
                backoff *= 2
