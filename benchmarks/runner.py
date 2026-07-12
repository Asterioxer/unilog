import argparse
import datetime
import json
import os
import sys
import time

from engines.mock_engine import MockEngine  # type: ignore
from engines.gemini_engine import GeminiEngine  # type: ignore
from evaluator import BenchmarkEvaluator  # type: ignore

def load_yaml_config(file_path):
    """Simple parser to load configurations without external yaml dependency."""
    config = {}
    if not os.path.exists(file_path):
        return config
    with open(file_path, "r", encoding="utf-8") as f:
        current_section = None
        for line in f:
            line = line.split("#")[0].strip()
            if not line:
                continue
            if line.endswith(":"):
                current_section = line[:-1].strip()
                config[current_section] = {}
            elif ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val.isdigit():
                    val = int(val)
                elif val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                
                if current_section:
                    config[current_section][key] = val
                else:
                    config[key] = val
            elif line.startswith("-") and current_section:
                val = line[1:].strip().strip('"').strip("'")
                if not isinstance(config[current_section], list):
                    if not config[current_section]:
                        config[current_section] = []
                    else:
                        config[current_section] = list(config[current_section].keys())
                config[current_section].append(val)
    return config

def main():
    parser = argparse.ArgumentParser(description="Maintainer Intelligence Benchmark Runner")
    parser.add_argument("--engine", required=True, choices=["mock", "gemini"], help="Review engine to test")
    parser.add_argument("--fixtures", default="v1", help="Versioned fixtures suite directory")
    parser.add_argument("--report", action="store_true", help="Save historical report to benchmarks/reports/")
    parser.add_argument("--tag", help="Filter scenarios by tag (comma-separated)")
    args = parser.parse_args()

    # Load local maintainer configuration
    config_path = os.path.join(os.path.dirname(__file__), "maintainer-config.yml")
    config = load_yaml_config(config_path) if os.path.exists(config_path) else {}

    base_dir = os.path.dirname(__file__)
    fixtures_dir = os.path.join(base_dir, "fixtures", args.fixtures)
    manifest_path = os.path.join(fixtures_dir, "manifest.json")

    if not os.path.exists(manifest_path):
        print(f"Error: Manifest not found at {manifest_path}")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    scenarios = manifest.get("scenarios", [])
    
    # Filter by tag if requested
    if args.tag:
        filter_tags = [t.strip().lower() for t in args.tag.split(",")]
        scenarios = [
            s for s in scenarios 
            if any(t in [st.lower() for st in s.get("tags", [])] for t in filter_tags)
        ]

    if not scenarios:
        print("No matching scenarios found to execute.")
        sys.exit(0)

    print("=" * 70)
    print("      MAINTAINER INTELLIGENCE BENCHMARK SUITE")
    print(f"      Engine:   {args.engine.upper()}")
    print(f"      Fixtures: {args.fixtures} (Version {manifest.get('fixture_version', 1)})")
    print("=" * 70)

    results = []
    total_latency = 0.0
    total_score = 0.0
    passed_count = 0
    failures = []
    
    # Setup reports folder
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    for scenario in scenarios:
        scenario_path = scenario["path"]
        diff_file = os.path.join(fixtures_dir, scenario_path, "pr.diff")
        metadata_file = os.path.join(fixtures_dir, scenario_path, "metadata.json")
        expected_file = os.path.join(fixtures_dir, scenario_path, "expected.json")

        if not (os.path.exists(diff_file) and os.path.exists(metadata_file) and os.path.exists(expected_file)):
            print(f"Skipping {scenario_path}: Missing fixture files.")
            continue

        print(f"Running Scenario: {scenario_path} [{scenario.get('difficulty', 'medium')}]...")

        # Load inputs
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        with open(diff_file, "r", encoding="utf-8") as f:
            diff_content = f.read()

        # Prompt build timing
        t_start_build = time.perf_counter()
        # Mocking prompt build elapsed
        t_end_build = time.perf_counter()
        build_latency = (t_end_build - t_start_build) * 1000.0

        # Initialize engine
        if args.engine == "mock":
            engine = MockEngine(expected_file_path=expected_file)
        else:
            timeout = float(config.get("timeout_seconds", 60.0))
            retries = int(config.get("retries", 1))
            engine = GeminiEngine(timeout=timeout, retries=retries)

        # Inference timing
        t_start_inference = time.perf_counter()
        try:
            actual_review = engine.review(diff_content, metadata)
            inference_success = True
        except Exception as e:
            print(f"❌ Engine execution failed: {e}")
            actual_review = {}
            inference_success = False
        t_end_inference = time.perf_counter()
        inference_latency = (t_end_inference - t_start_inference) * 1000.0

        # Evaluation timing
        t_start_eval = time.perf_counter()
        evaluator = BenchmarkEvaluator(expected_file)
        eval_result = evaluator.evaluate(actual_review) if inference_success else {
            "score": 0.0, "passed": False, "precision": 0.0, "recall": 0.0, "details": {"error": "Execution failure"}
        }
        t_end_eval = time.perf_counter()
        eval_latency = (t_end_eval - t_start_eval) * 1000.0

        total_runtime = build_latency + inference_latency + eval_latency
        total_latency += total_runtime
        total_score += eval_result["score"]
        
        if eval_result["passed"]:
            passed_count += 1
            status_symbol = "[PASS]"
        else:
            status_symbol = "[FAIL]"
            failures.append(scenario_path)

        print(f"  {status_symbol} Score: {eval_result['score']:.1f}/100.0 | Latency: {total_runtime/1000.0:.2f}s")
        
        results.append({
            "scenario": scenario_path,
            "difficulty": scenario.get("difficulty", "medium"),
            "tags": scenario.get("tags", []),
            "passed": eval_result["passed"],
            "score": eval_result["score"],
            "precision": eval_result["precision"],
            "recall": eval_result["recall"],
            "latencies_ms": {
                "prompt_build": build_latency,
                "inference": inference_latency,
                "evaluation": eval_latency,
                "total": total_runtime
            }
        })

    # Summary calculations
    scenarios_run = len(results)
    avg_accuracy = (total_score / scenarios_run) if scenarios_run > 0 else 0.0
    avg_latency = (total_latency / scenarios_run) / 1000.0 if scenarios_run > 0 else 0.0
    passed_pct = (passed_count / scenarios_run) * 100.0 if scenarios_run > 0 else 0.0
    
    tp_count = sum(r["recall"] >= 1.0 for r in results if "security" in r["tags"])
    fn_count = sum(r["recall"] < 1.0 for r in results if "security" in r["tags"])

    print("\n" + "=" * 70)
    print("      BENCHMARK REPORT SUMMARY")
    print("=" * 70)
    print(f"Scenarios Executed: {scenarios_run}")
    print(f"Passed Scenarios:   {passed_count} ({passed_pct:.1f}%)")
    print(f"Average Accuracy:   {avg_accuracy:.1f}%")
    print(f"Average Latency:    {avg_latency:.2f} s")
    print(f"Security Recall:    {tp_count}/{tp_count + fn_count} detections")
    print("-" * 70)
    
    recommendation = "PASS" if passed_count == scenarios_run else "REGRESSION_DETECTED"
    print(f"RESULT RECOMMENDATION: {recommendation}")
    print("=" * 70)

    # Save historical report if requested
    if args.report:
        report_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "engine": {
                "provider": "google" if args.engine == "gemini" else "mock",
                "model": "gemini-2.5-flash" if args.engine == "gemini" else "static-fixtures",
                "temperature": 0,
                "prompt_version": 1
            },
            "fixture_version": manifest.get("fixture_version", 1),
            "schema_version": manifest.get("schema_version", 1),
            "scenarios_count": scenarios_run,
            "passed_count": passed_count,
            "accuracy_rate": avg_accuracy,
            "average_latency_seconds": avg_latency,
            "recommendation": recommendation,
            "results": results
        }
        
        filename = f"{datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')}.json"
        report_path = os.path.join(reports_dir, filename)
        with open(report_path, "w", encoding="utf-8") as rf:
            json.dump(report_data, rf, indent=2)
        print(f"Historical report successfully archived to benchmarks/reports/{filename}")

    if recommendation == "PASS":
        sys.exit(0)
    else:
        print(f"Benchmark run failed due to scenario regressions: {failures}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
