import json
import os

from typing import Any

class BenchmarkEvaluator:
    """Evaluates actual JSON reviews against expected ground truth schemas using weighted scoring and precision/recall calculations."""
    
    def __init__(self, expected_schema_path: str):
        self.expected_path = expected_schema_path
        self.expected: dict[str, Any] = {}
        self.schema_version = 1
        self.load_expected()
        
    def load_expected(self):
        if os.path.exists(self.expected_path):
            with open(self.expected_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.schema_version = data.get("schema_version", 1)
                self.expected = data.get("expected", {})
                
    def evaluate(self, actual_review: dict) -> dict:
        """Compares actual review to expected results and returns a weighted score, precision/recall, and detailed logs."""
        if not self.expected:
            return {
                "score": 0.0,
                "passed": False,
                "details": {"error": "Missing expected.json ground truth file"},
                "precision": 0.0,
                "recall": 0.0
            }
            
        score = 0.0
        details = {}
        
        # 1. Evaluate Risk (Weight: 25)
        exp_risk = self.expected.get("risk", "low").lower()
        act_risk = actual_review.get("risk", "low").lower()
        if exp_risk == act_risk:
            score += 25.0
            details["risk"] = {"passed": True, "score": 25.0, "expected": exp_risk, "actual": act_risk}
        else:
            details["risk"] = {"passed": False, "score": 0.0, "expected": exp_risk, "actual": act_risk}
            
        # 2. Evaluate Tests Missing (Weight: 20)
        exp_tests_missing = bool(self.expected.get("tests_missing", False))
        act_tests_missing = bool(actual_review.get("tests_missing", False))
        if exp_tests_missing == act_tests_missing:
            score += 20.0
            details["tests_missing"] = {"passed": True, "score": 20.0, "expected": exp_tests_missing, "actual": act_tests_missing}
        else:
            details["tests_missing"] = {"passed": False, "score": 0.0, "expected": exp_tests_missing, "actual": act_tests_missing}

        # 3. Evaluate Docs Missing (Weight: 15)
        exp_docs_missing = bool(self.expected.get("documentation_missing", False))
        act_docs_missing = bool(actual_review.get("documentation_missing", False))
        if exp_docs_missing == act_docs_missing:
            score += 15.0
            details["documentation_missing"] = {"passed": True, "score": 15.0, "expected": exp_docs_missing, "actual": act_docs_missing}
        else:
            details["documentation_missing"] = {"passed": False, "score": 0.0, "expected": exp_docs_missing, "actual": act_docs_missing}

        # 4. Evaluate Recommendation (Weight: 15)
        exp_rec = self.expected.get("recommendation", "ready").lower()
        act_rec = actual_review.get("recommendation", "ready").lower()
        if exp_rec == act_rec:
            score += 15.0
            details["recommendation"] = {"passed": True, "score": 15.0, "expected": exp_rec, "actual": act_rec}
        else:
            details["recommendation"] = {"passed": False, "score": 0.0, "expected": exp_rec, "actual": act_rec}

        # 5. Evaluate Security (Weight: 25)
        exp_keywords = self.expected.get("security_keywords", [])
        
        # Flatten actual security issues list and summary for keyword checks
        act_sec_list = actual_review.get("security", [])
        if isinstance(act_sec_list, list):
            act_sec_text = " ".join(act_sec_list).lower()
        else:
            act_sec_text = str(act_sec_list).lower()
            
        act_sec_text += " " + str(actual_review.get("summary", "")).lower()

        # True Positives: Keywords expected that are found
        tp = 0
        fn = 0  # False Negatives: Keywords expected but missing
        
        for kw in exp_keywords:
            if kw.lower() in act_sec_text:
                tp += 1
            else:
                fn += 1
                
        # Calculate recall
        recall = 1.0
        if exp_keywords:
            recall = float(tp) / len(exp_keywords)
            sec_score = 25.0 * recall
        else:
            sec_score = 25.0 # If no security warnings are expected, getting none is a perfect score
            
        score += sec_score
        
        details["security"] = {
            "score": sec_score,
            "expected_keywords": exp_keywords,
            "matched_count": tp,
            "missing_count": fn,
            "recall": recall
        }
        
        passed = (score >= 80.0) # passes if weighted score is at least 80%
        
        return {
            "score": score,
            "passed": passed,
            "details": details,
            "precision": 1.0 if tp > 0 or not exp_keywords else 0.0, # Simple classification
            "recall": recall
        }
