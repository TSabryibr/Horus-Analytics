from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BATCHES: dict[int, list[str]] = {
    1: [
        "tests/backend/test_exclusion_manager.py",
        "tests/test_ai_asset_report.py",
        "tests/test_ai_daily_report.py",
        "tests/test_ai_report_boundary_service.py",
        "tests/test_ai_report_generation_service.py",
        "tests/test_ai_report_lifecycle.py",
        "tests/test_ai_report_snapshot_service.py",
        "tests/test_ai_report_transport_service.py",
        "tests/test_alpha_sentiment.py",
        "tests/test_analysis_reports.py",
        "tests/test_analytics_coverage.py",
        "tests/test_analytics_new_features.py",
        "tests/test_api_contract_full_app.py",
        "tests/test_api_endpoints.py",
        "tests/test_api_runner_config.py",
        "tests/test_autotrader.py",
        "tests/test_autotrader_mechanisms.py",
        "tests/test_backend_multithreading.py",
        "tests/test_broadcast_reliability.py",
        "tests/test_broadcast_simulation.py",
    ],
    2: [
        "tests/test_build_exe.py",
        "tests/test_data_engine_api_cache.py",
        "tests/test_data_engine_intraday_store_api.py",
        "tests/test_data_freshness_canonical.py",
        "tests/test_data_quality_dlq.py",
        "tests/test_datamanager.py",
        "tests/test_deduplication_simulate.py",
        "tests/test_deep_coverage.py",
        "tests/test_treasury_ledger.py",
        "tests/test_dryrun_engine.py",
        "tests/test_egx_microstructure_contract.py",
        "tests/test_enforcement_calibration.py",
        "tests/test_enforcement_gates.py",
        "tests/test_error_paths.py",
        "tests/test_execution_model.py",
        "tests/test_momentum_breakout_scanner.py",
        "tests/test_final_coverage.py",
        "tests/test_frontend_ci_hardening.py",
        "tests/test_frontend_static_routes.py",
        "tests/test_health_routes.py",
    ],
    3: [
        "tests/test_heat_type_safety.py",
        "tests/test_helheim_casket.py",
        "tests/test_historical_backfill.py",
        "tests/test_horus_execution_service.py",
        "tests/test_horus_identity_service.py",
        "tests/test_horus_monitor_service.py",
        "tests/test_horus_reporting_integration.py",
        "tests/test_horus_signal_intake_service.py",
        "tests/test_horus_spec.py",
        "tests/test_ingest_history_incremental.py",
        "tests/test_ingest_history_logging.py",
        "tests/test_ingest_intraday_incremental.py",
        "tests/test_ingest_ticks.py",
        "tests/test_sandbox_registry.py",
        "tests/test_live_and_simulation.py",
        "tests/test_live_feed_manager.py",
        "tests/test_live_streaming_zmq.py",
        "tests/test_local_feed_selector.py",
        "tests/test_logger_format.py",
        "tests/test_market_predictor.py",
    ],
    4: [
        "tests/test_market_watchdog_registration.py",
        "tests/test_walk_forward_validation.py",
        "tests/test_monte_carlo.py",
        "tests/test_mubasher_realtime_source.py",
        "tests/test_mubasher_sqlite_source.py",
        "tests/test_no_container_runtime.py",
        "tests/test_observability_and_metadata.py",
        "tests/test_partitioned_parquet_compaction.py",
        "tests/test_phase2_risk_contract.py",
        "tests/test_pine_comment_filter.py",
        "tests/test_pine_logic_import.py",
        "tests/test_pine_profile_promotion.py",
        "tests/test_pipeline_stale_mode.py",
        "tests/test_pipeline_state_snapshot.py",
        "tests/test_pipeline_worker.py",
        "tests/test_portfolio_audit.py",
        "tests/test_portfolio_command_service.py",
        "tests/test_portfolio_csv_backup.py",
        "tests/test_portfolio_identity_service.py",
        "tests/test_portfolio_import_export_service.py",
    ],
    5: [
        "tests/test_portfolio_management_service.py",
        "tests/test_portfolio_management_service_seams.py",
        "tests/test_portfolio_operations.py",
        "tests/test_portfolio_query_service.py",
        "tests/test_portfolio_remaining.py",
        "tests/test_portfolio_simulator_microstructure.py",
        "tests/test_position_tracker.py",
        "tests/test_precision_coverage.py",
        "tests/test_price_action_executor.py",
        "tests/test_price_action_models.py",
        "tests/test_price_action_routes.py",
        "tests/test_provider_selection_service.py",
        "tests/test_provisioning_state.py",
        "tests/test_published_signal_lifecycle.py",
        "tests/test_ragnarok_simulator.py",
        "tests/test_sentiment_crawler.py",
        "tests/test_regime_router.py",
        "tests/test_replay_engine.py",
        "tests/test_report_generator_excel.py",
        "tests/test_risk_manager.py",
    ],
    6: [
        "tests/test_routes_settings.py",
        "tests/test_routes_simulation.py",
        "tests/test_runtime_ticker_quarantine.py",
        "tests/test_scanner_and_data.py",
        "tests/test_session_mode.py",
        "tests/test_settings_crud.py",
        "tests/test_settings_offsets.py",
        "tests/test_signal_channel_policy.py",
        "tests/test_signal_engine.py",
        "tests/test_signal_executor.py",
        "tests/test_signal_followup_queue.py",
        "tests/test_signal_validation.py",
        "tests/test_signals_boundary_service.py",
        "tests/test_signals_coverage.py",
        "tests/test_signals_desk.py",
        "tests/test_signals_outcomes_service.py",
        "tests/test_signals_p0.py",
        "tests/test_signals_publish_service.py",
        "tests/test_signals_run_service.py",
    ],
    7: [
        "tests/test_simulation_performance.py",
        "tests/test_simulator_room_contract.py",
        "tests/test_startup_browser_autolaunch.py",
        "tests/test_strategy_and_system.py",
        "tests/test_strategy_audit.py",
        "tests/test_subscription_productization.py",
        "tests/test_swift_strategy_core.py",
        "tests/test_sync_parallelism.py",
        "tests/test_system_security.py",
        "tests/test_telegram_broadcast.py",
        "tests/test_telegram_followups.py",
        "tests/test_time_utils.py",
        "tests/test_v1_coverage_gap.py",
        "tests/test_whale_trap_metadata_contract.py",
        "tests/test_whale_trap_seams.py",
    ],
    8: [
        "tests/test_action_matrix_remediations.py",
        "tests/test_auth_boundaries.py",
        "tests/test_backend_test_suite_coverage.py",
        "tests/test_broker_order_manager.py",
        "tests/test_confluence_engine.py",
        "tests/test_currency_fetcher.py",
        "tests/test_domain_services.py",
        "tests/test_excel_generator.py",
        "tests/test_harvester_service.py",
        "tests/test_intraday_pipeline_fixes.py",
        "tests/test_lifespan_provisioning.py",
        "tests/test_live_scan_alignment.py",
        "tests/test_live_scans_and_stale_report_fixes.py",
        "tests/test_manipulation_sentry.py",
        "tests/test_morning_daily_signal.py",
        "tests/test_operational_readiness.py",
        "tests/test_phase3_harvester_power_scheduler.py",
        "tests/test_phase4_adversarial_verification.py",
        "tests/test_phase4_disaster_recovery.py",
        "tests/test_phase5_compute_universe_sla.py",
        "tests/test_portfolio_enhancements_backend.py",
        "tests/test_portfolio_excel_export.py",
        "tests/test_portfolio_queries.py",
        "tests/test_portfolio_routes_enhancements.py",
    ],
    9: [
        "tests/test_pre_scanner_middleware.py",
        "tests/test_preclose_freshness_notice.py",
        "tests/test_purchasing_power_filter.py",
        "tests/test_realtime_streamer.py",
        "tests/test_redis_client.py",
        "tests/test_replay_recursion.py",
        "tests/test_route_service_wiring.py",
        "tests/test_rvu_scanner.py",
        "tests/test_schemas.py",
        "tests/test_session_closing_catchup.py",
        "tests/test_shadow_execution.py",
        "tests/test_shadow_live.py",
        "tests/test_signal_delivery_dispatcher.py",
        "tests/test_signal_dispatcher.py",
        "tests/test_signal_rate_limiter.py",
        "tests/test_signal_sla_and_watchdog.py",
        "tests/test_signal_telemetry.py",
        "tests/test_slippage_reconciler.py",
        "tests/test_subscriber_template.py",
        "tests/test_tracing.py",
        "tests/test_treasury_ledger_usd.py",
        "tests/test_usd_feed.py",
        "tests/test_worker_pool.py",
    ],
}


def get_discoverable_test_files() -> set[str]:
    """Find all active test files in tests/, excluding legacy and browser-only tests."""
    return {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "tests").rglob("test_*.py")
        if "legacy_root" not in p.as_posix() and "playwright_router_test" not in p.as_posix()
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Horus backend pytest suite in stable batches.",
        epilog="Extra pytest args can be passed after --, for example: python scripts/run_backend_tests.py --batch 6 -- --maxfail=1",
    )
    parser.add_argument(
        "--batch",
        action="append",
        type=int,
        choices=sorted(BATCHES),
        help="Run only a specific batch. Can be supplied more than once.",
    )
    parser.add_argument("--collect-only", action="store_true", help="Collect tests without executing them.")
    parser.add_argument("--check-coverage", action="store_true", help="Verify all discoverable test files are accounted for in BATCHES.")
    parser.add_argument("--durations", type=int, default=10, help="Pass --durations to pytest for each batch.")
    parser.add_argument("--fail-fast", action="store_true", help="Stop after the first failed batch.")
    parser.add_argument("--list", action="store_true", help="List batches and exit.")
    parser.add_argument(
        "--log-dir",
        default=str(ROOT / "test-results" / "backend"),
        help="Directory for per-batch logs.",
    )
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Extra pytest arguments after --.")
    return parser.parse_args()


def stream_command(command: list[str], *, env: dict[str, str], log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            log_file.write(line)
        return process.wait()


def build_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("HORUS_DISABLE_READINESS_GATE", "1")
    env.setdefault("HORUS_DISABLE_STARTUP_THREAD", "1")
    env.setdefault("SKIP_STARTUP_SYNC", "true")
    env.setdefault("LIVE_ARM_GUARD_ENABLED", "0")
    env.setdefault(
        "HORUS_SETTINGS_FILE",
        str(Path(tempfile.gettempdir()) / f"horus_backend_tests_settings_{os.getpid()}.json"),
    )
    return env


def main() -> int:
    args = parse_args()
    if args.check_coverage:
        discoverable = get_discoverable_test_files()
        batched = {f.replace("\\", "/") for b in BATCHES.values() for f in b}
        missing = sorted(discoverable - batched)
        unknown = sorted(batched - discoverable)
        if missing or unknown:
            if missing:
                print(f"Error: {len(missing)} active test file(s) are missing from BATCHES:")
                for f in missing:
                    print(f"  + {f}")
            if unknown:
                print(f"Warning: {len(unknown)} file(s) in BATCHES no longer exist on disk:")
                for f in unknown:
                    print(f"  - {f}")
            return 1
        print(f"Coverage check passed: all {len(discoverable)} active test files are mapped to BATCHES.")
        return 0

    if args.list:
        for batch_id, files in BATCHES.items():
            print(f"Batch {batch_id}: {len(files)} files")
            for file_name in files:
                print(f"  {file_name}")
        return 0

    extra_args = list(args.pytest_args)
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]

    batch_ids = args.batch or sorted(BATCHES)
    env = build_env()
    log_dir = Path(args.log_dir)
    results: list[tuple[int, int, float, Path]] = []

    for batch_id in batch_ids:
        command = [sys.executable, "-m", "pytest", "-q", *BATCHES[batch_id]]
        if args.collect_only:
            command.append("--collect-only")
        if args.durations >= 0 and not args.collect_only:
            command.append(f"--durations={args.durations}")
        command.extend(extra_args)

        log_path = log_dir / f"batch-{batch_id}.log"
        print(f"\n=== Backend batch {batch_id}/{max(BATCHES)} ===")
        print(" ".join(command))
        started = time.perf_counter()
        return_code = stream_command(command, env=env, log_path=log_path)
        elapsed = time.perf_counter() - started
        results.append((batch_id, return_code, elapsed, log_path))

        if return_code != 0 and args.fail_fast:
            break

    print("\n=== Backend test summary ===")
    failed = False
    for batch_id, return_code, elapsed, log_path in results:
        status = "PASS" if return_code == 0 else f"FAIL({return_code})"
        failed = failed or return_code != 0
        print(f"Batch {batch_id}: {status} in {elapsed:.1f}s | {log_path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
