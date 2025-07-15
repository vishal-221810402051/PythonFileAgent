import subprocess
import json

def run_bandit(filepath):
    try:
        result = subprocess.run(
            ["bandit", "-f", "json", "-q", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output = result.stdout
        bandit_data = json.loads(output) if output else {"results": []}
        # Simplify structure to just relevant info
        issues = []
        for issue in bandit_data.get("results", []):
            issues.append({
                "filename": issue.get("filename"),
                "line_number": issue.get("line_number"),
                "issue_text": issue.get("issue_text"),
                "severity": issue.get("issue_severity"),
                "confidence": issue.get("issue_confidence"),
                "code": issue.get("code").strip()
            })
        return issues
    except Exception as e:
        return [{"error": str(e)}]
