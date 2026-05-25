import json
import urllib.request

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
        "options": {"temperature": 0.1, "top_p": 0.2}
    }
    
    headers = {"Content-Type": "application/json"}
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            inner_json_str = res_data.get("message", {}).get("content", "{}")
            return json.loads(inner_json_str)
    except Exception as e:
        print(f"Network error to connect to LLM: {e}")
        return {}