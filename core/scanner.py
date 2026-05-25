import os
import sys
import subprocess
import json

def run_trivy_scan(target_file: str, report_output: str) -> bool:
    command = ["trivy", "config", "--format", "json", "--output", report_output, target_file]
    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return os.path.exists(report_output)
    except FileNotFoundError:
        print("!!!Critical error: Trivy CLI not in PATH!!!")
        sys.exit(1)

def run_hadolint_scan(target_file: str) -> list:

    command = ["./hadolint.exe", "--format", "json", target_file]
    try:
        res = subprocess.run(command, capture_output=True, text=True)
        if res.stdout.strip():
            return json.loads(res.stdout)
    except FileNotFoundError:
        print("hadolint.exe not in root. Skip linter check")
        return []
    except Exception as e:
        print(f"Error in Hadolint execution {e}")
        return []
    return []