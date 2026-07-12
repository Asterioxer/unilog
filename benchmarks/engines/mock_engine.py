import json
import os
from .base_engine import ReviewEngine  # type: ignore

class MockEngine(ReviewEngine):
    """Mock review engine returning expected structured review shapes for local runs."""
    
    def __init__(self, expected_file_path: str = ""):
        self.expected_file_path = expected_file_path

    def review(self, diff_content: str, metadata: dict) -> dict:
        if self.expected_file_path and os.path.exists(self.expected_file_path):
            try:
                with open(self.expected_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    expected = data.get("expected", {})
                    
                    # Synthesize mock response properties based on expected ground truth
                    return {
                        "summary": f"Mock review generated for simulated scenario: {metadata.get('title', 'PR')}.",
                        "risk": expected.get("risk", "low"),
                        "breaking_changes": expected.get("breaking_changes", []),
                        "testing": "Mock tests evaluation output.",
                        "tests_missing": expected.get("tests_missing", False),
                        "documentation_missing": expected.get("documentation_missing", False),
                        "security": [f"Unsafe pattern check: {kw}" for kw in expected.get("security_keywords", [])],
                        "performance": [],
                        "maintainability": [],
                        "recommendation": expected.get("recommendation", "ready")
                    }
            except Exception as e:
                print(f"Warning: MockEngine failed to load expected file {self.expected_file_path}: {e}")
                
        return {
            "summary": "Fallback mock review.",
            "risk": "low",
            "breaking_changes": [],
            "testing": "Verified.",
            "tests_missing": False,
            "documentation_missing": False,
            "security": [],
            "performance": [],
            "maintainability": [],
            "recommendation": "ready"
        }
