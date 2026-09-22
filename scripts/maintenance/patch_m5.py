
from core.settings import settings
import sys

with open("data_engine/freshness.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add imports and global cache if not present
if "_EVALUATE_FRESHNESS_CACHE" not in content:
    content = content.replace("import threading\n", "import threading\nimport time\n\n_EVALUATE_FRESHNESS_CACHE = {}\n_EVALUATE_FRESHNESS_LOCK = threading.Lock()\n")

old_def = 'def evaluate_freshness(realm: str, run_date: date, scan_type: str = "DAILY") -> dict:\n    scan_type = (scan_type or "DAILY").upper()'

new_def = '''def evaluate_freshness(realm: str, run_date: date, scan_type: str = "DAILY") -> dict:
    scan_type = (scan_type or "DAILY").upper()
    cache_key = f"{realm}_{run_date.isoformat()}_{scan_type}"
    now_ts = time.time()
    with _EVALUATE_FRESHNESS_LOCK:
        if cache_key in _EVALUATE_FRESHNESS_CACHE:
            cached_data, cached_time = _EVALUATE_FRESHNESS_CACHE[cache_key]
            if now_ts - cached_time < 5.0:
                return cached_data'''

content = content.replace(old_def, new_def)

# We need to cache the result at the very end
# Let's find the `return {` at the end
old_return = '    return {\n        "scan_type": scan_type'
new_return = '    result = {\n        "scan_type": scan_type'

content = content.replace(old_return, new_return)

if "with _EVALUATE_FRESHNESS_LOCK:" not in content.split("result = {")[-1]:
    old_end = '        "system_ok": bool(settings.get_active_trading_regime()),\n    }'
    new_end = '        "system_ok": bool(settings.get_active_trading_regime()),\n    }\n    with _EVALUATE_FRESHNESS_LOCK:\n        _EVALUATE_FRESHNESS_CACHE[cache_key] = (result, now_ts)\n    return result'
    content = content.replace(old_end, new_end)


with open("data_engine/freshness.py", "w", encoding="utf-8") as f:
    f.write(content)
print("done patched")
