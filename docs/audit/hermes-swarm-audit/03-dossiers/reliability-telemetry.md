# Layer 3: Reliability Telemetry, Error Logs & Test Regressions

**Author:** `site-reliability-engineer`  
**System:** Horus Analytics II (`c:\Users\TSabr\Horus\Horus-Analytics-II`)

---

## 1. Raw Telemetry: Missing Schema Table Failure Cascade

**Log File Reference:** [`api_errors.log.1`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/api_errors.log.1) (5.2 MB)  
**Sample Traceback:**
```text
Traceback (most recent call last):
  File "C:\Users\TSabr\AppData\Local\Programs\Python\Python313\Lib\site-packages\peewee.py", line 3322, in execute_sql
    cursor.execute(sql, params or ())
peewee.OperationalError: no such table: signalguardstate

During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "core\signals\guard.py", line 27, in get_guard_state
    state, _ = SignalGuardState.get_or_create(name="PUBLISH")
  File "C:\Users\TSabr\AppData\Local\Programs\Python\Python313\Lib\site-packages\peewee.py", line 6873, in get_or_create
    return query.get(), False
  File "C:\Users\TSabr\AppData\Local\Programs\Python\Python313\Lib\site-packages\peewee.py", line 7297, in get
    return clone.execute(database)[0]
  File "C:\Users\TSabr\AppData\Local\Programs\Python\Python313\Lib\site-packages\peewee.py", line 3088, in __exit__
    reraise(new_type, new_type(exc_value, *exc_args), traceback)
peewee.OperationalError: no such table: signalguardstate
```
**SRE Finding:** This error re-occurred every 30 seconds when `followup_processing` or `trade_monitor` triggered before `initialize_db()` completed or when testing on clean database fixtures.

---

## 2. Raw Telemetry: PyInstaller Build Crash Traceback

**Log File Reference:** [`crash_report.txt`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/crash_report.txt)
```text
Traceback (most recent call last):
  File "api.py", line 69, in <module>
    from routes import system, data, portfolio, analytics, settings, simulation, scanner, strategy, live, signals, reports, ai_report
  File "pyimod02_importers.py", line 457, in exec_module
  File "routes\settings.py", line 7, in <module>
    import ReportGenerator
  File "pyimod02_importers.py", line 457, in exec_module
  File "ReportGenerator.py", line 2, in <module>
    import matplotlib.pyplot as plt
  File "pyimod02_importers.py", line 457, in exec_module
  File "matplotlib\__init__.py", line 161, in <module>
  File "pyimod02_importers.py", line 457, in exec_module
  File "matplotlib\rcsetup.py", line 29, in <module>
  File "pyimod02_importers.py", line 457, in exec_module
  File "matplotlib\_fontconfig_pattern.py", line 15, in <module>
  File "pyimod02_importers.py", line 457, in exec_module
  File "pyparsing\__init__.py", line 156, in <module>
  File "pyimod02_importers.py", line 457, in exec_module
  File "pyparsing\testing.py", line 6, in <module>
ModuleNotFoundError: No module named 'unittest'
[PYI-56904:ERROR] Failed to execute script 'api' due to unhandled exception!
```

---

## 3. Failed Test Suite Breakdown (98 Failures)

**Source File:** [`failed_tests_r2.txt`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/failed_tests_r2.txt) (Total: 98 failures / 503 tests)

### Category A: Portfolio Management & Intake Calculation Regressions (28 tests)
- `tests/test_portfolio_management_service.py::test_portfolio_management_intake_and_report_builds_tp2`
- `tests/test_portfolio_management_service.py::test_portfolio_management_intake_supports_total_cost`
- `tests/test_portfolio_management_service.py::test_portfolio_management_intake_skips_blocked_ticker`
- `tests/test_portfolio_operations.py::TestTradeLifecycle::test_add_trade_blacklisted_ticker_blocked`
- `tests/test_portfolio_operations.py::TestTradeLifecycle::test_add_trade_new_position`
- `tests/test_portfolio_remaining.py::TestPortfolioEdgeCases::test_add_trade_missing_ticker_validation`
- `tests/test_precision_coverage.py::TestPortfolioManagement::test_parse_holding_input_from_total_cost`

### Category B: Signals CRUD & Guard State (24 tests)
- `tests/test_signals_coverage.py::TestGuardState::test_get_guard_state`
- `tests/test_signals_coverage.py::TestGuardState::test_set_guard_state_block`
- `tests/test_signals_coverage.py::TestRunDailySignals::test_run_daily_guard_blocked`
- `tests/test_signals_coverage.py::TestRunDailySignals::test_run_daily_freshness_blocked`
- `tests/test_signals_coverage.py::TestClientManagement::*` (Client & API key creation tests)

### Category C: Risk Management & Correlation Matrix (15 tests)
- `tests/test_risk_manager.py::test_correlation_matrix_returns_dataframe`
- `tests/test_risk_manager.py::test_check_new_trade_correlation_safe`
- `tests/test_autotrader_mechanisms.py::TestAutoTraderMechanisms::test_correlation_deadbolt`

### Category D: Ingestion & Parquet Compaction (12 tests)
- `tests/test_ingest_ticks.py::test_ingest_ticks_writes_parquet`
- `tests/test_partitioned_parquet_compaction.py::test_partitioned_append_and_compaction_flow`

---

## 4. APScheduler Concurrency & Overlap Profile

```
Job ID: scheduled_trade_monitor
  - Frequency: Every 30 seconds
  - Max Instances: 2 (Allows concurrent instances!)
  - Lock Impact: Holds SQLite write lock while evaluating trailing stops and updating position PnL.

Job ID: scheduled_followup_processing
  - Frequency: Every 30 seconds
  - Max Instances: 1
  - Lock Impact: Writes to PublishedSignalFollowUp and SignalDelivery tables.

Job ID: scheduled_daily_signal_pipeline
  - Frequency: Daily at 14:45 Cairo Time
  - Lock Impact: Heavy batch insert of daily scan signals across all 240+ EGX tickers.
```
