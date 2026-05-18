import json
import os

def parse_trivy_report(report_path: str) -> list:
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Trivy report didn't find in this path: {report_path}")
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    findings = []
    #check results
    results = data.get("Results", [])
    for result in results:
        misconfigurations = result.get("Misconfigurations", [])
        for misconf in misconfigurations:
            severity = misconf.get("Severity")
            # focus in HIGH and CRITICAL vulnerabilities
            if severity in ["HIGH", "CRITICAL"]:
                cause_metadata = misconf.get("CauseMetadata", {})
                start_line = cause_metadata.get("StartLine", "Unknown")
                end_line = cause_metadata.get("EndLine", "Unknown")
                
                finding = {
                    "id": misconf.get("ID"),
                    "title": misconf.get("Title"),
                    "description": misconf.get("Description"),
                    "message": misconf.get("Message"),
                    "severity": severity,
                    "start_line": start_line,
                    "end_line": end_line
                }
                findings.append(finding)

    return findings

if __name__ == "__main__":
    test_path = os.path.join(os.path.dirname(__file__), "../tests/trivy_report.json")
    try:
        results = parse_trivy_report(test_path)
        print(f"Successfully parsed: {len(results)}")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Parse error: {e}")