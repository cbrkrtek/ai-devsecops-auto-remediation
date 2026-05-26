import os
import sys
import subprocess
import json

def run_trivy_scan(target_file: str, report_output: str) -> bool:
    command = ["trivy", "config", "--format", "json", "--output", report_output, target_file]
    try:
        subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
        return True
    except subprocess.CalledProcessError:
        return os.path.exists(report_output)
    except subprocess.TimeoutExpired:
        print(f"  ❌ Trivy scan timed out for {target_file}")
        return False
    except FileNotFoundError:
        print("!!! Critical error: Trivy CLI not found in PATH !!!")
        sys.exit(1)

def run_hadolint_scan(target_file: str) -> list:
    hadolint_path = "./hadolint.exe" if os.path.exists("./hadolint.exe") else "hadolint"
    command = [hadolint_path, "--format", "json", target_file]
    try:
        res = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if res.stdout.strip():
            return json.loads(res.stdout)
    except FileNotFoundError:
        print("  ℹ️ Hadolint not found. Skipping linter checks.")
        return []
    except Exception as e:
        print(f"  ❌ Error in Hadolint execution: {e}")
        return []
    return []