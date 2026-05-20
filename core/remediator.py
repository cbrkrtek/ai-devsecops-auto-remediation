import json
import os
import urllib.request
from parser import parse_trivy_report

def load_file_content(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def ask_local_ai(prompt: str) -> str:
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "qwen2.5-coder:1.5b",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("message", {}).get("content", "")
    except Exception as e:
        return f"Error of execution Ollama: {e}. Make sure, that Ollama has executed."

def clean_ai_response(response_text: str) -> str:
    lines = response_text.strip().split('\n')
    clean_lines = []
    
    for line in lines:
        #delete markdown lines like "```"
        if line.strip().startswith("```"):
            continue
        clean_lines.append(line)
        
    return '\n'.join(clean_lines).strip()

def generate_fix(dockerfile_path: str, report_path: str) -> str:
    #recieve vulnerabilities from parser
    vulnerabilities = parse_trivy_report(report_path)
    #read the Dockerfile
    dockerfile_content = load_file_content(dockerfile_path)
    
    #create promt
    prompt = f"""
You are an expert in DevSecOps and Docker security. Your task is to modify the provided Dockerfile to fix the specific security vulnerabilities identified by the Trivy scanner.

--- TARGET VULNERABILITIES TO FIX ---
{json.dumps(vulnerabilities, indent=2, ensure_ascii=False)}
-------------------------------------

--- ORIGINAL DOCKERFILE CODE ---
{dockerfile_content}
--------------------------------

CRITICAL INSTRUCTIONS:
1. Fix EVERY vulnerability listed in the 'TARGET VULNERABILITIES' section by applying industry-standard security best practices.
2. Output ONLY the resulting corrected Dockerfile code. Do NOT include any explanations, introduction, markdown formatting, or markdown code blocks (like ```dockerfile).
3. Ensure the modified Dockerfile is completely valid, syntactically correct, and preserves the original application's functionality (e.g., keep the same base image, exposed ports, and startup commands unless they cause a vulnerability).
4. Order instructions logically: run system package updates/installations as 'root' first, clean up package caches to reduce image size, and switch to a secure non-root user context at the end of the file if a root execution vulnerability is reported.

The corrected, secure Dockerfile is:
"""
    
    print("Send a promt to Ollama...")
    ai_response = ask_local_ai(prompt)
    return ai_response

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(__file__)
    dockerfile = os.path.join(BASE_DIR, "../tests/vulnerable.Dockerfile")
    report = os.path.join(BASE_DIR, "../tests/trivy_report.json")
    
    raw_fixed_dockerfile = generate_fix(dockerfile, report)
    clean_dockerfile = clean_ai_response(raw_fixed_dockerfile)
    
    print("\n Result:")
    print(clean_dockerfile)