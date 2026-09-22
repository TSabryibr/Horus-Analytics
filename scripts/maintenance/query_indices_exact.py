from core.settings import settings
from data_engine.mubasher_sqlite_source import build_paths, list_history_symbols
from pathlib import Path

try:
    paths = build_paths(
        Path(settings.MUBASHER_ROOT_DIR),
        user_id=(settings.MUBASHER_USER_ID or None),
    )
    symbols = list_history_symbols(paths)
    
    print("Searching for EGX70...")
    print([s for s in symbols if "EGX70" in s])
    
    print("Searching for EGX100...")
    print([s for s in symbols if "EGX100" in s])
    
except Exception as e:
    print(f"Failed: {e}")
