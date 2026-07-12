import argparse
import fnmatch
import json
import os
import re
import sys

# Ensure parent directory is on sys.path for importing llm module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm.gemini import GeminiClient  # type: ignore

def load_yaml_config(file_path):
    """Simple YAML parser to avoid external PyYAML dependency."""
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
                
                # Check integer types
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
                        # Convert dict to list if it was initialized as dict
                        config[current_section] = list(config[current_section].keys())
                config[current_section].append(val)
    return config

def filter_diff(diff_content, ignore_patterns):
    """Filters blocks of a git diff to exclude matches against ignore patterns."""
    filtered_lines = []
    current_file_ignored = False
    
    file_header_pattern = re.compile(r"^diff --git a/(.*) b/(.*)$")
    
    for line in diff_content.splitlines():
        match = file_header_pattern.match(line)
        if match:
            # Get path and check ignores
            filepath = match.group(2)
            current_file_ignored = False
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(filepath, pattern):
                    current_file_ignored = True
                    break
        if not current_file_ignored:
            filtered_lines.append(line)
            
    return "\n".join(filtered_lines)

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", required=True)
    parser.add_argument("--diff-file", required=True)
    parser.add_argument("--metadata-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    # 1. Check API Key presence - fail gracefully if missing
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("⚠ AI Review skipped")
        print("Reason: Missing GEMINI_API_KEY environment credentials.")
        with open(args.output_file, "w", encoding="utf-8") as out:
            json.dump({"skipped": True, "reason": "Missing GEMINI_API_KEY"}, out)
        sys.exit(0)

    # 2. Load Configuration
    config_path = os.path.join(os.path.dirname(__file__), "../../maintainer-config.yml")
    config = load_yaml_config(config_path)
    
    timeout = float(config.get("timeout_seconds", 60.0))
    retries = int(config.get("retries", 1))
    ignore_patterns = config.get("ignore_paths", [])
    if not isinstance(ignore_patterns, list):
        ignore_patterns = []

    # 3. Read Diff and filter ignored files
    try:
        with open(args.diff_file, "r", encoding="utf-8", errors="ignore") as f:
            raw_diff = f.read()
    except Exception as e:
        print(f"Error reading diff file: {e}")
        sys.exit(1)

    filtered_diff = filter_diff(raw_diff, ignore_patterns)
    
    # Context Budget Limit check
    max_diff_len = 100000
    if len(filtered_diff) > max_diff_len:
        filtered_diff = filtered_diff[:max_diff_len] + "\n\n[Diff truncated due to Context Budget restrictions]"

    # 4. Load Metadata
    try:
        with open(args.metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"Error reading metadata file: {e}")
        sys.exit(1)

    # 5. Read System Prompt and Context Files
    prompts_dir = os.path.join(os.path.dirname(__file__), "../../prompts")
    try:
        with open(os.path.join(prompts_dir, "review.md"), "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        print(f"Error reading review.md prompt: {e}")
        sys.exit(1)

    context_dir = os.path.join(os.path.dirname(__file__), "../../context")
    context_text = ""
    if os.path.exists(context_dir):
        for filename in sorted(os.listdir(context_dir)):
            if filename.endswith(".md"):
                try:
                    with open(os.path.join(context_dir, filename), "r", encoding="utf-8") as cf:
                        context_text += f"\n\n--- Context: {filename} ---\n{cf.read()}"
                except Exception as ex:
                    print(f"Warning: skipped reading context file {filename}: {ex}")

    # 6. Build the compilation prompt
    user_prompt = f"""
PR Number: {args.pr}
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
{filtered_diff}
```
"""

    # 7. Run AI Client with timeout and retries
    try:
        client = GeminiClient(api_key=api_key, timeout=timeout, retries=retries)
        raw_json_response = client.generate_text(prompt=user_prompt, system_prompt=system_prompt)
        
        # Clean up any potential markdown wraps
        cleaned_json = raw_json_response.strip()
        if cleaned_json.startswith("```"):
            # strip off ```json and ```
            cleaned_json = re.sub(r"^```(?:json)?\s*", "", cleaned_json)
            cleaned_json = re.sub(r"\s*```$", "", cleaned_json)
        
        # Validate that response is JSON parseable
        parsed_response = json.loads(cleaned_json)
        
        # Write response to file
        with open(args.output_file, "w", encoding="utf-8") as out:
            json.dump(parsed_response, out, indent=2)
            
        print("AI review completed successfully.")
    except Exception as ex:
        print("⚠ AI Review skipped")
        print(f"Reason: AI review generation failed: {ex}")
        with open(args.output_file, "w", encoding="utf-8") as out:
            json.dump({"skipped": True, "reason": str(ex)}, out)

if __name__ == "__main__":
    run()
