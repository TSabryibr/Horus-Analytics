from core.settings import settings
from data_engine.mubasher_sqlite_source import build_paths, list_history_symbols
from pathlib import Path

try:
    paths = build_paths(
        Path(settings.MUBASHER_ROOT_DIR),
        user_id=(settings.MUBASHER_USER_ID or None),
    )
    symbols = list_history_symbols(paths)
    
    # Let's find anything with "70", "100", or "EWI" in it
    print("Searching for anything with 70:")
    print([s for s in symbols if "70" in s])
    
    print("Searching for anything with 100:")
    print([s for s in symbols if "100" in s])
    
    print("Searching for anything with EWI:")
    print([s for s in symbols if "EWI" in s])
    
except Exception as e:
    print(f"Failed: {e}")
