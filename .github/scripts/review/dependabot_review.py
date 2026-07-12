import argparse
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

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", required=True)
    parser.add_argument("--metadata-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    # 1. Check API Key presence - fail gracefully if missing
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("⚠ Dependabot Review skipped")
        print("Reason: Missing GEMINI_API_KEY environment credentials.")
        with open(args.output_file, "w", encoding="utf-8") as out:
            json.dump({"skipped": True, "reason": "Missing GEMINI_API_KEY"}, out)
        sys.exit(0)

    # 2. Load Configuration
    config_path = os.path.join(os.path.dirname(__file__), "../../maintainer-config.yml")
    config = load_yaml_config(config_path)
    
    timeout = float(config.get("timeout_seconds", 60.0))
    retries = int(config.get("retries", 1))

    # 3. Load Metadata
    try:
        with open(args.metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"Error reading metadata file: {e}")
        sys.exit(1)

    # 4. Read Prompt
    prompts_dir = os.path.join(os.path.dirname(__file__), "../../prompts")
    try:
        with open(os.path.join(prompts_dir, "dependabot.md"), "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        print(f"Error reading dependabot.md prompt: {e}")
        sys.exit(1)

    # 5. Build user prompt targeting dependency analysis
    user_prompt = f"""
PR Number: {args.pr}
PR Title: {metadata.get("title", "")}
PR Body (Dependabot Release Notes / Changelog / Commits / Advisory details):
{metadata.get("body", "")}

Changed Files list:
{chr(10).join(metadata.get("changed_files", []))}
"""

    # 6. Execute call
    try:
        client = GeminiClient(api_key=api_key, timeout=timeout, retries=retries)
        raw_json_response = client.generate_text(prompt=user_prompt, system_prompt=system_prompt)
        
        # Clean up any potential markdown wraps
        cleaned_json = raw_json_response.strip()
        if cleaned_json.startswith("```"):
            cleaned_json = re.sub(r"^```(?:json)?\s*", "", cleaned_json)
            cleaned_json = re.sub(r"\s*```$", "", cleaned_json)
            
        parsed_response = json.loads(cleaned_json)
        
        with open(args.output_file, "w", encoding="utf-8") as out:
            json.dump(parsed_response, out, indent=2)
            
        print("Dependabot review completed successfully.")
    except Exception as ex:
        print("⚠ Dependabot Review skipped")
        print(f"Reason: Dependabot review generation failed: {ex}")
        with open(args.output_file, "w", encoding="utf-8") as out:
            json.dump({"skipped": True, "reason": str(ex)}, out)

if __name__ == "__main__":
    run()
