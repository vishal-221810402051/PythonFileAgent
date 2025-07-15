import sys
import os

from src.ast_parser import analyze_file
from src.code_metrics import analyze_complexity
from src.style_checker import run_flake8
from src.report import save_json_report, save_md_report
from src.anomaly import detect_anomalies
from src.security_checker import run_bandit


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <python_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.isfile(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)

    # Run AST structure analysis
    result = analyze_file(filepath)

    # Run complexity analysis
    complexity_data, mi = analyze_complexity(filepath)

    # Detect anomalies
    anomalies = detect_anomalies(complexity_data)

    # Run linting
    flake8_issues = run_flake8(filepath)

        # Run security scan
    bandit_issues = run_bandit(filepath)


    # Build unified data for report
    report_data = {
        "file": filepath,
        "classes": [{"name": cname, "lineno": line} for cname, line in result.classes],
        "functions": [{"name": fname, "lineno": line} for fname, line in result.functions],
        "complexity": complexity_data,
        "maintainability": mi,
        "lint": flake8_issues,
        "anomalies": anomalies,
        "security": bandit_issues
    }



    # Print summary
    print(f"\nSummary for {filepath}:")
    print(f"- Classes: {len(report_data['classes'])}")
    print(f"- Functions: {len(report_data['functions'])}")
    print(f"- Maintainability Index: {mi:.2f}")
    print(f"- Lint issues: {len([l for l in flake8_issues if 'No style issues' not in l])}")

    # Generate reports
    filename_base = os.path.splitext(os.path.basename(filepath))[0]
    json_path = save_json_report(report_data, "reports", filename_base)
    md_path = save_md_report(report_data, "reports", filename_base)

    print(f"\nReports saved to:")
    print(f"- {json_path}")
    print(f"- {md_path}")
