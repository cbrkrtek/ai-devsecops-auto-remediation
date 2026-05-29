import json
import urllib.request
import re

def query_local_llm(system_prompt: str, user_prompt: str, model_name: str = "qwen2.5-coder:7b") -> dict:
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "format": "json", 
        "options": {
            "temperature": 0.1, 
            "top_p": 0.2
        }
    }
    
    headers = {"Content-Type": "application/json"}
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=300) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            inner_json_str = res_data.get("message", {}).get("content", "{}").strip()
            
            if inner_json_str.startswith("```"):
                inner_json_str = re.sub(r'^```[a-zA-Z0-9]*', '', inner_json_str)
                inner_json_str = re.sub(r'```$', '', inner_json_str)
                inner_json_str = inner_json_str.strip()
            
            return json.loads(inner_json_str)
    except Exception as e:
        print(f"  ❌ Error parsing LLM response in client.py: {e}")
        try:
            clean_fallback = re.search(r'"remediated_dockerfile"\s*:\s*"(.*)"', inner_json_str, re.DOTALL)
            if clean_fallback:
                return {"remediated_dockerfile": clean_fallback.group(1)}
        except:
            pass
        return {}