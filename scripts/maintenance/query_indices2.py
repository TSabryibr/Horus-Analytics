from core.settings import settings
from data_engine.mubasher_sqlite_source import build_paths, list_history_symbols
from pathlib import Path

try:
    paths = build_paths(
        Path(settings.MUBASHER_ROOT_DIR),
        user_id=(settings.MUBASHER_USER_ID or None),
    )
    symbols = list_history_symbols(paths)
    egx_symbols = [s for s in symbols if s.startswith("EGX")]
    print("Found EGX Indices in Mubasher DB:")
    print(egx_symbols)
except Exception as e:
    print(f"Failed: {e}")
