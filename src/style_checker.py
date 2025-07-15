import subprocess

def run_flake8(filepath):
    try:
        result = subprocess.run(
            ['flake8', filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output = result.stdout.strip()
        if output == "":
            return ["No style issues found."]
        return output.splitlines()
    except Exception as e:
        return [f"Error running flake8: {e}"]
