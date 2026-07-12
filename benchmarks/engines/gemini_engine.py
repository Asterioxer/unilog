import json
import os
import re
import sys

# Ensure parent and scripts paths are loaded
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.github/scripts")))
from llm.gemini import GeminiClient  # type: ignore
from .base_engine import ReviewEngine  # type: ignore

class GeminiEngine(ReviewEngine):
    """Real Gemini review engine communicating with the live Gemini API."""
    
    def __init__(self, api_key: str = "", timeout: float = 60.0, retries: int = 1):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.timeout = timeout
        self.retries = retries
        
    def review(self, diff_content: str, metadata: dict) -> dict:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing.")
            
        # Read system prompt
        prompts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.github/prompts"))
        with open(os.path.join(prompts_dir, "review.md"), "r", encoding="utf-8") as f:
            system_prompt = f.read()
            
        # Load Context Files
        context_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.github/context"))
        context_text = ""
        if os.path.exists(context_dir):
            for filename in sorted(os.listdir(context_dir)):
                if filename.endswith(".md"):
                    with open(os.path.join(context_dir, filename), "r", encoding="utf-8") as cf:
                        context_text += f"\n\n--- Context: {filename} ---\n{cf.read()}"

        user_prompt = f"""
PR Title: {metadata.get("title", "")}
PR Description: {metadata.get("body", "")}

Commit Messages:
{chr(10).join(metadata.get("commits", []))}

Changed Files List:
{chr(10).join(metadata.get("changed_files", []))}

Changed Test Files:
{chr(10).join(metadata.get("changed_tests", []))}

Repository Context Reference Guidelines:
{context_text}

Pull Request Code Diff:
```diff
{diff_content}
```
"""
        client = GeminiClient(api_key=self.api_key, timeout=self.timeout, retries=self.retries)
        raw_json_response = client.generate_text(prompt=user_prompt, system_prompt=system_prompt)
        
        # Clean up potential markdown code wraps
        cleaned_json = raw_json_response.strip()
        if cleaned_json.startswith("```"):
            cleaned_json = re.sub(r"^```(?:json)?\s*", "", cleaned_json)
            cleaned_json = re.sub(r"\s*```$", "", cleaned_json)
            
        return json.loads(cleaned_json)
