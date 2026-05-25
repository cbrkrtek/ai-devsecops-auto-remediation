import json
import os

def parse_trivy_report(report_path: str) -> list:
    if not os.path.exists(report_path):
        return []
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return []
        
    findings = []
    results = data.get("Results", [])
    if not results:
        return []

    for result in results:
        for misconf in result.get("Misconfigurations", []):
            if misconf.get("Severity") in ["HIGH", "CRITICAL"]:
                findings.append({
                    "id": misconf.get("ID"),
                    "type": "SecurityVulnerability",
                    "title": misconf.get("Title"),
                    "message": misconf.get("Message"),
                    "severity": misconf.get("Severity")
                })
    return findings

def parse_hadolint_results(hadolint_raw_data: list) -> list:
    findings = []
    for issue in hadolint_raw_data:
        if issue.get("level") in ["error", "warning"]:
            findings.append({
                "id": issue.get("code"),
                "type": "LinterBuildError",
                "title": f" Line{issue.get('line')}: Error of creating/logic Dockerfile",
                "message": issue.get("message"),
                "severity": issue.get("level").upper()
            })
    return findings