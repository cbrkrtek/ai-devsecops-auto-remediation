import json
import os
import urllib.request
from parser import parse_trivy_report

def load_file_content(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def ask_local_ai(prompt: str) -> str:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2.5-coder:1.5b",
        "prompt": prompt,
        "stream": False
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("response", "")
    except Exception as e:
        return f"An error to connect to Ollama {e}."

def generate_fix(dockerfile_path: str, report_path: str) -> str:
    #recieve vulnerabilities
    vulnerabilities = parse_trivy_report(report_path)
    #read the whole dockerfile
    dockerfile_content = load_file_content(dockerfile_path)
    
    #create a promt
    prompt = f"""
You are a Docker security expert and a DevSecOps engineer.
Your task is to fix the vulnerabilities in the Dockerfile that were found by the Trivy scanner.

Dockerfile source code:
{dockerfile_content}
-------------------------------

A list vulnerabilities from Trivy
{json.dumps(vulnerabilities, indent=2, ensure_ascii=False)}
-----------------------------------

REQUIREMENTS FOR THE ANSWER:
1. Return ONLY the corrected Dockerfile code. Start immediately with the FROM instruction.
2. Do not write any explanations, greetings, markdown wrappers (```), or extra text.
3. The code must be valid and ready for building.
4. Avoid using the root user (create a secure user if necessary).
5. Add the missing flags for apt-get if required by the report.

Corrected Dockerfile:
"""
    
    print("Send a request to AI (Ollama)")
    ai_response = ask_local_ai(prompt)
    return ai_response

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(__file__)
    dockerfile = os.path.join(BASE_DIR, "../tests/vulnerable.Dockerfile")
    report = os.path.join(BASE_DIR, "../tests/trivy_report.json")
    
    fixed_dockerfile = generate_fix(dockerfile, report)
    
    print("\n Result:")
    print(fixed_dockerfile.strip())