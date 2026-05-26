import json
import os

def parse_trivy_report(report_path: str) -> list:
    if not os.path.exists(report_path):
        return []
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ Ошибка чтения отчета Trivy: {e}")
        return []
        
    findings = []
    results = data.get("Results", [])
    if not results or not isinstance(results, list):
        return []

    for result in results:
        for misconf in result.get("Misconfigurations", []):
            if misconf.get("Severity") in ["HIGH", "CRITICAL", "MEDIUM"]:
                findings.append({
                    "id": misconf.get("ID", "UNKNOWN_ID"),
                    "type": "SecurityMisconfiguration",
                    "title": misconf.get("Title", "Security Issue"),
                    "message": misconf.get("Message", "No message provided"),
                    "severity": misconf.get("Severity")
                })
        for vuln in result.get("Vulnerabilities", []):
            if vuln.get("Severity") in ["HIGH", "CRITICAL", "MEDIUM"]:
                findings.append({
                    "id": vuln.get("VulnerabilityID", "UNKNOWN_CVE"),
                    "type": "PackageVulnerability",
                    "title": vuln.get("Title", "Package Vulnerability"),
                    "message": vuln.get("Description", "No description provided"),
                    "severity": vuln.get("Severity")
                })
    return findings

def parse_hadolint_results(hadolint_raw_data: list) -> list:
    findings = []
    if not hadolint_raw_data or not isinstance(hadolint_raw_data, list):
        return []
        
    for issue in hadolint_raw_data:
        if issue.get("level") in ["error", "warning", "info", "style"]:
            findings.append({
                "id": issue.get("code", "UNKNOWN_RULE"),
                "type": "LinterBuildError",
                "title": f"Line {issue.get('line')}: {issue.get('message')}",
                "message": f"Rule {issue.get('code')}: {issue.get('message', '')}",
                "severity": issue.get("level", "WARNING").upper()
            })
    return findings