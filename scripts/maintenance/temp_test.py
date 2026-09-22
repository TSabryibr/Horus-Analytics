import traceback
import sys

try:
    import tests.conftest
except Exception as e:
    traceback.print_exc()
