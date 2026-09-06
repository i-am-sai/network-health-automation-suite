import json
import time
from datetime import datetime

test_results = [] # list defined but called in test file

def record_result(test_name, url, status, duration_ms, extra=None):
    test_results.append({
        "test_name": test_name,
        "url": url,
        "status": status,
        "duration_ms": round(duration_ms, 2),
        "timestamp": datetime.now().isoformat(),
        "extra": extra or {}
    })