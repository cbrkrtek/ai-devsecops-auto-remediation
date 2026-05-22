import os
import json
import urllib.request

def parse_trivy_report(report_path: str) -> list:
    if not os.path.exists(report_path):
        return []
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            results = data.get("Results", [])
            if results and isinstance(results, list):
                first_result = results[0]
                if "Misconfigurations" in first_result:
                    return first_result["Misconfigurations"]
                elif "Vulnerabilities" in first_result:
                    return first_result["Vulnerabilities"]
    except Exception as e:
        print(f"Error parsing report {os.path.basename(report_path)}: {e}")
    return []

def load_file_content(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def clean_ai_response(ai_response: str) -> str:
    lines = ai_response.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith("```"):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()

def generate_fix(dockerfile_path: str, report_path: str) -> str:
    
    vulnerabilities = parse_trivy_report(report_path)
    dockerfile_content = load_file_content(dockerfile_path)
    
    if not vulnerabilities:
        print(f"ℹ️ Trivy detected no vulnerabilities in {os.path.basename(dockerfile_path)}.")
        return dockerfile_content

    system_instruction = (
        "You are an automated DevSecOps remediation agent. Your objective is to rewrite the provided Dockerfile "
        "to resolve all security findings listed in the vulnerability report while applying standard container hardening practices.\n"
        "STRICT EXECUTION CONSTRAINTS:\n"
        "1. Output ONLY the valid, compilable, raw Dockerfile code lines. Do not include any introductory text, explanations, or markdown code blocks (NEVER use ```).\n"
        "2. Functional Parity: Retain the original base image, application logic, multi-stage architectures, environment variables, exposed ports, volume mounts, and execution commands (CMD/ENTRYPOINT).\n"
        "3. Least Privilege Principle: If the report indicates root privilege vulnerabilities, enforce a non-root user execution context. You must write the appropriate commands to create a system user/group based on the detected OS distribution (e.g., Debian/Ubuntu vs Alpine) and switch to it using the 'USER' directive before the application entrypoint.\n"
        "4. Layer Optimization & Hygene: Combine package manager operations (e.g., update, installation of specified dependencies) into a single 'RUN' layer to minimize image size. Ensure that package manager caches, temporary files, and logs are completely removed within that exact same layer.\n"
        "5. Compliance: Ensure the remediated Dockerfile adheres to standard container security benchmarks (e.g., avoiding pinning to 'latest' tags where applicable, eliminating unnecessary privileges, and preventing leak of credentials)."
    )
    
    user_context = f"""Remediate all security flaws found in the scanner report for the given Dockerfile.

--- ORIGINAL DOCKERFILE ---
{dockerfile_content}

--- SCANNER REPORT (FINDINGS) ---
{json.dumps(vulnerabilities, indent=2, ensure_ascii=False)}

Remediated and hardened Dockerfile:"""

    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "qwen2.5-coder:7b",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_context}
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,  
            "top_p": 0.3
        }
    }
    
    headers = {"Content-Type": "application/json"}
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("message", {}).get("content", "")
    except Exception as e:
        print(f"Error sending request to Ollama API: {e}")
        return dockerfile_content