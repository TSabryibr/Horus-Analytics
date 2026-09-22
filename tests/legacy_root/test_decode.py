from core.settings import settings
from pathlib import Path
from data_engine.metastock_dat_source import read_history_file

p = Path(settings.METASTOCK_DAT_HISTORY_FOLDER) / "F83.DAT"
df = read_history_file(p)
print(f"Total rows decoded: {len(df)}")
print(df.tail())
print(df.head())
