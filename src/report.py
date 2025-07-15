import json
import os

def save_json_report(data, output_dir, filename_base):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{filename_base}_report.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
    return path

def save_md_report(data, output_dir, filename_base):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{filename_base}_report.md")
    with open(path, "w") as f:
        f.write(f"# Analysis Report for {data['file']}\n\n")
        
        f.write("## Classes\n")
        if data['classes']:
            for cls in data['classes']:
                f.write(f"- `{cls['name']}` at line {cls['lineno']}\n")
        else:
            f.write("No classes found.\n")
        
        f.write("\n## Functions\n")
        if data['functions']:
            for fn in data['functions']:
                f.write(f"- `{fn['name']}` at line {fn['lineno']}\n")
        else:
            f.write("No functions found.\n")
        
        f.write("\n## Complexity\n")
        for comp in data['complexity']:
            f.write(f"- `{comp['name']}` at line {comp['lineno']}: complexity {comp['complexity']}\n")
        
        f.write(f"\n## Maintainability Index: {data['maintainability']:.2f}\n")
        
        f.write("\n## Style & Linting Issues\n")
        if data['lint']:
            for issue in data['lint']:
                f.write(f"- {issue}\n")
        else:
            f.write("No style issues found.\n")

        f.write("\n## Anomalies Detected\n")
        if data.get('anomalies'):
            for anomaly in data['anomalies']:
                f.write(f"- {anomaly['name']} at line {anomaly['lineno']}: {anomaly['reason']}\n")
        else:
            f.write("No anomalies detected.\n")

        f.write("\n## Security Scan (Bandit)\n")
        if data.get('security'):
            for issue in data['security']:
                if 'error' in issue:
                    f.write(f"- Error running bandit: {issue['error']}\n")
                else:
                    f.write(f"- {issue['severity']} issue in `{issue['filename']}` "
                            f"line {issue['line_number']}: {issue['issue_text']} "
                            f"(Confidence: {issue['confidence']})\n")
        else:
            f.write("No security issues detected.\n")
        
    
    return path
