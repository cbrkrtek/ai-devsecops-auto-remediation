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
You are a Docker security expert. Your task is to strictly fix the vulnerabilities in the Dockerfile that were found by the Trivy scanner.

--- SOURCE CODE OF THE DOCKERFILE ---
{dockerfile_content}
-------------------------------

--- LIST OF VULNERABILITIES FROM TRIVY ---
{json.dumps(vulnerabilities, indent=2, ensure_ascii=False)}
-----------------------------------

STRICT RULES:
1. Output ONLY the finished Dockerfile code. No explanations, no comments.
2. To fix the 'root' vulnerability (DS-0002): create a user with the command 'RUN useradd -u 10011 appuser' BEFORE the USER instruction, and switch to it at the very end of the file: 'USER appuser'. All system commands (apt-get) should be executed under root (at the beginning of the file).
3. To fix the apt-get vulnerability (DS-0029): BE SURE to add the '--no-install-recommends' flag immediately after 'apt-get install -y'.
4. Don't add unnecessary folder and password settings if they weren't in the source code.

The corrected Dockerfile is:
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