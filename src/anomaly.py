import numpy as np

def detect_anomalies(complexity_data):
    if not complexity_data:
        return []

    complexities = np.array([item['complexity'] for item in complexity_data])
    mean = np.mean(complexities)
    std = np.std(complexities)

    anomalies = []
    threshold = mean + 3 * std

    for item in complexity_data:
        if item['complexity'] > threshold:
            anomalies.append({
                'name': item['name'],
                'lineno': item['lineno'],
                'complexity': item['complexity'],
                'reason': f"Complexity {item['complexity']} exceeds threshold {threshold:.2f}"
            })
    return anomalies
