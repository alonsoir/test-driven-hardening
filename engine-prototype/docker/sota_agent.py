#!/usr/bin/env python3
"""
SOTA Agent for TDH Engine – Autonomous Mode

Reads a task from stdin, loads llm_council.yaml, and executes the full
test/fix/document cycle for a given vulnerability.
"""

import os
import sys
import json
import yaml
import re
import subprocess
import requests
from pathlib import Path

# ----------------------------------------------------------------------
# Constants
DEFAULT_CONFIG_PATH = "/etc/tdh/llm_council.yaml"
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1/chat/completions"
COMMAND_TIMEOUT = 60  # seconds
DEFAULT_MAX_ITER = 3


# ----------------------------------------------------------------------
def log(msg, model_name="", state=""):
    """Emit log with SOTA and optional state prefix."""
    prefix = f"[SOTA:{model_name}]"
    if state:
        prefix += f"[STATE:{state}]"
    print(f"{prefix} {msg}", flush=True)


# ----------------------------------------------------------------------
def load_config(config_path=None):
    """Load llm_council.yaml. Exit if not found."""
    if config_path is None:
        config_path = os.environ.get("TDH_COUNCIL_CONFIG", DEFAULT_CONFIG_PATH)

    if not Path(config_path).is_file():
        log(f"ERROR: Configuration file not found: {config_path}", state="FATAL")
        sys.exit(1)

    with open(config_path, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            log(f"ERROR: Invalid YAML in {config_path}: {e}", state="FATAL")
            sys.exit(1)


# ----------------------------------------------------------------------
def call_openrouter(model_id, prompt, api_key, temperature=0.1, max_tokens=4000):
    """Call OpenRouter API and return content or error."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "TDH-Engine-SOTA"
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        resp = requests.post(OPENROUTER_API_BASE, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return {"success": True, "content": content, "model": model_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ----------------------------------------------------------------------
def run_command(cmd, cwd):
    """Execute a shell command and return stdout, stderr, returncode."""
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", -1
    except Exception as e:
        return "", str(e), -1


# ----------------------------------------------------------------------
def extract_code_blocks(text):
    """Extract code blocks labeled with ```tag```."""
    blocks = {}
    pattern = r'```(\w+)\s*\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    for tag, code in matches:
        tag = tag.lower()
        if tag in ('test', 'fix', 'command') and tag not in blocks:
            blocks[tag] = code.strip()
    return blocks


# ----------------------------------------------------------------------
def get_prompt(config, state_name, vulnerability, extra_context=""):
    state_prompts = config.get("state_prompts", {})
    if state_name not in state_prompts:
        log(f"WARNING: No prompt defined for state '{state_name}'.", state=state_name)
        system = "You are a security expert."
    else:
        system = state_prompts[state_name].get("system", "You are a security expert.")

    # Format the single system string with all needed placeholders
    try:
        # extra_context puede ser repo_path, o un dict con más campos
        if isinstance(extra_context, dict):
            filled = system.format(vulnerability=vulnerability, **extra_context)
        else:
            # Por defecto, asumimos que extra_context es repo_path
            filled = system.format(vulnerability=vulnerability, repo_path=extra_context)
    except KeyError as e:
        log(f"WARNING: Missing placeholder {e} in prompt for state '{state_name}'", state=state_name)
        filled = system

    return filled


# ----------------------------------------------------------------------
def phase_test_design(config, model_config, vulnerability, repo_path, api_key, max_iter):
    model_display = model_config["model"]
    temperature = model_config.get("temperature", 0.1)
    max_tokens = model_config.get("max_tokens", 4000)

    log("Starting test design", model_display, state="test_designing")
    prompt = get_prompt(config, "test_designing", vulnerability, extra_context=repo_path)

    test_code, command, success, output_log = "", "", False, ""

    for attempt in range(1, max_iter + 1):
        log(f"Attempt {attempt}/{max_iter}", model_display, state="test_designing")
        result = call_openrouter(model_display, prompt, api_key, temperature, max_tokens)
        
        if not result["success"]:
            log(f"LLM call failed: {result['error']}", model_display, state="test_designing")
            continue

        response = result["content"]
        blocks = extract_code_blocks(response)
        test_code = blocks.get("test", "")
        command = blocks.get("command", "")

        if not test_code or not command:
            log("Missing test code or command block", model_display, state="test_designing")
            prompt = response + "\n\nProvide both a ```test``` and a ```command``` block."
            continue

        test_path = Path(repo_path) / "tdh_test.c"
        try:
            test_path.write_text(test_code)
            stdout, stderr, retcode = run_command(command, repo_path)
            output_log = stdout + stderr
            
            eval_prompt = f"Output:\n{output_log}\nExit code: {retcode}\nDid it reproduce the bug? YES/NO."
            eval_res = call_openrouter(model_display, eval_prompt, api_key, temperature=0.0, max_tokens=100)
            
            if eval_res["success"] and eval_res["content"].strip().upper().startswith("YES"):
                success = True
                log("Test successfully reproduced the vulnerability!", model_display, state="test_designing")
                break
            else:
                prompt = f"Previous test failed to reproduce. Output:\n{output_log}\nTry again."
        except Exception as e:
            log(f"Error: {e}", model_display, state="test_designing")

    return test_code, command, success, output_log


# ----------------------------------------------------------------------
def phase_fix_design(config, model_config, vulnerability, test_code, test_command, repo_path, api_key, max_iter):
    model_display = model_config["model"]
    temperature = model_config.get("temperature", 0.1)
    max_tokens = model_config.get("max_tokens", 4000)

    log("Starting fix design", model_display, state="fix_designing")
    context = f"Vulnerability: {vulnerability}\nTest: {test_code}"
    prompt = get_prompt(config, "fix_designing", vulnerability, extra_context=context)

    fix_code, fix_command, success, output_log = "", "", False, ""

    for attempt in range(1, max_iter + 1):
        log(f"Attempt {attempt}/{max_iter}", model_display, state="fix_designing")
        result = call_openrouter(model_display, prompt, api_key, temperature, max_tokens)
        
        if not result["success"]: continue

        blocks = extract_code_blocks(result["content"])
        fix_code = blocks.get("fix", "")
        fix_command = blocks.get("command", test_command)

        if not fix_code:
            prompt += "\nMissing ```fix``` block."
            continue

        vuln_file = vulnerability.get("file")
        if not vuln_file: break

        file_path = Path(repo_path) / vuln_file
        try:
            if file_path.exists():
                file_path.rename(file_path.with_suffix(".bak"))
            file_path.write_text(fix_code)

            stdout, stderr, retcode = run_command(fix_command, repo_path)
            output_log = stdout + stderr

            eval_prompt = f"Output after fix:\n{output_log}\nIs it fixed? YES/NO."
            eval_res = call_openrouter(model_display, eval_prompt, api_key, temperature=0.0, max_tokens=100)
            
            if eval_res["success"] and eval_res["content"].strip().upper().startswith("NO"): # NO = not present
                success = True
                break
            else:
                prompt = f"Fix failed. Output:\n{output_log}\nTry again."
        except Exception as e:
            log(f"Error: {e}")

    return fix_code, fix_command, success, output_log


# ----------------------------------------------------------------------
def phase_document(config, model_config, vulnerability, test_code, fix_code, context, api_key):
    model_display = model_config["model"]
    log("Starting documentation", model_display, state="documenting")
    
    extra = f"Test: {test_code}\nFix: {fix_code}\nContext: {context}"
    prompt = get_prompt(config, "documenting", vulnerability, extra_context=extra)
    
    result = call_openrouter(model_display, prompt, api_key)
    return result["content"] if result["success"] else "Documentation failed."


# ----------------------------------------------------------------------
def main():
    try:
        task = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    required = ["model", "vulnerability", "repo_path", "openrouter_api_key"]
    if not all(k in task for k in required):
        print(json.dumps({"status": "error", "error": "Missing fields"}))
        sys.exit(1)

    model_key = task["model"]
    vulnerability = task["vulnerability"]
    repo_path = task["repo_path"]
    api_key = task["openrouter_api_key"]
    max_iter = task.get("max_iterations", DEFAULT_MAX_ITER)

    config = load_config()
    llm_configs = config.get("llm_configs", {})
    if model_key not in llm_configs:
        log(f"Model {model_key} not found", state="FATAL")
        sys.exit(1)

    model_config = llm_configs[model_key]
    log("Starting autonomous agent", model_config["model"], state="initialized")

    # Flow
    t_code, t_cmd, t_ok, _ = phase_test_design(config, model_config, vulnerability, repo_path, api_key, max_iter)
    
    f_code, f_cmd, f_ok, _ = ("", "", False, "")
    if t_ok:
        f_code, f_cmd, f_ok, _ = phase_fix_design(config, model_config, vulnerability, t_code, t_cmd, repo_path, api_key, max_iter)
    
    summary = f"Test: {t_ok}, Fix: {f_ok}"
    explanation = phase_document(config, model_config, vulnerability, t_code, f_code, summary, api_key)

    output = {
        "status": "success",
        "test_verified": t_ok,
        "fix_verified": f_ok,
        "explanation": explanation,
        "model_used": model_config["model"]
    }
    print(json.dumps(output, indent=2))
    log("SOTA agent finished", model_config["model"], state="completed")


if __name__ == "__main__":
    main()