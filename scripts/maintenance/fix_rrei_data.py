import pandas as pd
from pathlib import Path

file_path = Path("data/EGX/history/RREI.parquet")
if file_path.exists():
    df = pd.read_parquet(file_path)
    # Remove any bars from the future (e.g. > 2027)
    original_len = len(df)
    df = df[df.index < pd.Timestamp("2027-01-01")]
    new_len = len(df)
    if original_len != new_len:
        print(f"Removed {original_len - new_len} future bars from RREI.parquet")
        df.to_parquet(file_path, compression="snappy")
    else:
        print("No future bars found in RREI.parquet")
else:
    print("RREI.parquet not found")
