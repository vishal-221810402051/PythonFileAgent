from radon.complexity import cc_visit
from radon.metrics import mi_visit

def analyze_complexity(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        code = file.read()
    
    # Cyclomatic Complexity
    complexity_results = cc_visit(code)
    complexity_data = []
    for item in complexity_results:
        complexity_data.append({
            'name': item.name,
            'complexity': item.complexity,
            'lineno': item.lineno
        })
    
    # Maintainability Index
    mi = mi_visit(code, True)
    
    return complexity_data, mi

