from core.settings import settings
from core.exclusions import get_all_exclusions
from pathlib import Path


def test_csv_history_ingest_warns_and_summarizes_missing_files(monkeypatch, capsys):
    from data_engine import ingest_history

    missing_file = Path("MISSING.csv")

    class FakeHistoryPath:
        def exists(self):
            return True

        def glob(self, pattern):
            assert pattern == "*.csv"
            return [missing_file]

    monkeypatch.setattr("data_engine.ingest_history.Path", lambda value: FakeHistoryPath())
    monkeypatch.setattr(settings, "METASTOCK_HISTORY_FOLDER", "fake-history", raising=False)
    monkeypatch.setattr("data_engine.ingest_history.get_all_exclusions", lambda: set())
    monkeypatch.setattr("data_engine.ingest_history.is_supported_ticker", lambda ticker: True)
    monkeypatch.setattr("data_engine.ingest_history._get_last_parquet_date", lambda ticker: None)
    monkeypatch.setattr("data_engine.ingest_history._read_csv_last_date", lambda path: None)

    def raise_missing(*args, **kwargs):
        raise FileNotFoundError("missing source")

    monkeypatch.setattr("data_engine.ingest_history.pd.read_csv", raise_missing)

    updated = ingest_history._ingest_history_from_csv()

    output = capsys.readouterr().out
    assert updated == 0
    assert "[Warn] Skipped missing history CSV MISSING.csv" in output
    assert "history CSV ingest completed: updated=0 missing=1 failed=0" in output

