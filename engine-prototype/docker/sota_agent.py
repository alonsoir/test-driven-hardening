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
import time

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

def extract_code_blocks(text):
    """Extrae bloques de código etiquetados como test, command, fix, soportando varios formatos."""
    blocks = {}
    # Patrón 1: [test] seguido de triple backticks (con o sin lenguaje)
    pattern1 = r'\[(test|command|fix)\]\s*```(?:\w*)\n(.*?)```'
    matches1 = re.findall(pattern1, text, re.DOTALL | re.IGNORECASE)
    for marker, code in matches1:
        blocks[marker.lower()] = code.strip()
    # Patrón 2: triple backticks con etiqueta directa (```test ...```)
    pattern2 = r'```(test|command|fix)\s*\n(.*?)```'
    matches2 = re.findall(pattern2, text, re.DOTALL | re.IGNORECASE)
    for marker, code in matches2:
        blocks[marker.lower()] = code.strip()
    # Patrón 3: si no se encontró con los patrones anteriores, buscar bloques de código genéricos
    if not blocks:
        pattern3 = r'```(?:\w*)\n(.*?)```'
        code_blocks = re.findall(pattern3, text, re.DOTALL)
        if len(code_blocks) >= 2:
            # Asumir que el primero es test y el segundo command (o fix)
            blocks["test"] = code_blocks[0].strip()
            blocks["command"] = code_blocks[1].strip()
    return blocks


def get_prompt(config, state_name, vulnerability, placeholders=None):
    """Obtiene el prompt para un estado, reemplazando placeholders manualmente."""
    state_prompts = config.get("state_prompts", {})
    if state_name not in state_prompts:
        log(f"WARNING: No prompt defined for state '{state_name}'.", state=state_name)
        system = "You are a security expert."
    else:
        system = state_prompts[state_name].get("system", "You are a security expert.")

    if placeholders is None:
        placeholders = {}
    # Asegurar que la vulnerabilidad esté disponible como placeholder
    placeholders.setdefault("vulnerability", str(vulnerability))

    filled = system
    for key, value in placeholders.items():
        filled = filled.replace("{" + key + "}", str(value))
    return filled


# ----------------------------------------------------------------------
def phase_test_design(config, model_config, vulnerability, repo_path, api_key, max_iter):
    model_display = model_config["model"]
    temperature = model_config.get("temperature", 0.1)
    max_tokens = model_config.get("max_tokens", 4000)

    log("Starting test design", model_display, state="test_designing")
    placeholders = {
        "repo_path": repo_path,
        "vuln_file": vulnerability.get("file", "")  # ruta relativa del archivo vulnerable
    }
    prompt = get_prompt(config, "test_designing", vulnerability, placeholders)

    test_code, command, success, output_log = "", "", False, ""

    for attempt in range(1, max_iter + 1):
        log(f"Attempt {attempt}/{max_iter}", model_display, state="test_designing")
        result = call_openrouter(model_display, prompt, api_key, temperature, max_tokens)
        
        if not result["success"]:
            log(f"LLM call failed (sleeping): {result['error']}", model_display, state="test_designing")
            time.sleep(5 * attempt)
            continue

        response = result["content"]
        debug_path = Path(repo_path) / f"llm_response_test_attempt{attempt}.txt"
        debug_path.write_text(response)

        blocks = extract_code_blocks(response)
        test_code = blocks.get("test", "")
        command = blocks.get("command", "")

        if not test_code or not command:
            log("Missing test code or command block", model_display, state="test_designing")
            prompt = f"ERROR: La respuesta anterior no contenía los bloques requeridos. Debes incluir [test] y [command] con el formato especificado.\n\nRespuesta anterior (incorrecta):\n{response}\n\nGenera una nueva respuesta con el formato correcto."
            continue

        # Determinar extensión del test según el lenguaje detectado en el bloque de código
        # Por simplicidad, asumimos .c para C/C++ y .sh para bash. Podríamos mejorarlo.
        test_filename = "tdh_test.c"  # por defecto
        if "bash" in response or "sh" in response:
            test_filename = "tdh_test.sh"
        elif "python" in response:
            test_filename = "tdh_test.py"
        test_path = Path(repo_path) / test_filename

        try:
            test_path.write_text(test_code)
            stdout, stderr, retcode = run_command(command, repo_path)
            output_log = stdout + stderr

            eval_prompt = f"Output:\n{output_log}\nExit code: {retcode}\nDid it reproduce the bug? Answer YES or NO."
            eval_res = call_openrouter(model_display, eval_prompt, api_key, temperature=0.0, max_tokens=100)
            
            if eval_res["success"] and eval_res["content"].strip().upper().startswith("YES"):
                success = True
                log("Test successfully reproduced the vulnerability!", model_display, state="test_designing")
                break
            else:
                prompt = f"Previous test failed to reproduce. Output:\n{output_log}\nTry again. Remember the format."
        except Exception as e:
            log(f"Error: {e}", model_display, state="test_designing")
            prompt = f"Error during execution: {e}. Try again."

    return test_code, command, success, output_log


# ----------------------------------------------------------------------
def phase_fix_design(config, model_config, vulnerability, test_code, test_command, repo_path, api_key, max_iter):
    model_display = model_config["model"]
    temperature = model_config.get("temperature", 0.1)
    max_tokens = model_config.get("max_tokens", 4000)

    log("Starting fix design", model_display, state="fix_designing")
    placeholders = {
        "test_code": test_code,
        "test_command": test_command,
        "repo_path": repo_path,
        "vuln_file": vulnerability.get("file", "")
    }
    prompt = get_prompt(config, "fix_designing", vulnerability, placeholders)

    fix_code, fix_command, success, output_log = "", "", False, ""

    for attempt in range(1, max_iter + 1):
        log(f"Attempt {attempt}/{max_iter}", model_display, state="fix_designing")
        result = call_openrouter(model_display, prompt, api_key, temperature, max_tokens)
        
        if not result["success"]:
            log(f"LLM call failed: {result['error']}", model_display, state="fix_designing")
            time.sleep(5 * attempt)
            continue

        response = result["content"]
        debug_path = Path(repo_path) / f"llm_response_fix_attempt{attempt}.txt"
        debug_path.write_text(response)

        blocks = extract_code_blocks(response)
        fix_code = blocks.get("fix", "")
        fix_command = blocks.get("command", test_command)

        if not fix_code:
            log("Missing fix code block", model_display, state="fix_designing")
            prompt = f"ERROR: La respuesta anterior no contenía el bloque [fix]. Respuesta:\n{response}\n\nGenera una nueva respuesta con el bloque [fix]."
            continue

        vuln_file = vulnerability.get("file")
        if not vuln_file:
            log("No file specified in vulnerability", model_display, state="fix_designing")
            break

        file_path = Path(repo_path) / vuln_file
        try:
            if file_path.exists():
                file_path.rename(file_path.with_suffix(".bak"))
            file_path.write_text(fix_code)

            stdout, stderr, retcode = run_command(fix_command, repo_path)
            output_log = stdout + stderr

            eval_prompt = f"Output after fix:\n{output_log}\nIs the vulnerability still present? Answer YES if still present, NO if fixed."
            eval_res = call_openrouter(model_display, eval_prompt, api_key, temperature=0.0, max_tokens=100)
            
            if eval_res["success"] and eval_res["content"].strip().upper().startswith("NO"): # NO = fixed
                success = True
                break
            else:
                prompt = f"Fix failed. Output:\n{output_log}\nTry again."
        except Exception as e:
            log(f"Error: {e}")
            prompt = f"Error: {e}. Try again."

    return fix_code, fix_command, success, output_log


# ----------------------------------------------------------------------
def phase_document(config, model_config, vulnerability, test_code, fix_code, t_ok, f_ok, api_key):
    model_display = model_config["model"]
    log("Starting documentation", model_display, state="documenting")
    
    placeholders = {
        "test_code": test_code,
        "fix_code": fix_code,
        "test_verified": "YES" if t_ok else "NO",
        "fix_verified": "YES" if f_ok else "NO"
    }
    prompt = get_prompt(config, "documenting", vulnerability, placeholders)
    
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
    
    if not t_ok:
        log("Test phase failed, exiting", model_config["model"], state="failed")
        output = {
            "status": "error",
            "reason": "test_failed",
            "model_used": model_config["model"]
        }
        print(json.dumps(output))
        sys.exit(1)

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