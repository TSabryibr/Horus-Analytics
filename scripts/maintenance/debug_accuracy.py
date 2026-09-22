import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from routes.ai_report import _generate_rule_based_report

empty_snapshot = {}
try:
    report = _generate_rule_based_report(empty_snapshot)
    with open('debug_output.json', 'w') as f:
        json.dump(report, f, indent=2)
except Exception as e:
    import traceback
    traceback.print_exc()
