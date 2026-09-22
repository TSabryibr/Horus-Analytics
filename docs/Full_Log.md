INFO:     Started server process [16100]
INFO:     Waiting for application startup.
2026-05-17 09:41:31,331 - horus.audit - INFO - Audit: AuditLog table created.
2026-05-17 09:41:31,333 - horus.api - INFO - [Startup] Ollama AI report runtime is managed on demand. Startup warmup skipped.
INFO:     Application startup complete.
2026-05-17 09:41:31,410 - horus.api - INFO - [Startup] Local provider auto-selection disabled. LOCAL_FEED_PROVIDER=AUTO history=CSV intraday=CSV
INFO:     Uvicorn running on http://127.0.0.1:8100 (Press CTRL+C to quit)
2026-05-17 09:41:31,486 - horus.api - INFO - [Startup] Purging 39 excluded tickers from DB...
2026-05-17 09:41:31,529 - horus.api - INFO - [Startup] Exclusion purge counts: {'positions': 0, 'trades': 0, 'signals': 0, 'signal_recommendations': 0, 'signal_outcomes': 0, 'ticker_strategy_metrics': 0}
2026-05-17 09:41:31,574 - horus.api - INFO - [Startup] Global initialization complete.
2026-05-17 09:41:31,618 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,621 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,622 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,623 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,624 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,625 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,626 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,627 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,627 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,628 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,629 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,630 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,631 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,631 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,632 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,633 - apscheduler.scheduler - INFO - Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-05-17 09:41:31,634 - horus.api - INFO - [Startup] Session mode jobs registered: LIVE at 09:30 (trading days), ANALYSIS at 14:30.
2026-05-17 09:41:31,678 - apscheduler.scheduler - INFO - Added job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog" to job store "default"
2026-05-17 09:41:31,679 - apscheduler.scheduler - INFO - Added job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog" to job store "default"
2026-05-17 09:41:31,680 - apscheduler.scheduler - INFO - Added job "scheduled_intraday_scan" to job store "default"
2026-05-17 09:41:31,681 - apscheduler.scheduler - INFO - Added job "scheduled_pre_close_scan" to job store "default"
2026-05-17 09:41:31,682 - apscheduler.scheduler - INFO - Added job "scheduled_daily_signal_scan" to job store "default"
2026-05-17 09:41:31,683 - apscheduler.scheduler - INFO - Added job "scheduled_trade_monitor" to job store "default"
2026-05-17 09:41:31,683 - apscheduler.scheduler - INFO - Added job "scheduled_daily_signal_pipeline" to job store "default"
2026-05-17 09:41:31,684 - apscheduler.scheduler - INFO - Added job "scheduled_failed_delivery_retry" to job store "default"
2026-05-17 09:41:31,685 - apscheduler.scheduler - INFO - Added job "scheduled_weekly_walkforward_validation" to job store "default"
2026-05-17 09:41:31,686 - apscheduler.scheduler - INFO - Added job "scheduled_wfa_metrics_update" to job store "default"
2026-05-17 09:41:31,687 - apscheduler.scheduler - INFO - Added job "scheduled_system_audit" to job store "default"
2026-05-17 09:41:31,688 - apscheduler.scheduler - INFO - Added job "scheduled_daily_ai_report_dispatch" to job store "default"
2026-05-17 09:41:31,689 - apscheduler.scheduler - INFO - Added job "scheduled_weekly_analysis_report_dispatch" to job store "default"
2026-05-17 09:41:31,690 - apscheduler.scheduler - INFO - Added job "scheduled_monthly_analysis_report_dispatch" to job store "default"
2026-05-17 09:41:31,690 - apscheduler.scheduler - INFO - Added job "scheduled_enter_live_mode" to job store "default"
2026-05-17 09:41:31,691 - apscheduler.scheduler - INFO - Added job "scheduled_enter_analysis_mode" to job store "default"
2026-05-17 09:41:31,692 - apscheduler.scheduler - INFO - Scheduler started
2026-05-17 09:41:31,694 - horus.api - INFO - [Startup] Scheduler Started.
2026-05-17 09:41:31,749 - horus.scheduling - INFO - [Scheduler] Edge Pipeline Watcher started on reports\edge_pipeline\validation
2026-05-17 09:41:31,790 - horus.api - INFO - [Startup] Session mode config=LIVE forced=false effective=LIVE reason=live_window
Horus is ready at http://localhost:8100
Open frontend in your browser now? [y/N] y
2026-05-17 09:41:37,304 - horus.api - INFO - [SyncWorker] Started.
2026-05-17 09:41:37,304 - horus.api - INFO - [Startup] Adaptive sync worker started (mode=internal).
2026-05-17 09:41:37,389 - horus.api - INFO - [SyncWorker] Data not fresh (state=DEGRADED, history_ratio=0.0, intraday_ratio=0.0). Running sync_all...
2026-05-17 09:41:37,411 - TelegramBot - INFO - Starting Telegram Command Listener...
2026-05-17 09:41:37,411 - horus.api - INFO - [Startup] Telegram command listener started.
--- Starting Data Lake Synchronization ---
{"ts":"2026-05-17T06:41:37+00:00","event":"pipeline.sync.start","realm":"EGX","intraday_provider":"CSV","intraday_provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"}},"history_provider":"CSV","history_provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"}},"ticks_provider":"MUBASHER_DB","ticks_provider_context":{"provider":"MUBASHER_DB","reason":"configured_ticks_provider","fallback_from":null,"evidence":{"configured_provider":"MUBASHER_DB"}}}
[LocalFeed] Provider policy intraday=CSV, history=CSV

[Parallel] Dispatching Intraday, History, and Ticks sync stages...INFO:     127.0.0.1:53565 - "GET / HTTP/1.1" 200 OK


[1/3] Syncing Intraday (1min)...
[2/3] Syncing History (Daily)...
[3/3] Market is CLOSED. Skipping Tick Sync.INFO:     127.0.0.1:53565 - "GET /_next/static/chunks/0.k_9iy9n5xfe.css HTTP/1.1" 200 OK



INFO:     127.0.0.1:57318 - "GET /_next/static/chunks/0fldi-4fgo6om.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:54161 - "GET /_next/static/chunks/112-5li8x88or.js HTTP/1.1" 200 OK
[Info] Found 312 history CSV files to ingest.[Info] Found 273 intraday CSV files to ingest.INFO:     127.0.0.1:57318 - "GET /_next/static/chunks/0ex4.~rziiv.s.js HTTP/1.1" 200 OK


INFO:     127.0.0.1:53565 - "GET /_next/static/chunks/0l1_47-31-frg.js HTTP/1.1" 200 OK
[Success] Saved 2725 total rows for AALR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AALR.parquetINFO:     127.0.0.1:54301 - "GET /_next/static/chunks/07uz2g0_38qia.js HTTP/1.1" 200 OK

INFO:     127.0.0.1:55680 - "GET /_next/static/chunks/0-6oq2baer~7r.js HTTP/1.1" 200 OK
[Success] Saved 5230 total rows for ABUK to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ABUK.parquetINFO:     127.0.0.1:59619 - "GET /_next/static/chunks/turbopack-0midtuni~1h87.js HTTP/1.1" 200 OK

INFO:     127.0.0.1:54161 - "GET /_next/static/chunks/01tjzl_j4g1d_.js HTTP/1.1" 200 OK
[Success] Saved 1906 total rows for ACAMD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACAMD.parquetINFO:     127.0.0.1:57318 - "GET /_next/static/chunks/0huuykmf09wip.js HTTP/1.1" 200 OK

INFO:     127.0.0.1:54301 - "GET /_next/static/chunks/0jl8ply017rwj.js HTTP/1.1" 200 OK
[Success] Saved 718 total rows for ACAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACAP.parquetINFO:     127.0.0.1:59619 - "GET /_next/static/chunks/0xq0lhl8~gozj.js HTTP/1.1" 200 OK

INFO:     127.0.0.1:55680 - "GET /_next/static/chunks/14d95v2q-d4b-.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:54161 - "GET /_next/static/chunks/0ppu8ust56k.u.js HTTP/1.1" 200 OK
[Success] Saved 5453 total rows for ACGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACGC.parquetINFO:     127.0.0.1:53565 - "GET /_next/static/chunks/139sbmt_wxpui.js HTTP/1.1" 200 OK

INFO:     127.0.0.1:57318 - "GET /_next/static/chunks/0cgs-q5irvwtw.js HTTP/1.1" 200 OK
[Success] Saved 4302 total rows for ACRO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACRO.parquetINFO:     127.0.0.1:59619 - "GET /_next/static/chunks/01n2.srkf_uh0.js HTTP/1.1" 200 OK

[Success] Saved 437 total rows for ACTF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACTF.parquetINFO:     127.0.0.1:57318 - "GET /android-chrome-192x192.png HTTP/1.1" 200 OK

INFO:     127.0.0.1:59619 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
[Success] Saved 4497 total rows for ADCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADCI.parquet
[Success] Saved 5386 total rows for ADIB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADIB.parquet
[Success] Saved 2386 total rows for ADPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADPC.parquet
[Success] Saved 2555 total rows for ADRI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADRI.parquet
[Success] Saved 5393 total rows for AFDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AFDI.parquet
[Success] Saved 5158 total rows for AFMC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AFMC.parquet
[Success] Saved 188 total rows for AIDC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AIDC.parquet
[Success] Saved 3207 total rows for AIFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AIFI.parquet
[Success] Saved 1210 total rows for AIHC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AIHC.parquet
[Success] Saved 3691 total rows for AJWA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AJWA.parquet
[Success] Saved 4819 total rows for ALCN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ALCN.parquet
[Success] Saved 3353 total rows for ALEX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ALEX.parquet
[Success] Saved 4300 total rows for ALUM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ALUM.parquet
[Success] Saved 3710 total rows for AMER to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMER.parquet
[Success] Saved 2647 total rows for AMES to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMES.parquet
[Success] Saved 10 total rows for AMES_R2 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMES_R2.parquet
[Success] Saved 3909 total rows for AMIA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMIA.parquet
[Success] Saved 4986 total rows for AMOC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMOC.parquet
[Success] Saved 3089 total rows for AMPI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMPI.parquet
[Success] Saved 2106 total rows for ANFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ANFI.parquet
[Success] Saved 1258 total rows for APPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\APPC.parquet
[Success] Saved 2958 total rows for APSW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\APSW.parquet
[Success] Saved 2569 total rows for ARAB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARAB.parquet
[Success] Saved 5 total rows for ARAB_R2 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARAB_R2.parquet
[Success] Saved 2903 total rows for ARCC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARCC.parquet
[Success] Saved 4428 total rows for AREH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AREH.parquet
[Success] Saved 3783 total rows for ARVA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARVA.parquet
[Success] Saved 4642 total rows for ASCM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ASCM.parquet
[Success] Saved 4306 total rows for ASPI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ASPI.parquet
[Success] Saved 1944 total rows for ATLC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ATLC.parquet
[Success] Saved 2766 total rows for ATQA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ATQA.parquet
[Success] Saved 4566 total rows for AXPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AXPH.parquet
[Success] Saved 2219 total rows for BIDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BIDI.parquet
[Success] Saved 3549 total rows for BIGP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BIGP.parquet
[Success] Saved 1914 total rows for BINV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BINV.parquet
[Success] Saved 3834 total rows for BIOC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BIOC.parquet
[Success] Saved 201 total rows for BONY to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BONY.parquet
[Success] Saved 3334 total rows for BTFH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BTFH.parquet
[Success] Saved 2422 total rows for CAED to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CAED.parquet
[Success] Saved 5172 total rows for CANA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CANA.parquet
[Success] Saved 3067 total rows for CCAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CCAP.parquet
[Success] Saved 2980 total rows for CCRS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CCRS.parquet
[Success] Saved 5140 total rows for CEFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CEFM.parquet
[Success] Saved 4796 total rows for CERA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CERA.parquet
[Success] Saved 1068 total rows for CFGH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CFGH.parquet
[Success] Saved 1943 total rows for CICH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CICH.parquet
[Success] Saved 4827 total rows for CIEB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CIEB.parquet
[Success] Saved 3493 total rows for CIRA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CIRA.parquet
[Success] Saved 2402 total rows for CLHO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CLHO.parquet
[Success] Saved 1570 total rows for CNFN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CNFN.parquet
[Success] Saved 5453 total rows for COMI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\COMI.parquet
[Success] Saved 4211 total rows for COPR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\COPR.parquet
[Success] Saved 4499 total rows for COSG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\COSG.parquet
[Success] Saved 4560 total rows for CPCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CPCI.parquet
[Success] Saved 52 total rows for CPME to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CPME.parquet
[Success] Saved 1213 total rows for CRST to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CRST.parquet
[Success] Saved 3069 total rows for CSAG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CSAG.parquet
[Success] Saved 4870 total rows for DAPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DAPH.parquet
[Success] Saved 4304 total rows for DCRC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DCRC.parquet
{"ts":"2026-05-17T06:41:58+00:00","event":"pipeline.stage.complete","stage":"intraday","provider":"CSV","provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":273,"status":"completed"}},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":273,"status":"completed"},"updated_symbols":273}
[Success] Saved 3423 total rows for DEIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DEIN.parquet
[Success] Saved 622 total rows for DGTZ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DGTZ.parquet
[Success] Saved 774 total rows for DIFC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DIFC.parquet
[Success] Saved 2382 total rows for DOMT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DOMT.parquet
[Success] Saved 1999 total rows for DSCW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DSCW.parquet
[Success] Saved 3107 total rows for DTPP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DTPP.parquet
[Success] Saved 2398 total rows for EALR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EALR.parquet
[Success] Saved 3626 total rows for EASB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EASB.parquet
[Success] Saved 5046 total rows for EAST to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EAST.parquet
[Success] Saved 1493 total rows for EBSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EBSC.parquet
[Success] Saved 5431 total rows for ECAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ECAP.parquet
[Success] Saved 2650 total rows for EDFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EDFM.parquet
[Success] Saved 3255 total rows for EEII to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EEII.parquet
[Success] Saved 5424 total rows for EFIC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EFIC.parquet
[Success] Saved 2491 total rows for EFID to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EFID.parquet
[Success] Saved 1108 total rows for EFIH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EFIH.parquet
[Success] Saved 5026 total rows for EGAL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGAL.parquet
[Success] Saved 5026 total rows for EGAS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGAS.parquet
[Success] Saved 5153 total rows for EGBE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGBE.parquet
[Success] Saved 5055 total rows for EGCH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGCH.parquet
[Success] Saved 743 total rows for EGREF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGREF.parquet
[Success] Saved 4417 total rows for EGSA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGSA.parquet
[Success] Saved 3057 total rows for EGTS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGTS.parquet
{"ts":"2026-05-17T06:42:01+00:00","event":"pipeline.data_quality.rejected_rows","ticker":"EGX100 EWI","stream":"history","realm":"EGX","rejected_rows":6,"input_rows":4928,"dlq_path":"C:\\Users\\TSabr\\Horus\\Horus-Analytics-II\\dist\\HorusApp\\data\\EGX\\dlq\\history\\EGX100 EWI.parquet","rejection_reason_counts":{"negative_volume":6},"source_note":null}
[Success] Saved 4922 total rows for EGX100 EWI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX100 EWI.parquet
[Success] Saved 3250 total rows for EGX30 CAPPED to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30 CAPPED.parquet
[Success] Saved 4172 total rows for EGX30 TR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30 TR.parquet
[Success] Saved 3073 total rows for EGX30 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30.parquet
2026-05-17 09:42:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:42:01 EEST)" (scheduled at 2026-05-17 09:42:01.625095+03:00)
2026-05-17 09:42:01,638 - horus.scheduling - INFO - [Monitor] skipped: market is closed.
[Success] Saved 1789 total rows for EGX30ETF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30ETF.parquet2026-05-17 09:42:01,740 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:42:31 EEST)" executed successfully

[Success] Saved 194 total rows for EGX35-LV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX35-LV.parquet
[Success] Saved 4434 total rows for EGX70 EWI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX70 EWI.parquet
[Success] Saved 4710 total rows for EHDR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EHDR.parquet
[Success] Saved 1272 total rows for EITP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EITP.parquet
[Success] Saved 5435 total rows for ELEC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELEC.parquet
[Success] Saved 5144 total rows for ELKA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELKA.parquet
[Success] Saved 2576 total rows for ELNA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELNA.parquet
[Success] Saved 5447 total rows for ELSH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELSH.parquet
[Success] Saved 3235 total rows for ELWA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELWA.parquet
[Success] Saved 2639 total rows for EMFD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EMFD.parquet
[Success] Saved 5116 total rows for ENGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ENGC.parquet
[Success] Saved 1569 total rows for EOSB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EOSB.parquet
[Success] Saved 5281 total rows for EPCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EPCO.parquet
[Success] Saved 2493 total rows for EPPK to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EPPK.parquet
[Success] Saved 1211 total rows for ESAC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ESAC.parquet
[Success] Saved 5277 total rows for ESRS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ESRS.parquet
[Success] Saved 3074 total rows for ETEL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ETEL.parquet
[Success] Saved 4663 total rows for ETRS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ETRS.parquet
[Success] Saved 5411 total rows for EXPA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EXPA.parquet
[Success] Saved 4829 total rows for FAIT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FAIT.parquet
[Success] Saved 5121 total rows for FAITA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FAITA.parquet
[Success] Saved 26 total rows for FCMD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FCMD.parquet
[Success] Saved 683 total rows for FERC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FERC.parquet
[Success] Saved 1638 total rows for FIRE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FIRE.parquet
[Success] Saved 2012 total rows for FNAR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FNAR.parquet
[Success] Saved 585 total rows for FTNS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FTNS.parquet
[Success] Saved 1643 total rows for FWRY to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FWRY.parquet
[Success] Saved 3011 total rows for GBCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GBCO.parquet
[Success] Saved 1115 total rows for GDWA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GDWA.parquet
{"ts":"2026-05-17T06:42:05+00:00","event":"pipeline.data_quality.rejected_rows","ticker":"GGCC","stream":"history","realm":"EGX","rejected_rows":167,"input_rows":5391,"dlq_path":"C:\\Users\\TSabr\\Horus\\Horus-Analytics-II\\dist\\HorusApp\\data\\EGX\\dlq\\history\\GGCC.parquet","rejection_reason_counts":{"invalid_price":167},"source_note":"Legacy vendor source contains zero-price OHLC rows; quarantined as expected."}
[Success] Saved 5224 total rows for GGCC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GGCC.parquet
[Success] Saved 296 total rows for GGRN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GGRN.parquet
[Success] Saved 4426 total rows for GIHD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GIHD.parquet
[Success] Saved 2661 total rows for GMCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GMCI.parquet
[Success] Saved 62 total rows for GOUR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GOUR.parquet
[Success] Saved 1193 total rows for GPIM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GPIM.parquet
[Success] Saved 567 total rows for GPPL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GPPL.parquet
[Success] Saved 2116 total rows for GRCA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GRCA.parquet
[Success] Saved 5095 total rows for GSSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GSSC.parquet
[Success] Saved 461 total rows for GTEX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GTEX.parquet
[Success] Saved 1962 total rows for GTHE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GTHE.parquet
[Success] Saved 2323 total rows for GTWL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GTWL.parquet
[Success] Saved 333 total rows for HBCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HBCO.parquet
[Success] Saved 1106 total rows for HCFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HCFI.parquet
[Success] Saved 5297 total rows for HDBK to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HDBK.parquet
[Success] Saved 5238 total rows for HELI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HELI.parquet
[Success] Saved 5455 total rows for HRHO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HRHO.parquet
[Success] Saved 1419 total rows for IBCT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IBCT.parquet
[Success] Saved 2663 total rows for ICFC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ICFC.parquet
[Success] Saved 4077 total rows for ICID to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ICID.parquet
[Success] Saved 219 total rows for ICLE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ICLE.parquet
[Success] Saved 2930 total rows for IDRE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IDRE.parquet
[Success] Saved 1780 total rows for IEEC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IEEC.parquet
[Success] Saved 3119 total rows for IFAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IFAP.parquet
[Success] Saved 2214 total rows for INEG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\INEG.parquet
[Success] Saved 4412 total rows for INFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\INFI.parquet
[Success] Saved 4604 total rows for IRAX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IRAX.parquet
[Success] Saved 4958 total rows for IRON to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IRON.parquet
[Success] Saved 4326 total rows for ISMA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ISMA.parquet
[Success] Saved 1204 total rows for ISMQ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ISMQ.parquet
[Success] Saved 2044 total rows for ISPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ISPH.parquet
[Success] Saved 3777 total rows for JUFO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\JUFO.parquet
[Success] Saved 5371 total rows for KABO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KABO.parquet
[Success] Saved 230 total rows for KASABF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KASABF.parquet
[Success] Saved 1040 total rows for KRDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KRDI.parquet
[Success] Saved 10 total rows for KRDI_R1 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KRDI_R1.parquet
[Success] Saved 1860 total rows for KWIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KWIN.parquet
[Success] Saved 4559 total rows for KZPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KZPC.parquet
[Success] Saved 4233 total rows for LCSW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\LCSW.parquet
[Success] Saved 715 total rows for LUTS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\LUTS.parquet
[Success] Saved 2313 total rows for MAAL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MAAL.parquet
[Success] Saved 3098 total rows for MASR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MASR.parquet
[Success] Saved 1167 total rows for MBEG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MBEG.parquet
[Success] Saved 5042 total rows for MBSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MBSC.parquet
{"ts":"2026-05-17T06:42:10+00:00","event":"pipeline.data_quality.rejected_rows","ticker":"MCQE","stream":"history","realm":"EGX","rejected_rows":107,"input_rows":5322,"dlq_path":"C:\\Users\\TSabr\\Horus\\Horus-Analytics-II\\dist\\HorusApp\\data\\EGX\\dlq\\history\\MCQE.parquet","rejection_reason_counts":{"invalid_price":107},"source_note":"Legacy vendor source contains zero-price OHLC rows; quarantined as expected."}
[Success] Saved 5215 total rows for MCQE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MCQE.parquet
[Success] Saved 1030 total rows for MCRO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MCRO.parquet
[Success] Saved 20 total rows for MEGM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MEGM.parquet
[Success] Saved 5358 total rows for MENA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MENA.parquet
[Success] Saved 3491 total rows for MEPA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MEPA.parquet
[Success] Saved 2343 total rows for MFPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MFPC.parquet
[Success] Saved 5014 total rows for MFSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MFSC.parquet
[Success] Saved 4237 total rows for MHOT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MHOT.parquet
[Success] Saved 5437 total rows for MICH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MICH.parquet
[Success] Saved 2945 total rows for MILS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MILS.parquet
[Success] Saved 2656 total rows for MIPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MIPH.parquet
[Success] Saved 342 total rows for MISR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MISR.parquet
[Success] Saved 1212 total rows for MKIT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MKIT.parquet
[Success] Saved 2407 total rows for MMAT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MMAT.parquet
[Success] Saved 3005 total rows for MOED to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOED.parquet
[Success] Saved 4356 total rows for MOIL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOIL.parquet
[Success] Saved 4000 total rows for MOIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOIN.parquet
[Success] Saved 1816 total rows for MOSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOSC.parquet
[Success] Saved 2633 total rows for MPCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MPCI.parquet
[Success] Saved 4654 total rows for MPCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MPCO.parquet
[Success] Saved 5442 total rows for MPRC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MPRC.parquet
[Success] Saved 2125 total rows for MTIE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MTIE.parquet
[Success] Saved 4597 total rows for NAHO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NAHO.parquet
[Success] Saved 192 total rows for NAPR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NAPR.parquet
[Success] Saved 1193 total rows for NARE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NARE.parquet
[Success] Saved 3560 total rows for NBKE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NBKE.parquet
[Success] Saved 4695 total rows for NCCW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NCCW.parquet
[Success] Saved 241 total rows for NCGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NCGC.parquet
[Success] Saved 107 total rows for NDRL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NDRL.parquet
[Success] Saved 4671 total rows for NEDA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NEDA.parquet
[Success] Saved 1773 total rows for NHPS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NHPS.parquet
[Success] Saved 3419 total rows for NINH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NINH.parquet
[Success] Saved 4009 total rows for NIPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NIPH.parquet
[Success] Saved 3131 total rows for OBRI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OBRI.parquet
{"ts":"2026-05-17T06:42:14+00:00","event":"pipeline.data_quality.rejected_rows","ticker":"OCDI","stream":"history","realm":"EGX","rejected_rows":32,"input_rows":5410,"dlq_path":"C:\\Users\\TSabr\\Horus\\Horus-Analytics-II\\dist\\HorusApp\\data\\EGX\\dlq\\history\\OCDI.parquet","rejection_reason_counts":{"invalid_price":32},"source_note":"Legacy vendor source contains zero-price OHLC rows; quarantined as expected."}
[Success] Saved 5378 total rows for OCDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OCDI.parquet
[Success] Saved 1126 total rows for OCPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OCPH.parquet
[Success] Saved 4985 total rows for ODIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ODIN.parquet
[Success] Saved 1270 total rows for OFH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OFH.parquet
[Success] Saved 3474 total rows for OIH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OIH.parquet
[Success] Saved 2155 total rows for OLFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OLFI.parquet
[Success] Saved 2708 total rows for ORAS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ORAS.parquet
[Success] Saved 4185 total rows for ORHD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ORHD.parquet
[Success] Saved 5394 total rows for ORWE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ORWE.parquet
[Success] Saved 4597 total rows for PACH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PACH.parquet
[Success] Saved 4887 total rows for PHAR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHAR.parquet
[Success] Saved 4353 total rows for PHDC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHDC.parquet
[Success] Saved 502 total rows for PHGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHGC.parquet
[Success] Saved 3795 total rows for PHTV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHTV.parquet
[Success] Saved 5018 total rows for POUL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\POUL.parquet
[Success] Saved 4860 total rows for PRCL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PRCL.parquet
[Success] Saved 1115 total rows for PRDC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PRDC.parquet
[Success] Saved 3900 total rows for PRMH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PRMH.parquet
[Success] Saved 1200 total rows for QNBE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\QNBE.parquet
[Success] Saved 1938 total rows for RACC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RACC.parquet
[Success] Saved 3047 total rows for RAKT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RAKT.parquet
[Success] Saved 5018 total rows for RAYA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RAYA.parquet
[Success] Saved 1753 total rows for RKAZ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RKAZ.parquet
[Success] Saved 1558 total rows for RMDA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RMDA.parquet
[Success] Saved 1 total rows for RMTV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RMTV.parquet
[Success] Saved 4318 total rows for ROTO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ROTO.parquet
[Success] Saved 3074 total rows for RREI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RREI.parquet
[Success] Saved 4607 total rows for RTVC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RTVC.parquet
[Success] Saved 4204 total rows for RUBX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RUBX.parquet
[Success] Saved 501 total rows for SAIB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SAIB.parquet
[Success] Saved 5236 total rows for SAUD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SAUD.parquet
{"ts":"2026-05-17T06:42:18+00:00","event":"pipeline.data_quality.rejected_rows","ticker":"SCEM","stream":"history","realm":"EGX","rejected_rows":219,"input_rows":5326,"dlq_path":"C:\\Users\\TSabr\\Horus\\Horus-Analytics-II\\dist\\HorusApp\\data\\EGX\\dlq\\history\\SCEM.parquet","rejection_reason_counts":{"invalid_price":219},"source_note":null}
[Success] Saved 5107 total rows for SCEM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SCEM.parquet
[Success] Saved 4025 total rows for SCFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SCFM.parquet
[Success] Saved 1960 total rows for SCTS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SCTS.parquet
[Success] Saved 4733 total rows for SDTI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SDTI.parquet
[Success] Saved 3747 total rows for SEIG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SEIG.parquet
[Success] Saved 1058 total rows for SHARIAH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SHARIAH.parquet
[Success] Saved 2685 total rows for SIPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SIPC.parquet
[Success] Saved 5057 total rows for SKPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SKPC.parquet
[Success] Saved 5205 total rows for SMFR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SMFR.parquet
[Success] Saved 2683 total rows for SMPP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SMPP.parquet
[Success] Saved 4430 total rows for SNFC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SNFC.parquet
[Success] Saved 2101 total rows for SNFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SNFI.parquet
[Success] Saved 64 total rows for SPHT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SPHT.parquet
[Success] Saved 5047 total rows for SPIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SPIN.parquet
[Success] Saved 1713 total rows for SPMD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SPMD.parquet
[Success] Saved 2109 total rows for SUCE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SUCE.parquet
[Success] Saved 4933 total rows for SUGR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SUGR.parquet
[Success] Saved 3069 total rows for SVCE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SVCE.parquet
[Success] Saved 9 total rows for SVCE_R1 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SVCE_R1.parquet
[Success] Saved 4805 total rows for SWDY to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SWDY.parquet
[Success] Saved 1230 total rows for TALM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TALM.parquet
[Success] Saved 1788 total rows for TAMAYUZ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TAMAYUZ.parquet
[Success] Saved 1184 total rows for TANM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TANM.parquet
[Success] Saved 692 total rows for TAQA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TAQA.parquet
[Success] Saved 4459 total rows for TMGH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TMGH.parquet
[Success] Saved 2097 total rows for TORA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TORA.parquet
[Success] Saved 3764 total rows for TRTO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TRTO.parquet
[Success] Saved 122 total rows for TWSA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TWSA.parquet
[Success] Saved 9 total rows for TWSA_R1 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TWSA_R1.parquet
[Success] Saved 969 total rows for TYCN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TYCN.parquet
[Success] Saved 2848 total rows for UASG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UASG.parquet
[Success] Saved 345 total rows for UBEE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UBEE.parquet
[Success] Saved 2442 total rows for UEFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UEFM.parquet
[Success] Saved 5142 total rows for UEGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UEGC.parquet
{"ts":"2026-05-17T06:42:22+00:00","event":"pipeline.data_quality.rejected_rows","ticker":"UNIP","stream":"history","realm":"EGX","rejected_rows":71,"input_rows":4515,"dlq_path":"C:\\Users\\TSabr\\Horus\\Horus-Analytics-II\\dist\\HorusApp\\data\\EGX\\dlq\\history\\UNIP.parquet","rejection_reason_counts":{"invalid_price":71},"source_note":"Legacy vendor source contains zero-price OHLC rows; quarantined as expected."}
[Success] Saved 4444 total rows for UNIP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UNIP.parquet
[Success] Saved 5434 total rows for UNIT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UNIT.parquet
[Success] Saved 1415 total rows for UPMS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UPMS.parquet
[Success] Saved 2238 total rows for UTOP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UTOP.parquet
[Success] Saved 219 total rows for VALU to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VALU.parquet
[Success] Saved 1313 total rows for VERT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VERT.parquet
[Success] Saved 1215 total rows for VLMR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VLMR.parquet
[Success] Saved 1130 total rows for VLMRA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VLMRA.parquet
[Success] Saved 1797 total rows for WATP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\WATP.parquet
[Success] Saved 2739 total rows for WCDF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\WCDF.parquet
[Success] Saved 2586 total rows for WKOL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\WKOL.parquet
[Success] Saved 5444 total rows for ZEOT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ZEOT.parquet
[Success] Saved 4109 total rows for ZMID to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ZMID.parquet
{"ts":"2026-05-17T06:42:24+00:00","event":"pipeline.stage.complete","stage":"history","provider":"CSV","provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":279,"status":"completed"}},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":279,"status":"completed"},"updated_symbols":279}
{"ts":"2026-05-17T06:42:24+00:00","event":"pipeline.compaction.complete","realm":"EGX","folder":"history","compacted":0,"scanned":0}
{"ts":"2026-05-17T06:42:24+00:00","event":"pipeline.compaction.complete","realm":"EGX","folder":"intraday","compacted":0,"scanned":0}
{"ts":"2026-05-17T06:42:24+00:00","event":"pipeline.alert","alert_key":"history_fresh_ratio_low","observed":0.2193,"threshold":0.9,"stale_sample":["ACRO","ALEX","APPC","DCRC","DEIN","DGTZ","DIFC","DOMT","DSCW","DTPP"],"stale_sample_count":210}
[Alerts] ['history_fresh_ratio_low: observed=0.2193 threshold=0.9000 stale_sample=ACRO,ALEX,APPC,DCRC,DEIN,DGTZ,DIFC,DOMT,DSCW,DTPP']
{"ts":"2026-05-17T06:42:24+00:00","event":"pipeline.sync.complete","realm":"EGX","duration_sec":47.3,"metrics":{"counters":{"dq.input_rows.total":1317355.0,"dq.input_rows.history":835440.0,"dq.valid_rows.total":1316728.0,"dq.valid_rows.history":834813.0,"dq.input_rows.intraday_store":481915.0,"dq.valid_rows.intraday_store":481915.0,"dq.rejected_rows.total":627.0,"dq.rejected_rows.history":627.0,"pipeline.stage.success.intraday":1.0},"gauges":{"pipeline.stage.updated_symbols.intraday":273.0,"pipeline.compaction.compacted.history":0.0,"pipeline.compaction.compacted.intraday":0.0,"pipeline.fresh_ratio.history":0.2193,"pipeline.live_ratio.intraday":0.8736,"pipeline.sync.duration_sec":47.299423694610596}}}

[Done] Synchronization complete in 47.30 seconds.
2026-05-17 09:42:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:43:01 EEST)" (scheduled at 2026-05-17 09:42:31.625095+03:00)
2026-05-17 09:42:31,632 - horus.scheduling - INFO - [Monitor] skipped: market is closed.
2026-05-17 09:42:31,678 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:43:01 EEST)" executed successfully
2026-05-17 09:43:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:43:31 EEST)" (scheduled at 2026-05-17 09:43:01.625095+03:00)
2026-05-17 09:43:01,636 - horus.scheduling - INFO - [Monitor] skipped: market is closed.
2026-05-17 09:43:01,681 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:43:31 EEST)" executed successfully
2026-05-17 09:43:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:44:01 EEST)" (scheduled at 2026-05-17 09:43:31.625095+03:00)
2026-05-17 09:43:31,637 - horus.scheduling - INFO - [Monitor] skipped: market is closed.
2026-05-17 09:43:31,685 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:44:01 EEST)" executed successfully
2026-05-17 09:44:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:44:31 EEST)" (scheduled at 2026-05-17 09:44:01.625095+03:00)
2026-05-17 09:44:01,645 - horus.scheduling - INFO - [Monitor] skipped: market is closed.
2026-05-17 09:44:01,688 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:44:31 EEST)" executed successfully
2026-05-17 09:44:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:45:01 EEST)" (scheduled at 2026-05-17 09:44:31.625095+03:00)
2026-05-17 09:44:31,637 - horus.scheduling - INFO - [Monitor] skipped: market is closed.
2026-05-17 09:44:31,680 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:45:01 EEST)" executed successfully
2026-05-17 09:45:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:45:31 EEST)" (scheduled at 2026-05-17 09:45:01.625095+03:00)
2026-05-17 09:45:01,635 - horus.scheduling - INFO - [Monitor] skipped: market is closed.
2026-05-17 09:45:01,685 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:45:31 EEST)" executed successfully
2026-05-17 09:45:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:46:01 EEST)" (scheduled at 2026-05-17 09:45:31.625095+03:00)
2026-05-17 09:45:31,631 - horus.scheduling - INFO - [Monitor] skipped: market is closed.
2026-05-17 09:45:31,674 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:46:01 EEST)" executed successfully
2026-05-17 09:46:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:46:31 EEST)" (scheduled at 2026-05-17 09:46:01.625095+03:00)
2026-05-17 09:46:01,627 - horus.scheduling - INFO - [Monitor] skipped: market is closed.
2026-05-17 09:46:01,673 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 09:46:31 EEST)" executed successfully
2026-05-17 09:46:31,622 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 09:51:31 EEST)" (scheduled at 2026-05-17 09:46:31.618104+03:00)
2026-05-17 09:46:31,625 - horus.api - INFO - [Watchdog] Market closed. Heavy background tasks paused.
2026-05-17 09:46:31,671 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 09:51:31 EEST)" executed successfully
2026-05-17 09:47:38,980 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T09:42:25.355655). Version incremented to 1.
INFO:     127.0.0.1:50603 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /api/v1/scanner/history HTTP/1.1" 200 OK
INFO:     127.0.0.1:65000 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65195 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:64037 - "GET /api/v1/signals/lifecycle/summary HTTP/1.1" 200 OK
INFO:     127.0.0.1:62699 - "GET /api/v1/signals/lifecycle?limit=24 HTTP/1.1" 200 OK
INFO:     127.0.0.1:65000 - "GET /api/v1/signals/followups/summary HTTP/1.1" 200 OK
INFO:     127.0.0.1:64037 - "GET /api/v1/portfolios HTTP/1.1" 200 OK
INFO:     127.0.0.1:65195 - "GET /api/v1/signals/followups?limit=24 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62699 - "GET /api/v1/portfolios/default HTTP/1.1" 200 OK
INFO:     127.0.0.1:65000 - "HEAD /telegram HTTP/1.1" 200 OK
INFO:     127.0.0.1:65195 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64037 - "HEAD / HTTP/1.1" 200 OK
INFO:     127.0.0.1:62699 - "GET /api/v1/portfolio/metrics?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:65000 - "GET /api/v1/portfolio/curve?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65195 - "GET /api/v1/scanner/history HTTP/1.1" 200 OK
INFO:     127.0.0.1:64037 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:54661 - "GET /api/v1/strategy/health?days=60 HTTP/1.1" 200 OK
INFO:     127.0.0.1:65000 - "GET /api/v1/portfolio/curve?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62699 - "GET /api/v1/portfolio/metrics?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /api/v1/strategy/health?days=60 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64037 - "GET /telegram/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:65195 - "GET /status/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:54661 - "GET /__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:65000 - "GET /_next/static/chunks/0qpn_abl5rpbi.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:62699 - "GET /_next/static/chunks/0i13l3hiw~z8h.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /_next/static/chunks/0izczcbq05-4w.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:64037 - "GET /telegram/__next._index.txt?_rsc=yIp22O3xgPPxC28X HTTP/1.1" 200 OK
INFO:     127.0.0.1:65195 - "GET /telegram/__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:54661 - "GET /telegram/__next.telegram.txt?_rsc=lk5o7horzjemOb45 HTTP/1.1" 200 OK
INFO:     127.0.0.1:65000 - "GET /_next/static/chunks/0dtr2~tudylt3.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:62699 - "GET /telegram/__next.telegram.__PAGE__.txt?_rsc=uSQeOdax5UYzN25q HTTP/1.1" 200 OK
INFO:     127.0.0.1:64037 - "GET /__next.__PAGE__.txt?_rsc=8nTjltbQWvg6NcbE HTTP/1.1" 200 OK
INFO:     127.0.0.1:65195 - "GET /__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:54661 - "GET /status/__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:62699 - "GET /_next/static/chunks/0b..pu7-sz7c0.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /_next/static/chunks/0wgfge.5oeehi.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:65195 - "GET /status/__next.status.__PAGE__.txt?_rsc=nJzitYr0nLzkFtU7 HTTP/1.1" 200 OK
INFO:     127.0.0.1:65000 - "GET /status/__next.status.txt?_rsc=IeafhV2wQjA87Ccb HTTP/1.1" 200 OK
INFO:     127.0.0.1:65000 - "GET /_next/static/chunks/06o67r049xw26.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:59842 - "GET /api/v1/scanner/history HTTP/1.1" 200 OK
INFO:     127.0.0.1:59842 - "HEAD /arbitrage HTTP/1.1" 200 OK
INFO:     127.0.0.1:57323 - "HEAD /simulation HTTP/1.1" 200 OK
INFO:     127.0.0.1:59842 - "HEAD /optimization HTTP/1.1" 200 OK
INFO:     127.0.0.1:57323 - "HEAD /strategy HTTP/1.1" 200 OK
INFO:     127.0.0.1:59842 - "HEAD /audit HTTP/1.1" 200 OK
INFO:     127.0.0.1:57323 - "GET /arbitrage/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:63251 - "GET /simulation/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:63341 - "GET /optimization/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:59842 - "GET /strategy/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:64664 - "GET /audit/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:57323 - "GET /arbitrage/__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:53959 - "GET /arbitrage/__next.arbitrage.txt?_rsc=WueSyvOqLqtpJd8j HTTP/1.1" 200 OK
INFO:     127.0.0.1:63251 - "GET /arbitrage/__next.arbitrage.__PAGE__.txt?_rsc=Yem9O1JU2nqLzA9P HTTP/1.1" 200 OK
INFO:     127.0.0.1:64664 - "HEAD /reports/weekly HTTP/1.1" 200 OK
INFO:     127.0.0.1:63251 - "GET /_next/static/chunks/123u3bym96m8d.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:64664 - "GET /reports/weekly/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:64664 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 09:51:31,619 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 09:56:31 EEST)" (scheduled at 2026-05-17 09:51:31.618104+03:00)
2026-05-17 09:51:31,622 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 09:56:31 EEST)" executed successfully
INFO:     127.0.0.1:49674 - "GET /api/v1/scanner/history HTTP/1.1" 200 OK
INFO:     127.0.0.1:54278 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61330 - "GET /api/v1/portfolio/metrics?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60144 - "GET /api/v1/portfolio/curve?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49674 - "HEAD /telegram HTTP/1.1" 200 OK
INFO:     127.0.0.1:52221 - "HEAD / HTTP/1.1" 200 OK
INFO:     127.0.0.1:49674 - "GET /telegram/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:52221 - "GET /__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:52221 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60144 - "GET /telegram/__next._index.txt?_rsc=yIp22O3xgPPxC28X HTTP/1.1" 200 OK
INFO:     127.0.0.1:49674 - "GET /telegram/__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:61330 - "GET /telegram/__next.telegram.txt?_rsc=lk5o7horzjemOb45 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54278 - "GET /telegram/__next.telegram.__PAGE__.txt?_rsc=uSQeOdax5UYzN25q HTTP/1.1" 200 OK
INFO:     127.0.0.1:52221 - "GET /status.txt?_rsc=2Md0sTUZcnjCijMr HTTP/1.1" 200 OK
INFO:     127.0.0.1:61330 - "GET /status/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:60144 - "GET /__next.__PAGE__.txt?_rsc=8nTjltbQWvg6NcbE HTTP/1.1" 200 OK
INFO:     127.0.0.1:49674 - "GET /__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:61330 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52221 - "GET /_next/static/chunks/06o67r049xw26.js HTTP/1.1" 304 Not Modified
INFO:     127.0.0.1:65432 - "GET /api/v1/strategy/health?days=60 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61330 - "GET /api/v1/data/sync/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52221 - "GET /api/v1/portfolios HTTP/1.1" 200 OK
INFO:     127.0.0.1:65432 - "GET /api/v1/portfolios/default HTTP/1.1" 200 OK
INFO:     127.0.0.1:61330 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61330 - "GET /status/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:61330 - "GET /status/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:65432 - "GET /status/__next.status.txt?_rsc=50rOQS8YzswLD0DR HTTP/1.1" 200 OK
2026-05-17 09:56:31,623 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:01:31 EEST)" (scheduled at 2026-05-17 09:56:31.618104+03:00)
2026-05-17 09:56:31,644 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:01:31 EEST)" executed successfully
INFO:     127.0.0.1:52221 - "GET /status/__next.status.__PAGE__.txt?_rsc=_grtAnSmDF_oUHwj HTTP/1.1" 200 OK
INFO:     127.0.0.1:49674 - "GET /api/v1/data/runtime-universe HTTP/1.1" 200 OK
INFO:     127.0.0.1:60144 - "GET /api/v1/system/full-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54278 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63270 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58393 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64863 - "GET /api/v1/data/runtime-universe HTTP/1.1" 200 OK
INFO:     127.0.0.1:64947 - "GET /api/v1/system/full-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64947 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64947 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64947 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50864 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51636 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62152 - "GET /api/v1/data/runtime-universe HTTP/1.1" 200 OK
INFO:     127.0.0.1:60284 - "GET /api/v1/system/full-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60284 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60284 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55312 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49674 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51816 - "GET /api/v1/system/full-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51757 - "GET /api/v1/data/runtime-universe HTTP/1.1" 200 OK
2026-05-17 10:00:00,008 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: cron[hour='10', minute='0'], next run at: 2026-05-18 10:00:00 EEST)" (scheduled at 2026-05-17 10:00:00+03:00)
2026-05-17 10:00:00,010 - horus.api - INFO - [Watchdog] Market opened. Heavy background tasks resumed.
2026-05-17 10:00:00,075 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: cron[hour='10', minute='0'], next run at: 2026-05-18 10:00:00 EEST)" executed successfully
2026-05-17 10:00:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:00:31 EEST)" (scheduled at 2026-05-17 10:00:01.625095+03:00)
2026-05-17 10:00:01,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:00:31 EEST)" executed successfully
INFO:     127.0.0.1:62811 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62811 - "HEAD /seasonality HTTP/1.1" 200 OK
INFO:     127.0.0.1:51618 - "HEAD /sectors HTTP/1.1" 200 OK
INFO:     127.0.0.1:62811 - "HEAD /news HTTP/1.1" 200 OK
INFO:     127.0.0.1:51618 - "HEAD /live HTTP/1.1" 200 OK
INFO:     127.0.0.1:62811 - "HEAD /whales HTTP/1.1" 200 OK
INFO:     127.0.0.1:51618 - "GET /seasonality/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:59472 - "GET /sectors/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:61928 - "GET /news/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62811 - "GET /live/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:53251 - "GET /whales/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
2026-05-17 10:00:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:01:01 EEST)" (scheduled at 2026-05-17 10:00:31.625095+03:00)
2026-05-17 10:00:31,629 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:01:01 EEST)" executed successfully
INFO:     127.0.0.1:61330 - "GET /api/v1/data/runtime-universe HTTP/1.1" 200 OK
{"ts":"2026-05-17T07:00:38+00:00","event":"pipeline.alert","alert_key":"intraday_live_ratio_low","observed":0.0,"threshold":0.65}
INFO:     127.0.0.1:53251 - "GET /api/v1/system/full-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52006 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64653 - "HEAD /portfolio HTTP/1.1" 200 OK
INFO:     127.0.0.1:57553 - "HEAD /settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:64653 - "GET /portfolio/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:57553 - "GET /settings/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:57553 - "GET /settings/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:64653 - "GET /settings/__next.settings.txt?_rsc=bypY-lgJtWE1htkG HTTP/1.1" 200 OK
INFO:     127.0.0.1:51572 - "GET /settings/__next.settings.__PAGE__.txt?_rsc=Dy7bFjl2J4dryOJp HTTP/1.1" 200 OK
INFO:     127.0.0.1:57553 - "GET /portfolio/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:64653 - "GET /portfolio/__next.portfolio.__PAGE__.txt?_rsc=d_Fwz1zmRCOVzyzG HTTP/1.1" 200 OK
INFO:     127.0.0.1:51572 - "GET /portfolio/__next.portfolio.txt?_rsc=jMDDsYmCMTF2sLQP HTTP/1.1" 200 OK
INFO:     127.0.0.1:57553 - "GET /_next/static/chunks/0b4p8co1ro0.d.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:59348 - "GET /_next/static/chunks/09r_4pbj~6hcf.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:64653 - "GET /_next/static/chunks/13sjwypsgf9.v.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:57553 - "GET /_next/static/chunks/0tvkhfi7mmhn2.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:51572 - "GET /_next/static/chunks/0kw~49m4zhtr5.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:64653 - "GET /api/v1/settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:51572 - "GET /api/v1/settings/exclusions HTTP/1.1" 200 OK
INFO:     127.0.0.1:57553 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /api/v1/settings/exclusions HTTP/1.1" 200 OK
INFO:     127.0.0.1:64653 - "GET /api/v1/settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:60245 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:60245 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64412 - "GET /api/v1/data/tickers HTTP/1.1" 200 OK
INFO:     127.0.0.1:65104 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:01:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:01:31 EEST)" (scheduled at 2026-05-17 10:01:01.625095+03:00)
2026-05-17 10:01:01,629 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:01:31 EEST)" executed successfully
2026-05-17 10:01:01,972 - horus.settings - INFO - [Settings] AUTO_TRADE_ENABLED update requested=True previous=False current=True changed=True
INFO:     127.0.0.1:65104 - "POST /api/v1/settings HTTP/1.1" 200 OK
2026-05-17 10:01:02,037 - core.StockLoader - INFO - StockLoader: Cache cleared.
[Cache] All analytics caches purged.INFO:     127.0.0.1:65104 - "POST /api/v1/signals/desk/mode HTTP/1.1" 200 OK

INFO:     127.0.0.1:50719 - "POST /api/v1/settings/exclusions HTTP/1.1" 200 OK
INFO:     127.0.0.1:64430 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52050 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64958 - "POST /api/v1/ai/provider/test HTTP/1.1" 400 Bad Request
INFO:     127.0.0.1:49787 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49787 - "POST /api/v1/ai/provider/test HTTP/1.1" 200 OK
INFO:     127.0.0.1:49787 - "POST /api/v1/settings HTTP/1.1" 200 OK
2026-05-17 10:01:31,621 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:06:31 EEST)" (scheduled at 2026-05-17 10:01:31.618104+03:00)
2026-05-17 10:01:31,623 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:06:31 EEST)" executed successfully
2026-05-17 10:01:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:06:31 EEST)" (scheduled at 2026-05-17 10:01:31.622651+03:00)
2026-05-17 10:01:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:02:01 EEST)" (scheduled at 2026-05-17 10:01:31.625095+03:00)
2026-05-17 10:01:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 10:11:31 EEST)" (scheduled at 2026-05-17 10:01:31.627072+03:00)
2026-05-17 10:01:31,638 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:01:31,645 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 10:11:31 EEST)" executed successfully
2026-05-17 10:01:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:02:01 EEST)" executed successfully
INFO:     127.0.0.1:57315 - "HEAD /telegram HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "HEAD / HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57208 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60909 - "GET /telegram/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:63580 - "GET /__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "GET /status/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
2026-05-17 10:01:32,872 - horus.settings - INFO - [Settings] AUTO_TRADE_ENABLED update requested=True previous=True current=True changed=False
INFO:     127.0.0.1:57208 - "GET /telegram/__next._index.txt?_rsc=ERfXn7tGRj5EupPH HTTP/1.1" 200 OK
2026-05-17 10:01:32,896 - core.StockLoader - INFO - StockLoader: Cache cleared.
[Cache] All analytics caches purged.
INFO:     127.0.0.1:60909 - "GET /telegram/__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "GET /telegram/__next.telegram.txt?_rsc=aKACAGocL3t4-4Xd HTTP/1.1" 200 OK
INFO:     127.0.0.1:63580 - "POST /api/v1/signals/desk/mode HTTP/1.1" 200 OK
INFO:     127.0.0.1:65239 - "POST /api/v1/settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:51656 - "POST /api/v1/settings/exclusions HTTP/1.1" 200 OK
INFO:     127.0.0.1:57208 - "GET /__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "GET /__next.__PAGE__.txt?_rsc=cdk-OvPaaQdzy3F4 HTTP/1.1" 200 OK
2026-05-17 10:01:34,648 - DailyScanner - INFO - Intraday sync start (throttle=5m)
[Info] Found 273 intraday CSV files to ingest.INFO:     127.0.0.1:60909 - "GET /telegram/__next.telegram.__PAGE__.txt?_rsc=WHz_FkIDzWrFoQE3 HTTP/1.1" 200 OK

INFO:     127.0.0.1:51656 - "GET /status/__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60909 - "HEAD /arbitrage HTTP/1.1" 200 OK
INFO:     127.0.0.1:51656 - "HEAD /simulation HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "GET /status/__next.status.txt?_rsc=s0FEf9OOxbpuBOef HTTP/1.1" 200 OK
INFO:     127.0.0.1:57208 - "GET /status/__next.status.__PAGE__.txt?_rsc=ESW-ijXE9EWSHgP1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60909 - "GET /arbitrage/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:51656 - "GET /simulation/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51656 - "GET /api/v1/scanner/history HTTP/1.1" 200 OK
INFO:     127.0.0.1:65239 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:63580 - "GET /api/v1/signals/lifecycle/summary HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "GET /api/v1/signals/lifecycle?limit=24 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63580 - "GET /api/v1/portfolios HTTP/1.1" 200 OK
INFO:     127.0.0.1:51656 - "GET /api/v1/signals/followups/summary HTTP/1.1" 200 OK
INFO:     127.0.0.1:65239 - "GET /api/v1/signals/followups?limit=24 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "GET /api/v1/portfolios/default HTTP/1.1" 200 OK
INFO:     127.0.0.1:51656 - "GET /api/v1/scanner/history HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "GET /api/v1/portfolio/metrics?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:65239 - "GET /api/v1/portfolio/curve?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63580 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:57208 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51656 - "GET /api/v1/portfolio/metrics?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:65239 - "POST /api/v1/control/scan HTTP/1.1" 200 OK
INFO:     127.0.0.1:63580 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "GET /api/v1/portfolio/curve?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60909 - "GET /api/v1/strategy/health?days=60 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57315 - "GET /api/v1/strategy/health?days=60 HTTP/1.1" 200 OK
2026-05-17 10:01:53,964 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 10:01:54,055 - DailyScanner - INFO - Scanning 272 tickers. Intraday=False PreClose=False
2026-05-17 10:01:54,882 - DailyScanner - INFO - Parallel scoring 10 candidates...
2026-05-17 10:01:54,891 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 8 signals across 272 tickers.
2026-05-17 10:01:54,892 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 8 signals. Regime: BULLISH (72.6%)
2026-05-17 10:01:56,311 - DailyScanner - INFO - Parallel scoring 2 candidates...
2026-05-17 10:01:56,314 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 0 signals across 272 tickers.
2026-05-17 10:01:56,315 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 0 signals. Regime: BULLISH (76.8%)
2026-05-17 10:01:56,316 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 0 signals (regime=BULLISH).
2026-05-17 10:01:57,601 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=1
2026-05-17 10:01:57,668 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=1
2026-05-17 10:01:57,669 - horus.scheduling - INFO - [Scheduler] Intraday: no eligible signals after scheduler filters.
2026-05-17 10:01:58,495 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted per-run no-signal notice.
2026-05-17 10:01:58,563 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:06:31 EEST)" executed successfully
2026-05-17 10:02:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:02:31 EEST)" (scheduled at 2026-05-17 10:02:01.625095+03:00)
2026-05-17 10:02:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:02:31 EEST)" executed successfully
INFO:     127.0.0.1:64968 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:02:09,422 - AutoTrader - INFO - Processing 8 scanner signals for portfolio: Horus Core
2026-05-17 10:02:09,425 - AutoTrader - ERROR - Portfolio 'Horus Core' not found. Skipping auto-entry.
INFO:     127.0.0.1:64215 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59830 - "GET /api/v1/settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:64257 - "GET /api/v1/settings/exclusions HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:59830 - "GET /api/v1/portfolios/default HTTP/1.1" 200 OK
INFO:     127.0.0.1:64215 - "GET /api/v1/portfolios HTTP/1.1" 200 OK
INFO:     127.0.0.1:53735 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60700 - "GET /api/v1/data/tickers HTTP/1.1" 200 OK
INFO:     127.0.0.1:53305 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59433 - "POST /api/v1/alerts/test HTTP/1.1" 400 Bad Request
2026-05-17 10:02:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:03:01 EEST)" (scheduled at 2026-05-17 10:02:31.625095+03:00)
2026-05-17 10:02:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:03:01 EEST)" executed successfully
INFO:     127.0.0.1:59433 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59433 - "POST /api/v1/alerts/test HTTP/1.1" 400 Bad Request
INFO:     127.0.0.1:59433 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59433 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53265 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:03:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:03:31 EEST)" (scheduled at 2026-05-17 10:03:01.625095+03:00)
2026-05-17 10:03:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:03:31 EEST)" executed successfully
2026-05-17 10:03:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:04:01 EEST)" (scheduled at 2026-05-17 10:03:31.625095+03:00)
2026-05-17 10:03:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:04:01 EEST)" executed successfully
2026-05-17 10:04:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:04:31 EEST)" (scheduled at 2026-05-17 10:04:01.625095+03:00)
2026-05-17 10:04:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:04:31 EEST)" executed successfully
2026-05-17 10:04:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:05:01 EEST)" (scheduled at 2026-05-17 10:04:31.625095+03:00)
2026-05-17 10:04:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:05:01 EEST)" executed successfully
INFO:     127.0.0.1:64098 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:05:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:05:31 EEST)" (scheduled at 2026-05-17 10:05:01.625095+03:00)
2026-05-17 10:05:01,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:05:31 EEST)" executed successfully
INFO:     127.0.0.1:49674 - "POST /api/v1/alerts/test HTTP/1.1" 200 OK
INFO:     127.0.0.1:49674 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59124 - "POST /api/v1/telegram/config HTTP/1.1" 200 OK
INFO:     127.0.0.1:59124 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59124 - "HEAD /optimization HTTP/1.1" 200 OK
INFO:     127.0.0.1:52465 - "HEAD /strategy HTTP/1.1" 200 OK
INFO:     127.0.0.1:59124 - "HEAD /audit HTTP/1.1" 200 OK
INFO:     127.0.0.1:52465 - "HEAD /reports/weekly HTTP/1.1" 200 OK
INFO:     127.0.0.1:52465 - "GET /strategy/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:59124 - "GET /optimization/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:63554 - "GET /reports/weekly/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:62303 - "GET /audit/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:62303 - "GET /api/v1/scanner/history HTTP/1.1" 200 OK
INFO:     127.0.0.1:52465 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51785 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:54563 - "GET /api/v1/signals/lifecycle/summary HTTP/1.1" 200 OK
INFO:     127.0.0.1:62303 - "GET /api/v1/signals/lifecycle?limit=24 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52465 - "GET /api/v1/signals/followups/summary HTTP/1.1" 200 OK
INFO:     127.0.0.1:54563 - "GET /api/v1/portfolios HTTP/1.1" 200 OK
INFO:     127.0.0.1:51785 - "GET /api/v1/signals/followups?limit=24 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62303 - "GET /api/v1/portfolios/default HTTP/1.1" 200 OK
INFO:     127.0.0.1:52465 - "HEAD /analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:51785 - "HEAD /oracle HTTP/1.1" 200 OK
INFO:     127.0.0.1:54563 - "HEAD /traps HTTP/1.1" 200 OK
INFO:     127.0.0.1:62303 - "HEAD /scanner HTTP/1.1" 200 OK
INFO:     127.0.0.1:51785 - "GET /api/v1/portfolio/metrics?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59124 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52465 - "POST /api/v1/control/scan HTTP/1.1" 200 OK
INFO:     127.0.0.1:54563 - "GET /api/v1/portfolio/curve?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62303 - "GET /api/v1/scanner/history HTTP/1.1" 200 OK
INFO:     127.0.0.1:54563 - "GET /oracle/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:51785 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:63554 - "GET /api/v1/strategy/health?days=60 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52465 - "GET /analytics/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:59124 - "GET /api/v1/strategy/health?days=60 HTTP/1.1" 200 OK
2026-05-17 10:05:25,935 - DailyScanner - INFO - Scanning 272 tickers. Intraday=False PreClose=False
INFO:     127.0.0.1:62303 - "GET /traps/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:54563 - "GET /scanner/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
2026-05-17 10:05:26,492 - DailyScanner - INFO - Parallel scoring 10 candidates...
2026-05-17 10:05:26,505 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 8 signals across 272 tickers.
2026-05-17 10:05:26,508 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 8 signals. Regime: BULLISH (72.6%)
2026-05-17 10:05:26,511 - horus.alerts - INFO - [Deduplicator] label=DAILY_CONFIRMED kept=0 dropped=8 counts_by_reason={'repeat_cooldown': 8} dropped_tickers=['TAQA', 'CRST', 'COSG', 'CCAP', 'EGCH', 'AFDI', 'ALUM', 'MILS']
2026-05-17 10:05:26,520 - AutoTrader - INFO - Processing 8 scanner signals for portfolio: Horus Core
2026-05-17 10:05:26,522 - AutoTrader - ERROR - Portfolio 'Horus Core' not found. Skipping auto-entry.
INFO:     127.0.0.1:54563 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:05:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:06:01 EEST)" (scheduled at 2026-05-17 10:05:31.625095+03:00)
2026-05-17 10:05:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:06:01 EEST)" executed successfully
2026-05-17 10:06:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:06:31 EEST)" (scheduled at 2026-05-17 10:06:01.625095+03:00)
2026-05-17 10:06:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:06:31 EEST)" executed successfully
INFO:     127.0.0.1:50382 - "GET /api/v1/scanner/history HTTP/1.1" 200 OK
INFO:     127.0.0.1:63251 - "GET /api/v1/portfolio/metrics?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63251 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63251 - "POST /api/v1/signals/desk/mode HTTP/1.1" 200 OK
INFO:     127.0.0.1:63251 - "GET /api/v1/signals/lifecycle/summary HTTP/1.1" 200 OK
INFO:     127.0.0.1:50382 - "GET /api/v1/signals/lifecycle?limit=24 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63251 - "GET /api/v1/signals/followups?limit=24 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50382 - "GET /api/v1/signals/followups/summary HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "HEAD /seasonality HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "HEAD /sectors HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "HEAD /news HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "HEAD /live HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "GET /seasonality/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "HEAD /whales HTTP/1.1" 200 OK
INFO:     127.0.0.1:58570 - "GET /sectors/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:53548 - "GET /live/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:60638 - "GET /news/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "GET /whales/__next._tree.txt?_rsc=5CB68i4pnAekjehf HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "GET /seasonality/__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:53548 - "GET /seasonality/__next.seasonality.__PAGE__.txt?_rsc=JpYsXQwMvjk4zO0D HTTP/1.1" 200 OK
INFO:     127.0.0.1:58570 - "GET /sectors/__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:60638 - "GET /seasonality/__next.seasonality.txt?_rsc=OGavTD-aLMTRY9X9 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "GET /sectors/__next.sectors.txt?_rsc=QcbRwC8TJmGhTImN HTTP/1.1" 200 OK
INFO:     127.0.0.1:53548 - "GET /news/__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:58570 - "GET /sectors/__next.sectors.__PAGE__.txt?_rsc=dYmA9KIDeDxxdzm1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60121 - "GET /news/__next.news.txt?_rsc=AxJWtL9sY4KpFFZZ HTTP/1.1" 200 OK
INFO:     127.0.0.1:60638 - "GET /_next/static/chunks/0mr6~5g7vgcw2.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:58570 - "GET /_next/static/chunks/16k8edsjq.c3k.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:58570 - "GET /news/__next.news.__PAGE__.txt?_rsc=ZBRZ9e84RvjbRE0z HTTP/1.1" 200 OK
INFO:     127.0.0.1:60121 - "GET /live/__next.live.txt?_rsc=FHPuQZHssXgn5gxV HTTP/1.1" 200 OK
INFO:     127.0.0.1:53548 - "GET /live/__next.live.__PAGE__.txt?_rsc=4TB-DAqkiH1L8mku HTTP/1.1" 200 OK
INFO:     127.0.0.1:60638 - "GET /live/__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:58570 - "GET /analytics/__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:59727 - "GET /analytics/__next.analytics.txt?_rsc=b-4OWIjttFjasBiH HTTP/1.1" 200 OK
INFO:     127.0.0.1:60121 - "GET /_next/static/chunks/0ip6xaj8_2--j.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "GET /_next/static/chunks/0mz8s715-6t4o.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:53548 - "GET /analytics/__next.analytics.__PAGE__.txt?_rsc=mo_AgHTT1zezsrdY HTTP/1.1" 200 OK
INFO:     127.0.0.1:60638 - "GET /_next/static/chunks/0rga1efswmc.f.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:58570 - "GET /traps/__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:60121 - "GET /scanner/__next._head.txt?_rsc=7h4NYy5eoyMcNlUN HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "GET /traps/__next.traps.txt?_rsc=7wdg5TFJxJkso_xa HTTP/1.1" 200 OK
INFO:     127.0.0.1:59727 - "GET /scanner/__next.scanner.txt?_rsc=uQTdRGvvOIFN-3qx HTTP/1.1" 200 OK
INFO:     127.0.0.1:60638 - "GET /scanner/__next.scanner.__PAGE__.txt?_rsc=VoMwq0ULiFO8gTXI HTTP/1.1" 200 OK
INFO:     127.0.0.1:53548 - "GET /_next/static/chunks/174_5v60iih2w.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:58570 - "GET /scanner.txt?_rsc=uOyPrqDANHFA88fE HTTP/1.1" 200 OK
INFO:     127.0.0.1:59727 - "GET /_next/static/chunks/0ma9t-bvrm55u.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:60638 - "GET /_next/static/chunks/0tj25uykj93nn.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:53548 - "GET /_next/static/chunks/0u0xynnqdc6_..js HTTP/1.1" 200 OK
INFO:     127.0.0.1:60638 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59727 - "GET /api/v1/scanner/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58410 - "GET /api/v1/portfolios HTTP/1.1" 200 OK
INFO:     127.0.0.1:60121 - "GET /api/v1/portfolios/default HTTP/1.1" 200 OK
INFO:     127.0.0.1:58570 - "GET /api/v1/strategy/pine/scanner-profiles HTTP/1.1" 200 OK
INFO:     127.0.0.1:53548 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63143 - "POST /api/v1/scanner/start?index=ALL&intraday=true&use_active_profile=false HTTP/1.1" 200 OK
INFO:     127.0.0.1:63143 - "GET /api/v1/scanner/status HTTP/1.1" 200 OK
2026-05-17 10:06:31,620 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:11:31 EEST)" (scheduled at 2026-05-17 10:06:31.618104+03:00)
2026-05-17 10:06:31,623 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:11:31 EEST)" (scheduled at 2026-05-17 10:06:31.622651+03:00)
2026-05-17 10:06:31,624 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:11:31 EEST)" executed successfully
2026-05-17 10:06:31,626 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:06:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:07:01 EEST)" (scheduled at 2026-05-17 10:06:31.625095+03:00)
2026-05-17 10:06:31,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:07:01 EEST)" executed successfully
INFO:     127.0.0.1:63143 - "GET /api/v1/scanner/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56827 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56827 - "GET /api/v1/scanner/status HTTP/1.1" 200 OK
2026-05-17 10:06:36,078 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 10:06:36,084 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 10:06:36,714 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 10:06:36,716 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 10:06:40,724 - DailyScanner - INFO - Parallel scoring 2 candidates...
2026-05-17 10:06:40,729 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 0 signals across 272 tickers.
2026-05-17 10:06:40,731 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 0 signals. Regime: BULLISH (76.8%)
2026-05-17 10:06:42,505 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=2
2026-05-17 10:06:44,271 - DailyScanner - INFO - Parallel scoring 2 candidates...
2026-05-17 10:06:44,276 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 0 signals across 272 tickers.
2026-05-17 10:06:44,277 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 0 signals. Regime: BULLISH (76.8%)
2026-05-17 10:06:44,280 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 0 signals (regime=BULLISH).
2026-05-17 10:06:45,823 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=3
2026-05-17 10:06:45,888 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=3
2026-05-17 10:06:45,890 - horus.scheduling - INFO - [Scheduler] Intraday: no eligible signals after scheduler filters.
2026-05-17 10:06:46,722 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted per-run no-signal notice.
2026-05-17 10:06:46,795 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:11:31 EEST)" executed successfully
2026-05-17 10:07:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:07:31 EEST)" (scheduled at 2026-05-17 10:07:01.625095+03:00)
2026-05-17 10:07:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:07:31 EEST)" executed successfully
2026-05-17 10:07:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:08:01 EEST)" (scheduled at 2026-05-17 10:07:31.625095+03:00)
2026-05-17 10:07:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:08:01 EEST)" executed successfully
2026-05-17 10:08:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:08:31 EEST)" (scheduled at 2026-05-17 10:08:01.625095+03:00)
2026-05-17 10:08:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:08:31 EEST)" executed successfully
2026-05-17 10:08:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:09:01 EEST)" (scheduled at 2026-05-17 10:08:31.625095+03:00)
2026-05-17 10:08:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:09:01 EEST)" executed successfully
2026-05-17 10:09:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:09:31 EEST)" (scheduled at 2026-05-17 10:09:01.625095+03:00)
2026-05-17 10:09:01,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:09:31 EEST)" executed successfully
2026-05-17 10:09:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:10:01 EEST)" (scheduled at 2026-05-17 10:09:31.625095+03:00)
2026-05-17 10:09:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:10:01 EEST)" executed successfully
2026-05-17 10:10:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:10:31 EEST)" (scheduled at 2026-05-17 10:10:01.625095+03:00)
2026-05-17 10:10:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:10:31 EEST)" executed successfully
2026-05-17 10:10:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:11:01 EEST)" (scheduled at 2026-05-17 10:10:31.625095+03:00)
2026-05-17 10:10:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:11:01 EEST)" executed successfully
2026-05-17 10:11:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:11:31 EEST)" (scheduled at 2026-05-17 10:11:01.625095+03:00)
2026-05-17 10:11:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:11:31 EEST)" executed successfully
2026-05-17 10:11:31,632 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:16:31 EEST)" (scheduled at 2026-05-17 10:11:31.618104+03:00)
2026-05-17 10:11:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 10:21:31 EEST)" (scheduled at 2026-05-17 10:11:31.627072+03:00)
2026-05-17 10:11:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:16:31 EEST)" (scheduled at 2026-05-17 10:11:31.622651+03:00)
2026-05-17 10:11:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:12:01 EEST)" (scheduled at 2026-05-17 10:11:31.625095+03:00)
2026-05-17 10:11:31,634 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:16:31 EEST)" executed successfully
2026-05-17 10:11:31,637 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:11:31,642 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 10:21:31 EEST)" executed successfully
2026-05-17 10:11:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:12:01 EEST)" executed successfully
2026-05-17 10:11:32,624 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 10:11:34,463 - DailyScanner - INFO - Parallel scoring 2 candidates...
2026-05-17 10:11:34,466 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 0 signals across 272 tickers.
2026-05-17 10:11:34,467 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 0 signals. Regime: BULLISH (76.8%)
2026-05-17 10:11:34,469 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 0 signals (regime=BULLISH).
2026-05-17 10:11:35,372 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=4
2026-05-17 10:11:35,419 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=4
2026-05-17 10:11:35,420 - horus.scheduling - INFO - [Scheduler] Intraday: no eligible signals after scheduler filters.
2026-05-17 10:11:36,252 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted per-run no-signal notice.
2026-05-17 10:11:36,306 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:16:31 EEST)" executed successfully
2026-05-17 10:12:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:12:31 EEST)" (scheduled at 2026-05-17 10:12:01.625095+03:00)
2026-05-17 10:12:01,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:12:31 EEST)" executed successfully
2026-05-17 10:12:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:13:01 EEST)" (scheduled at 2026-05-17 10:12:31.625095+03:00)
2026-05-17 10:12:31,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:13:01 EEST)" executed successfully
2026-05-17 10:13:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:13:31 EEST)" (scheduled at 2026-05-17 10:13:01.625095+03:00)
2026-05-17 10:13:01,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:13:31 EEST)" executed successfully
2026-05-17 10:13:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:14:01 EEST)" (scheduled at 2026-05-17 10:13:31.625095+03:00)
2026-05-17 10:13:31,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:14:01 EEST)" executed successfully
2026-05-17 10:14:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:14:31 EEST)" (scheduled at 2026-05-17 10:14:01.625095+03:00)
2026-05-17 10:14:01,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:14:31 EEST)" executed successfully
2026-05-17 10:14:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:15:01 EEST)" (scheduled at 2026-05-17 10:14:31.625095+03:00)
2026-05-17 10:14:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:15:01 EEST)" executed successfully
2026-05-17 10:15:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:15:31 EEST)" (scheduled at 2026-05-17 10:15:01.625095+03:00)
2026-05-17 10:15:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:15:31 EEST)" executed successfully
2026-05-17 10:15:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:16:01 EEST)" (scheduled at 2026-05-17 10:15:31.625095+03:00)
2026-05-17 10:15:31,652 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:16:01 EEST)" executed successfully
2026-05-17 10:16:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:16:31 EEST)" (scheduled at 2026-05-17 10:16:01.625095+03:00)
2026-05-17 10:16:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:16:31 EEST)" executed successfully
2026-05-17 10:16:31,631 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:21:31 EEST)" (scheduled at 2026-05-17 10:16:31.618104+03:00)
2026-05-17 10:16:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:21:31 EEST)" (scheduled at 2026-05-17 10:16:31.622651+03:00)
2026-05-17 10:16:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:17:01 EEST)" (scheduled at 2026-05-17 10:16:31.625095+03:00)
2026-05-17 10:16:31,632 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:21:31 EEST)" executed successfully
2026-05-17 10:16:31,634 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:16:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:17:01 EEST)" executed successfully
2026-05-17 10:16:33,501 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 10:16:33,502 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 10:16:35,299 - DailyScanner - INFO - Parallel scoring 2 candidates...
2026-05-17 10:16:35,302 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 0 signals across 272 tickers.
2026-05-17 10:16:35,303 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 0 signals. Regime: BULLISH (76.8%)
2026-05-17 10:16:35,305 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 0 signals (regime=BULLISH).
2026-05-17 10:16:36,228 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=5
2026-05-17 10:16:36,273 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=5
2026-05-17 10:16:36,274 - horus.scheduling - INFO - [Scheduler] Intraday: no eligible signals after scheduler filters.
2026-05-17 10:16:37,111 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted per-run no-signal notice.
2026-05-17 10:16:37,165 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:21:31 EEST)" executed successfully
2026-05-17 10:17:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:17:31 EEST)" (scheduled at 2026-05-17 10:17:01.625095+03:00)
2026-05-17 10:17:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:17:31 EEST)" executed successfully
2026-05-17 10:17:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:18:01 EEST)" (scheduled at 2026-05-17 10:17:31.625095+03:00)
2026-05-17 10:17:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:18:01 EEST)" executed successfully
2026-05-17 10:18:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:18:31 EEST)" (scheduled at 2026-05-17 10:18:01.625095+03:00)
2026-05-17 10:18:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:18:31 EEST)" executed successfully
2026-05-17 10:18:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:19:01 EEST)" (scheduled at 2026-05-17 10:18:31.625095+03:00)
2026-05-17 10:18:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:19:01 EEST)" executed successfully
2026-05-17 10:19:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:19:31 EEST)" (scheduled at 2026-05-17 10:19:01.625095+03:00)
2026-05-17 10:19:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:19:31 EEST)" executed successfully
2026-05-17 10:19:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:20:01 EEST)" (scheduled at 2026-05-17 10:19:31.625095+03:00)
2026-05-17 10:19:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:20:01 EEST)" executed successfully
INFO:     127.0.0.1:62299 - "GET /api/v1/scanner/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62299 - "HEAD /sectors HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "HEAD /seasonality HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "HEAD /news HTTP/1.1" 200 OK
INFO:     127.0.0.1:62299 - "HEAD /live HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "HEAD /scanner HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "HEAD /traps HTTP/1.1" 200 OK
INFO:     127.0.0.1:52188 - "HEAD /whales HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "HEAD /oracle HTTP/1.1" 200 OK
INFO:     127.0.0.1:62299 - "HEAD /analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "GET /sectors/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:52188 - "GET /news/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /live/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "GET /seasonality/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:62299 - "GET /scanner/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /traps/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "GET /whales/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "GET /oracle/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /analytics/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "HEAD /telegram HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "HEAD / HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "GET /status/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /telegram/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "GET /__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /status/__next._head.txt?_rsc=Ng-S3qYZFBQr2y55 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /telegram/__next._head.txt?_rsc=Ng-S3qYZFBQr2y55 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "GET /status/__next._index.txt?_rsc=AzefABwAL7L_Mv7D HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "GET /telegram/__next.telegram.txt?_rsc=Pqzid0NLGNSfsO0S HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /__next.__PAGE__.txt?_rsc=a-VZwvdwo8kRH58V HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "GET /telegram/__next.telegram.__PAGE__.txt?_rsc=6WfSdAwZg4lRK1ou HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /__next._head.txt?_rsc=Ng-S3qYZFBQr2y55 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "GET /status/__next.status.txt?_rsc=sB01jkdk-7Fq1_Of HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "HEAD /optimization HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "HEAD /simulation HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "HEAD /arbitrage HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "HEAD /strategy HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "GET /simulation/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /optimization/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /arbitrage/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "GET /strategy/__next._tree.txt?_rsc=ruyf0wavgcxh1uyq HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "GET /seasonality/__next.seasonality.txt?_rsc=d7GhZzYTSWPNPDHn HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /seasonality/__next._head.txt?_rsc=Ng-S3qYZFBQr2y55 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /seasonality/__next.seasonality.__PAGE__.txt?_rsc=H1T5EJ9hbQeDYHv- HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "GET /sectors/__next._head.txt?_rsc=Ng-S3qYZFBQr2y55 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62299 - "GET /scanner/__next.scanner.txt?_rsc=K6SGX3UpRPr5bxPH HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "GET /scanner/__next._head.txt?_rsc=Ng-S3qYZFBQr2y55 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /sectors/__next.sectors.txt?_rsc=zBemihyRRWVvd_m7 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52188 - "GET /scanner/__next.scanner.__PAGE__.txt?_rsc=VbD_W06uNg5Ib2u1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /oracle/__next._head.txt?_rsc=Ng-S3qYZFBQr2y55 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "GET /oracle/__next.oracle.txt?_rsc=_kHLFjGvQHJxSwlc HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "GET /oracle/__next.oracle.__PAGE__.txt?_rsc=ASBKDuHZNNoYmBQ5 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52188 - "GET /sectors/__next.sectors.__PAGE__.txt?_rsc=P-qazDULputo56r8 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /news/__next._head.txt?_rsc=Ng-S3qYZFBQr2y55 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49189 - "GET /news/__next.news.txt?_rsc=qHo9M51Sr_rCif6a HTTP/1.1" 200 OK
INFO:     127.0.0.1:62299 - "GET /status/__next.status.__PAGE__.txt?_rsc=edB_h7IG_Of_w2e9 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50178 - "GET /oracle.txt?_rsc=8Un_uN4QPr2Wi1Wk HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /_next/static/chunks/0kjck.49y598h.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /api/v1/ai/asset-reports/default HTTP/1.1" 200 OK
[THE COIL] Hunting for explosive moves...[THE CANARY] Calculating Market Breadth...[THE CANARY] Calculating Market Breadth...[THE CANARY] Calculating Market Breadth...INFO:     127.0.0.1:59224 - "GET /api/v1/ai/asset-reports/history?ticker=EGX30 HTTP/1.1" 200 OK
[THE CANARY] Calculating Market Breadth...




INFO:     127.0.0.1:59224 - "GET /news/__next.news.__PAGE__.txt?_rsc=k-pwZmLYndBqiIRz HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /live/__next._head.txt?_rsc=Uq2f8WKuJX_SrHVb HTTP/1.1" 200 OK
[Info] Found 273 intraday CSV files to ingest.INFO:     127.0.0.1:59224 - "GET /live/__next.live.txt?_rsc=OF37QUUPErZUOPDf HTTP/1.1" 200 OK

INFO:     127.0.0.1:59224 - "GET /live/__next.live.__PAGE__.txt?_rsc=TR_iqI3SoQfWt0pX HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /analytics/__next._head.txt?_rsc=Uq2f8WKuJX_SrHVb HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /analytics/__next.analytics.txt?_rsc=24N6TkivKLWziA_4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /analytics/__next.analytics.__PAGE__.txt?_rsc=flPM0eB7-vk4Ga2h HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /traps/__next._head.txt?_rsc=Uq2f8WKuJX_SrHVb HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /traps/__next.traps.txt?_rsc=NOKz6PnF7KA5DxSr HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /traps/__next.traps.__PAGE__.txt?_rsc=o7vw8emMVx7gmUzt HTTP/1.1" 200 OK
INFO:     127.0.0.1:59224 - "GET /_next/static/chunks/0frmc4ub6zh4v.js HTTP/1.1" 200 OK
2026-05-17 10:20:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:20:31 EEST)" (scheduled at 2026-05-17 10:20:01.625095+03:00)
2026-05-17 10:20:01,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:20:31 EEST)" executed successfully
INFO:     127.0.0.1:51634 - "POST /api/v1/prediction HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /api/v1/ai/asset-reports/default HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /api/v1/ai/asset-reports/history?ticker=EGX30 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /whales/__next._head.txt?_rsc=Uq2f8WKuJX_SrHVb HTTP/1.1" 200 OK
INFO:     127.0.0.1:63090 - "GET /whales/__next.whales.txt?_rsc=X7XQAjrw-P2bAknH HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /whales/__next.whales.__PAGE__.txt?_rsc=ODFPg-LaBkUEZNxD HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /_next/static/chunks/01v.fm7tf5508.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "HEAD /audit HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "HEAD /reports/weekly HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /arbitrage/__next._head.txt?_rsc=Uq2f8WKuJX_SrHVb HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /arbitrage/__next.arbitrage.txt?_rsc=AZvkJuRO5cA1HJne HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /audit/__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:51634 - "GET /reports/weekly/__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:63090 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57199 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK

[MACRO PREDICTION] (EGX30):
[MACRO PREDICTION] (EGX30):

[MACRO PREDICTION] (EGX100):
Correlation (Price vs Internal Strength): 0.95
Correlation (Price vs Internal Strength): 0.95
Correlation (Price vs Internal Strength): 0.97
2026-05-17 10:20:31,645 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:21:01 EEST)" (scheduled at 2026-05-17 10:20:31.625095+03:00)
2026-05-17 10:20:31,902 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:21:01 EEST)" executed successfully

[Jotunheim] Scoring 101 tickers for liquidity (EGX100 default universe)...INFO:     127.0.0.1:50178 - "POST /api/v1/prediction HTTP/1.1" 200 OK

[MACRO PREDICTION] (EGX70):
INFO:     127.0.0.1:49189 - "POST /api/v1/prediction HTTP/1.1" 200 OK

Correlation (Price vs Internal Strength): 0.96
INFO:     127.0.0.1:62299 - "POST /api/v1/prediction HTTP/1.1" 200 OK
  ... processed 50/101 ...
INFO:     127.0.0.1:49189 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:20:36,638 - httpx - INFO - HTTP Request: GET https://english.mubasher.info/markets/EGX "HTTP/1.1 200 OK"
  ... processed 100/101 ...
2026-05-17 10:20:36,979 - httpx - INFO - HTTP Request: GET https://enterpriseam.com/egypt/ "HTTP/1.1 200 OK"
2026-05-17 10:20:37,289 - httpx - INFO - HTTP Request: GET https://www.argaam.com/en "HTTP/1.1 200 OK"
2026-05-17 10:20:38,140 - httpx - INFO - HTTP Request: GET https://www.mubasher.info/news/eg/now/latest "HTTP/1.1 200 OK"
2026-05-17 10:20:39,125 - httpx - INFO - HTTP Request: GET https://www.mubasher.info/news/eg/pulse/stocks "HTTP/1.1 200 OK"
INFO:     127.0.0.1:52188 - "GET /api/v1/ai/asset-report?ticker=EGX30 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52188 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
[Jotunheim] Scoring 101 tickers for liquidity (EGX100 default universe)...
INFO:     127.0.0.1:52188 - "GET /api/v1/data/status HTTP/1.1" 200 OK
  ... processed 50/101 ...
  ... processed 100/101 ...
INFO:     127.0.0.1:52188 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
[THE CANARY] Calculating Market Breadth...
2026-05-17 10:21:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:21:31 EEST)" (scheduled at 2026-05-17 10:21:01.625095+03:00)
2026-05-17 10:21:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:21:31 EEST)" executed successfully

[MACRO PREDICTION] (EGX30):
Correlation (Price vs Internal Strength): 0.95
[THE COIL] Hunting for explosive moves...
2026-05-17 10:21:04,286 - horus.confluence - INFO - Confluence: Analyzing Sovereign Hedge signals...
INFO:     127.0.0.1:57285 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50380 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62299 - "GET /api/v1/ai/daily-report?use_llm=true HTTP/1.1" 200 OK
INFO:     127.0.0.1:62299 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62299 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:21:31,632 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:26:31 EEST)" (scheduled at 2026-05-17 10:21:31.618104+03:00)
2026-05-17 10:21:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:26:31 EEST)" (scheduled at 2026-05-17 10:21:31.622651+03:00)
2026-05-17 10:21:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:22:01 EEST)" (scheduled at 2026-05-17 10:21:31.625095+03:00)
2026-05-17 10:21:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 10:31:31 EEST)" (scheduled at 2026-05-17 10:21:31.627072+03:00)
2026-05-17 10:21:31,634 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:26:31 EEST)" executed successfully
2026-05-17 10:21:31,635 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:21:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:22:01 EEST)" executed successfully
2026-05-17 10:21:31,641 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 10:31:31 EEST)" executed successfully
2026-05-17 10:21:34,011 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 10:21:34,012 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 10:21:36,512 - DailyScanner - INFO - Parallel scoring 2 candidates...
2026-05-17 10:21:36,515 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 0 signals across 272 tickers.
2026-05-17 10:21:36,516 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 0 signals. Regime: BULLISH (73.8%)
2026-05-17 10:21:36,517 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 0 signals (regime=BULLISH).
2026-05-17 10:21:37,851 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=6
2026-05-17 10:21:37,909 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=6
2026-05-17 10:21:37,911 - horus.scheduling - INFO - [Scheduler] Intraday: no eligible signals after scheduler filters.
2026-05-17 10:21:38,739 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted per-run no-signal notice.
2026-05-17 10:21:38,797 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:26:31 EEST)" executed successfully
2026-05-17 10:22:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:22:31 EEST)" (scheduled at 2026-05-17 10:22:01.625095+03:00)
2026-05-17 10:22:01,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:22:31 EEST)" executed successfully
INFO:     127.0.0.1:53313 - "GET /api/v1/ai/asset-reports/default HTTP/1.1" 200 OK
INFO:     127.0.0.1:63957 - "GET /api/v1/ai/asset-reports/history?ticker=EGX30 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53101 - "GET /api/v1/ai/asset-report?ticker=EGX30 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63957 - "GET /simulation/__next._head.txt?_rsc=Uq2f8WKuJX_SrHVb HTTP/1.1" 200 OK
INFO:     127.0.0.1:53101 - "GET /arbitrage/__next.arbitrage.__PAGE__.txt?_rsc=_ZNg7N25YKTBT58c HTTP/1.1" 200 OK
INFO:     127.0.0.1:50610 - "GET /simulation/__next.simulation.__PAGE__.txt?_rsc=g_f9HLuT4dXJ9pHm HTTP/1.1" 200 OK
INFO:     127.0.0.1:53313 - "GET /simulation/__next.simulation.txt?_rsc=04Ydb1jP_pwZVlJk HTTP/1.1" 200 OK
INFO:     127.0.0.1:63957 - "HEAD /portfolio HTTP/1.1" 200 OK
INFO:     127.0.0.1:53101 - "HEAD /settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:53101 - "GET /optimization/__next.optimization.txt?_rsc=SfYN9thHGd86WoI_ HTTP/1.1" 200 OK
INFO:     127.0.0.1:63957 - "GET /optimization/__next._head.txt?_rsc=Uq2f8WKuJX_SrHVb HTTP/1.1" 200 OK
INFO:     127.0.0.1:53313 - "GET /_next/static/chunks/081se-ft_jhkj.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:50610 - "GET /_next/static/chunks/0h836-2iu34d8.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:63957 - "GET /settings/__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:53101 - "GET /portfolio/__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:53101 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60152 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60152 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60152 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:22:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:23:01 EEST)" (scheduled at 2026-05-17 10:22:31.625095+03:00)
2026-05-17 10:22:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:23:01 EEST)" executed successfully
INFO:     127.0.0.1:50760 - "GET /api/v1/ai/asset-reports/default HTTP/1.1" 200 OK
INFO:     127.0.0.1:50760 - "GET /api/v1/ai/asset-reports/history?ticker=EGX30 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50760 - "GET /api/v1/ai/asset-report?ticker=EGX30 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59742 - "GET /api/v1/ai/asset-reports/default HTTP/1.1" 200 OK
INFO:     127.0.0.1:50060 - "GET /api/v1/ai/asset-reports/history?ticker=EGX30 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59742 - "GET /api/v1/ai/asset-report?ticker=EGX30 HTTP/1.1" 200 OK
2026-05-17 10:23:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:23:31 EEST)" (scheduled at 2026-05-17 10:23:01.625095+03:00)
2026-05-17 10:23:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:23:31 EEST)" executed successfully
2026-05-17 10:23:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:24:01 EEST)" (scheduled at 2026-05-17 10:23:31.625095+03:00)
2026-05-17 10:23:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:24:01 EEST)" executed successfully
2026-05-17 10:24:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:24:31 EEST)" (scheduled at 2026-05-17 10:24:01.625095+03:00)
2026-05-17 10:24:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:24:31 EEST)" executed successfully
2026-05-17 10:24:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:25:01 EEST)" (scheduled at 2026-05-17 10:24:31.625095+03:00)
2026-05-17 10:24:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:25:01 EEST)" executed successfully
2026-05-17 10:25:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:25:31 EEST)" (scheduled at 2026-05-17 10:25:01.625095+03:00)
2026-05-17 10:25:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:25:31 EEST)" executed successfully
2026-05-17 10:25:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:26:01 EEST)" (scheduled at 2026-05-17 10:25:31.625095+03:00)
2026-05-17 10:25:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:26:01 EEST)" executed successfully
2026-05-17 10:26:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:26:31 EEST)" (scheduled at 2026-05-17 10:26:01.625095+03:00)
2026-05-17 10:26:01,630 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:26:31 EEST)" executed successfully
2026-05-17 10:26:05,663 - TelegramBot - WARNING - Telegram polling error (retry in 10s): HTTPSConnectionPool(host='api.telegram.org', port=443): Max retries exceeded with url: /bottoken/getUpdates?offset=1&timeout=30 (Caused by ConnectTimeoutError(<HTTPSConnection(host='api.telegram.org', port=443) at 0x1daef660cd0>, 'Connection to api.telegram.org timed out. (connect timeout=35)'))
2026-05-17 10:26:31,626 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:31:31 EEST)" (scheduled at 2026-05-17 10:26:31.618104+03:00)
2026-05-17 10:26:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:27:01 EEST)" (scheduled at 2026-05-17 10:26:31.625095+03:00)
2026-05-17 10:26:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:31:31 EEST)" (scheduled at 2026-05-17 10:26:31.622651+03:00)
2026-05-17 10:26:31,628 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:31:31 EEST)" executed successfully
2026-05-17 10:26:31,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:27:01 EEST)" executed successfully
2026-05-17 10:26:31,631 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:26:32,661 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 10:26:34,528 - DailyScanner - INFO - Parallel scoring 2 candidates...
2026-05-17 10:26:34,530 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 0 signals across 272 tickers.
2026-05-17 10:26:34,531 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 0 signals. Regime: BULLISH (73.8%)
2026-05-17 10:26:34,533 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 0 signals (regime=BULLISH).
2026-05-17 10:26:35,458 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=7
2026-05-17 10:26:35,505 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=7
2026-05-17 10:26:35,506 - horus.scheduling - INFO - [Scheduler] Intraday: no eligible signals after scheduler filters.
2026-05-17 10:26:36,347 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted per-run no-signal notice.
2026-05-17 10:26:36,400 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:31:31 EEST)" executed successfully
2026-05-17 10:27:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:27:31 EEST)" (scheduled at 2026-05-17 10:27:01.625095+03:00)
2026-05-17 10:27:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:27:31 EEST)" executed successfully
2026-05-17 10:27:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:28:01 EEST)" (scheduled at 2026-05-17 10:27:31.625095+03:00)
2026-05-17 10:27:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:28:01 EEST)" executed successfully
2026-05-17 10:28:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:28:31 EEST)" (scheduled at 2026-05-17 10:28:01.625095+03:00)
2026-05-17 10:28:01,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:28:31 EEST)" executed successfully
2026-05-17 10:28:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:29:01 EEST)" (scheduled at 2026-05-17 10:28:31.625095+03:00)
2026-05-17 10:28:31,650 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:29:01 EEST)" executed successfully
2026-05-17 10:29:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:29:31 EEST)" (scheduled at 2026-05-17 10:29:01.625095+03:00)
2026-05-17 10:29:01,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:29:31 EEST)" executed successfully
2026-05-17 10:29:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:30:01 EEST)" (scheduled at 2026-05-17 10:29:31.625095+03:00)
2026-05-17 10:29:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:30:01 EEST)" executed successfully
INFO:     127.0.0.1:61630 - "GET /api/v1/ai/asset-reports/default HTTP/1.1" 200 OK
[THE CANARY] Calculating Market Breadth...INFO:     127.0.0.1:54608 - "GET /api/v1/ai/asset-reports/history?ticker=EGX30 HTTP/1.1" 200 OK
[THE CANARY] Calculating Market Breadth...[THE CANARY] Calculating Market Breadth...[THE COIL] Hunting for explosive moves...INFO:     127.0.0.1:56574 - "GET /api/v1/ai/asset-report?ticker=EGX30 HTTP/1.1" 200 OK




[Info] Found 273 intraday CSV files to ingest.
INFO:     127.0.0.1:56574 - "HEAD /telegram HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "HEAD / HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /telegram/__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "HEAD /seasonality HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "HEAD /scanner HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "HEAD /oracle HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "HEAD /whales HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "HEAD /traps HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /whales.txt?_rsc=UFzp5-d06s6tD0gx HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /status/__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /seasonality/__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /api/v1/whales HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:30:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:30:31 EEST)" (scheduled at 2026-05-17 10:30:01.625095+03:00)
2026-05-17 10:30:01,674 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:30:31 EEST)" executed successfully
INFO:     127.0.0.1:54608 - "GET /scanner/__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /oracle/__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /whales/__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /traps/__next._tree.txt?_rsc=rB5t7FzcoklR81YW HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /_next/static/chunks/01v.fm7tf5508.js HTTP/1.1" 304 Not Modified
INFO:     127.0.0.1:56574 - "GET /telegram/__next._head.txt?_rsc=TF_-ybJ5J5etVK0q HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /telegram/__next._index.txt?_rsc=91MyYDxIgccYL8h3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /telegram/__next.telegram.txt?_rsc=h5c3MHSvLFjEnhFc HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /telegram/__next.telegram.__PAGE__.txt?_rsc=sZaPLMh9_SMRh_82 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /__next._head.txt?_rsc=TF_-ybJ5J5etVK0q HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /__next.__PAGE__.txt?_rsc=OslyClO1lmP6gxRY HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /status/__next._head.txt?_rsc=TF_-ybJ5J5etVK0q HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /status/__next.status.txt?_rsc=mB6tVQAYTRsNpBAP HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /status/__next.status.__PAGE__.txt?_rsc=NtIaqovqNeNUnkEv HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "HEAD /simulation HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "HEAD /arbitrage HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "HEAD /optimization HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "HEAD /strategy HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /simulation/__next._tree.txt?_rsc=QGzhGysM_lwLmeAK HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /arbitrage/__next._tree.txt?_rsc=QGzhGysM_lwLmeAK HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /optimization/__next._tree.txt?_rsc=QGzhGysM_lwLmeAK HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /strategy/__next._tree.txt?_rsc=QGzhGysM_lwLmeAK HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /scanner/__next._head.txt?_rsc=TF_-ybJ5J5etVK0q HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /scanner/__next.scanner.txt?_rsc=xUaWzwE-NwuSOGEo HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /traps.txt?_rsc=btuchEIsQS9Mh_es HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /scanner/__next.scanner.__PAGE__.txt?_rsc=TZukwdNiCC_-PgZm HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /oracle/__next._head.txt?_rsc=TF_-ybJ5J5etVK0q HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /oracle/__next.oracle.txt?_rsc=SNEASK7Nvai5KoAH HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /api/v1/traps HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /oracle/__next.oracle.__PAGE__.txt?_rsc=LJZYIzqx4ehAnPLY HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /whales/__next._head.txt?_rsc=TF_-ybJ5J5etVK0q HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /whales/__next.whales.txt?_rsc=Yf_BC3uc6aLumjeT HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /whales/__next.whales.__PAGE__.txt?_rsc=q8lcPRjuLLSStIjf HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /traps/__next._head.txt?_rsc=TF_-ybJ5J5etVK0q HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /traps/__next.traps.txt?_rsc=-1FKC2_Rqnkf40Xg HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /_next/static/chunks/0frmc4ub6zh4v.js HTTP/1.1" 304 Not Modified
INFO:     127.0.0.1:56574 - "GET /traps/__next.traps.__PAGE__.txt?_rsc=ttPA779xAHKGROJp HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "POST /api/v1/prediction HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "HEAD /sectors HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "HEAD /news HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "HEAD /live HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "HEAD /analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /sectors/__next._tree.txt?_rsc=amvuS9fQx_B9zkix HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /news/__next._tree.txt?_rsc=amvuS9fQx_B9zkix HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /live/__next._tree.txt?_rsc=amvuS9fQx_B9zkix HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /analytics/__next._tree.txt?_rsc=amvuS9fQx_B9zkix HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /seasonality/__next._head.txt?_rsc=I8huLZ2dkFLVllz7 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /seasonality/__next.seasonality.txt?_rsc=JyHNeeuv-ZMYmpqz HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /seasonality/__next.seasonality.__PAGE__.txt?_rsc=Rovs8lZfC73dcicv HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /analytics/__next._head.txt?_rsc=I8huLZ2dkFLVllz7 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /analytics/__next.analytics.txt?_rsc=QYA32x6bYLB6_3NC HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /sectors/__next._head.txt?_rsc=I8huLZ2dkFLVllz7 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /analytics/__next.analytics.__PAGE__.txt?_rsc=CDrIVd03SNzqqbHU HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /analytics.txt?_rsc=BB0443bOlCe6T39a HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /sectors/__next.sectors.txt?_rsc=lOiRErax8nQ6Wd8f HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /_next/static/chunks/174_5v60iih2w.js HTTP/1.1" 304 Not Modified
INFO:     127.0.0.1:54608 - "POST /api/v1/analytics/refresh HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /api/v1/analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /api/v1/analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /sectors/__next.sectors.__PAGE__.txt?_rsc=Km-UMdNdJGnfdURx HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /news/__next._head.txt?_rsc=22aXKK0pNCo6JOC8 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /news/__next.news.txt?_rsc=qqaIa_kJ1GgpaEVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /live.txt?_rsc=QTVJ0lxojjzMNLoY HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /news/__next.news.__PAGE__.txt?_rsc=dXwbJ7pHa1tOumjj HTTP/1.1" 200 OK
INFO:     ('127.0.0.1', 51951) - "WebSocket /ws" [accepted]
2026-05-17 10:30:31,649 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:31:01 EEST)" (scheduled at 2026-05-17 10:30:31.625095+03:00)
2026-05-17 10:30:31,815 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:31:01 EEST)" executed successfully
2026-05-17 10:30:34,515 - horus.websocket - INFO - WebSocket: New client connected. Total clients: 1
INFO:     connection open
INFO:     127.0.0.1:61630 - "GET /live/__next._head.txt?_rsc=22aXKK0pNCo6JOC8 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
2026-05-17 10:30:39,730 - LiveFeedManager - INFO - [LiveFeed] Refreshing resistance levels from shared analytics snapshot
2026-05-17 10:30:39,730 - LiveFeedManager - INFO - [LiveFeed] Starting real-time market ZMQ listener
2026-05-17 10:30:39,749 - LiveFeedManager - INFO - [LiveFeed] Loaded resistance levels for 268 tickers
INFO:     127.0.0.1:54608 - "POST /api/v1/live/start HTTP/1.1" 200 OK
2026-05-17 10:30:39,777 - LiveFeedManager - INFO - [LiveFeed] Connected to ZeroMQ stream on tcp://127.0.0.1:5556
INFO:     127.0.0.1:54608 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /live/__next.live.txt?_rsc=SN5XrT8E9BSJhwCG HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /live/__next.live.__PAGE__.txt?_rsc=zAT9CWCrGg-C0YcD HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /api/v1/data/tickers HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /_next/static/chunks/15983x1h..s50.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:56574 - "GET /_next/static/chunks/09i6ykbr4xxr0.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /api/v1/analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54608 - "GET /_next/static/chunks/0rga1efswmc.f.js HTTP/1.1" 304 Not Modified
INFO:     127.0.0.1:54608 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK

[MACRO PREDICTION] (EGX100):
[MACRO PREDICTION] (EGX70):

Correlation (Price vs Internal Strength): 0.97Correlation (Price vs Internal Strength): 0.96
INFO:     127.0.0.1:54608 - "GET /api/v1/live/status HTTP/1.1" 200 OK


[MACRO PREDICTION] (EGX30):INFO:     127.0.0.1:52459 - "POST /api/v1/prediction HTTP/1.1" 200 OK

INFO:     127.0.0.1:51635 - "POST /api/v1/prediction HTTP/1.1" 200 OK
Correlation (Price vs Internal Strength): 0.95INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK

INFO:     127.0.0.1:58359 - "POST /api/v1/prediction HTTP/1.1" 200 OK
[THE CANARY] Calculating Market Breadth...
INFO:     127.0.0.1:53690 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK

[MACRO PREDICTION] (EGX30):
Correlation (Price vs Internal Strength): 0.95
[THE COIL] Hunting for explosive moves...
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:31:00,521 - horus.confluence - INFO - Confluence: Analyzing Sovereign Hedge signals...
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
2026-05-17 10:31:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:31:31 EEST)" (scheduled at 2026-05-17 10:31:01.625095+03:00)
2026-05-17 10:31:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:31:31 EEST)" executed successfully
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:31:27,287 - horus.websocket - INFO - WebSocket: Client disconnected. Total clients: 0
INFO:     connection closed
INFO:     127.0.0.1:54694 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53690 - "GET /api/v1/analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics HTTP/1.1" 200 OK
2026-05-17 10:31:31,628 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:36:31 EEST)" (scheduled at 2026-05-17 10:31:31.618104+03:00)
2026-05-17 10:31:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:36:31 EEST)" (scheduled at 2026-05-17 10:31:31.622651+03:00)
2026-05-17 10:31:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 10:41:31 EEST)" (scheduled at 2026-05-17 10:31:31.627072+03:00)
2026-05-17 10:31:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:32:01 EEST)" (scheduled at 2026-05-17 10:31:31.625095+03:00)
2026-05-17 10:31:31,629 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:36:31 EEST)" executed successfully
2026-05-17 10:31:31,631 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:31:31,633 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 10:41:31 EEST)" executed successfully
2026-05-17 10:31:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:32:01 EEST)" executed successfully
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
2026-05-17 10:31:34,976 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 10:31:34,978 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
2026-05-17 10:31:38,305 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 10:31:38,310 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 1 signals across 272 tickers.
2026-05-17 10:31:38,310 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 1 signals. Regime: BULLISH (71.1%)
2026-05-17 10:31:38,312 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 1 signals (regime=BULLISH).
INFO:     127.0.0.1:60465 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
2026-05-17 10:31:40,749 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=8
2026-05-17 10:31:41,201 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=8
2026-05-17 10:31:41,211 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasting 1 signals after dedup.
INFO:     127.0.0.1:51659 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "POST /api/v1/analytics/refresh HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
2026-05-17 10:31:44,579 - horus.scheduling - INFO - [Scheduler] Intraday: broadcast completed (cards=1, summary_signals=1).
2026-05-17 10:31:44,871 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:36:31 EEST)" executed successfully
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60465 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60465 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60465 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60465 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
2026-05-17 10:32:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:32:31 EEST)" (scheduled at 2026-05-17 10:32:01.625095+03:00)
2026-05-17 10:32:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:32:31 EEST)" executed successfully
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51659 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/ai/daily-report?use_llm=true HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
2026-05-17 10:32:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:33:01 EEST)" (scheduled at 2026-05-17 10:32:31.625095+03:00)
2026-05-17 10:32:31,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:33:01 EEST)" executed successfully
INFO:     127.0.0.1:58359 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58359 - "GET /api/v1/analytics HTTP/1.1" 200 OK
2026-05-17 10:33:01,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:33:31 EEST)" (scheduled at 2026-05-17 10:33:01.625095+03:00)
2026-05-17 10:33:01,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:33:31 EEST)" executed successfully
2026-05-17 10:33:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:34:01 EEST)" (scheduled at 2026-05-17 10:33:31.625095+03:00)
2026-05-17 10:33:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:34:01 EEST)" executed successfully
2026-05-17 10:34:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:34:31 EEST)" (scheduled at 2026-05-17 10:34:01.625095+03:00)
2026-05-17 10:34:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:34:31 EEST)" executed successfully
INFO:     127.0.0.1:58525 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55646 - "GET /api/v1/data/sync/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56309 - "GET /api/v1/system/full-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60263 - "GET /api/v1/data/runtime-universe HTTP/1.1" 200 OK
INFO:     127.0.0.1:55646 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60263 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54441 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:34:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:35:01 EEST)" (scheduled at 2026-05-17 10:34:31.625095+03:00)
2026-05-17 10:34:31,630 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:35:01 EEST)" executed successfully
INFO:     127.0.0.1:57875 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:35:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:35:31 EEST)" (scheduled at 2026-05-17 10:35:01.625095+03:00)
2026-05-17 10:35:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:35:31 EEST)" executed successfully
INFO:     127.0.0.1:63510 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63510 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63510 - "GET /status/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:63510 - "GET /status/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /status/__next._index.txt?_rsc=4MEx1ygTCVrtW97z HTTP/1.1" 200 OK
INFO:     127.0.0.1:63510 - "GET /status/__next.status.txt?_rsc=50rOQS8YzswLD0DR HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /status/__next.status.__PAGE__.txt?_rsc=_grtAnSmDF_oUHwj HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "HEAD / HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "HEAD /telegram HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "GET /__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "GET /telegram/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "GET /__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /__next.__PAGE__.txt?_rsc=pjS4j3toLip68L1B HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "GET /telegram/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "GET /telegram/__next.telegram.txt?_rsc=iiCMEg1vWeky2Yqz HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /telegram/__next.telegram.__PAGE__.txt?_rsc=j6YW8APr_TVaTQM6 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:35:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:36:01 EEST)" (scheduled at 2026-05-17 10:35:31.625095+03:00)
2026-05-17 10:35:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:36:01 EEST)" executed successfully
INFO:     127.0.0.1:64687 - "HEAD /arbitrage HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "HEAD /simulation HTTP/1.1" 200 OK
INFO:     127.0.0.1:62344 - "HEAD /strategy HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "HEAD /optimization HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /arbitrage/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "GET /simulation/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62344 - "GET /strategy/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "GET /optimization/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "HEAD /seasonality HTTP/1.1" 200 OK
INFO:     127.0.0.1:62344 - "HEAD /sectors HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "HEAD /news HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "HEAD /live HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "GET /news/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62344 - "GET /sectors/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "GET /seasonality/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /live/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "HEAD /whales HTTP/1.1" 200 OK
INFO:     127.0.0.1:62344 - "HEAD /traps HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "HEAD /analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:62344 - "GET /traps/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "GET /whales/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "GET /analytics/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "HEAD /oracle HTTP/1.1" 200 OK
INFO:     127.0.0.1:62344 - "HEAD /scanner HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "GET /seasonality/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /seasonality/__next.seasonality.txt?_rsc=c__T35oKcmDKMxyU HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "GET /oracle/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62344 - "GET /scanner/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "GET /sectors/__next.sectors.txt?_rsc=Ubi_EAg4_U8pPfXo HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /seasonality/__next.seasonality.__PAGE__.txt?_rsc=g8cPKWi2iPLBA9Jd HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "GET /sectors/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:62344 - "GET /scanner/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "GET /scanner/__next.scanner.txt?_rsc=kUAJRUjKc1DLmpBG HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "GET /oracle/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /scanner/__next.scanner.__PAGE__.txt?_rsc=rMMHTuojG-ySHfev HTTP/1.1" 200 OK
INFO:     127.0.0.1:62344 - "GET /oracle/__next.oracle.txt?_rsc=ls9ie-F7xO1D9MiX HTTP/1.1" 200 OK
INFO:     127.0.0.1:61521 - "GET /oracle/__next.oracle.__PAGE__.txt?_rsc=G7LJPXUAafnbD-Dn HTTP/1.1" 200 OK
INFO:     127.0.0.1:50190 - "GET /whales/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "GET /whales/__next.whales.txt?_rsc=YU7ft0vI3I_UxvRJ HTTP/1.1" 200 OK
INFO:     127.0.0.1:64770 - "GET /traps/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /whales/__next.whales.__PAGE__.txt?_rsc=8QcRvE-Rc6E1UoD- HTTP/1.1" 200 OK
INFO:     127.0.0.1:62344 - "GET /traps/__next.traps.txt?_rsc=fHX1pRFVaab7Rhid HTTP/1.1" 200 OK
INFO:     127.0.0.1:61521 - "GET /traps/__next.traps.__PAGE__.txt?_rsc=Oe56S6y5oFjvDNFT HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "GET /analytics/__next.analytics.txt?_rsc=txKai92synJMYgKH HTTP/1.1" 200 OK
INFO:     127.0.0.1:50190 - "GET /analytics/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /analytics/__next.analytics.__PAGE__.txt?_rsc=j1fZUVtxGfT3-x1X HTTP/1.1" 200 OK
INFO:     127.0.0.1:50190 - "GET /sectors/__next.sectors.__PAGE__.txt?_rsc=MoOxbM3O1wn419iX HTTP/1.1" 200 OK
INFO:     127.0.0.1:62907 - "GET /news/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:61521 - "GET /news/__next.news.txt?_rsc=MA3Vx5v4-4kVq0H8 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /news/__next.news.__PAGE__.txt?_rsc=2ig0RtLsEIme-Y9A HTTP/1.1" 200 OK
INFO:     127.0.0.1:64687 - "GET /api/v1/analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:61521 - "GET /api/v1/analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:61521 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55670 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55670 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:36:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:36:31 EEST)" (scheduled at 2026-05-17 10:36:01.625095+03:00)
2026-05-17 10:36:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:36:31 EEST)" executed successfully
INFO:     127.0.0.1:64205 - "HEAD /audit HTTP/1.1" 200 OK
INFO:     127.0.0.1:64205 - "HEAD /reports/weekly HTTP/1.1" 200 OK
INFO:     127.0.0.1:64205 - "GET /arbitrage/__next._head.txt?_rsc=22aXKK0pNCo6JOC8 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64205 - "GET /arbitrage/__next.arbitrage.txt?_rsc=dCWoO-H1d7L6vGmY HTTP/1.1" 200 OK
INFO:     127.0.0.1:51647 - "GET /audit/__next._tree.txt?_rsc=ix5_aAief6TvBg04 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58046 - "GET /reports/weekly/__next._tree.txt?_rsc=ix5_aAief6TvBg04 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58046 - "GET /live/__next._head.txt?_rsc=22aXKK0pNCo6JOC8 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51647 - "GET /live/__next.live.txt?_rsc=SN5XrT8E9BSJhwCG HTTP/1.1" 200 OK
INFO:     127.0.0.1:64205 - "GET /live/__next.live.__PAGE__.txt?_rsc=zAT9CWCrGg-C0YcD HTTP/1.1" 200 OK
INFO:     127.0.0.1:64205 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55692 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53720 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:55692 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     ('127.0.0.1', 64998) - "WebSocket /ws" [accepted]
2026-05-17 10:36:17,951 - horus.websocket - INFO - WebSocket: New client connected. Total clients: 1
INFO:     connection open
INFO:     127.0.0.1:62678 - "GET /api/v1/data/tickers HTTP/1.1" 200 OK
INFO:     127.0.0.1:58230 - "GET /api/v1/analytics HTTP/1.1" 200 OK
INFO:     127.0.0.1:62678 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58230 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58230 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:36:31,629 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:41:31 EEST)" (scheduled at 2026-05-17 10:36:31.618104+03:00)
2026-05-17 10:36:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:41:31 EEST)" (scheduled at 2026-05-17 10:36:31.622651+03:00)
2026-05-17 10:36:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:37:01 EEST)" (scheduled at 2026-05-17 10:36:31.625095+03:00)
2026-05-17 10:36:31,630 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:41:31 EEST)" executed successfully
2026-05-17 10:36:31,631 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:36:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:37:01 EEST)" executed successfully
INFO:     127.0.0.1:58230 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54717 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49674 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 10:36:32,828 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 10:36:35,124 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 10:36:35,127 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 1 signals across 272 tickers.
2026-05-17 10:36:35,128 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 1 signals. Regime: BULLISH (71.1%)
2026-05-17 10:36:35,130 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 1 signals (regime=BULLISH).
2026-05-17 10:36:36,625 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=9
2026-05-17 10:36:36,685 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=9
2026-05-17 10:36:36,687 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=1 counts_by_reason={'repeat_cooldown': 1} dropped_tickers=['SUGR']
2026-05-17 10:36:36,689 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 1/1 signals.
2026-05-17 10:36:36,755 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 1 signals; nothing to broadcast.
2026-05-17 10:36:37,600 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 10:36:37,670 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:41:31 EEST)" executed successfully
INFO:     127.0.0.1:53443 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62795 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62795 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62795 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64433 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:37:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:37:31 EEST)" (scheduled at 2026-05-17 10:37:01.625095+03:00)
2026-05-17 10:37:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:37:31 EEST)" executed successfully
INFO:     127.0.0.1:64433 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64433 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63484 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56632 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56632 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:37:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:38:01 EEST)" (scheduled at 2026-05-17 10:37:31.625095+03:00)
2026-05-17 10:37:31,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:38:01 EEST)" executed successfully
INFO:     127.0.0.1:56781 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56781 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49743 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51380 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56901 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49678 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49678 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:38:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:38:31 EEST)" (scheduled at 2026-05-17 10:38:01.625095+03:00)
2026-05-17 10:38:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:38:31 EEST)" executed successfully
INFO:     127.0.0.1:52689 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52689 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60871 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61017 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54915 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53493 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53493 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:38:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:39:01 EEST)" (scheduled at 2026-05-17 10:38:31.625095+03:00)
2026-05-17 10:38:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:39:01 EEST)" executed successfully
INFO:     127.0.0.1:61972 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61632 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62061 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62061 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:39:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:39:31 EEST)" (scheduled at 2026-05-17 10:39:01.625095+03:00)
2026-05-17 10:39:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:39:31 EEST)" executed successfully
INFO:     127.0.0.1:50961 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56565 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:39:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:40:01 EEST)" (scheduled at 2026-05-17 10:39:31.625095+03:00)
2026-05-17 10:39:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:40:01 EEST)" executed successfully
INFO:     127.0.0.1:50061 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56687 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57440 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57440 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60571 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:40:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:40:31 EEST)" (scheduled at 2026-05-17 10:40:01.625095+03:00)
2026-05-17 10:40:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:40:31 EEST)" executed successfully
INFO:     127.0.0.1:62576 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55368 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60996 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:40:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:41:01 EEST)" (scheduled at 2026-05-17 10:40:31.625095+03:00)
2026-05-17 10:40:31,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:41:01 EEST)" executed successfully
INFO:     127.0.0.1:64445 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64445 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64445 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64445 - "GET /api/v1/data/status HTTP/1.1" 200 OK
2026-05-17 10:40:48,604 - TelegramBot - WARNING - Telegram polling error (retry in 80s): HTTPSConnectionPool(host='api.telegram.org', port=443): Max retries exceeded with url: /bottoken/getUpdates?offset=1&timeout=30 (Caused by ConnectTimeoutError(<HTTPSConnection(host='api.telegram.org', port=443) at 0x1daf232d090>, 'Connection to api.telegram.org timed out. (connect timeout=35)'))
INFO:     127.0.0.1:60064 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60064 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61111 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:41:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:41:31 EEST)" (scheduled at 2026-05-17 10:41:01.625095+03:00)
2026-05-17 10:41:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:41:31 EEST)" executed successfully
INFO:     127.0.0.1:57718 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51632 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61333 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61333 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56927 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56927 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50195 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:41:31,626 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:46:31 EEST)" (scheduled at 2026-05-17 10:41:31.618104+03:00)
2026-05-17 10:41:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:46:31 EEST)" (scheduled at 2026-05-17 10:41:31.622651+03:00)
2026-05-17 10:41:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:42:01 EEST)" (scheduled at 2026-05-17 10:41:31.625095+03:00)
2026-05-17 10:41:31,628 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:46:31 EEST)" executed successfully
2026-05-17 10:41:31,629 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:41:31,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:42:01 EEST)" executed successfully
2026-05-17 10:41:31,642 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 10:51:31 EEST)" (scheduled at 2026-05-17 10:41:31.627072+03:00)
2026-05-17 10:41:31,645 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 10:51:31 EEST)" executed successfully
2026-05-17 10:41:33,565 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 10:41:33,567 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
INFO:     127.0.0.1:50084 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:41:35,725 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 10:41:35,729 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 1 signals across 272 tickers.
2026-05-17 10:41:35,730 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 1 signals. Regime: BULLISH (71.1%)
2026-05-17 10:41:35,732 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 1 signals (regime=BULLISH).
2026-05-17 10:41:36,732 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=10
2026-05-17 10:41:36,779 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=10
2026-05-17 10:41:36,780 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=1 counts_by_reason={'repeat_cooldown': 1} dropped_tickers=['SUGR']
2026-05-17 10:41:36,781 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 1/1 signals.
2026-05-17 10:41:36,827 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 1 signals; nothing to broadcast.
2026-05-17 10:41:37,741 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 10:41:37,800 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:46:31 EEST)" executed successfully
INFO:     127.0.0.1:64456 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64456 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64456 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64456 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57866 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59096 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57866 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:42:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:42:31 EEST)" (scheduled at 2026-05-17 10:42:01.625095+03:00)
2026-05-17 10:42:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:42:31 EEST)" executed successfully
INFO:     127.0.0.1:59999 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59771 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56754 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56754 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:42:30,342 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T10:42:26.233893). Version incremented to 1.
INFO:     127.0.0.1:59862 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52435 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:42:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:43:01 EEST)" (scheduled at 2026-05-17 10:42:31.625095+03:00)
2026-05-17 10:42:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:43:01 EEST)" executed successfully
INFO:     127.0.0.1:49983 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60653 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52460 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:43:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:43:31 EEST)" (scheduled at 2026-05-17 10:43:01.625095+03:00)
2026-05-17 10:43:01,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:43:31 EEST)" executed successfully
INFO:     127.0.0.1:52460 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54947 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49674 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:43:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:44:01 EEST)" (scheduled at 2026-05-17 10:43:31.625095+03:00)
2026-05-17 10:43:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:44:01 EEST)" executed successfully
INFO:     127.0.0.1:53237 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56196 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61330 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58006 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:44:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:44:31 EEST)" (scheduled at 2026-05-17 10:44:01.625095+03:00)
2026-05-17 10:44:01,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:44:31 EEST)" executed successfully
INFO:     127.0.0.1:57456 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61791 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59677 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:44:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:45:01 EEST)" (scheduled at 2026-05-17 10:44:31.625095+03:00)
2026-05-17 10:44:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:45:01 EEST)" executed successfully
INFO:     127.0.0.1:61108 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50158 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50158 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:55291 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:45:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:45:31 EEST)" (scheduled at 2026-05-17 10:45:01.625095+03:00)
2026-05-17 10:45:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:45:31 EEST)" executed successfully
INFO:     127.0.0.1:55298 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65198 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58853 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:45:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:46:01 EEST)" (scheduled at 2026-05-17 10:45:31.625095+03:00)
2026-05-17 10:45:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:46:01 EEST)" executed successfully
INFO:     127.0.0.1:52982 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52572 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56748 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64285 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64285 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:46:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:46:31 EEST)" (scheduled at 2026-05-17 10:46:01.625095+03:00)
2026-05-17 10:46:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:46:31 EEST)" executed successfully
INFO:     127.0.0.1:56069 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55440 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:46:31,622 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:51:31 EEST)" (scheduled at 2026-05-17 10:46:31.618104+03:00)
2026-05-17 10:46:31,623 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:51:31 EEST)" executed successfully
2026-05-17 10:46:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:51:31 EEST)" (scheduled at 2026-05-17 10:46:31.622651+03:00)
2026-05-17 10:46:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:47:01 EEST)" (scheduled at 2026-05-17 10:46:31.625095+03:00)
2026-05-17 10:46:31,645 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:46:31,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:47:01 EEST)" executed successfully
INFO:     127.0.0.1:61688 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:46:33,614 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 10:46:33,615 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 10:46:35,496 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 10:46:35,499 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 1 signals across 272 tickers.
2026-05-17 10:46:35,500 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 1 signals. Regime: BULLISH (71.1%)
2026-05-17 10:46:35,502 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 1 signals (regime=BULLISH).
2026-05-17 10:46:36,436 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=11
2026-05-17 10:46:36,483 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=11
2026-05-17 10:46:36,484 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=1 counts_by_reason={'repeat_cooldown': 1} dropped_tickers=['SUGR']
2026-05-17 10:46:36,485 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 1/1 signals.
2026-05-17 10:46:36,529 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 1 signals; nothing to broadcast.
2026-05-17 10:46:37,397 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 10:46:37,452 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:51:31 EEST)" executed successfully
INFO:     127.0.0.1:62108 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55979 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60302 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:47:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:47:31 EEST)" (scheduled at 2026-05-17 10:47:01.625095+03:00)
2026-05-17 10:47:01,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:47:31 EEST)" executed successfully
INFO:     127.0.0.1:54202 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53127 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54808 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:47:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:48:01 EEST)" (scheduled at 2026-05-17 10:47:31.625095+03:00)
2026-05-17 10:47:31,645 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T10:47:27.209041). Version incremented to 2.
2026-05-17 10:47:31,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:48:01 EEST)" executed successfully
INFO:     127.0.0.1:54163 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63763 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50604 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59070 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59070 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:48:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:48:31 EEST)" (scheduled at 2026-05-17 10:48:01.625095+03:00)
2026-05-17 10:48:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:48:31 EEST)" executed successfully
INFO:     127.0.0.1:64054 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58519 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:48:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:49:01 EEST)" (scheduled at 2026-05-17 10:48:31.625095+03:00)
2026-05-17 10:48:31,651 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:49:01 EEST)" executed successfully
INFO:     127.0.0.1:60273 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51870 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61731 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61731 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60312 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:49:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:49:31 EEST)" (scheduled at 2026-05-17 10:49:01.625095+03:00)
2026-05-17 10:49:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:49:31 EEST)" executed successfully
INFO:     127.0.0.1:60734 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64553 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51822 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:49:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:50:01 EEST)" (scheduled at 2026-05-17 10:49:31.625095+03:00)
2026-05-17 10:49:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:50:01 EEST)" executed successfully
INFO:     127.0.0.1:65501 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63406 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50258 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56926 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56926 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:50:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:50:31 EEST)" (scheduled at 2026-05-17 10:50:01.625095+03:00)
2026-05-17 10:50:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:50:31 EEST)" executed successfully
INFO:     127.0.0.1:64356 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51710 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:50:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:51:01 EEST)" (scheduled at 2026-05-17 10:50:31.625095+03:00)
2026-05-17 10:50:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:51:01 EEST)" executed successfully
INFO:     127.0.0.1:52982 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57761 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63342 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63342 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59247 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:51:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:51:31 EEST)" (scheduled at 2026-05-17 10:51:01.625095+03:00)
2026-05-17 10:51:01,652 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:51:31 EEST)" executed successfully
INFO:     127.0.0.1:65192 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55197 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59121 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:51:31,629 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:56:31 EEST)" (scheduled at 2026-05-17 10:51:31.618104+03:00)
2026-05-17 10:51:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:56:31 EEST)" (scheduled at 2026-05-17 10:51:31.622651+03:00)
2026-05-17 10:51:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:01:31 EEST)" (scheduled at 2026-05-17 10:51:31.627072+03:00)
2026-05-17 10:51:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:52:01 EEST)" (scheduled at 2026-05-17 10:51:31.625095+03:00)
2026-05-17 10:51:31,634 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 10:56:31 EEST)" executed successfully
2026-05-17 10:51:31,636 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:51:31,640 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:01:31 EEST)" executed successfully
2026-05-17 10:51:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:52:01 EEST)" executed successfully
2026-05-17 10:51:33,950 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 10:51:33,951 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 10:51:36,904 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 10:51:36,908 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 1 signals across 272 tickers.
2026-05-17 10:51:36,909 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 1 signals. Regime: BULLISH (71.1%)
2026-05-17 10:51:36,911 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 1 signals (regime=BULLISH).
2026-05-17 10:51:38,308 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=12
2026-05-17 10:51:38,367 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=12
2026-05-17 10:51:38,369 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=1 counts_by_reason={'repeat_cooldown': 1} dropped_tickers=['SUGR']
2026-05-17 10:51:38,370 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 1/1 signals.
2026-05-17 10:51:38,428 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 1 signals; nothing to broadcast.
2026-05-17 10:51:39,273 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 10:51:39,336 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 10:56:31 EEST)" executed successfully
INFO:     127.0.0.1:63133 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52700 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61760 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59008 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:52:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:52:31 EEST)" (scheduled at 2026-05-17 10:52:01.625095+03:00)
2026-05-17 10:52:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:52:31 EEST)" executed successfully
INFO:     127.0.0.1:59008 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55202 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57616 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:52:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:53:01 EEST)" (scheduled at 2026-05-17 10:52:31.625095+03:00)
2026-05-17 10:52:31,640 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T10:52:28.114264). Version incremented to 3.
2026-05-17 10:52:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:53:01 EEST)" executed successfully
INFO:     127.0.0.1:57172 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61881 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57277 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62259 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:53:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:53:31 EEST)" (scheduled at 2026-05-17 10:53:01.625095+03:00)
2026-05-17 10:53:01,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:53:31 EEST)" executed successfully
INFO:     127.0.0.1:53167 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49313 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49676 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:53:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:54:01 EEST)" (scheduled at 2026-05-17 10:53:31.625095+03:00)
2026-05-17 10:53:31,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:54:01 EEST)" executed successfully
INFO:     127.0.0.1:64239 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62471 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54492 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51710 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:54:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:54:31 EEST)" (scheduled at 2026-05-17 10:54:01.625095+03:00)
2026-05-17 10:54:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:54:31 EEST)" executed successfully
INFO:     127.0.0.1:51710 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54277 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60621 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:54:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:55:01 EEST)" (scheduled at 2026-05-17 10:54:31.625095+03:00)
2026-05-17 10:54:31,655 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:55:01 EEST)" executed successfully
INFO:     127.0.0.1:63999 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53723 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61914 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57778 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:55:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:55:31 EEST)" (scheduled at 2026-05-17 10:55:01.625095+03:00)
2026-05-17 10:55:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:55:31 EEST)" executed successfully
INFO:     127.0.0.1:62626 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59418 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62446 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:55:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:56:01 EEST)" (scheduled at 2026-05-17 10:55:31.625095+03:00)
2026-05-17 10:55:31,650 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:56:01 EEST)" executed successfully
INFO:     127.0.0.1:57955 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51570 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:56:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:56:31 EEST)" (scheduled at 2026-05-17 10:56:01.625095+03:00)
2026-05-17 10:56:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:56:31 EEST)" executed successfully
INFO:     127.0.0.1:59139 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50721 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49867 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:56:31,619 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:01:31 EEST)" (scheduled at 2026-05-17 10:56:31.618104+03:00)
2026-05-17 10:56:31,620 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:01:31 EEST)" executed successfully
2026-05-17 10:56:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:01:31 EEST)" (scheduled at 2026-05-17 10:56:31.622651+03:00)
2026-05-17 10:56:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:57:01 EEST)" (scheduled at 2026-05-17 10:56:31.625095+03:00)
2026-05-17 10:56:31,636 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 10:56:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:57:01 EEST)" executed successfully
2026-05-17 10:56:34,154 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 10:56:34,156 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 10:56:36,469 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 10:56:36,474 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 1 signals across 272 tickers.
2026-05-17 10:56:36,475 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 1 signals. Regime: BULLISH (71.1%)
2026-05-17 10:56:36,477 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 1 signals (regime=BULLISH).
INFO:     127.0.0.1:60045 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:56:37,909 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=13
2026-05-17 10:56:37,967 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=13
2026-05-17 10:56:37,968 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=1 counts_by_reason={'repeat_cooldown': 1} dropped_tickers=['SUGR']
2026-05-17 10:56:37,969 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 1/1 signals.
2026-05-17 10:56:38,025 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 1 signals; nothing to broadcast.
2026-05-17 10:56:38,933 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 10:56:38,993 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:01:31 EEST)" executed successfully
INFO:     127.0.0.1:54137 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53708 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58330 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58330 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:57:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:57:31 EEST)" (scheduled at 2026-05-17 10:57:01.625095+03:00)
2026-05-17 10:57:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:57:31 EEST)" executed successfully
INFO:     127.0.0.1:58128 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52130 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:57:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:58:01 EEST)" (scheduled at 2026-05-17 10:57:31.625095+03:00)
2026-05-17 10:57:31,637 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T10:57:29.228312). Version incremented to 4.
2026-05-17 10:57:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:58:01 EEST)" executed successfully
INFO:     127.0.0.1:52832 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55836 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55416 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56060 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 10:58:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:58:31 EEST)" (scheduled at 2026-05-17 10:58:01.625095+03:00)
2026-05-17 10:58:01,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:58:31 EEST)" executed successfully
INFO:     127.0.0.1:52631 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53106 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57705 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:58:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:59:01 EEST)" (scheduled at 2026-05-17 10:58:31.625095+03:00)
2026-05-17 10:58:31,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:59:01 EEST)" executed successfully
INFO:     127.0.0.1:53195 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58535 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62928 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57255 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57255 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:59:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:59:31 EEST)" (scheduled at 2026-05-17 10:59:01.625095+03:00)
2026-05-17 10:59:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 10:59:31 EEST)" executed successfully
INFO:     127.0.0.1:60198 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51370 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 10:59:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:00:01 EEST)" (scheduled at 2026-05-17 10:59:31.625095+03:00)
2026-05-17 10:59:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:00:01 EEST)" executed successfully
INFO:     127.0.0.1:56304 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54892 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50846 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50846 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64159 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:00:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:00:31 EEST)" (scheduled at 2026-05-17 11:00:01.625095+03:00)
2026-05-17 11:00:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:00:31 EEST)" executed successfully
INFO:     127.0.0.1:53867 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60825 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59213 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:00:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:01:01 EEST)" (scheduled at 2026-05-17 11:00:31.625095+03:00)
2026-05-17 11:00:31,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:01:01 EEST)" executed successfully
INFO:     127.0.0.1:62699 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64258 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64848 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57151 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57151 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:01:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:01:31 EEST)" (scheduled at 2026-05-17 11:01:01.625095+03:00)
2026-05-17 11:01:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:01:31 EEST)" executed successfully
INFO:     127.0.0.1:51587 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65403 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:01:31,621 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:06:31 EEST)" (scheduled at 2026-05-17 11:01:31.618104+03:00)
2026-05-17 11:01:31,624 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:06:31 EEST)" executed successfully
2026-05-17 11:01:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:06:31 EEST)" (scheduled at 2026-05-17 11:01:31.622651+03:00)
2026-05-17 11:01:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:11:31 EEST)" (scheduled at 2026-05-17 11:01:31.627072+03:00)
2026-05-17 11:01:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:02:01 EEST)" (scheduled at 2026-05-17 11:01:31.625095+03:00)
2026-05-17 11:01:31,638 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 11:01:31,641 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:11:31 EEST)" executed successfully
2026-05-17 11:01:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:02:01 EEST)" executed successfully
2026-05-17 11:01:32,719 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
INFO:     127.0.0.1:53686 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:01:34,774 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:01:34,780 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 1 signals across 272 tickers.
2026-05-17 11:01:34,782 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 1 signals. Regime: BULLISH (71.1%)
2026-05-17 11:01:34,785 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 1 signals (regime=BULLISH).
2026-05-17 11:01:35,744 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=14
2026-05-17 11:01:35,796 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=14
2026-05-17 11:01:35,798 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=1 counts_by_reason={'repeat_cooldown': 1} dropped_tickers=['SUGR']
2026-05-17 11:01:35,800 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 1/1 signals.
2026-05-17 11:01:35,860 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 1 signals; nothing to broadcast.
2026-05-17 11:01:36,736 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 11:01:36,788 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:06:31 EEST)" executed successfully
INFO:     127.0.0.1:60546 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61683 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61683 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52466 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:02:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:02:31 EEST)" (scheduled at 2026-05-17 11:02:01.625095+03:00)
2026-05-17 11:02:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:02:31 EEST)" executed successfully
2026-05-17 11:02:03,429 - TelegramBot - WARNING - Telegram polling error (retry in 160s): HTTPSConnectionPool(host='api.telegram.org', port=443): Max retries exceeded with url: /bottoken/getUpdates?offset=1&timeout=30 (Caused by ConnectTimeoutError(<HTTPSConnection(host='api.telegram.org', port=443) at 0x1daef660cd0>, 'Connection to api.telegram.org timed out. (connect timeout=35)'))
INFO:     127.0.0.1:52982 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61631 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62564 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:02:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:03:01 EEST)" (scheduled at 2026-05-17 11:02:31.625095+03:00)
2026-05-17 11:02:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:03:01 EEST)" executed successfully
2026-05-17 11:02:40,026 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:02:30.249134). Version incremented to 5.
INFO:     127.0.0.1:51955 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62139 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49811 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53610 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:03:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:03:31 EEST)" (scheduled at 2026-05-17 11:03:01.625095+03:00)
2026-05-17 11:03:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:03:31 EEST)" executed successfully
INFO:     127.0.0.1:53610 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50898 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56377 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:03:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:04:01 EEST)" (scheduled at 2026-05-17 11:03:31.625095+03:00)
2026-05-17 11:03:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:04:01 EEST)" executed successfully
INFO:     127.0.0.1:61120 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53548 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62168 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62168 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50604 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:04:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:04:31 EEST)" (scheduled at 2026-05-17 11:04:01.625095+03:00)
2026-05-17 11:04:01,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:04:31 EEST)" executed successfully
INFO:     127.0.0.1:54436 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57935 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55525 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:04:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:05:01 EEST)" (scheduled at 2026-05-17 11:04:31.625095+03:00)
2026-05-17 11:04:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:05:01 EEST)" executed successfully
INFO:     127.0.0.1:49676 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49676 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63496 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58401 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:05:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:05:31 EEST)" (scheduled at 2026-05-17 11:05:01.625095+03:00)
2026-05-17 11:05:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:05:31 EEST)" executed successfully
INFO:     127.0.0.1:58401 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60403 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52272 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:05:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:06:01 EEST)" (scheduled at 2026-05-17 11:05:31.625095+03:00)
2026-05-17 11:05:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:06:01 EEST)" executed successfully
INFO:     127.0.0.1:55474 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56393 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53966 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58560 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:06:01,625 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:06:31 EEST)" (scheduled at 2026-05-17 11:06:01.625095+03:00)
2026-05-17 11:06:01,630 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:06:31 EEST)" executed successfully
INFO:     127.0.0.1:61332 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49306 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50967 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:06:31,619 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:11:31 EEST)" (scheduled at 2026-05-17 11:06:31.618104+03:00)
2026-05-17 11:06:31,621 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:11:31 EEST)" executed successfully
2026-05-17 11:06:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:11:31 EEST)" (scheduled at 2026-05-17 11:06:31.622651+03:00)
2026-05-17 11:06:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:07:01 EEST)" (scheduled at 2026-05-17 11:06:31.625095+03:00)
2026-05-17 11:06:31,636 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 11:06:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:07:01 EEST)" executed successfully
2026-05-17 11:06:34,078 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 11:06:34,079 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 11:06:36,535 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:06:36,539 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 1 signals across 272 tickers.
2026-05-17 11:06:36,540 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 1 signals. Regime: BULLISH (71.1%)
2026-05-17 11:06:36,542 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 1 signals (regime=BULLISH).
2026-05-17 11:06:37,672 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=15
2026-05-17 11:06:37,730 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=15
2026-05-17 11:06:37,732 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=1 counts_by_reason={'repeat_cooldown': 1} dropped_tickers=['SUGR']
2026-05-17 11:06:37,733 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 1/1 signals.
2026-05-17 11:06:37,790 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 1 signals; nothing to broadcast.
2026-05-17 11:06:38,617 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 11:06:38,683 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:11:31 EEST)" executed successfully
INFO:     127.0.0.1:53004 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50861 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50861 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:55055 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:07:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:07:31 EEST)" (scheduled at 2026-05-17 11:07:01.625095+03:00)
2026-05-17 11:07:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:07:31 EEST)" executed successfully
INFO:     127.0.0.1:51587 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49872 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50605 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:07:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:08:01 EEST)" (scheduled at 2026-05-17 11:07:31.625095+03:00)
2026-05-17 11:07:31,638 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:07:31.172560). Version incremented to 6.
2026-05-17 11:07:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:08:01 EEST)" executed successfully
INFO:     127.0.0.1:50719 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65452 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53328 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:55686 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:55686 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:08:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:08:31 EEST)" (scheduled at 2026-05-17 11:08:01.625095+03:00)
2026-05-17 11:08:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:08:31 EEST)" executed successfully
INFO:     127.0.0.1:57702 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62864 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:08:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:09:01 EEST)" (scheduled at 2026-05-17 11:08:31.625095+03:00)
2026-05-17 11:08:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:09:01 EEST)" executed successfully
INFO:     127.0.0.1:57325 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56082 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54865 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54865 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62176 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:09:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:09:31 EEST)" (scheduled at 2026-05-17 11:09:01.625095+03:00)
2026-05-17 11:09:01,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:09:31 EEST)" executed successfully
INFO:     127.0.0.1:57905 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56087 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60512 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:09:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:10:01 EEST)" (scheduled at 2026-05-17 11:09:31.625095+03:00)
2026-05-17 11:09:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:10:01 EEST)" executed successfully
INFO:     127.0.0.1:65428 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60908 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63180 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58045 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58045 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:10:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:10:31 EEST)" (scheduled at 2026-05-17 11:10:01.625095+03:00)
2026-05-17 11:10:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:10:31 EEST)" executed successfully
INFO:     127.0.0.1:64333 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58740 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:10:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:11:01 EEST)" (scheduled at 2026-05-17 11:10:31.625095+03:00)
2026-05-17 11:10:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:11:01 EEST)" executed successfully
INFO:     127.0.0.1:63629 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53576 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64152 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55894 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:11:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:11:31 EEST)" (scheduled at 2026-05-17 11:11:01.625095+03:00)
2026-05-17 11:11:01,629 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:11:31 EEST)" executed successfully
INFO:     127.0.0.1:49926 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56525 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61379 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:11:31,621 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:16:31 EEST)" (scheduled at 2026-05-17 11:11:31.618104+03:00)
2026-05-17 11:11:31,622 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:16:31 EEST)" executed successfully
2026-05-17 11:11:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:21:31 EEST)" (scheduled at 2026-05-17 11:11:31.627072+03:00)
2026-05-17 11:11:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:12:01 EEST)" (scheduled at 2026-05-17 11:11:31.625095+03:00)
2026-05-17 11:11:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:16:31 EEST)" (scheduled at 2026-05-17 11:11:31.622651+03:00)
2026-05-17 11:11:31,640 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:21:31 EEST)" executed successfully
2026-05-17 11:11:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:12:01 EEST)" executed successfully
2026-05-17 11:11:31,643 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 11:11:32,672 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 11:11:34,542 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:11:34,545 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 1 signals across 272 tickers.
2026-05-17 11:11:34,546 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 1 signals. Regime: BULLISH (71.1%)
2026-05-17 11:11:34,548 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 1 signals (regime=BULLISH).
2026-05-17 11:11:35,476 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=16
2026-05-17 11:11:35,523 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=16
2026-05-17 11:11:35,525 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=1 counts_by_reason={'repeat_cooldown': 1} dropped_tickers=['SUGR']
2026-05-17 11:11:35,525 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 1/1 signals.
2026-05-17 11:11:35,573 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 1 signals; nothing to broadcast.
2026-05-17 11:11:36,419 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 11:11:36,471 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:16:31 EEST)" executed successfully
INFO:     127.0.0.1:54202 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61722 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64491 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56414 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56414 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:12:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:12:31 EEST)" (scheduled at 2026-05-17 11:12:01.625095+03:00)
2026-05-17 11:12:01,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:12:31 EEST)" executed successfully
INFO:     127.0.0.1:55811 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63898 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:12:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:13:01 EEST)" (scheduled at 2026-05-17 11:12:31.625095+03:00)
2026-05-17 11:12:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:13:01 EEST)" executed successfully
INFO:     127.0.0.1:65496 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:12:45,038 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:12:32.194806). Version incremented to 7.
INFO:     127.0.0.1:61795 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49192 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60477 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49192 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:13:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:13:31 EEST)" (scheduled at 2026-05-17 11:13:01.625095+03:00)
2026-05-17 11:13:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:13:31 EEST)" executed successfully
INFO:     127.0.0.1:51940 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49280 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53940 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:13:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:14:01 EEST)" (scheduled at 2026-05-17 11:13:31.625095+03:00)
2026-05-17 11:13:31,649 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:14:01 EEST)" executed successfully
INFO:     127.0.0.1:64227 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57603 - "GET /api/v1/live/status HTTP/1.1" 200 OK
[Info] Found 273 intraday CSV files to ingest.
INFO:     127.0.0.1:51404 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:14:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:14:31 EEST)" (scheduled at 2026-05-17 11:14:01.625095+03:00)
2026-05-17 11:14:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:14:31 EEST)" executed successfully
INFO:     127.0.0.1:51404 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58401 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65530 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:14:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:15:01 EEST)" (scheduled at 2026-05-17 11:14:31.625095+03:00)
2026-05-17 11:14:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:15:01 EEST)" executed successfully
INFO:     127.0.0.1:50963 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58409 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49236 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53936 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:15:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:15:31 EEST)" (scheduled at 2026-05-17 11:15:01.625095+03:00)
2026-05-17 11:15:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:15:31 EEST)" executed successfully
INFO:     127.0.0.1:61809 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59373 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62970 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:15:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:16:01 EEST)" (scheduled at 2026-05-17 11:15:31.625095+03:00)
2026-05-17 11:15:31,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:16:01 EEST)" executed successfully
INFO:     127.0.0.1:54321 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59721 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53779 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:55946 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:16:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:16:31 EEST)" (scheduled at 2026-05-17 11:16:01.625095+03:00)
2026-05-17 11:16:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:16:31 EEST)" executed successfully
INFO:     127.0.0.1:55946 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54233 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:16:31,619 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:21:31 EEST)" (scheduled at 2026-05-17 11:16:31.618104+03:00)
2026-05-17 11:16:31,621 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:21:31 EEST)" executed successfully
2026-05-17 11:16:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:21:31 EEST)" (scheduled at 2026-05-17 11:16:31.622651+03:00)
2026-05-17 11:16:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:17:01 EEST)" (scheduled at 2026-05-17 11:16:31.625095+03:00)
2026-05-17 11:16:31,637 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 11:16:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:17:01 EEST)" executed successfully
2026-05-17 11:16:33,723 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 11:16:33,724 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 11:16:36,084 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:16:36,088 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 2 signals across 272 tickers.
2026-05-17 11:16:36,089 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 2 signals. Regime: BULLISH (71.1%)
2026-05-17 11:16:36,092 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 2 signals (regime=BULLISH).
INFO:     127.0.0.1:55664 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:16:37,157 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=17
2026-05-17 11:16:37,214 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=17
2026-05-17 11:16:37,218 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=1 dropped=1 counts_by_reason={'repeat_cooldown': 1} dropped_tickers=['SUGR']
2026-05-17 11:16:37,219 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 1/2 signals.
2026-05-17 11:16:37,274 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasting 1 signals after dedup.
2026-05-17 11:16:40,278 - horus.scheduling - INFO - [Scheduler] Intraday: broadcast completed (cards=1, summary_signals=1).
2026-05-17 11:16:40,339 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:21:31 EEST)" executed successfully
INFO:     127.0.0.1:62963 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54917 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61393 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:17:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:17:31 EEST)" (scheduled at 2026-05-17 11:17:01.625095+03:00)
2026-05-17 11:17:01,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:17:31 EEST)" executed successfully
INFO:     127.0.0.1:61687 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50719 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51495 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:17:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:18:01 EEST)" (scheduled at 2026-05-17 11:17:31.625095+03:00)
2026-05-17 11:17:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:18:01 EEST)" executed successfully
INFO:     127.0.0.1:54931 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:17:53,352 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:17:33.195617). Version incremented to 8.
INFO:     127.0.0.1:49675 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49675 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56238 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:18:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:18:31 EEST)" (scheduled at 2026-05-17 11:18:01.625095+03:00)
2026-05-17 11:18:01,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:18:31 EEST)" executed successfully
INFO:     127.0.0.1:54352 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58247 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58314 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:18:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:19:01 EEST)" (scheduled at 2026-05-17 11:18:31.625095+03:00)
2026-05-17 11:18:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:19:01 EEST)" executed successfully
INFO:     127.0.0.1:54998 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58005 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49675 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49733 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49733 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:19:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:19:31 EEST)" (scheduled at 2026-05-17 11:19:01.625095+03:00)
2026-05-17 11:19:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:19:31 EEST)" executed successfully
INFO:     127.0.0.1:50603 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58408 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:19:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:20:01 EEST)" (scheduled at 2026-05-17 11:19:31.625095+03:00)
2026-05-17 11:19:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:20:01 EEST)" executed successfully
INFO:     127.0.0.1:51319 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52757 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54208 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54208 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60067 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:20:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:20:31 EEST)" (scheduled at 2026-05-17 11:20:01.625095+03:00)
2026-05-17 11:20:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:20:31 EEST)" executed successfully
INFO:     127.0.0.1:62043 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61923 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61885 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:20:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:21:01 EEST)" (scheduled at 2026-05-17 11:20:31.625095+03:00)
2026-05-17 11:20:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:21:01 EEST)" executed successfully
INFO:     127.0.0.1:59294 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65158 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50788 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54655 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54655 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:21:01,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:21:31 EEST)" (scheduled at 2026-05-17 11:21:01.625095+03:00)
2026-05-17 11:21:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:21:31 EEST)" executed successfully
INFO:     127.0.0.1:57770 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54734 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:21:31,628 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:26:31 EEST)" (scheduled at 2026-05-17 11:21:31.618104+03:00)
2026-05-17 11:21:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:22:01 EEST)" (scheduled at 2026-05-17 11:21:31.625095+03:00)
2026-05-17 11:21:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:31:31 EEST)" (scheduled at 2026-05-17 11:21:31.627072+03:00)
2026-05-17 11:21:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:26:31 EEST)" (scheduled at 2026-05-17 11:21:31.622651+03:00)
2026-05-17 11:21:31,631 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:26:31 EEST)" executed successfully
2026-05-17 11:21:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:22:01 EEST)" executed successfully
2026-05-17 11:21:31,636 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:31:31 EEST)" executed successfully
2026-05-17 11:21:31,637 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
INFO:     127.0.0.1:62753 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:21:34,126 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 11:21:34,128 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 11:21:36,339 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:21:36,345 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 2 signals across 272 tickers.
2026-05-17 11:21:36,347 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 2 signals. Regime: BULLISH (71.1%)
2026-05-17 11:21:36,350 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 2 signals (regime=BULLISH).
2026-05-17 11:21:37,402 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=18
2026-05-17 11:21:37,456 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=18
2026-05-17 11:21:37,458 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=2 counts_by_reason={'repeat_cooldown': 2} dropped_tickers=['COPR', 'SUGR']
2026-05-17 11:21:37,459 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 2/2 signals.
2026-05-17 11:21:37,507 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 2 signals; nothing to broadcast.
2026-05-17 11:21:38,353 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 11:21:38,415 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:26:31 EEST)" executed successfully
INFO:     127.0.0.1:49675 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58501 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62582 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58501 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:22:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:22:31 EEST)" (scheduled at 2026-05-17 11:22:01.625095+03:00)
2026-05-17 11:22:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:22:31 EEST)" executed successfully
INFO:     127.0.0.1:65530 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55686 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63754 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:22:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:23:01 EEST)" (scheduled at 2026-05-17 11:22:31.625095+03:00)
2026-05-17 11:22:31,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:23:01 EEST)" executed successfully
2026-05-17 11:22:39,038 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:22:34.160834). Version incremented to 9.
INFO:     127.0.0.1:52063 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62569 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49160 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50719 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50719 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:23:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:23:31 EEST)" (scheduled at 2026-05-17 11:23:01.625095+03:00)
2026-05-17 11:23:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:23:31 EEST)" executed successfully
INFO:     127.0.0.1:64999 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60641 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:23:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:24:01 EEST)" (scheduled at 2026-05-17 11:23:31.625095+03:00)
2026-05-17 11:23:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:24:01 EEST)" executed successfully
INFO:     127.0.0.1:58563 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52829 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62591 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62591 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53230 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:24:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:24:31 EEST)" (scheduled at 2026-05-17 11:24:01.625095+03:00)
2026-05-17 11:24:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:24:31 EEST)" executed successfully
INFO:     127.0.0.1:54674 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64514 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55887 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:24:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:25:01 EEST)" (scheduled at 2026-05-17 11:24:31.625095+03:00)
2026-05-17 11:24:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:25:01 EEST)" executed successfully
INFO:     127.0.0.1:51956 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52236 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63177 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:25:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:25:31 EEST)" (scheduled at 2026-05-17 11:25:01.625095+03:00)
2026-05-17 11:25:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:25:31 EEST)" executed successfully
INFO:     127.0.0.1:63177 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49965 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53647 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:25:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:26:01 EEST)" (scheduled at 2026-05-17 11:25:31.625095+03:00)
2026-05-17 11:25:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:26:01 EEST)" executed successfully
INFO:     127.0.0.1:63357 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60831 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55486 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55486 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60291 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:26:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:26:31 EEST)" (scheduled at 2026-05-17 11:26:01.625095+03:00)
2026-05-17 11:26:01,630 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:26:31 EEST)" executed successfully
INFO:     127.0.0.1:63833 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59370 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51278 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:26:31,627 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:31:31 EEST)" (scheduled at 2026-05-17 11:26:31.618104+03:00)
2026-05-17 11:26:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:31:31 EEST)" (scheduled at 2026-05-17 11:26:31.622651+03:00)
2026-05-17 11:26:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:27:01 EEST)" (scheduled at 2026-05-17 11:26:31.625095+03:00)
2026-05-17 11:26:31,633 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:31:31 EEST)" executed successfully
2026-05-17 11:26:31,634 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 11:26:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:27:01 EEST)" executed successfully
2026-05-17 11:26:32,621 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 11:26:34,557 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:26:34,561 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 2 signals across 272 tickers.
2026-05-17 11:26:34,562 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 2 signals. Regime: BULLISH (71.1%)
2026-05-17 11:26:34,564 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 2 signals (regime=BULLISH).
2026-05-17 11:26:35,515 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=19
2026-05-17 11:26:35,567 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=19
2026-05-17 11:26:35,568 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=2 counts_by_reason={'repeat_cooldown': 2} dropped_tickers=['COPR', 'SUGR']
2026-05-17 11:26:35,569 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 2/2 signals.
2026-05-17 11:26:35,614 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 2 signals; nothing to broadcast.
2026-05-17 11:26:36,462 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 11:26:36,513 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:31:31 EEST)" executed successfully
INFO:     127.0.0.1:50075 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57265 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57836 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57138 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:27:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:27:31 EEST)" (scheduled at 2026-05-17 11:27:01.625095+03:00)
2026-05-17 11:27:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:27:31 EEST)" executed successfully
INFO:     127.0.0.1:57138 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49753 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60286 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:27:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:28:01 EEST)" (scheduled at 2026-05-17 11:27:31.625095+03:00)
2026-05-17 11:27:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:28:01 EEST)" executed successfully
INFO:     127.0.0.1:58734 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:27:47,030 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:27:35.167280). Version incremented to 10.
INFO:     127.0.0.1:61420 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49911 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52014 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:28:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:28:31 EEST)" (scheduled at 2026-05-17 11:28:01.625095+03:00)
2026-05-17 11:28:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:28:31 EEST)" executed successfully
INFO:     127.0.0.1:64917 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60651 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53400 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:28:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:29:01 EEST)" (scheduled at 2026-05-17 11:28:31.625095+03:00)
2026-05-17 11:28:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:29:01 EEST)" executed successfully
INFO:     127.0.0.1:64578 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52193 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52193 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64478 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:29:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:29:31 EEST)" (scheduled at 2026-05-17 11:29:01.625095+03:00)
2026-05-17 11:29:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:29:31 EEST)" executed successfully
INFO:     127.0.0.1:55486 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53540 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61641 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:29:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:30:01 EEST)" (scheduled at 2026-05-17 11:29:31.625095+03:00)
2026-05-17 11:29:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:30:01 EEST)" executed successfully
INFO:     127.0.0.1:57750 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54297 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60255 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61636 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61636 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:30:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:30:31 EEST)" (scheduled at 2026-05-17 11:30:01.625095+03:00)
2026-05-17 11:30:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:30:31 EEST)" executed successfully
INFO:     127.0.0.1:59297 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61686 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:30:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:31:01 EEST)" (scheduled at 2026-05-17 11:30:31.625095+03:00)
2026-05-17 11:30:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:31:01 EEST)" executed successfully
INFO:     127.0.0.1:53213 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64230 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60395 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60395 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53576 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:31:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:31:31 EEST)" (scheduled at 2026-05-17 11:31:01.625095+03:00)
2026-05-17 11:31:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:31:31 EEST)" executed successfully
INFO:     127.0.0.1:64833 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55438 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59746 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:31:31,631 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:36:31 EEST)" (scheduled at 2026-05-17 11:31:31.618104+03:00)
2026-05-17 11:31:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:36:31 EEST)" (scheduled at 2026-05-17 11:31:31.622651+03:00)
2026-05-17 11:31:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:32:01 EEST)" (scheduled at 2026-05-17 11:31:31.625095+03:00)
2026-05-17 11:31:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:41:31 EEST)" (scheduled at 2026-05-17 11:31:31.627072+03:00)
2026-05-17 11:31:31,633 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:36:31 EEST)" executed successfully
2026-05-17 11:31:31,634 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 11:31:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:32:01 EEST)" executed successfully
2026-05-17 11:31:31,638 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:41:31 EEST)" executed successfully
2026-05-17 11:31:33,862 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 11:31:33,863 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 11:31:36,123 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:31:36,127 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 2 signals across 272 tickers.
2026-05-17 11:31:36,128 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 2 signals. Regime: BULLISH (71.1%)
2026-05-17 11:31:36,130 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 2 signals (regime=BULLISH).
2026-05-17 11:31:37,173 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=20
2026-05-17 11:31:37,223 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=20
2026-05-17 11:31:37,225 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=2 counts_by_reason={'repeat_cooldown': 2} dropped_tickers=['SUGR', 'COPR']
2026-05-17 11:31:37,226 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 2/2 signals.
2026-05-17 11:31:37,279 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 2 signals; nothing to broadcast.
INFO:     127.0.0.1:63228 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:31:38,153 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 11:31:38,219 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:36:31 EEST)" executed successfully
INFO:     127.0.0.1:56811 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51340 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52403 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52403 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:32:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:32:31 EEST)" (scheduled at 2026-05-17 11:32:01.625095+03:00)
2026-05-17 11:32:01,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:32:31 EEST)" executed successfully
INFO:     127.0.0.1:50160 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55574 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:32:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:33:01 EEST)" (scheduled at 2026-05-17 11:32:31.625095+03:00)
2026-05-17 11:32:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:33:01 EEST)" executed successfully
INFO:     127.0.0.1:52327 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56050 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:32:55,342 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:32:36.363931). Version incremented to 11.
INFO:     127.0.0.1:62923 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62923 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:49378 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:33:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:33:31 EEST)" (scheduled at 2026-05-17 11:33:01.625095+03:00)
2026-05-17 11:33:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:33:31 EEST)" executed successfully
INFO:     127.0.0.1:61637 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62012 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63425 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:33:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:34:01 EEST)" (scheduled at 2026-05-17 11:33:31.625095+03:00)
2026-05-17 11:33:31,649 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:34:01 EEST)" executed successfully
INFO:     127.0.0.1:55749 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65467 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59823 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59823 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:34:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:34:31 EEST)" (scheduled at 2026-05-17 11:34:01.625095+03:00)
2026-05-17 11:34:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:34:31 EEST)" executed successfully
INFO:     127.0.0.1:63339 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64396 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:34:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:35:01 EEST)" (scheduled at 2026-05-17 11:34:31.625095+03:00)
2026-05-17 11:34:31,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:35:01 EEST)" executed successfully
INFO:     127.0.0.1:49982 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55864 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51439 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51439 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:55908 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:35:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:35:31 EEST)" (scheduled at 2026-05-17 11:35:01.625095+03:00)
2026-05-17 11:35:01,630 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:35:31 EEST)" executed successfully
INFO:     127.0.0.1:60751 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49674 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63849 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:35:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:36:01 EEST)" (scheduled at 2026-05-17 11:35:31.625095+03:00)
2026-05-17 11:35:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:36:01 EEST)" executed successfully
INFO:     127.0.0.1:55579 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62009 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57432 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51979 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:36:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:36:31 EEST)" (scheduled at 2026-05-17 11:36:01.625095+03:00)
2026-05-17 11:36:01,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:36:31 EEST)" executed successfully
INFO:     127.0.0.1:51979 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58308 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51458 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:36:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:41:31 EEST)" (scheduled at 2026-05-17 11:36:31.622651+03:00)
2026-05-17 11:36:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:37:01 EEST)" (scheduled at 2026-05-17 11:36:31.625095+03:00)
2026-05-17 11:36:31,629 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:41:31 EEST)" (scheduled at 2026-05-17 11:36:31.618104+03:00)
2026-05-17 11:36:31,631 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 11:36:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:37:01 EEST)" executed successfully
2026-05-17 11:36:31,639 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:41:31 EEST)" executed successfully
2026-05-17 11:36:32,708 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 11:36:34,772 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:36:34,775 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 2 signals across 272 tickers.
2026-05-17 11:36:34,776 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 2 signals. Regime: BULLISH (71.1%)
2026-05-17 11:36:34,778 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 2 signals (regime=BULLISH).
INFO:     127.0.0.1:65292 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:36:35,887 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=21
2026-05-17 11:36:35,943 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=21
2026-05-17 11:36:35,945 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=2 counts_by_reason={'repeat_cooldown': 2} dropped_tickers=['SUGR', 'COPR']
2026-05-17 11:36:35,946 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 2/2 signals.
2026-05-17 11:36:36,008 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 2 signals; nothing to broadcast.
2026-05-17 11:36:36,879 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 11:36:36,936 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:41:31 EEST)" executed successfully
INFO:     127.0.0.1:53485 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58052 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58052 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62394 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:37:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:37:31 EEST)" (scheduled at 2026-05-17 11:37:01.625095+03:00)
2026-05-17 11:37:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:37:31 EEST)" executed successfully
INFO:     127.0.0.1:59625 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53494 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51907 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:37:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:38:01 EEST)" (scheduled at 2026-05-17 11:37:31.625095+03:00)
2026-05-17 11:37:31,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:38:01 EEST)" executed successfully
2026-05-17 11:37:41,027 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:37:37.412214). Version incremented to 12.
INFO:     127.0.0.1:50810 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54187 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62971 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53328 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:38:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:38:31 EEST)" (scheduled at 2026-05-17 11:38:01.625095+03:00)
2026-05-17 11:38:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:38:31 EEST)" executed successfully
INFO:     127.0.0.1:53328 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59903 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64005 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:38:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:39:01 EEST)" (scheduled at 2026-05-17 11:38:31.625095+03:00)
2026-05-17 11:38:31,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:39:01 EEST)" executed successfully
INFO:     127.0.0.1:50395 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52533 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60951 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65073 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:39:01,625 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:39:31 EEST)" (scheduled at 2026-05-17 11:39:01.625095+03:00)
2026-05-17 11:39:01,629 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:39:31 EEST)" executed successfully
INFO:     127.0.0.1:56997 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56488 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51710 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:39:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:40:01 EEST)" (scheduled at 2026-05-17 11:39:31.625095+03:00)
2026-05-17 11:39:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:40:01 EEST)" executed successfully
INFO:     127.0.0.1:51511 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64419 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64419 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64419 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64419 - "GET /api/v1/data/status HTTP/1.1" 200 OK
2026-05-17 11:40:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:40:31 EEST)" (scheduled at 2026-05-17 11:40:01.625095+03:00)
2026-05-17 11:40:01,630 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:40:31 EEST)" executed successfully
INFO:     127.0.0.1:60166 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61630 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63504 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63504 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57870 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56212 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:40:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:41:01 EEST)" (scheduled at 2026-05-17 11:40:31.625095+03:00)
2026-05-17 11:40:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:41:01 EEST)" executed successfully
INFO:     127.0.0.1:51562 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51562 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50079 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58138 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49843 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:55067 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:55067 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:41:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:41:31 EEST)" (scheduled at 2026-05-17 11:41:01.625095+03:00)
2026-05-17 11:41:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:41:31 EEST)" executed successfully
INFO:     127.0.0.1:49315 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58335 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:41:31,631 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:46:31 EEST)" (scheduled at 2026-05-17 11:41:31.618104+03:00)
2026-05-17 11:41:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:46:31 EEST)" (scheduled at 2026-05-17 11:41:31.622651+03:00)
2026-05-17 11:41:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:42:01 EEST)" (scheduled at 2026-05-17 11:41:31.625095+03:00)
2026-05-17 11:41:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:51:31 EEST)" (scheduled at 2026-05-17 11:41:31.627072+03:00)
2026-05-17 11:41:31,637 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:46:31 EEST)" executed successfully
2026-05-17 11:41:31,641 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 11:41:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:42:01 EEST)" executed successfully
2026-05-17 11:41:31,646 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 11:51:31 EEST)" executed successfully
INFO:     127.0.0.1:49785 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:41:33,615 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 11:41:33,616 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 11:41:35,473 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:41:35,476 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 2 signals across 272 tickers.
2026-05-17 11:41:35,477 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 2 signals. Regime: BULLISH (71.1%)
2026-05-17 11:41:35,479 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 2 signals (regime=BULLISH).
2026-05-17 11:41:36,388 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=22
2026-05-17 11:41:36,435 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=22
2026-05-17 11:41:36,436 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=2 counts_by_reason={'repeat_cooldown': 2} dropped_tickers=['SUGR', 'COPR']
2026-05-17 11:41:36,437 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 2/2 signals.
2026-05-17 11:41:36,481 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 2 signals; nothing to broadcast.
2026-05-17 11:41:37,341 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 11:41:37,391 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:46:31 EEST)" executed successfully
INFO:     127.0.0.1:59443 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62155 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62155 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:55385 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:42:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:42:31 EEST)" (scheduled at 2026-05-17 11:42:01.625095+03:00)
2026-05-17 11:42:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:42:31 EEST)" executed successfully
INFO:     127.0.0.1:59642 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61477 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54817 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:42:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:43:01 EEST)" (scheduled at 2026-05-17 11:42:31.625095+03:00)
2026-05-17 11:42:31,649 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:43:01 EEST)" executed successfully
INFO:     127.0.0.1:55722 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:42:49,342 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:42:38.479458). Version incremented to 13.
INFO:     127.0.0.1:61630 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52348 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50827 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50827 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:43:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:43:31 EEST)" (scheduled at 2026-05-17 11:43:01.625095+03:00)
2026-05-17 11:43:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:43:31 EEST)" executed successfully
INFO:     127.0.0.1:58552 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57291 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:43:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:44:01 EEST)" (scheduled at 2026-05-17 11:43:31.625095+03:00)
2026-05-17 11:43:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:44:01 EEST)" executed successfully
INFO:     127.0.0.1:51138 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53725 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61696 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61696 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53038 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:44:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:44:31 EEST)" (scheduled at 2026-05-17 11:44:01.625095+03:00)
2026-05-17 11:44:01,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:44:31 EEST)" executed successfully
INFO:     127.0.0.1:52066 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57403 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65341 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:44:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:45:01 EEST)" (scheduled at 2026-05-17 11:44:31.625095+03:00)
2026-05-17 11:44:31,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:45:01 EEST)" executed successfully
INFO:     127.0.0.1:53985 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54960 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64070 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59866 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59866 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:45:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:45:31 EEST)" (scheduled at 2026-05-17 11:45:01.625095+03:00)
2026-05-17 11:45:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:45:31 EEST)" executed successfully
INFO:     127.0.0.1:57393 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64819 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:45:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:46:01 EEST)" (scheduled at 2026-05-17 11:45:31.625095+03:00)
2026-05-17 11:45:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:46:01 EEST)" executed successfully
INFO:     127.0.0.1:56803 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55642 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60993 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60993 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53151 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:46:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:46:31 EEST)" (scheduled at 2026-05-17 11:46:01.625095+03:00)
2026-05-17 11:46:01,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:46:31 EEST)" executed successfully
INFO:     127.0.0.1:57238 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53790 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65029 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:46:31,625 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:51:31 EEST)" (scheduled at 2026-05-17 11:46:31.618104+03:00)
2026-05-17 11:46:31,625 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:51:31 EEST)" (scheduled at 2026-05-17 11:46:31.622651+03:00)
2026-05-17 11:46:31,629 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:51:31 EEST)" executed successfully
2026-05-17 11:46:31,630 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 11:46:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:47:01 EEST)" (scheduled at 2026-05-17 11:46:31.625095+03:00)
2026-05-17 11:46:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:47:01 EEST)" executed successfully
2026-05-17 11:46:32,614 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 11:46:34,467 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:46:34,470 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 2 signals across 272 tickers.
2026-05-17 11:46:34,471 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 2 signals. Regime: BULLISH (71.1%)
2026-05-17 11:46:34,473 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 2 signals (regime=BULLISH).
2026-05-17 11:46:35,401 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=23
2026-05-17 11:46:35,447 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=23
2026-05-17 11:46:35,449 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=2 counts_by_reason={'repeat_cooldown': 2} dropped_tickers=['COPR', 'SUGR']
2026-05-17 11:46:35,449 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 2/2 signals.
2026-05-17 11:46:35,492 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 2 signals; nothing to broadcast.
2026-05-17 11:46:36,327 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 11:46:36,383 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:51:31 EEST)" executed successfully
INFO:     127.0.0.1:64137 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49675 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56582 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60463 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:47:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:47:31 EEST)" (scheduled at 2026-05-17 11:47:01.625095+03:00)
2026-05-17 11:47:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:47:31 EEST)" executed successfully
INFO:     127.0.0.1:60463 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56642 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60893 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:47:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:48:01 EEST)" (scheduled at 2026-05-17 11:47:31.625095+03:00)
2026-05-17 11:47:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:48:01 EEST)" executed successfully
INFO:     127.0.0.1:61368 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63886 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:47:57,331 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:47:39.462195). Version incremented to 14.
INFO:     127.0.0.1:65285 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65285 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51501 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:48:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:48:31 EEST)" (scheduled at 2026-05-17 11:48:01.625095+03:00)
2026-05-17 11:48:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:48:31 EEST)" executed successfully
INFO:     127.0.0.1:55506 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52982 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60524 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:48:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:49:01 EEST)" (scheduled at 2026-05-17 11:48:31.625095+03:00)
2026-05-17 11:48:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:49:01 EEST)" executed successfully
INFO:     127.0.0.1:53734 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57528 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52186 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51754 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:49:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:49:31 EEST)" (scheduled at 2026-05-17 11:49:01.625095+03:00)
2026-05-17 11:49:01,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:49:31 EEST)" executed successfully
INFO:     127.0.0.1:51754 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61076 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58738 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:49:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:50:01 EEST)" (scheduled at 2026-05-17 11:49:31.625095+03:00)
2026-05-17 11:49:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:50:01 EEST)" executed successfully
INFO:     127.0.0.1:56344 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49981 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61390 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58078 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:50:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:50:31 EEST)" (scheduled at 2026-05-17 11:50:01.625095+03:00)
2026-05-17 11:50:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:50:31 EEST)" executed successfully
INFO:     127.0.0.1:55217 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59908 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57882 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:50:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:51:01 EEST)" (scheduled at 2026-05-17 11:50:31.625095+03:00)
2026-05-17 11:50:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:51:01 EEST)" executed successfully
INFO:     127.0.0.1:60890 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61331 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49350 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:51:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:51:31 EEST)" (scheduled at 2026-05-17 11:51:01.625095+03:00)
2026-05-17 11:51:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:51:31 EEST)" executed successfully
INFO:     127.0.0.1:52089 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51886 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53664 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53664 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63688 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:51:31,626 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:56:31 EEST)" (scheduled at 2026-05-17 11:51:31.618104+03:00)
2026-05-17 11:51:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:56:31 EEST)" (scheduled at 2026-05-17 11:51:31.622651+03:00)
2026-05-17 11:51:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:52:01 EEST)" (scheduled at 2026-05-17 11:51:31.625095+03:00)
2026-05-17 11:51:31,628 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 11:56:31 EEST)" executed successfully
2026-05-17 11:51:31,629 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 11:51:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:52:01 EEST)" executed successfully
2026-05-17 11:51:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:01:31 EEST)" (scheduled at 2026-05-17 11:51:31.627072+03:00)
2026-05-17 11:51:31,644 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:01:31 EEST)" executed successfully
2026-05-17 11:51:34,188 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 11:51:34,189 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 11:51:36,527 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:51:36,535 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 2 signals across 272 tickers.
2026-05-17 11:51:36,536 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 2 signals. Regime: BULLISH (71.1%)
2026-05-17 11:51:36,538 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 2 signals (regime=BULLISH).
INFO:     127.0.0.1:62721 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:51:37,824 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=24
2026-05-17 11:51:37,890 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=24
2026-05-17 11:51:37,892 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=2 counts_by_reason={'repeat_cooldown': 2} dropped_tickers=['SUGR', 'COPR']
2026-05-17 11:51:37,893 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 2/2 signals.
2026-05-17 11:51:37,950 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 2 signals; nothing to broadcast.
2026-05-17 11:51:38,900 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 11:51:38,959 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 11:56:31 EEST)" executed successfully
INFO:     127.0.0.1:65219 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63366 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63366 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:52:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:52:31 EEST)" (scheduled at 2026-05-17 11:52:01.625095+03:00)
2026-05-17 11:52:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:52:31 EEST)" executed successfully
INFO:     127.0.0.1:54606 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50402 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:52:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:53:01 EEST)" (scheduled at 2026-05-17 11:52:31.625095+03:00)
2026-05-17 11:52:31,652 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:53:01 EEST)" executed successfully
INFO:     127.0.0.1:52809 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57907 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:52:54,335 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:52:40.526836). Version incremented to 15.
INFO:     127.0.0.1:60819 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60819 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52801 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:53:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:53:31 EEST)" (scheduled at 2026-05-17 11:53:01.625095+03:00)
2026-05-17 11:53:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:53:31 EEST)" executed successfully
INFO:     127.0.0.1:58883 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:60793 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61864 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:53:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:54:01 EEST)" (scheduled at 2026-05-17 11:53:31.625095+03:00)
2026-05-17 11:53:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:54:01 EEST)" executed successfully
INFO:     127.0.0.1:51849 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51849 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61331 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57401 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50719 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52221 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52221 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:54:01,642 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:54:31 EEST)" (scheduled at 2026-05-17 11:54:01.625095+03:00)
2026-05-17 11:54:01,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:54:31 EEST)" executed successfully
INFO:     127.0.0.1:52019 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51369 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:54:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:55:01 EEST)" (scheduled at 2026-05-17 11:54:31.625095+03:00)
2026-05-17 11:54:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:55:01 EEST)" executed successfully
INFO:     127.0.0.1:59872 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65287 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56183 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65076 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:56183 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:55:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:55:31 EEST)" (scheduled at 2026-05-17 11:55:01.625095+03:00)
2026-05-17 11:55:01,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:55:31 EEST)" executed successfully
INFO:     127.0.0.1:62123 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49742 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56025 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:55:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:56:01 EEST)" (scheduled at 2026-05-17 11:55:31.625095+03:00)
2026-05-17 11:55:31,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:56:01 EEST)" executed successfully
INFO:     127.0.0.1:55354 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54961 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52441 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60598 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:60598 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:56:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:56:31 EEST)" (scheduled at 2026-05-17 11:56:01.625095+03:00)
2026-05-17 11:56:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:56:31 EEST)" executed successfully
INFO:     127.0.0.1:53218 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62263 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:56:31,627 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:01:31 EEST)" (scheduled at 2026-05-17 11:56:31.618104+03:00)
2026-05-17 11:56:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:01:31 EEST)" (scheduled at 2026-05-17 11:56:31.622651+03:00)
2026-05-17 11:56:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:57:01 EEST)" (scheduled at 2026-05-17 11:56:31.625095+03:00)
2026-05-17 11:56:31,629 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:01:31 EEST)" executed successfully
2026-05-17 11:56:31,631 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 11:56:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:57:01 EEST)" executed successfully
2026-05-17 11:56:32,630 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
INFO:     127.0.0.1:64128 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:56:34,577 - DailyScanner - INFO - Parallel scoring 3 candidates...
2026-05-17 11:56:34,581 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 2 signals across 272 tickers.
2026-05-17 11:56:34,583 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 2 signals. Regime: BULLISH (71.1%)
2026-05-17 11:56:34,585 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 2 signals (regime=BULLISH).
2026-05-17 11:56:35,498 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=25
2026-05-17 11:56:35,545 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=25
2026-05-17 11:56:35,547 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=2 counts_by_reason={'repeat_cooldown': 2} dropped_tickers=['COPR', 'SUGR']
2026-05-17 11:56:35,547 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 2/2 signals.
2026-05-17 11:56:35,593 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 2 signals; nothing to broadcast.
2026-05-17 11:56:36,414 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 11:56:36,473 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:01:31 EEST)" executed successfully
INFO:     127.0.0.1:63177 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49714 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49714 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:65082 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:57:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:57:31 EEST)" (scheduled at 2026-05-17 11:57:01.625095+03:00)
2026-05-17 11:57:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:57:31 EEST)" executed successfully
INFO:     127.0.0.1:61519 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52671 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:57:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:58:01 EEST)" (scheduled at 2026-05-17 11:57:31.625095+03:00)
2026-05-17 11:57:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:58:01 EEST)" executed successfully
INFO:     127.0.0.1:51042 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53387 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:57:58,031 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T11:57:41.599130). Version incremented to 16.
[Info] Found 273 intraday CSV files to ingest.
INFO:     127.0.0.1:49402 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
2026-05-17 11:58:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:58:31 EEST)" (scheduled at 2026-05-17 11:58:01.625095+03:00)
2026-05-17 11:58:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:58:31 EEST)" executed successfully
INFO:     127.0.0.1:49402 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57558 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52982 - "GET /api/v1/live/status HTTP/1.1" 200 OK
2026-05-17 11:58:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:59:01 EEST)" (scheduled at 2026-05-17 11:58:31.625095+03:00)
2026-05-17 11:58:31,630 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:59:01 EEST)" executed successfully
INFO:     127.0.0.1:52372 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64970 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64970 - "GET /api/v1/data/intraday/COMI?limit=240 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64660 - "GET /api/v1/live/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:64970 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62692 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52099 - "HEAD /telegram HTTP/1.1" 200 OK
INFO:     127.0.0.1:64660 - "HEAD / HTTP/1.1" 200 OK
INFO:     127.0.0.1:62692 - "GET /status/__next._tree.txt?_rsc=MTj2NC-7G28rXwox HTTP/1.1" 200 OK
INFO:     127.0.0.1:52099 - "GET /telegram/__next._tree.txt?_rsc=MTj2NC-7G28rXwox HTTP/1.1" 200 OK
INFO:     127.0.0.1:64660 - "GET /__next._tree.txt?_rsc=MTj2NC-7G28rXwox HTTP/1.1" 200 OK
INFO:     127.0.0.1:64970 - "GET /status/__next._index.txt?_rsc=KM5CHlXwCdUP3Ok2 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62692 - "GET /status/__next._head.txt?_rsc=BVtwKo2ofwonmDmf HTTP/1.1" 200 OK
INFO:     127.0.0.1:52099 - "GET /telegram/__next._head.txt?_rsc=BVtwKo2ofwonmDmf HTTP/1.1" 200 OK
INFO:     127.0.0.1:64660 - "GET /telegram/__next.telegram.txt?_rsc=EjHdGAHLoHf4tF7Z HTTP/1.1" 200 OK
INFO:     127.0.0.1:64970 - "GET /__next._head.txt?_rsc=BVtwKo2ofwonmDmf HTTP/1.1" 200 OK
INFO:     127.0.0.1:62692 - "GET /telegram/__next.telegram.__PAGE__.txt?_rsc=ABPR4gfQSdob1s5l HTTP/1.1" 200 OK
INFO:     127.0.0.1:52099 - "GET /__next.__PAGE__.txt?_rsc=ZkglTNqM56N61_kl HTTP/1.1" 200 OK
INFO:     127.0.0.1:64660 - "GET /status/__next.status.txt?_rsc=MlnJ3t90elp-Ilq3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:64970 - "GET /status/__next.status.__PAGE__.txt?_rsc=6XmiRgOqOcag_yXe HTTP/1.1" 200 OK
INFO:     127.0.0.1:64970 - "HEAD /arbitrage HTTP/1.1" 200 OK
INFO:     127.0.0.1:64660 - "HEAD /simulation HTTP/1.1" 200 OK
INFO:     127.0.0.1:62692 - "HEAD /strategy HTTP/1.1" 200 OK
INFO:     127.0.0.1:52099 - "HEAD /optimization HTTP/1.1" 200 OK
INFO:     127.0.0.1:64970 - "GET /arbitrage/__next._tree.txt?_rsc=MTj2NC-7G28rXwox HTTP/1.1" 200 OK
INFO:     127.0.0.1:64660 - "GET /simulation/__next._tree.txt?_rsc=MTj2NC-7G28rXwox HTTP/1.1" 200 OK
INFO:     127.0.0.1:62692 - "GET /strategy/__next._tree.txt?_rsc=MTj2NC-7G28rXwox HTTP/1.1" 200 OK
INFO:     127.0.0.1:52099 - "GET /optimization/__next._tree.txt?_rsc=MTj2NC-7G28rXwox HTTP/1.1" 200 OK
INFO:     127.0.0.1:64970 - "HEAD /settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:62692 - "HEAD /portfolio HTTP/1.1" 200 OK
INFO:     127.0.0.1:64970 - "GET /settings/__next._tree.txt?_rsc=MTj2NC-7G28rXwox HTTP/1.1" 200 OK
INFO:     127.0.0.1:62692 - "GET /portfolio/__next._tree.txt?_rsc=MTj2NC-7G28rXwox HTTP/1.1" 200 OK
INFO:     127.0.0.1:57847 - "GET /portfolio/__next.portfolio.txt?_rsc=C41GwzoGFA_lNmrj HTTP/1.1" 200 OK
INFO:     127.0.0.1:62692 - "GET /settings/__next._head.txt?_rsc=BVtwKo2ofwonmDmf HTTP/1.1" 200 OK
INFO:     127.0.0.1:64970 - "GET /settings/__next.settings.txt?_rsc=jrmUVESS87dfH3lI HTTP/1.1" 200 OK
INFO:     127.0.0.1:52099 - "GET /settings/__next.settings.__PAGE__.txt?_rsc=g8DwLkxXH8zUswcs HTTP/1.1" 200 OK
INFO:     127.0.0.1:64660 - "GET /portfolio/__next._head.txt?_rsc=BVtwKo2ofwonmDmf HTTP/1.1" 200 OK
INFO:     127.0.0.1:57847 - "GET /portfolio/__next.portfolio.__PAGE__.txt?_rsc=vxsDLbuarQ3uVB_5 HTTP/1.1" 200 OK
2026-05-17 11:58:48,185 - horus.websocket - INFO - WebSocket: Client disconnected. Total clients: 0
INFO:     connection closed
INFO:     127.0.0.1:57847 - "GET /api/v1/settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:64660 - "GET /api/v1/settings/exclusions HTTP/1.1" 200 OK
INFO:     127.0.0.1:52099 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:64660 - "GET /api/v1/settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:57847 - "GET /api/v1/settings/exclusions HTTP/1.1" 200 OK
INFO:     127.0.0.1:62692 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:54990 - "GET /api/v1/data/tickers HTTP/1.1" 200 OK
INFO:     127.0.0.1:54990 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 11:59:01,625 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:59:31 EEST)" (scheduled at 2026-05-17 11:59:01.625095+03:00)
2026-05-17 11:59:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 11:59:31 EEST)" executed successfully
INFO:     127.0.0.1:49684 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63976 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63976 - "GET /api/v1/data/status HTTP/1.1" 200 OK
2026-05-17 11:59:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:00:01 EEST)" (scheduled at 2026-05-17 11:59:31.625095+03:00)
2026-05-17 11:59:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:00:01 EEST)" executed successfully
2026-05-17 12:00:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:00:31 EEST)" (scheduled at 2026-05-17 12:00:01.625095+03:00)
2026-05-17 12:00:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:00:31 EEST)" executed successfully
2026-05-17 12:00:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:01:01 EEST)" (scheduled at 2026-05-17 12:00:31.625095+03:00)
2026-05-17 12:00:31,650 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:01:01 EEST)" executed successfully
2026-05-17 12:01:01,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:01:31 EEST)" (scheduled at 2026-05-17 12:01:01.625095+03:00)
2026-05-17 12:01:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:01:31 EEST)" executed successfully
2026-05-17 12:01:31,633 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:06:31 EEST)" (scheduled at 2026-05-17 12:01:31.618104+03:00)
2026-05-17 12:01:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:06:31 EEST)" (scheduled at 2026-05-17 12:01:31.622651+03:00)
2026-05-17 12:01:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:11:31 EEST)" (scheduled at 2026-05-17 12:01:31.627072+03:00)
2026-05-17 12:01:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:02:01 EEST)" (scheduled at 2026-05-17 12:01:31.625095+03:00)
2026-05-17 12:01:31,634 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:06:31 EEST)" executed successfully
2026-05-17 12:01:31,636 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:01:31,637 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:11:31 EEST)" executed successfully
2026-05-17 12:01:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:02:01 EEST)" executed successfully
2026-05-17 12:01:33,506 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 12:01:33,507 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:01:35,647 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:01:35,653 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:01:35,654 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:01:35,655 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:01:36,609 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=26
2026-05-17 12:01:36,661 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=26
2026-05-17 12:01:36,664 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=4 dropped=2 counts_by_reason={'repeat_cooldown': 2} dropped_tickers=['COPR', 'SUGR']
2026-05-17 12:01:36,665 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 2/6 signals.
2026-05-17 12:01:36,711 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasting 4 signals after dedup.
2026-05-17 12:01:43,205 - horus.scheduling - INFO - [Scheduler] Intraday: broadcast completed (cards=4, summary_signals=4).
2026-05-17 12:01:43,259 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:06:31 EEST)" executed successfully
2026-05-17 12:02:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:02:31 EEST)" (scheduled at 2026-05-17 12:02:01.625095+03:00)
2026-05-17 12:02:01,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:02:31 EEST)" executed successfully
2026-05-17 12:02:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:03:01 EEST)" (scheduled at 2026-05-17 12:02:31.625095+03:00)
2026-05-17 12:02:31,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:03:01 EEST)" executed successfully
2026-05-17 12:03:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:03:31 EEST)" (scheduled at 2026-05-17 12:03:01.625095+03:00)
2026-05-17 12:03:01,641 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:02:42.614846). Version incremented to 17.
2026-05-17 12:03:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:03:31 EEST)" executed successfully
2026-05-17 12:03:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:04:01 EEST)" (scheduled at 2026-05-17 12:03:31.625095+03:00)
2026-05-17 12:03:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:04:01 EEST)" executed successfully
INFO:     127.0.0.1:56885 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62362 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62362 - "HEAD /telegram HTTP/1.1" 200 OK
INFO:     127.0.0.1:62023 - "HEAD / HTTP/1.1" 200 OK
INFO:     127.0.0.1:62362 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62023 - "GET /telegram/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:62362 - "GET /__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:62023 - "GET /status/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:62362 - "GET /telegram/__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63293 - "GET /telegram/__next._index.txt?_rsc=ERfXn7tGRj5EupPH HTTP/1.1" 200 OK
INFO:     127.0.0.1:62023 - "GET /telegram/__next.telegram.txt?_rsc=aKACAGocL3t4-4Xd HTTP/1.1" 200 OK
INFO:     127.0.0.1:61375 - "GET /telegram/__next.telegram.__PAGE__.txt?_rsc=WHz_FkIDzWrFoQE3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62362 - "GET /__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63293 - "GET /__next.__PAGE__.txt?_rsc=cdk-OvPaaQdzy3F4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62023 - "GET /status/__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61375 - "GET /status/__next.status.txt?_rsc=s0FEf9OOxbpuBOef HTTP/1.1" 200 OK
INFO:     127.0.0.1:63293 - "GET /status/__next.status.__PAGE__.txt?_rsc=ESW-ijXE9EWSHgP1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63293 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 12:04:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:04:31 EEST)" (scheduled at 2026-05-17 12:04:01.625095+03:00)
2026-05-17 12:04:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:04:31 EEST)" executed successfully
INFO:     127.0.0.1:61087 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57466 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57466 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:65272 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 12:04:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:05:01 EEST)" (scheduled at 2026-05-17 12:04:31.625095+03:00)
2026-05-17 12:04:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:05:01 EEST)" executed successfully
INFO:     127.0.0.1:64766 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56527 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56527 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54371 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 12:05:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:05:31 EEST)" (scheduled at 2026-05-17 12:05:01.625095+03:00)
2026-05-17 12:05:01,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:05:31 EEST)" executed successfully
INFO:     127.0.0.1:53113 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56346 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:56346 - "GET /api/v1/data/status HTTP/1.1" 200 OK
2026-05-17 12:05:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:06:01 EEST)" (scheduled at 2026-05-17 12:05:31.625095+03:00)
2026-05-17 12:05:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:06:01 EEST)" executed successfully
INFO:     127.0.0.1:58367 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51712 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 12:06:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:06:31 EEST)" (scheduled at 2026-05-17 12:06:01.625095+03:00)
2026-05-17 12:06:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:06:31 EEST)" executed successfully
2026-05-17 12:06:31,623 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:11:31 EEST)" (scheduled at 2026-05-17 12:06:31.618104+03:00)
2026-05-17 12:06:31,624 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:11:31 EEST)" (scheduled at 2026-05-17 12:06:31.622651+03:00)
2026-05-17 12:06:31,625 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:11:31 EEST)" executed successfully
2026-05-17 12:06:31,626 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:06:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:07:01 EEST)" (scheduled at 2026-05-17 12:06:31.625095+03:00)
2026-05-17 12:06:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:07:01 EEST)" executed successfully
2026-05-17 12:06:33,694 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 12:06:33,695 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:06:35,858 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:06:35,865 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:06:35,866 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:06:35,868 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:06:36,886 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=27
2026-05-17 12:06:36,940 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=27
2026-05-17 12:06:36,942 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=6 counts_by_reason={'repeat_cooldown': 6} dropped_tickers=['MILS', 'COPR', 'ACGC', 'FAIT', 'BONY', 'SUGR']
2026-05-17 12:06:36,945 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 6/6 signals.
2026-05-17 12:06:36,998 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 6 signals; nothing to broadcast.
2026-05-17 12:06:37,830 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 12:06:37,888 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:11:31 EEST)" executed successfully
2026-05-17 12:07:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:07:31 EEST)" (scheduled at 2026-05-17 12:07:01.625095+03:00)
2026-05-17 12:07:01,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:07:31 EEST)" executed successfully
2026-05-17 12:07:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:08:01 EEST)" (scheduled at 2026-05-17 12:07:31.625095+03:00)
2026-05-17 12:07:31,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:08:01 EEST)" executed successfully
2026-05-17 12:08:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:08:31 EEST)" (scheduled at 2026-05-17 12:08:01.625095+03:00)
2026-05-17 12:08:01,632 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:07:43.663609). Version incremented to 18.
2026-05-17 12:08:01,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:08:31 EEST)" executed successfully
2026-05-17 12:08:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:09:01 EEST)" (scheduled at 2026-05-17 12:08:31.625095+03:00)
2026-05-17 12:08:31,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:09:01 EEST)" executed successfully
2026-05-17 12:09:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:09:31 EEST)" (scheduled at 2026-05-17 12:09:01.625095+03:00)
2026-05-17 12:09:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:09:31 EEST)" executed successfully
2026-05-17 12:09:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:10:01 EEST)" (scheduled at 2026-05-17 12:09:31.625095+03:00)
2026-05-17 12:09:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:10:01 EEST)" executed successfully
2026-05-17 12:10:01,625 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:10:31 EEST)" (scheduled at 2026-05-17 12:10:01.625095+03:00)
2026-05-17 12:10:01,630 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:10:31 EEST)" executed successfully
2026-05-17 12:10:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:11:01 EEST)" (scheduled at 2026-05-17 12:10:31.625095+03:00)
2026-05-17 12:10:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:11:01 EEST)" executed successfully
2026-05-17 12:11:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:11:31 EEST)" (scheduled at 2026-05-17 12:11:01.625095+03:00)
2026-05-17 12:11:01,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:11:31 EEST)" executed successfully
2026-05-17 12:11:31,631 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:16:31 EEST)" (scheduled at 2026-05-17 12:11:31.618104+03:00)
2026-05-17 12:11:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:16:31 EEST)" (scheduled at 2026-05-17 12:11:31.622651+03:00)
2026-05-17 12:11:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:21:31 EEST)" (scheduled at 2026-05-17 12:11:31.627072+03:00)
2026-05-17 12:11:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:12:01 EEST)" (scheduled at 2026-05-17 12:11:31.625095+03:00)
2026-05-17 12:11:31,633 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:16:31 EEST)" executed successfully
2026-05-17 12:11:31,635 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:11:31,637 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:21:31 EEST)" executed successfully
2026-05-17 12:11:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:12:01 EEST)" executed successfully
2026-05-17 12:11:32,666 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:11:34,630 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:11:34,636 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:11:34,637 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:11:34,639 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:11:35,575 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=28
2026-05-17 12:11:35,622 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=28
2026-05-17 12:11:35,624 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=6 counts_by_reason={'repeat_cooldown': 6} dropped_tickers=['FAIT', 'ACGC', 'MILS', 'COPR', 'BONY', 'SUGR']
2026-05-17 12:11:35,625 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 6/6 signals.
2026-05-17 12:11:35,671 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 6 signals; nothing to broadcast.
2026-05-17 12:11:36,506 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 12:11:36,567 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:16:31 EEST)" executed successfully
2026-05-17 12:12:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:12:31 EEST)" (scheduled at 2026-05-17 12:12:01.625095+03:00)
2026-05-17 12:12:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:12:31 EEST)" executed successfully
2026-05-17 12:12:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:13:01 EEST)" (scheduled at 2026-05-17 12:12:31.625095+03:00)
2026-05-17 12:12:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:13:01 EEST)" executed successfully
2026-05-17 12:13:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:13:31 EEST)" (scheduled at 2026-05-17 12:13:01.625095+03:00)
2026-05-17 12:13:01,638 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:12:44.636195). Version incremented to 19.
2026-05-17 12:13:01,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:13:31 EEST)" executed successfully
2026-05-17 12:13:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:14:01 EEST)" (scheduled at 2026-05-17 12:13:31.625095+03:00)
2026-05-17 12:13:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:14:01 EEST)" executed successfully
INFO:     127.0.0.1:57970 - "HEAD /telegram HTTP/1.1" 200 OK
INFO:     127.0.0.1:52086 - "HEAD / HTTP/1.1" 200 OK
INFO:     127.0.0.1:58519 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:52086 - "GET /__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:57970 - "GET /telegram/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:58519 - "GET /status/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:58519 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57970 - "GET /__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /telegram/__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52086 - "GET /__next._index.txt?_rsc=ERfXn7tGRj5EupPH HTTP/1.1" 200 OK
INFO:     127.0.0.1:58519 - "GET /telegram/__next.telegram.txt?_rsc=aKACAGocL3t4-4Xd HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /__next.__PAGE__.txt?_rsc=cdk-OvPaaQdzy3F4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57970 - "GET /status/__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52086 - "GET /telegram/__next.telegram.__PAGE__.txt?_rsc=WHz_FkIDzWrFoQE3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58519 - "GET /status/__next.status.txt?_rsc=s0FEf9OOxbpuBOef HTTP/1.1" 200 OK
2026-05-17 12:13:41,616 - horus.settings - INFO - [Settings] AUTO_TRADE_ENABLED update requested=True previous=True current=True changed=False
INFO:     127.0.0.1:52499 - "POST /api/v1/settings HTTP/1.1" 200 OK
2026-05-17 12:13:41,782 - core.StockLoader - INFO - StockLoader: Cache cleared.
[Cache] All analytics caches purged.INFO:     127.0.0.1:50603 - "POST /api/v1/signals/desk/mode HTTP/1.1" 200 OK

INFO:     127.0.0.1:52086 - "GET /status/__next.status.__PAGE__.txt?_rsc=ESW-ijXE9EWSHgP1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:65403 - "POST /api/v1/settings/exclusions HTTP/1.1" 200 OK
INFO:     127.0.0.1:65403 - "HEAD /seasonality HTTP/1.1" 200 OK
INFO:     127.0.0.1:52086 - "HEAD /sectors HTTP/1.1" 200 OK
INFO:     127.0.0.1:52499 - "HEAD /live HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "HEAD /news HTTP/1.1" 200 OK
INFO:     127.0.0.1:65403 - "GET /seasonality/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:52499 - "GET /live/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:52086 - "GET /sectors/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:50603 - "GET /news/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
2026-05-17 12:14:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:14:31 EEST)" (scheduled at 2026-05-17 12:14:01.625095+03:00)
2026-05-17 12:14:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:14:31 EEST)" executed successfully
2026-05-17 12:14:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:15:01 EEST)" (scheduled at 2026-05-17 12:14:31.625095+03:00)
2026-05-17 12:14:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:15:01 EEST)" executed successfully
2026-05-17 12:15:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:15:31 EEST)" (scheduled at 2026-05-17 12:15:01.625095+03:00)
2026-05-17 12:15:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:15:31 EEST)" executed successfully
2026-05-17 12:15:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:16:01 EEST)" (scheduled at 2026-05-17 12:15:31.625095+03:00)
2026-05-17 12:15:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:16:01 EEST)" executed successfully
2026-05-17 12:16:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:16:31 EEST)" (scheduled at 2026-05-17 12:16:01.625095+03:00)
2026-05-17 12:16:01,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:16:31 EEST)" executed successfully
2026-05-17 12:16:31,628 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:21:31 EEST)" (scheduled at 2026-05-17 12:16:31.618104+03:00)
2026-05-17 12:16:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:21:31 EEST)" (scheduled at 2026-05-17 12:16:31.622651+03:00)
2026-05-17 12:16:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:17:01 EEST)" (scheduled at 2026-05-17 12:16:31.625095+03:00)
2026-05-17 12:16:31,630 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:21:31 EEST)" executed successfully
2026-05-17 12:16:31,631 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:16:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:17:01 EEST)" executed successfully
2026-05-17 12:16:33,614 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 12:16:33,615 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:16:36,168 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:16:36,173 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:16:36,174 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:16:36,177 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:16:37,102 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=29
2026-05-17 12:16:37,154 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=29
2026-05-17 12:16:37,155 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=6 counts_by_reason={'repeat_cooldown': 6} dropped_tickers=['ACGC', 'BONY', 'MILS', 'COPR', 'FAIT', 'SUGR']
2026-05-17 12:16:37,156 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 6/6 signals.
2026-05-17 12:16:37,201 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 6 signals; nothing to broadcast.
2026-05-17 12:16:38,029 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 12:16:38,089 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:21:31 EEST)" executed successfully
2026-05-17 12:17:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:17:31 EEST)" (scheduled at 2026-05-17 12:17:01.625095+03:00)
2026-05-17 12:17:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:17:31 EEST)" executed successfully
2026-05-17 12:17:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:18:01 EEST)" (scheduled at 2026-05-17 12:17:31.625095+03:00)
2026-05-17 12:17:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:18:01 EEST)" executed successfully
2026-05-17 12:18:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:18:31 EEST)" (scheduled at 2026-05-17 12:18:01.625095+03:00)
2026-05-17 12:18:01,642 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:17:45.687902). Version incremented to 1.
2026-05-17 12:18:01,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:18:31 EEST)" executed successfully
2026-05-17 12:18:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:19:01 EEST)" (scheduled at 2026-05-17 12:18:31.625095+03:00)
2026-05-17 12:18:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:19:01 EEST)" executed successfully
2026-05-17 12:19:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:19:31 EEST)" (scheduled at 2026-05-17 12:19:01.625095+03:00)
2026-05-17 12:19:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:19:31 EEST)" executed successfully
2026-05-17 12:19:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:20:01 EEST)" (scheduled at 2026-05-17 12:19:31.625095+03:00)
2026-05-17 12:19:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:20:01 EEST)" executed successfully
2026-05-17 12:19:55,540 - TelegramBot - WARNING - Telegram polling error (retry in 300s): HTTPSConnectionPool(host='api.telegram.org', port=443): Max retries exceeded with url: /bottoken/getUpdates?offset=1&timeout=30 (Caused by ConnectTimeoutError(<HTTPSConnection(host='api.telegram.org', port=443) at 0x1daf22774d0>, 'Connection to api.telegram.org timed out. (connect timeout=35)'))
2026-05-17 12:20:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:20:31 EEST)" (scheduled at 2026-05-17 12:20:01.625095+03:00)
2026-05-17 12:20:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:20:31 EEST)" executed successfully
2026-05-17 12:20:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:21:01 EEST)" (scheduled at 2026-05-17 12:20:31.625095+03:00)
2026-05-17 12:20:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:21:01 EEST)" executed successfully
2026-05-17 12:21:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:21:31 EEST)" (scheduled at 2026-05-17 12:21:01.625095+03:00)
2026-05-17 12:21:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:21:31 EEST)" executed successfully
2026-05-17 12:21:31,626 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:26:31 EEST)" (scheduled at 2026-05-17 12:21:31.618104+03:00)
2026-05-17 12:21:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:22:01 EEST)" (scheduled at 2026-05-17 12:21:31.625095+03:00)
2026-05-17 12:21:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:26:31 EEST)" (scheduled at 2026-05-17 12:21:31.622651+03:00)
2026-05-17 12:21:31,627 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:26:31 EEST)" executed successfully
2026-05-17 12:21:31,631 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:21:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:22:01 EEST)" executed successfully
2026-05-17 12:21:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:31:31 EEST)" (scheduled at 2026-05-17 12:21:31.627072+03:00)
2026-05-17 12:21:31,644 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:31:31 EEST)" executed successfully
2026-05-17 12:21:33,821 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 12:21:33,823 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:21:36,955 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:21:36,964 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:21:36,966 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:21:36,969 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:21:37,987 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=30
2026-05-17 12:21:38,040 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=30
2026-05-17 12:21:38,042 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=6 counts_by_reason={'repeat_cooldown': 6} dropped_tickers=['SUGR', 'FAIT', 'BONY', 'MILS', 'COPR', 'ACGC']
2026-05-17 12:21:38,043 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 6/6 signals.
2026-05-17 12:21:38,093 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 6 signals; nothing to broadcast.
2026-05-17 12:21:39,058 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 12:21:39,120 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:26:31 EEST)" executed successfully
2026-05-17 12:22:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:22:31 EEST)" (scheduled at 2026-05-17 12:22:01.625095+03:00)
2026-05-17 12:22:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:22:31 EEST)" executed successfully
2026-05-17 12:22:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:23:01 EEST)" (scheduled at 2026-05-17 12:22:31.625095+03:00)
2026-05-17 12:22:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:23:01 EEST)" executed successfully
2026-05-17 12:23:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:23:31 EEST)" (scheduled at 2026-05-17 12:23:01.625095+03:00)
2026-05-17 12:23:01,640 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:22:47.198306). Version incremented to 2.
2026-05-17 12:23:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:23:31 EEST)" executed successfully
2026-05-17 12:23:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:24:01 EEST)" (scheduled at 2026-05-17 12:23:31.625095+03:00)
2026-05-17 12:23:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:24:01 EEST)" executed successfully
2026-05-17 12:24:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:24:31 EEST)" (scheduled at 2026-05-17 12:24:01.625095+03:00)
2026-05-17 12:24:01,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:24:31 EEST)" executed successfully
2026-05-17 12:24:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:25:01 EEST)" (scheduled at 2026-05-17 12:24:31.625095+03:00)
2026-05-17 12:24:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:25:01 EEST)" executed successfully
2026-05-17 12:25:01,625 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:25:31 EEST)" (scheduled at 2026-05-17 12:25:01.625095+03:00)
2026-05-17 12:25:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:25:31 EEST)" executed successfully
2026-05-17 12:25:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:26:01 EEST)" (scheduled at 2026-05-17 12:25:31.625095+03:00)
2026-05-17 12:25:31,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:26:01 EEST)" executed successfully
2026-05-17 12:26:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:26:31 EEST)" (scheduled at 2026-05-17 12:26:01.625095+03:00)
2026-05-17 12:26:01,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:26:31 EEST)" executed successfully
2026-05-17 12:26:31,633 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:31:31 EEST)" (scheduled at 2026-05-17 12:26:31.618104+03:00)
2026-05-17 12:26:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:31:31 EEST)" (scheduled at 2026-05-17 12:26:31.622651+03:00)
2026-05-17 12:26:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:27:01 EEST)" (scheduled at 2026-05-17 12:26:31.625095+03:00)
2026-05-17 12:26:31,634 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:31:31 EEST)" executed successfully
2026-05-17 12:26:31,635 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:26:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:27:01 EEST)" executed successfully
2026-05-17 12:26:32,645 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:26:35,097 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:26:35,103 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:26:35,104 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:26:35,106 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:26:36,013 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=31
2026-05-17 12:26:36,059 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=31
2026-05-17 12:26:36,060 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=6 counts_by_reason={'repeat_cooldown': 6} dropped_tickers=['MILS', 'COPR', 'FAIT', 'ACGC', 'BONY', 'SUGR']
2026-05-17 12:26:36,061 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 6/6 signals.
2026-05-17 12:26:36,106 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 6 signals; nothing to broadcast.
2026-05-17 12:26:36,951 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 12:26:37,023 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:31:31 EEST)" executed successfully
2026-05-17 12:27:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:27:31 EEST)" (scheduled at 2026-05-17 12:27:01.625095+03:00)
2026-05-17 12:27:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:27:31 EEST)" executed successfully
2026-05-17 12:27:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:28:01 EEST)" (scheduled at 2026-05-17 12:27:31.625095+03:00)
2026-05-17 12:27:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:28:01 EEST)" executed successfully
2026-05-17 12:28:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:28:31 EEST)" (scheduled at 2026-05-17 12:28:01.625095+03:00)
2026-05-17 12:28:01,644 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:27:48.154320). Version incremented to 3.
2026-05-17 12:28:01,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:28:31 EEST)" executed successfully
2026-05-17 12:28:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:29:01 EEST)" (scheduled at 2026-05-17 12:28:31.625095+03:00)
2026-05-17 12:28:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:29:01 EEST)" executed successfully
2026-05-17 12:29:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:29:31 EEST)" (scheduled at 2026-05-17 12:29:01.625095+03:00)
2026-05-17 12:29:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:29:31 EEST)" executed successfully
2026-05-17 12:29:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:30:01 EEST)" (scheduled at 2026-05-17 12:29:31.625095+03:00)
2026-05-17 12:29:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:30:01 EEST)" executed successfully
2026-05-17 12:30:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:30:31 EEST)" (scheduled at 2026-05-17 12:30:01.625095+03:00)
2026-05-17 12:30:01,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:30:31 EEST)" executed successfully
2026-05-17 12:30:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:31:01 EEST)" (scheduled at 2026-05-17 12:30:31.625095+03:00)
2026-05-17 12:30:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:31:01 EEST)" executed successfully
2026-05-17 12:31:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:31:31 EEST)" (scheduled at 2026-05-17 12:31:01.625095+03:00)
2026-05-17 12:31:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:31:31 EEST)" executed successfully
2026-05-17 12:31:31,628 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:36:31 EEST)" (scheduled at 2026-05-17 12:31:31.618104+03:00)
2026-05-17 12:31:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:36:31 EEST)" (scheduled at 2026-05-17 12:31:31.622651+03:00)
2026-05-17 12:31:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:32:01 EEST)" (scheduled at 2026-05-17 12:31:31.625095+03:00)
2026-05-17 12:31:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:41:31 EEST)" (scheduled at 2026-05-17 12:31:31.627072+03:00)
2026-05-17 12:31:31,630 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:36:31 EEST)" executed successfully
2026-05-17 12:31:31,632 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:31:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:32:01 EEST)" executed successfully
2026-05-17 12:31:31,636 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:41:31 EEST)" executed successfully
2026-05-17 12:31:33,663 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 12:31:33,664 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:31:36,117 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:31:36,123 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:31:36,124 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:31:36,126 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:31:37,056 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=32
2026-05-17 12:31:37,103 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=32
2026-05-17 12:31:37,104 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=6 counts_by_reason={'repeat_cooldown': 6} dropped_tickers=['BONY', 'ACGC', 'MILS', 'COPR', 'FAIT', 'SUGR']
2026-05-17 12:31:37,105 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 6/6 signals.
2026-05-17 12:31:37,151 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 6 signals; nothing to broadcast.
2026-05-17 12:31:37,993 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 12:31:38,050 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:36:31 EEST)" executed successfully
2026-05-17 12:32:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:32:31 EEST)" (scheduled at 2026-05-17 12:32:01.625095+03:00)
2026-05-17 12:32:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:32:31 EEST)" executed successfully
2026-05-17 12:32:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:33:01 EEST)" (scheduled at 2026-05-17 12:32:31.625095+03:00)
2026-05-17 12:32:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:33:01 EEST)" executed successfully
2026-05-17 12:33:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:33:31 EEST)" (scheduled at 2026-05-17 12:33:01.625095+03:00)
2026-05-17 12:33:01,642 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:32:49.168277). Version incremented to 4.
2026-05-17 12:33:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:33:31 EEST)" executed successfully
2026-05-17 12:33:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:34:01 EEST)" (scheduled at 2026-05-17 12:33:31.625095+03:00)
2026-05-17 12:33:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:34:01 EEST)" executed successfully
2026-05-17 12:34:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:34:31 EEST)" (scheduled at 2026-05-17 12:34:01.625095+03:00)
2026-05-17 12:34:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:34:31 EEST)" executed successfully
2026-05-17 12:34:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:35:01 EEST)" (scheduled at 2026-05-17 12:34:31.625095+03:00)
2026-05-17 12:34:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:35:01 EEST)" executed successfully
2026-05-17 12:35:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:35:31 EEST)" (scheduled at 2026-05-17 12:35:01.625095+03:00)
2026-05-17 12:35:01,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:35:31 EEST)" executed successfully
2026-05-17 12:35:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:36:01 EEST)" (scheduled at 2026-05-17 12:35:31.625095+03:00)
2026-05-17 12:35:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:36:01 EEST)" executed successfully
2026-05-17 12:36:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:36:31 EEST)" (scheduled at 2026-05-17 12:36:01.625095+03:00)
2026-05-17 12:36:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:36:31 EEST)" executed successfully
2026-05-17 12:36:31,629 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:41:31 EEST)" (scheduled at 2026-05-17 12:36:31.618104+03:00)
2026-05-17 12:36:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:41:31 EEST)" (scheduled at 2026-05-17 12:36:31.622651+03:00)
2026-05-17 12:36:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:37:01 EEST)" (scheduled at 2026-05-17 12:36:31.625095+03:00)
2026-05-17 12:36:31,635 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:41:31 EEST)" executed successfully
2026-05-17 12:36:31,639 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:36:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:37:01 EEST)" executed successfully
2026-05-17 12:36:32,683 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:36:35,104 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:36:35,110 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:36:35,111 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:36:35,114 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:36:36,050 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=33
2026-05-17 12:36:36,095 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=33
2026-05-17 12:36:36,096 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=6 counts_by_reason={'repeat_cooldown': 6} dropped_tickers=['BONY', 'ACGC', 'COPR', 'FAIT', 'MILS', 'SUGR']
2026-05-17 12:36:36,097 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 6/6 signals.
2026-05-17 12:36:36,142 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 6 signals; nothing to broadcast.
2026-05-17 12:36:36,972 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 12:36:37,036 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:41:31 EEST)" executed successfully
2026-05-17 12:37:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:37:31 EEST)" (scheduled at 2026-05-17 12:37:01.625095+03:00)
2026-05-17 12:37:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:37:31 EEST)" executed successfully
2026-05-17 12:37:31,625 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:38:01 EEST)" (scheduled at 2026-05-17 12:37:31.625095+03:00)
2026-05-17 12:37:31,629 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:38:01 EEST)" executed successfully
2026-05-17 12:38:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:38:31 EEST)" (scheduled at 2026-05-17 12:38:01.625095+03:00)
2026-05-17 12:38:01,630 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:37:50.247515). Version incremented to 5.
2026-05-17 12:38:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:38:31 EEST)" executed successfully
2026-05-17 12:38:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:39:01 EEST)" (scheduled at 2026-05-17 12:38:31.625095+03:00)
2026-05-17 12:38:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:39:01 EEST)" executed successfully
2026-05-17 12:39:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:39:31 EEST)" (scheduled at 2026-05-17 12:39:01.625095+03:00)
2026-05-17 12:39:01,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:39:31 EEST)" executed successfully
2026-05-17 12:39:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:40:01 EEST)" (scheduled at 2026-05-17 12:39:31.625095+03:00)
2026-05-17 12:39:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:40:01 EEST)" executed successfully
2026-05-17 12:40:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:40:31 EEST)" (scheduled at 2026-05-17 12:40:01.625095+03:00)
2026-05-17 12:40:01,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:40:31 EEST)" executed successfully
2026-05-17 12:40:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:41:01 EEST)" (scheduled at 2026-05-17 12:40:31.625095+03:00)
2026-05-17 12:40:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:41:01 EEST)" executed successfully
2026-05-17 12:41:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:41:31 EEST)" (scheduled at 2026-05-17 12:41:01.625095+03:00)
2026-05-17 12:41:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:41:31 EEST)" executed successfully
2026-05-17 12:41:31,624 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:46:31 EEST)" (scheduled at 2026-05-17 12:41:31.618104+03:00)
2026-05-17 12:41:31,625 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:46:31 EEST)" (scheduled at 2026-05-17 12:41:31.622651+03:00)
2026-05-17 12:41:31,630 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:46:31 EEST)" executed successfully
2026-05-17 12:41:31,632 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:41:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:51:31 EEST)" (scheduled at 2026-05-17 12:41:31.627072+03:00)
2026-05-17 12:41:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:42:01 EEST)" (scheduled at 2026-05-17 12:41:31.625095+03:00)
2026-05-17 12:41:31,645 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 12:51:31 EEST)" executed successfully
2026-05-17 12:41:31,649 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:42:01 EEST)" executed successfully
2026-05-17 12:41:33,561 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 12:41:33,562 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:41:36,022 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:41:36,028 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:41:36,030 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:41:36,033 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:41:36,948 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=34
2026-05-17 12:41:37,004 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=34
2026-05-17 12:41:37,005 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=6 counts_by_reason={'repeat_cooldown': 6} dropped_tickers=['COPR', 'ACGC', 'FAIT', 'MILS', 'BONY', 'SUGR']
2026-05-17 12:41:37,006 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 6/6 signals.
2026-05-17 12:41:37,054 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 6 signals; nothing to broadcast.
2026-05-17 12:41:37,922 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 12:41:37,977 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:46:31 EEST)" executed successfully
2026-05-17 12:42:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:42:31 EEST)" (scheduled at 2026-05-17 12:42:01.625095+03:00)
2026-05-17 12:42:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:42:31 EEST)" executed successfully
2026-05-17 12:42:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:43:01 EEST)" (scheduled at 2026-05-17 12:42:31.625095+03:00)
2026-05-17 12:42:31,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:43:01 EEST)" executed successfully
2026-05-17 12:43:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:43:31 EEST)" (scheduled at 2026-05-17 12:43:01.625095+03:00)
2026-05-17 12:43:01,644 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:42:51.223784). Version incremented to 6.
2026-05-17 12:43:01,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:43:31 EEST)" executed successfully
2026-05-17 12:43:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:44:01 EEST)" (scheduled at 2026-05-17 12:43:31.625095+03:00)
2026-05-17 12:43:31,650 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:44:01 EEST)" executed successfully
2026-05-17 12:44:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:44:31 EEST)" (scheduled at 2026-05-17 12:44:01.625095+03:00)
2026-05-17 12:44:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:44:31 EEST)" executed successfully
2026-05-17 12:44:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:45:01 EEST)" (scheduled at 2026-05-17 12:44:31.625095+03:00)
2026-05-17 12:44:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:45:01 EEST)" executed successfully
2026-05-17 12:45:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:45:31 EEST)" (scheduled at 2026-05-17 12:45:01.625095+03:00)
2026-05-17 12:45:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:45:31 EEST)" executed successfully
2026-05-17 12:45:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:46:01 EEST)" (scheduled at 2026-05-17 12:45:31.625095+03:00)
2026-05-17 12:45:31,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:46:01 EEST)" executed successfully
2026-05-17 12:46:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:46:31 EEST)" (scheduled at 2026-05-17 12:46:01.625095+03:00)
2026-05-17 12:46:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:46:31 EEST)" executed successfully
2026-05-17 12:46:31,624 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:51:31 EEST)" (scheduled at 2026-05-17 12:46:31.618104+03:00)
2026-05-17 12:46:31,624 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:51:31 EEST)" (scheduled at 2026-05-17 12:46:31.622651+03:00)
2026-05-17 12:46:31,629 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:51:31 EEST)" executed successfully
2026-05-17 12:46:31,635 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:46:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:47:01 EEST)" (scheduled at 2026-05-17 12:46:31.625095+03:00)
2026-05-17 12:46:31,649 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:47:01 EEST)" executed successfully
2026-05-17 12:46:32,648 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:46:35,067 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:46:35,073 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:46:35,074 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:46:35,077 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:46:35,991 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=35
2026-05-17 12:46:36,039 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=35
2026-05-17 12:46:36,040 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=6 counts_by_reason={'repeat_cooldown': 6} dropped_tickers=['FAIT', 'MILS', 'ACGC', 'COPR', 'BONY', 'SUGR']
2026-05-17 12:46:36,041 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 6/6 signals.
2026-05-17 12:46:36,092 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 6 signals; nothing to broadcast.
2026-05-17 12:46:36,929 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 12:46:36,982 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:51:31 EEST)" executed successfully
2026-05-17 12:47:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:47:31 EEST)" (scheduled at 2026-05-17 12:47:01.625095+03:00)
2026-05-17 12:47:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:47:31 EEST)" executed successfully
2026-05-17 12:47:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:48:01 EEST)" (scheduled at 2026-05-17 12:47:31.625095+03:00)
2026-05-17 12:47:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:48:01 EEST)" executed successfully
2026-05-17 12:48:01,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:48:31 EEST)" (scheduled at 2026-05-17 12:48:01.625095+03:00)
2026-05-17 12:48:01,639 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:47:52.180063). Version incremented to 7.
2026-05-17 12:48:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:48:31 EEST)" executed successfully
2026-05-17 12:48:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:49:01 EEST)" (scheduled at 2026-05-17 12:48:31.625095+03:00)
2026-05-17 12:48:31,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:49:01 EEST)" executed successfully
2026-05-17 12:49:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:49:31 EEST)" (scheduled at 2026-05-17 12:49:01.625095+03:00)
2026-05-17 12:49:01,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:49:31 EEST)" executed successfully
2026-05-17 12:49:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:50:01 EEST)" (scheduled at 2026-05-17 12:49:31.625095+03:00)
2026-05-17 12:49:31,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:50:01 EEST)" executed successfully
2026-05-17 12:50:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:50:31 EEST)" (scheduled at 2026-05-17 12:50:01.625095+03:00)
2026-05-17 12:50:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:50:31 EEST)" executed successfully
2026-05-17 12:50:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:51:01 EEST)" (scheduled at 2026-05-17 12:50:31.625095+03:00)
2026-05-17 12:50:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:51:01 EEST)" executed successfully
2026-05-17 12:51:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:51:31 EEST)" (scheduled at 2026-05-17 12:51:01.625095+03:00)
2026-05-17 12:51:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:51:31 EEST)" executed successfully
2026-05-17 12:51:31,626 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:56:31 EEST)" (scheduled at 2026-05-17 12:51:31.618104+03:00)
2026-05-17 12:51:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:56:31 EEST)" (scheduled at 2026-05-17 12:51:31.622651+03:00)
2026-05-17 12:51:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:52:01 EEST)" (scheduled at 2026-05-17 12:51:31.625095+03:00)
2026-05-17 12:51:31,628 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 12:56:31 EEST)" executed successfully
2026-05-17 12:51:31,630 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:51:31,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:52:01 EEST)" executed successfully
2026-05-17 12:51:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:01:31 EEST)" (scheduled at 2026-05-17 12:51:31.627072+03:00)
2026-05-17 12:51:31,644 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:01:31 EEST)" executed successfully
2026-05-17 12:51:33,512 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 12:51:33,513 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:51:35,944 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:51:35,950 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:51:35,951 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:51:35,953 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:51:36,895 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=36
2026-05-17 12:51:36,943 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=36
2026-05-17 12:51:36,944 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=6 counts_by_reason={'repeat_cooldown': 6} dropped_tickers=['MILS', 'FAIT', 'ACGC', 'COPR', 'BONY', 'SUGR']
2026-05-17 12:51:36,945 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 6/6 signals.
2026-05-17 12:51:36,994 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 6 signals; nothing to broadcast.
2026-05-17 12:51:37,823 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 12:51:37,880 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 12:56:31 EEST)" executed successfully
2026-05-17 12:52:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:52:31 EEST)" (scheduled at 2026-05-17 12:52:01.625095+03:00)
2026-05-17 12:52:01,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:52:31 EEST)" executed successfully
2026-05-17 12:52:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:53:01 EEST)" (scheduled at 2026-05-17 12:52:31.625095+03:00)
2026-05-17 12:52:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:53:01 EEST)" executed successfully
2026-05-17 12:53:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:53:31 EEST)" (scheduled at 2026-05-17 12:53:01.625095+03:00)
2026-05-17 12:53:01,630 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:52:53.156410). Version incremented to 8.
2026-05-17 12:53:01,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:53:31 EEST)" executed successfully
2026-05-17 12:53:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:54:01 EEST)" (scheduled at 2026-05-17 12:53:31.625095+03:00)
2026-05-17 12:53:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:54:01 EEST)" executed successfully
2026-05-17 12:54:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:54:31 EEST)" (scheduled at 2026-05-17 12:54:01.625095+03:00)
2026-05-17 12:54:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:54:31 EEST)" executed successfully
2026-05-17 12:54:31,625 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:55:01 EEST)" (scheduled at 2026-05-17 12:54:31.625095+03:00)
2026-05-17 12:54:31,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:55:01 EEST)" executed successfully
2026-05-17 12:55:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:55:31 EEST)" (scheduled at 2026-05-17 12:55:01.625095+03:00)
2026-05-17 12:55:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:55:31 EEST)" executed successfully
2026-05-17 12:55:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:56:01 EEST)" (scheduled at 2026-05-17 12:55:31.625095+03:00)
2026-05-17 12:55:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:56:01 EEST)" executed successfully
2026-05-17 12:56:01,642 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:56:31 EEST)" (scheduled at 2026-05-17 12:56:01.625095+03:00)
2026-05-17 12:56:01,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:56:31 EEST)" executed successfully
2026-05-17 12:56:31,620 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:01:31 EEST)" (scheduled at 2026-05-17 12:56:31.618104+03:00)
2026-05-17 12:56:31,622 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:01:31 EEST)" executed successfully
2026-05-17 12:56:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:01:31 EEST)" (scheduled at 2026-05-17 12:56:31.622651+03:00)
2026-05-17 12:56:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:57:01 EEST)" (scheduled at 2026-05-17 12:56:31.625095+03:00)
2026-05-17 12:56:31,640 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 12:56:31,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:57:01 EEST)" executed successfully
2026-05-17 12:56:33,530 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 12:56:33,531 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 12:56:35,939 - DailyScanner - INFO - Parallel scoring 8 candidates...
2026-05-17 12:56:35,945 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 6 signals across 272 tickers.
2026-05-17 12:56:35,946 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 6 signals. Regime: BULLISH (69.6%)
2026-05-17 12:56:35,948 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 6 signals (regime=BULLISH).
2026-05-17 12:56:36,875 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=37
2026-05-17 12:56:36,920 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=37
2026-05-17 12:56:36,921 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=6 counts_by_reason={'repeat_cooldown': 6} dropped_tickers=['COPR', 'BONY', 'MILS', 'ACGC', 'FAIT', 'SUGR']
2026-05-17 12:56:36,922 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 6/6 signals.
2026-05-17 12:56:36,968 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 6 signals; nothing to broadcast.
2026-05-17 12:56:37,823 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 12:56:37,875 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:01:31 EEST)" executed successfully
2026-05-17 12:57:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:57:31 EEST)" (scheduled at 2026-05-17 12:57:01.625095+03:00)
2026-05-17 12:57:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:57:31 EEST)" executed successfully
2026-05-17 12:57:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:58:01 EEST)" (scheduled at 2026-05-17 12:57:31.625095+03:00)
2026-05-17 12:57:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:58:01 EEST)" executed successfully
2026-05-17 12:57:54,213 - horus.api - INFO - [SyncWorker] Data not fresh (state=STALE, history_ratio=0.924, intraday_ratio=0.0). Running sync_all...
--- Starting Data Lake Synchronization ---
{"ts":"2026-05-17T09:57:54+00:00","event":"pipeline.sync.start","realm":"EGX","intraday_provider":"CSV","intraday_provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"}},"history_provider":"CSV","history_provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"}},"ticks_provider":"MUBASHER_DB","ticks_provider_context":{"provider":"MUBASHER_DB","reason":"configured_ticks_provider","fallback_from":null,"evidence":{"configured_provider":"MUBASHER_DB"}}}
[LocalFeed] Provider policy intraday=CSV, history=CSV

[Parallel] Dispatching Intraday, History, and Ticks sync stages...

[1/3] Syncing Intraday (1min)...
[2/3] Syncing History (Daily)...
[3/3] Syncing Ticks (Trade-by-Trade)...


[Info] Found 312 history CSV files to ingest.[Info] Found 273 intraday CSV files to ingest.

{"ts":"2026-05-17T09:58:00+00:00","event":"pipeline.stage.complete","stage":"history","provider":"CSV","provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":0,"status":"completed"}},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":0,"status":"completed"},"updated_symbols":0}
[2/3] History already up-to-date. Skipping.
2026-05-17 12:58:01,670 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:58:31 EEST)" (scheduled at 2026-05-17 12:58:01.625095+03:00)
2026-05-17 12:58:01,846 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:58:31 EEST)" executed successfully
[3/3] Tick sync: status=ok date=20260514 symbols=236 rows_added=153261
{"ts":"2026-05-17T09:58:10+00:00","event":"pipeline.stage.complete","stage":"intraday","provider":"CSV","provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":240,"status":"completed"}},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":240,"status":"completed"},"updated_symbols":240}
{"ts":"2026-05-17T09:58:10+00:00","event":"pipeline.compaction.complete","realm":"EGX","folder":"history","compacted":0,"scanned":0}
{"ts":"2026-05-17T09:58:10+00:00","event":"pipeline.compaction.complete","realm":"EGX","folder":"intraday","compacted":0,"scanned":0}
{"ts":"2026-05-17T09:58:11+00:00","event":"pipeline.sync.complete","realm":"EGX","duration_sec":17.36,"metrics":{"counters":{"dq.input_rows.total":1342591.0,"dq.input_rows.history":835440.0,"dq.valid_rows.total":1341964.0,"dq.valid_rows.history":834813.0,"dq.input_rows.intraday_store":507151.0,"dq.valid_rows.intraday_store":507151.0,"dq.rejected_rows.total":627.0,"dq.rejected_rows.history":627.0,"pipeline.stage.success.intraday":2.0},"gauges":{"pipeline.stage.updated_symbols.intraday":240.0,"pipeline.compaction.compacted.history":0.0,"pipeline.compaction.compacted.intraday":0.0,"pipeline.fresh_ratio.history":0.924,"pipeline.live_ratio.intraday":0.9087,"pipeline.sync.duration_sec":17.36417245864868}}}

[Done] Synchronization complete in 17.36 seconds.
2026-05-17 12:58:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:59:01 EEST)" (scheduled at 2026-05-17 12:58:31.625095+03:00)
2026-05-17 12:58:31,640 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T12:58:12.723473). Version incremented to 9.
2026-05-17 12:58:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:59:01 EEST)" executed successfully
2026-05-17 12:59:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:59:31 EEST)" (scheduled at 2026-05-17 12:59:01.625095+03:00)
2026-05-17 12:59:01,655 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 12:59:31 EEST)" executed successfully
2026-05-17 12:59:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:00:01 EEST)" (scheduled at 2026-05-17 12:59:31.625095+03:00)
2026-05-17 12:59:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:00:01 EEST)" executed successfully
2026-05-17 13:00:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:00:31 EEST)" (scheduled at 2026-05-17 13:00:01.625095+03:00)
2026-05-17 13:00:01,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:00:31 EEST)" executed successfully
2026-05-17 13:00:27,745 - TelegramBot - WARNING - Telegram polling error (retry in 300s): HTTPSConnectionPool(host='api.telegram.org', port=443): Max retries exceeded with url: /bottoken/getUpdates?offset=1&timeout=30 (Caused by ConnectTimeoutError(<HTTPSConnection(host='api.telegram.org', port=443) at 0x1daf22774d0>, 'Connection to api.telegram.org timed out. (connect timeout=35)'))
2026-05-17 13:00:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:01:01 EEST)" (scheduled at 2026-05-17 13:00:31.625095+03:00)
2026-05-17 13:00:31,649 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:01:01 EEST)" executed successfully
2026-05-17 13:01:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:01:31 EEST)" (scheduled at 2026-05-17 13:01:01.625095+03:00)
2026-05-17 13:01:01,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:01:31 EEST)" executed successfully
2026-05-17 13:01:31,626 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:06:31 EEST)" (scheduled at 2026-05-17 13:01:31.618104+03:00)
2026-05-17 13:01:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:06:31 EEST)" (scheduled at 2026-05-17 13:01:31.622651+03:00)
2026-05-17 13:01:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:02:01 EEST)" (scheduled at 2026-05-17 13:01:31.625095+03:00)
2026-05-17 13:01:31,628 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:06:31 EEST)" executed successfully
2026-05-17 13:01:31,629 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:01:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:11:31 EEST)" (scheduled at 2026-05-17 13:01:31.627072+03:00)
2026-05-17 13:01:31,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:02:01 EEST)" executed successfully
2026-05-17 13:01:31,638 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:11:31 EEST)" executed successfully
2026-05-17 13:01:33,644 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 13:01:33,646 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:01:36,415 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:01:36,430 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:01:36,432 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:01:36,436 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:01:37,542 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=38
2026-05-17 13:01:37,591 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=38
2026-05-17 13:01:37,595 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=2 dropped=5 counts_by_reason={'repeat_cooldown': 5} dropped_tickers=['FAIT', 'BONY', 'ACGC', 'COPR', 'SUGR']
2026-05-17 13:01:37,596 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 5/7 signals.
2026-05-17 13:01:37,647 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasting 2 signals after dedup.
2026-05-17 13:01:41,803 - horus.scheduling - INFO - [Scheduler] Intraday: broadcast completed (cards=2, summary_signals=2).
2026-05-17 13:01:41,860 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:06:31 EEST)" executed successfully
2026-05-17 13:02:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:02:31 EEST)" (scheduled at 2026-05-17 13:02:01.625095+03:00)
2026-05-17 13:02:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:02:31 EEST)" executed successfully
2026-05-17 13:02:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:03:01 EEST)" (scheduled at 2026-05-17 13:02:31.625095+03:00)
2026-05-17 13:02:31,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:03:01 EEST)" executed successfully
2026-05-17 13:03:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:03:31 EEST)" (scheduled at 2026-05-17 13:03:01.625095+03:00)
2026-05-17 13:03:01,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:03:31 EEST)" executed successfully
2026-05-17 13:03:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:04:01 EEST)" (scheduled at 2026-05-17 13:03:31.625095+03:00)
2026-05-17 13:03:31,645 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:03:13.677652). Version incremented to 10.
2026-05-17 13:03:31,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:04:01 EEST)" executed successfully
2026-05-17 13:04:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:04:31 EEST)" (scheduled at 2026-05-17 13:04:01.625095+03:00)
2026-05-17 13:04:01,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:04:31 EEST)" executed successfully
2026-05-17 13:04:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:05:01 EEST)" (scheduled at 2026-05-17 13:04:31.625095+03:00)
2026-05-17 13:04:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:05:01 EEST)" executed successfully
2026-05-17 13:05:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:05:31 EEST)" (scheduled at 2026-05-17 13:05:01.625095+03:00)
2026-05-17 13:05:01,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:05:31 EEST)" executed successfully
2026-05-17 13:05:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:06:01 EEST)" (scheduled at 2026-05-17 13:05:31.625095+03:00)
2026-05-17 13:05:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:06:01 EEST)" executed successfully
2026-05-17 13:06:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:06:31 EEST)" (scheduled at 2026-05-17 13:06:01.625095+03:00)
2026-05-17 13:06:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:06:31 EEST)" executed successfully
2026-05-17 13:06:31,620 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:11:31 EEST)" (scheduled at 2026-05-17 13:06:31.618104+03:00)
2026-05-17 13:06:31,622 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:11:31 EEST)" executed successfully
2026-05-17 13:06:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:11:31 EEST)" (scheduled at 2026-05-17 13:06:31.622651+03:00)
2026-05-17 13:06:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:07:01 EEST)" (scheduled at 2026-05-17 13:06:31.625095+03:00)
2026-05-17 13:06:31,638 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:06:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:07:01 EEST)" executed successfully
2026-05-17 13:06:33,618 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 13:06:33,620 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:06:36,066 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:06:36,072 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:06:36,074 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:06:36,076 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:06:37,001 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=39
2026-05-17 13:06:37,052 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=39
2026-05-17 13:06:37,053 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=7 counts_by_reason={'repeat_cooldown': 7} dropped_tickers=['BONY', 'ACGC', 'FAIT', 'COPR', 'SUGR', 'MEPA', 'ZMID']
2026-05-17 13:06:37,054 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 7/7 signals.
2026-05-17 13:06:37,098 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 7 signals; nothing to broadcast.
2026-05-17 13:06:37,948 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 13:06:37,999 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:11:31 EEST)" executed successfully
2026-05-17 13:07:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:07:31 EEST)" (scheduled at 2026-05-17 13:07:01.625095+03:00)
2026-05-17 13:07:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:07:31 EEST)" executed successfully
2026-05-17 13:07:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:08:01 EEST)" (scheduled at 2026-05-17 13:07:31.625095+03:00)
2026-05-17 13:07:31,649 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:08:01 EEST)" executed successfully
2026-05-17 13:08:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:08:31 EEST)" (scheduled at 2026-05-17 13:08:01.625095+03:00)
2026-05-17 13:08:01,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:08:31 EEST)" executed successfully
2026-05-17 13:08:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:09:01 EEST)" (scheduled at 2026-05-17 13:08:31.625095+03:00)
2026-05-17 13:08:31,639 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:08:14.679152). Version incremented to 11.
2026-05-17 13:08:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:09:01 EEST)" executed successfully
2026-05-17 13:09:01,642 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:09:31 EEST)" (scheduled at 2026-05-17 13:09:01.625095+03:00)
2026-05-17 13:09:01,651 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:09:31 EEST)" executed successfully
2026-05-17 13:09:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:10:01 EEST)" (scheduled at 2026-05-17 13:09:31.625095+03:00)
2026-05-17 13:09:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:10:01 EEST)" executed successfully
2026-05-17 13:10:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:10:31 EEST)" (scheduled at 2026-05-17 13:10:01.625095+03:00)
2026-05-17 13:10:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:10:31 EEST)" executed successfully
2026-05-17 13:10:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:11:01 EEST)" (scheduled at 2026-05-17 13:10:31.625095+03:00)
2026-05-17 13:10:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:11:01 EEST)" executed successfully
2026-05-17 13:11:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:11:31 EEST)" (scheduled at 2026-05-17 13:11:01.625095+03:00)
2026-05-17 13:11:01,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:11:31 EEST)" executed successfully
2026-05-17 13:11:31,620 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:16:31 EEST)" (scheduled at 2026-05-17 13:11:31.618104+03:00)
2026-05-17 13:11:31,621 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:16:31 EEST)" executed successfully
2026-05-17 13:11:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:16:31 EEST)" (scheduled at 2026-05-17 13:11:31.622651+03:00)
2026-05-17 13:11:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:12:01 EEST)" (scheduled at 2026-05-17 13:11:31.625095+03:00)
2026-05-17 13:11:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:21:31 EEST)" (scheduled at 2026-05-17 13:11:31.627072+03:00)
2026-05-17 13:11:31,639 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:11:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:12:01 EEST)" executed successfully
2026-05-17 13:11:31,645 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:21:31 EEST)" executed successfully
2026-05-17 13:11:32,716 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:11:35,507 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:11:35,515 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:11:35,517 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:11:35,520 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:11:36,637 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=40
2026-05-17 13:11:36,697 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=40
2026-05-17 13:11:36,699 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=7 counts_by_reason={'repeat_cooldown': 7} dropped_tickers=['COPR', 'BONY', 'ACGC', 'FAIT', 'SUGR', 'MEPA', 'ZMID']
2026-05-17 13:11:36,700 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 7/7 signals.
2026-05-17 13:11:36,751 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 7 signals; nothing to broadcast.
2026-05-17 13:11:37,579 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 13:11:37,633 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:16:31 EEST)" executed successfully
2026-05-17 13:12:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:12:31 EEST)" (scheduled at 2026-05-17 13:12:01.625095+03:00)
2026-05-17 13:12:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:12:31 EEST)" executed successfully
2026-05-17 13:12:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:13:01 EEST)" (scheduled at 2026-05-17 13:12:31.625095+03:00)
2026-05-17 13:12:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:13:01 EEST)" executed successfully
2026-05-17 13:13:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:13:31 EEST)" (scheduled at 2026-05-17 13:13:01.625095+03:00)
2026-05-17 13:13:01,630 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:13:31 EEST)" executed successfully
2026-05-17 13:13:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:14:01 EEST)" (scheduled at 2026-05-17 13:13:31.625095+03:00)
2026-05-17 13:13:31,633 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:13:15.624163). Version incremented to 12.
2026-05-17 13:13:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:14:01 EEST)" executed successfully
2026-05-17 13:14:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:14:31 EEST)" (scheduled at 2026-05-17 13:14:01.625095+03:00)
2026-05-17 13:14:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:14:31 EEST)" executed successfully
2026-05-17 13:14:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:15:01 EEST)" (scheduled at 2026-05-17 13:14:31.625095+03:00)
2026-05-17 13:14:31,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:15:01 EEST)" executed successfully
2026-05-17 13:15:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:15:31 EEST)" (scheduled at 2026-05-17 13:15:01.625095+03:00)
2026-05-17 13:15:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:15:31 EEST)" executed successfully
2026-05-17 13:15:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:16:01 EEST)" (scheduled at 2026-05-17 13:15:31.625095+03:00)
2026-05-17 13:15:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:16:01 EEST)" executed successfully
2026-05-17 13:16:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:16:31 EEST)" (scheduled at 2026-05-17 13:16:01.625095+03:00)
2026-05-17 13:16:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:16:31 EEST)" executed successfully
2026-05-17 13:16:31,631 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:21:31 EEST)" (scheduled at 2026-05-17 13:16:31.618104+03:00)
2026-05-17 13:16:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:21:31 EEST)" (scheduled at 2026-05-17 13:16:31.622651+03:00)
2026-05-17 13:16:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:17:01 EEST)" (scheduled at 2026-05-17 13:16:31.625095+03:00)
2026-05-17 13:16:31,633 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:21:31 EEST)" executed successfully
2026-05-17 13:16:31,634 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:16:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:17:01 EEST)" executed successfully
2026-05-17 13:16:33,466 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 13:16:33,467 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:16:35,868 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:16:35,874 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:16:35,875 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:16:35,877 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:16:36,806 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=41
2026-05-17 13:16:36,851 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=41
2026-05-17 13:16:36,852 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=7 counts_by_reason={'repeat_cooldown': 7} dropped_tickers=['ACGC', 'BONY', 'COPR', 'FAIT', 'SUGR', 'MEPA', 'ZMID']
2026-05-17 13:16:36,853 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 7/7 signals.
2026-05-17 13:16:36,897 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 7 signals; nothing to broadcast.
2026-05-17 13:16:37,738 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 13:16:37,797 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:21:31 EEST)" executed successfully
2026-05-17 13:17:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:17:31 EEST)" (scheduled at 2026-05-17 13:17:01.625095+03:00)
2026-05-17 13:17:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:17:31 EEST)" executed successfully
2026-05-17 13:17:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:18:01 EEST)" (scheduled at 2026-05-17 13:17:31.625095+03:00)
2026-05-17 13:17:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:18:01 EEST)" executed successfully
2026-05-17 13:18:01,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:18:31 EEST)" (scheduled at 2026-05-17 13:18:01.625095+03:00)
2026-05-17 13:18:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:18:31 EEST)" executed successfully
2026-05-17 13:18:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:19:01 EEST)" (scheduled at 2026-05-17 13:18:31.625095+03:00)
2026-05-17 13:18:31,645 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:18:16.572261). Version incremented to 13.
2026-05-17 13:18:31,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:19:01 EEST)" executed successfully
2026-05-17 13:19:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:19:31 EEST)" (scheduled at 2026-05-17 13:19:01.625095+03:00)
2026-05-17 13:19:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:19:31 EEST)" executed successfully
2026-05-17 13:19:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:20:01 EEST)" (scheduled at 2026-05-17 13:19:31.625095+03:00)
2026-05-17 13:19:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:20:01 EEST)" executed successfully
2026-05-17 13:20:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:20:31 EEST)" (scheduled at 2026-05-17 13:20:01.625095+03:00)
2026-05-17 13:20:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:20:31 EEST)" executed successfully
2026-05-17 13:20:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:21:01 EEST)" (scheduled at 2026-05-17 13:20:31.625095+03:00)
2026-05-17 13:20:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:21:01 EEST)" executed successfully
2026-05-17 13:21:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:21:31 EEST)" (scheduled at 2026-05-17 13:21:01.625095+03:00)
2026-05-17 13:21:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:21:31 EEST)" executed successfully
2026-05-17 13:21:31,618 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:26:31 EEST)" (scheduled at 2026-05-17 13:21:31.618104+03:00)
2026-05-17 13:21:31,620 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:26:31 EEST)" executed successfully
2026-05-17 13:21:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:26:31 EEST)" (scheduled at 2026-05-17 13:21:31.622651+03:00)
2026-05-17 13:21:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:31:31 EEST)" (scheduled at 2026-05-17 13:21:31.627072+03:00)
2026-05-17 13:21:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:22:01 EEST)" (scheduled at 2026-05-17 13:21:31.625095+03:00)
2026-05-17 13:21:31,639 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:21:31,641 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:31:31 EEST)" executed successfully
2026-05-17 13:21:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:22:01 EEST)" executed successfully
2026-05-17 13:21:33,911 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 13:21:33,912 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:21:36,563 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:21:36,570 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:21:36,571 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:21:36,573 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:21:37,688 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=42
2026-05-17 13:21:37,745 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=42
2026-05-17 13:21:37,746 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=7 counts_by_reason={'repeat_cooldown': 7} dropped_tickers=['BONY', 'ACGC', 'COPR', 'FAIT', 'SUGR', 'MEPA', 'ZMID']
2026-05-17 13:21:37,747 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 7/7 signals.
2026-05-17 13:21:37,804 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 7 signals; nothing to broadcast.
2026-05-17 13:21:38,673 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 13:21:38,740 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:26:31 EEST)" executed successfully
2026-05-17 13:22:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:22:31 EEST)" (scheduled at 2026-05-17 13:22:01.625095+03:00)
2026-05-17 13:22:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:22:31 EEST)" executed successfully
2026-05-17 13:22:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:23:01 EEST)" (scheduled at 2026-05-17 13:22:31.625095+03:00)
2026-05-17 13:22:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:23:01 EEST)" executed successfully
2026-05-17 13:23:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:23:31 EEST)" (scheduled at 2026-05-17 13:23:01.625095+03:00)
2026-05-17 13:23:01,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:23:31 EEST)" executed successfully
2026-05-17 13:23:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:24:01 EEST)" (scheduled at 2026-05-17 13:23:31.625095+03:00)
2026-05-17 13:23:31,640 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:23:17.619002). Version incremented to 14.
2026-05-17 13:23:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:24:01 EEST)" executed successfully
2026-05-17 13:24:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:24:31 EEST)" (scheduled at 2026-05-17 13:24:01.625095+03:00)
2026-05-17 13:24:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:24:31 EEST)" executed successfully
2026-05-17 13:24:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:25:01 EEST)" (scheduled at 2026-05-17 13:24:31.625095+03:00)
2026-05-17 13:24:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:25:01 EEST)" executed successfully
2026-05-17 13:25:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:25:31 EEST)" (scheduled at 2026-05-17 13:25:01.625095+03:00)
2026-05-17 13:25:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:25:31 EEST)" executed successfully
2026-05-17 13:25:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:26:01 EEST)" (scheduled at 2026-05-17 13:25:31.625095+03:00)
2026-05-17 13:25:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:26:01 EEST)" executed successfully
2026-05-17 13:26:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:26:31 EEST)" (scheduled at 2026-05-17 13:26:01.625095+03:00)
2026-05-17 13:26:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:26:31 EEST)" executed successfully
2026-05-17 13:26:31,619 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:31:31 EEST)" (scheduled at 2026-05-17 13:26:31.618104+03:00)
2026-05-17 13:26:31,621 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:31:31 EEST)" executed successfully
2026-05-17 13:26:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:31:31 EEST)" (scheduled at 2026-05-17 13:26:31.622651+03:00)
2026-05-17 13:26:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:27:01 EEST)" (scheduled at 2026-05-17 13:26:31.625095+03:00)
2026-05-17 13:26:31,637 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:26:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:27:01 EEST)" executed successfully
2026-05-17 13:26:32,819 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:26:35,438 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:26:35,448 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:26:35,449 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:26:35,452 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:26:36,454 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=43
2026-05-17 13:26:36,508 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=43
2026-05-17 13:26:36,510 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=7 counts_by_reason={'repeat_cooldown': 7} dropped_tickers=['COPR', 'BONY', 'FAIT', 'ACGC', 'SUGR', 'MEPA', 'ZMID']
2026-05-17 13:26:36,512 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 7/7 signals.
2026-05-17 13:26:36,564 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 7 signals; nothing to broadcast.
2026-05-17 13:26:37,475 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 13:26:37,540 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:31:31 EEST)" executed successfully
2026-05-17 13:27:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:27:31 EEST)" (scheduled at 2026-05-17 13:27:01.625095+03:00)
2026-05-17 13:27:01,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:27:31 EEST)" executed successfully
2026-05-17 13:27:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:28:01 EEST)" (scheduled at 2026-05-17 13:27:31.625095+03:00)
2026-05-17 13:27:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:28:01 EEST)" executed successfully
2026-05-17 13:28:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:28:31 EEST)" (scheduled at 2026-05-17 13:28:01.625095+03:00)
2026-05-17 13:28:01,655 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:28:31 EEST)" executed successfully
2026-05-17 13:28:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:29:01 EEST)" (scheduled at 2026-05-17 13:28:31.625095+03:00)
2026-05-17 13:28:31,639 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:28:18.678366). Version incremented to 15.
2026-05-17 13:28:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:29:01 EEST)" executed successfully
2026-05-17 13:29:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:29:31 EEST)" (scheduled at 2026-05-17 13:29:01.625095+03:00)
2026-05-17 13:29:01,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:29:31 EEST)" executed successfully
2026-05-17 13:29:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:30:01 EEST)" (scheduled at 2026-05-17 13:29:31.625095+03:00)
2026-05-17 13:29:31,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:30:01 EEST)" executed successfully
2026-05-17 13:30:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:30:31 EEST)" (scheduled at 2026-05-17 13:30:01.625095+03:00)
2026-05-17 13:30:01,630 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:30:31 EEST)" executed successfully
2026-05-17 13:30:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:31:01 EEST)" (scheduled at 2026-05-17 13:30:31.625095+03:00)
2026-05-17 13:30:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:31:01 EEST)" executed successfully
2026-05-17 13:31:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:31:31 EEST)" (scheduled at 2026-05-17 13:31:01.625095+03:00)
2026-05-17 13:31:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:31:31 EEST)" executed successfully
2026-05-17 13:31:31,634 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:36:31 EEST)" (scheduled at 2026-05-17 13:31:31.618104+03:00)
2026-05-17 13:31:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:36:31 EEST)" (scheduled at 2026-05-17 13:31:31.622651+03:00)
2026-05-17 13:31:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:32:01 EEST)" (scheduled at 2026-05-17 13:31:31.625095+03:00)
2026-05-17 13:31:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:41:31 EEST)" (scheduled at 2026-05-17 13:31:31.627072+03:00)
2026-05-17 13:31:31,637 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:36:31 EEST)" executed successfully
2026-05-17 13:31:31,639 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:31:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:32:01 EEST)" executed successfully
2026-05-17 13:31:31,644 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:41:31 EEST)" executed successfully
2026-05-17 13:31:33,518 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 13:31:33,519 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:31:36,051 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:31:36,057 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:31:36,059 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:31:36,061 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:31:37,031 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=44
2026-05-17 13:31:37,078 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=44
2026-05-17 13:31:37,079 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=7 counts_by_reason={'repeat_cooldown': 7} dropped_tickers=['BONY', 'ACGC', 'COPR', 'FAIT', 'SUGR', 'MEPA', 'ZMID']
2026-05-17 13:31:37,080 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 7/7 signals.
2026-05-17 13:31:37,130 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 7 signals; nothing to broadcast.
2026-05-17 13:31:37,974 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 13:31:38,030 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:36:31 EEST)" executed successfully
2026-05-17 13:32:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:32:31 EEST)" (scheduled at 2026-05-17 13:32:01.625095+03:00)
2026-05-17 13:32:01,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:32:31 EEST)" executed successfully
2026-05-17 13:32:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:33:01 EEST)" (scheduled at 2026-05-17 13:32:31.625095+03:00)
2026-05-17 13:32:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:33:01 EEST)" executed successfully
2026-05-17 13:33:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:33:31 EEST)" (scheduled at 2026-05-17 13:33:01.625095+03:00)
2026-05-17 13:33:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:33:31 EEST)" executed successfully
2026-05-17 13:33:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:34:01 EEST)" (scheduled at 2026-05-17 13:33:31.625095+03:00)
2026-05-17 13:33:31,637 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:33:19.664160). Version incremented to 16.
2026-05-17 13:33:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:34:01 EEST)" executed successfully
INFO:     127.0.0.1:56053 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55556 - "GET /api/v1/data/status HTTP/1.1" 200 OK
2026-05-17 13:34:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:34:31 EEST)" (scheduled at 2026-05-17 13:34:01.625095+03:00)
2026-05-17 13:34:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:34:31 EEST)" executed successfully
2026-05-17 13:34:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:35:01 EEST)" (scheduled at 2026-05-17 13:34:31.625095+03:00)
2026-05-17 13:34:31,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:35:01 EEST)" executed successfully
2026-05-17 13:35:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:35:31 EEST)" (scheduled at 2026-05-17 13:35:01.625095+03:00)
2026-05-17 13:35:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:35:31 EEST)" executed successfully
2026-05-17 13:35:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:36:01 EEST)" (scheduled at 2026-05-17 13:35:31.625095+03:00)
2026-05-17 13:35:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:36:01 EEST)" executed successfully
2026-05-17 13:36:01,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:36:31 EEST)" (scheduled at 2026-05-17 13:36:01.625095+03:00)
2026-05-17 13:36:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:36:31 EEST)" executed successfully
2026-05-17 13:36:31,631 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:41:31 EEST)" (scheduled at 2026-05-17 13:36:31.618104+03:00)
2026-05-17 13:36:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:41:31 EEST)" (scheduled at 2026-05-17 13:36:31.622651+03:00)
2026-05-17 13:36:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:37:01 EEST)" (scheduled at 2026-05-17 13:36:31.625095+03:00)
2026-05-17 13:36:31,633 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:41:31 EEST)" executed successfully
2026-05-17 13:36:31,635 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:36:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:37:01 EEST)" executed successfully
2026-05-17 13:36:33,773 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 13:36:33,774 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:36:36,568 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:36:36,576 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:36:36,577 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:36:36,580 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:36:37,621 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=45
2026-05-17 13:36:37,675 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=45
2026-05-17 13:36:37,676 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=7 counts_by_reason={'repeat_cooldown': 7} dropped_tickers=['COPR', 'FAIT', 'ACGC', 'BONY', 'SUGR', 'MEPA', 'ZMID']
2026-05-17 13:36:37,677 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 7/7 signals.
2026-05-17 13:36:37,731 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 7 signals; nothing to broadcast.
2026-05-17 13:36:38,562 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 13:36:38,629 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:41:31 EEST)" executed successfully
2026-05-17 13:37:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:37:31 EEST)" (scheduled at 2026-05-17 13:37:01.625095+03:00)
2026-05-17 13:37:01,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:37:31 EEST)" executed successfully
2026-05-17 13:37:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:38:01 EEST)" (scheduled at 2026-05-17 13:37:31.625095+03:00)
2026-05-17 13:37:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:38:01 EEST)" executed successfully
2026-05-17 13:38:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:38:31 EEST)" (scheduled at 2026-05-17 13:38:01.625095+03:00)
2026-05-17 13:38:01,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:38:31 EEST)" executed successfully
2026-05-17 13:38:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:39:01 EEST)" (scheduled at 2026-05-17 13:38:31.625095+03:00)
2026-05-17 13:38:31,634 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:38:20.793224). Version incremented to 17.
2026-05-17 13:38:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:39:01 EEST)" executed successfully
2026-05-17 13:39:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:39:31 EEST)" (scheduled at 2026-05-17 13:39:01.625095+03:00)
2026-05-17 13:39:01,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:39:31 EEST)" executed successfully
2026-05-17 13:39:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:40:01 EEST)" (scheduled at 2026-05-17 13:39:31.625095+03:00)
2026-05-17 13:39:31,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:40:01 EEST)" executed successfully
2026-05-17 13:40:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:40:31 EEST)" (scheduled at 2026-05-17 13:40:01.625095+03:00)
2026-05-17 13:40:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:40:31 EEST)" executed successfully
2026-05-17 13:40:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:41:01 EEST)" (scheduled at 2026-05-17 13:40:31.625095+03:00)
2026-05-17 13:40:31,649 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:41:01 EEST)" executed successfully
2026-05-17 13:41:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:41:31 EEST)" (scheduled at 2026-05-17 13:41:01.625095+03:00)
2026-05-17 13:41:01,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:41:31 EEST)" executed successfully
2026-05-17 13:41:31,622 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:46:31 EEST)" (scheduled at 2026-05-17 13:41:31.618104+03:00)
2026-05-17 13:41:31,623 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:46:31 EEST)" (scheduled at 2026-05-17 13:41:31.622651+03:00)
2026-05-17 13:41:31,624 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:46:31 EEST)" executed successfully
2026-05-17 13:41:31,626 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:41:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:51:31 EEST)" (scheduled at 2026-05-17 13:41:31.627072+03:00)
2026-05-17 13:41:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:42:01 EEST)" (scheduled at 2026-05-17 13:41:31.625095+03:00)
2026-05-17 13:41:31,641 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 13:51:31 EEST)" executed successfully
2026-05-17 13:41:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:42:01 EEST)" executed successfully
2026-05-17 13:41:32,691 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:41:35,325 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:41:35,332 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:41:35,334 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:41:35,337 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:41:36,317 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=46
2026-05-17 13:41:36,372 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=46
2026-05-17 13:41:36,374 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=7 counts_by_reason={'repeat_cooldown': 7} dropped_tickers=['COPR', 'ACGC', 'FAIT', 'BONY', 'SUGR', 'MEPA', 'ZMID']
2026-05-17 13:41:36,375 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 7/7 signals.
2026-05-17 13:41:36,431 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 7 signals; nothing to broadcast.
2026-05-17 13:41:37,254 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 13:41:37,310 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:46:31 EEST)" executed successfully
2026-05-17 13:42:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:42:31 EEST)" (scheduled at 2026-05-17 13:42:01.625095+03:00)
2026-05-17 13:42:01,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:42:31 EEST)" executed successfully
2026-05-17 13:42:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:43:01 EEST)" (scheduled at 2026-05-17 13:42:31.625095+03:00)
2026-05-17 13:42:31,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:43:01 EEST)" executed successfully
2026-05-17 13:43:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:43:31 EEST)" (scheduled at 2026-05-17 13:43:01.625095+03:00)
2026-05-17 13:43:01,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:43:31 EEST)" executed successfully
2026-05-17 13:43:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:44:01 EEST)" (scheduled at 2026-05-17 13:43:31.625095+03:00)
2026-05-17 13:43:31,634 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:43:21.902066). Version incremented to 18.
2026-05-17 13:43:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:44:01 EEST)" executed successfully
2026-05-17 13:44:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:44:31 EEST)" (scheduled at 2026-05-17 13:44:01.625095+03:00)
2026-05-17 13:44:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:44:31 EEST)" executed successfully
2026-05-17 13:44:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:45:01 EEST)" (scheduled at 2026-05-17 13:44:31.625095+03:00)
2026-05-17 13:44:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:45:01 EEST)" executed successfully
2026-05-17 13:45:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:45:31 EEST)" (scheduled at 2026-05-17 13:45:01.625095+03:00)
2026-05-17 13:45:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:45:31 EEST)" executed successfully
2026-05-17 13:45:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:46:01 EEST)" (scheduled at 2026-05-17 13:45:31.625095+03:00)
2026-05-17 13:45:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:46:01 EEST)" executed successfully
2026-05-17 13:46:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:46:31 EEST)" (scheduled at 2026-05-17 13:46:01.625095+03:00)
2026-05-17 13:46:01,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:46:31 EEST)" executed successfully
2026-05-17 13:46:31,619 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:51:31 EEST)" (scheduled at 2026-05-17 13:46:31.618104+03:00)
2026-05-17 13:46:31,620 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:51:31 EEST)" executed successfully
2026-05-17 13:46:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:51:31 EEST)" (scheduled at 2026-05-17 13:46:31.622651+03:00)
2026-05-17 13:46:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:47:01 EEST)" (scheduled at 2026-05-17 13:46:31.625095+03:00)
2026-05-17 13:46:31,640 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:46:31,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:47:01 EEST)" executed successfully
2026-05-17 13:46:33,720 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 13:46:33,721 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:46:36,348 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:46:36,354 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:46:36,356 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:46:36,359 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:46:37,343 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=47
2026-05-17 13:46:37,394 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=47
2026-05-17 13:46:37,395 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=7 counts_by_reason={'repeat_cooldown': 7} dropped_tickers=['FAIT', 'COPR', 'BONY', 'ACGC', 'SUGR', 'MEPA', 'ZMID']
2026-05-17 13:46:37,396 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 7/7 signals.
2026-05-17 13:46:37,445 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 7 signals; nothing to broadcast.
2026-05-17 13:46:38,299 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 13:46:38,355 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:51:31 EEST)" executed successfully
2026-05-17 13:47:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:47:31 EEST)" (scheduled at 2026-05-17 13:47:01.625095+03:00)
2026-05-17 13:47:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:47:31 EEST)" executed successfully
2026-05-17 13:47:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:48:01 EEST)" (scheduled at 2026-05-17 13:47:31.625095+03:00)
2026-05-17 13:47:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:48:01 EEST)" executed successfully
2026-05-17 13:48:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:48:31 EEST)" (scheduled at 2026-05-17 13:48:01.625095+03:00)
2026-05-17 13:48:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:48:31 EEST)" executed successfully
2026-05-17 13:48:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:49:01 EEST)" (scheduled at 2026-05-17 13:48:31.625095+03:00)
2026-05-17 13:48:31,634 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:48:22.927442). Version incremented to 19.
2026-05-17 13:48:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:49:01 EEST)" executed successfully
2026-05-17 13:49:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:49:31 EEST)" (scheduled at 2026-05-17 13:49:01.625095+03:00)
2026-05-17 13:49:01,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:49:31 EEST)" executed successfully
2026-05-17 13:49:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:50:01 EEST)" (scheduled at 2026-05-17 13:49:31.625095+03:00)
2026-05-17 13:49:31,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:50:01 EEST)" executed successfully
2026-05-17 13:50:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:50:31 EEST)" (scheduled at 2026-05-17 13:50:01.625095+03:00)
2026-05-17 13:50:01,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:50:31 EEST)" executed successfully
2026-05-17 13:50:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:51:01 EEST)" (scheduled at 2026-05-17 13:50:31.625095+03:00)
2026-05-17 13:50:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:51:01 EEST)" executed successfully
2026-05-17 13:51:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:51:31 EEST)" (scheduled at 2026-05-17 13:51:01.625095+03:00)
2026-05-17 13:51:01,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:51:31 EEST)" executed successfully
2026-05-17 13:51:31,620 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:56:31 EEST)" (scheduled at 2026-05-17 13:51:31.618104+03:00)
2026-05-17 13:51:31,622 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 13:56:31 EEST)" executed successfully
2026-05-17 13:51:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:56:31 EEST)" (scheduled at 2026-05-17 13:51:31.622651+03:00)
2026-05-17 13:51:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 14:01:31 EEST)" (scheduled at 2026-05-17 13:51:31.627072+03:00)
2026-05-17 13:51:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:52:01 EEST)" (scheduled at 2026-05-17 13:51:31.625095+03:00)
2026-05-17 13:51:31,643 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:51:31,647 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 14:01:31 EEST)" executed successfully
2026-05-17 13:51:31,651 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:52:01 EEST)" executed successfully
2026-05-17 13:51:32,720 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:51:35,326 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:51:35,333 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:51:35,335 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:51:35,338 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:51:36,344 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=48
2026-05-17 13:51:36,394 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=48
2026-05-17 13:51:36,396 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=7 counts_by_reason={'repeat_cooldown': 7} dropped_tickers=['FAIT', 'ACGC', 'BONY', 'COPR', 'SUGR', 'MEPA', 'ZMID']
2026-05-17 13:51:36,397 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 7/7 signals.
2026-05-17 13:51:36,447 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 7 signals; nothing to broadcast.
2026-05-17 13:51:37,293 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 13:51:37,351 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 13:56:31 EEST)" executed successfully
2026-05-17 13:52:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:52:31 EEST)" (scheduled at 2026-05-17 13:52:01.625095+03:00)
2026-05-17 13:52:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:52:31 EEST)" executed successfully
2026-05-17 13:52:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:53:01 EEST)" (scheduled at 2026-05-17 13:52:31.625095+03:00)
2026-05-17 13:52:31,635 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:53:01 EEST)" executed successfully
2026-05-17 13:53:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:53:31 EEST)" (scheduled at 2026-05-17 13:53:01.625095+03:00)
2026-05-17 13:53:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:53:31 EEST)" executed successfully
2026-05-17 13:53:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:54:01 EEST)" (scheduled at 2026-05-17 13:53:31.625095+03:00)
2026-05-17 13:53:31,642 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:53:23.913860). Version incremented to 20.
2026-05-17 13:53:31,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:54:01 EEST)" executed successfully
2026-05-17 13:54:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:54:31 EEST)" (scheduled at 2026-05-17 13:54:01.625095+03:00)
2026-05-17 13:54:01,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:54:31 EEST)" executed successfully
INFO:     127.0.0.1:50605 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
{"ts":"2026-05-17T10:54:30+00:00","event":"pipeline.alert","alert_key":"intraday_live_ratio_low","observed":0.6464,"threshold":0.65}
INFO:     127.0.0.1:63386 - "GET /api/v1/data/status HTTP/1.1" 200 OK
2026-05-17 13:54:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:55:01 EEST)" (scheduled at 2026-05-17 13:54:31.625095+03:00)
2026-05-17 13:54:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:55:01 EEST)" executed successfully
INFO:     127.0.0.1:63386 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63386 - "HEAD /telegram HTTP/1.1" 200 OK
INFO:     127.0.0.1:63386 - "HEAD / HTTP/1.1" 200 OK
INFO:     127.0.0.1:63386 - "GET /telegram/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:63386 - "GET /__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:63386 - "GET /telegram/__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63386 - "GET /telegram/__next.telegram.txt?_rsc=aKACAGocL3t4-4Xd HTTP/1.1" 200 OK
INFO:     127.0.0.1:61331 - "GET /telegram/__next._index.txt?_rsc=ERfXn7tGRj5EupPH HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /telegram/__next.telegram.__PAGE__.txt?_rsc=WHz_FkIDzWrFoQE3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54646 - "GET /__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61331 - "GET /__next.__PAGE__.txt?_rsc=cdk-OvPaaQdzy3F4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54646 - "HEAD /portfolio HTTP/1.1" 200 OK
INFO:     127.0.0.1:61331 - "HEAD /settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:54646 - "GET /portfolio/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:61331 - "GET /settings/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /portfolio/__next.portfolio.txt?_rsc=YjTEZ0V8rdGUR4wk HTTP/1.1" 200 OK
INFO:     127.0.0.1:63386 - "GET /portfolio/__next.portfolio.__PAGE__.txt?_rsc=OgI3Hua9Z5sXnHWS HTTP/1.1" 200 OK
INFO:     127.0.0.1:54646 - "GET /portfolio/__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61331 - "GET /settings/__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63386 - "GET /settings/__next.settings.__PAGE__.txt?_rsc=STmVY4j0xRDbRMWT HTTP/1.1" 200 OK
INFO:     127.0.0.1:54646 - "GET /settings/__next.settings.txt?_rsc=OVhHU-mI8u6GSunH HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/system-comparison HTTP/1.1" 200 OK
INFO:     127.0.0.1:54646 - "GET /_next/static/chunks/0kw~49m4zhtr5.js HTTP/1.1" 304 Not Modified
INFO:     127.0.0.1:51217 - "GET /api/v1/settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:63386 - "GET /_next/static/chunks/13sjwypsgf9.v.js HTTP/1.1" 304 Not Modified
INFO:     127.0.0.1:61331 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/performance/4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54646 - "GET /api/v1/portfolio/execution-history/4?limit=100 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63386 - "GET /api/v1/portfolio/system-comparison HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:61331 - "GET /api/v1/portfolio?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/analytics/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/portfolio/performance/4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio/execution-history/4?limit=100 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54646 - "GET /api/v1/portfolio/analysis?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63386 - "GET /api/v1/portfolio/report?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:61331 - "GET /api/v1/portfolio?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/analytics/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio/analysis?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/portfolio/report?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /_next/static/chunks/0hzrquxeldib2.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /status/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /status/__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /status/__next.status.__PAGE__.txt?_rsc=ESW-ijXE9EWSHgP1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /status/__next.status.txt?_rsc=s0FEf9OOxbpuBOef HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/system-comparison HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/performance/3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/portfolio/execution-history/3?limit=100 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio?portfolio_id=3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/analytics/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/portfolio/analysis?portfolio_id=3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio/report?portfolio_id=3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/portfolio/system-comparison HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/portfolio/performance/4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/execution-history/4?limit=100 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53637 - "GET /api/v1/analytics/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/portfolio/analysis?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/portfolio/report?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/portfolio/system-comparison HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/portfolio/performance/5 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio/execution-history/5?limit=100 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/portfolio?portfolio_id=5 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53637 - "GET /api/v1/analytics/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/analysis?portfolio_id=5 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/portfolio/report?portfolio_id=5 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/system-comparison HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/performance/2 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53637 - "GET /api/v1/portfolio/execution-history/2?limit=100 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/portfolio?portfolio_id=2 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/analytics/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio/analysis?portfolio_id=2 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/portfolio/report?portfolio_id=2 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio/system-comparison HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio/performance/1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/portfolio/execution-history/1?limit=100 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/analytics/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/portfolio?portfolio_id=1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/report?portfolio_id=1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53637 - "GET /api/v1/portfolio/analysis?portfolio_id=1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/system-comparison HTTP/1.1" 200 OK
INFO:     127.0.0.1:53637 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/performance/5 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/portfolio/execution-history/5?limit=100 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/analytics/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:53637 - "GET /api/v1/portfolio?portfolio_id=5 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/portfolio/analysis?portfolio_id=5 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio/report?portfolio_id=5 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/portfolio/system-comparison HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/portfolio/performance/6 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53637 - "GET /api/v1/portfolio/execution-history/6?limit=100 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/analytics/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio?portfolio_id=6 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/portfolio/analysis?portfolio_id=6 HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/report?portfolio_id=6 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/data/status HTTP/1.1" 200 OK
2026-05-17 13:55:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:55:31 EEST)" (scheduled at 2026-05-17 13:55:01.625095+03:00)
2026-05-17 13:55:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:55:31 EEST)" executed successfully
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/system-comparison HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/system/boot-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/portfolio/performance/4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/portfolio/execution-history/4?limit=100 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50952 - "GET /api/v1/analytics/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:53637 - "GET /api/v1/portfolio/analysis?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/portfolio?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/portfolio/report?portfolio_id=4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/settings/exclusions HTTP/1.1" 200 OK
INFO:     127.0.0.1:53637 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:62368 - "GET /api/v1/settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:50720 - "GET /api/v1/settings/exclusions HTTP/1.1" 200 OK
INFO:     127.0.0.1:51217 - "GET /api/v1/signals/desk HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/data/tickers HTTP/1.1" 200 OK
INFO:     127.0.0.1:57901 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58136 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 13:55:31,669 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:56:01 EEST)" (scheduled at 2026-05-17 13:55:31.625095+03:00)
2026-05-17 13:55:31,674 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:56:01 EEST)" executed successfully
INFO:     127.0.0.1:61486 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61486 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:50204 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 13:56:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:56:31 EEST)" (scheduled at 2026-05-17 13:56:01.625095+03:00)
2026-05-17 13:56:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:56:31 EEST)" executed successfully
INFO:     127.0.0.1:53298 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 13:56:31,619 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:01:31 EEST)" (scheduled at 2026-05-17 13:56:31.618104+03:00)
2026-05-17 13:56:31,621 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:01:31 EEST)" executed successfully
2026-05-17 13:56:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:01:31 EEST)" (scheduled at 2026-05-17 13:56:31.622651+03:00)
2026-05-17 13:56:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:57:01 EEST)" (scheduled at 2026-05-17 13:56:31.625095+03:00)
2026-05-17 13:56:31,643 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 13:56:31,653 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:57:01 EEST)" executed successfully
2026-05-17 13:56:34,451 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 13:56:34,452 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 13:56:37,487 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 13:56:37,495 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 13:56:37,496 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (71.5%)
2026-05-17 13:56:37,498 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 7 signals (regime=BULLISH).
2026-05-17 13:56:38,512 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=49
2026-05-17 13:56:38,566 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=49
2026-05-17 13:56:38,567 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=7 counts_by_reason={'repeat_cooldown': 7} dropped_tickers=['FAIT', 'BONY', 'ACGC', 'COPR', 'SUGR', 'MEPA', 'ZMID']
2026-05-17 13:56:38,568 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 7/7 signals.
2026-05-17 13:56:38,621 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 7 signals; nothing to broadcast.
2026-05-17 13:56:39,452 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 13:56:39,509 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:01:31 EEST)" executed successfully
2026-05-17 13:57:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:57:31 EEST)" (scheduled at 2026-05-17 13:57:01.625095+03:00)
2026-05-17 13:57:01,644 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:57:31 EEST)" executed successfully
INFO:     127.0.0.1:55276 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 13:57:31,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:58:01 EEST)" (scheduled at 2026-05-17 13:57:31.625095+03:00)
2026-05-17 13:57:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:58:01 EEST)" executed successfully
2026-05-17 13:58:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:58:31 EEST)" (scheduled at 2026-05-17 13:58:01.625095+03:00)
2026-05-17 13:58:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:58:31 EEST)" executed successfully
2026-05-17 13:58:24,944 - horus.api - INFO - [SyncWorker] Data not fresh (state=STALE, history_ratio=0.924, intraday_ratio=0.0). Running sync_all...
--- Starting Data Lake Synchronization ---
{"ts":"2026-05-17T10:58:25+00:00","event":"pipeline.sync.start","realm":"EGX","intraday_provider":"CSV","intraday_provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"}},"history_provider":"CSV","history_provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"}},"ticks_provider":"MUBASHER_DB","ticks_provider_context":{"provider":"MUBASHER_DB","reason":"configured_ticks_provider","fallback_from":null,"evidence":{"configured_provider":"MUBASHER_DB"}}}
[LocalFeed] Provider policy intraday=CSV, history=CSV

[Parallel] Dispatching Intraday, History, and Ticks sync stages...

[1/3] Syncing Intraday (1min)...
[2/3] Syncing History (Daily)...
[3/3] Syncing Ticks (Trade-by-Trade)...


[Info] Found 273 intraday CSV files to ingest.[Info] Found 312 history CSV files to ingest.

2026-05-17 13:58:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:59:01 EEST)" (scheduled at 2026-05-17 13:58:31.625095+03:00)
2026-05-17 13:58:31,654 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:59:01 EEST)" executed successfully
{"ts":"2026-05-17T10:58:31+00:00","event":"pipeline.stage.complete","stage":"history","provider":"CSV","provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":0,"status":"completed"}},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":0,"status":"completed"},"updated_symbols":0}
[2/3] History already up-to-date. Skipping.
[3/3] Tick sync: status=ok date=20260514 symbols=0 rows_added=0
{"ts":"2026-05-17T10:58:41+00:00","event":"pipeline.stage.complete","stage":"intraday","provider":"CSV","provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":242,"status":"completed"}},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":242,"status":"completed"},"updated_symbols":242}
{"ts":"2026-05-17T10:58:41+00:00","event":"pipeline.compaction.complete","realm":"EGX","folder":"history","compacted":0,"scanned":0}
{"ts":"2026-05-17T10:58:41+00:00","event":"pipeline.compaction.complete","realm":"EGX","folder":"intraday","compacted":0,"scanned":0}
{"ts":"2026-05-17T10:58:42+00:00","event":"pipeline.sync.complete","realm":"EGX","duration_sec":17.83,"metrics":{"counters":{"dq.input_rows.total":1351258.0,"dq.input_rows.history":835440.0,"dq.valid_rows.total":1350631.0,"dq.valid_rows.history":834813.0,"dq.input_rows.intraday_store":515818.0,"dq.valid_rows.intraday_store":515818.0,"dq.rejected_rows.total":627.0,"dq.rejected_rows.history":627.0,"pipeline.stage.success.intraday":3.0},"gauges":{"pipeline.stage.updated_symbols.intraday":242.0,"pipeline.compaction.compacted.history":0.0,"pipeline.compaction.compacted.intraday":0.0,"pipeline.fresh_ratio.history":0.924,"pipeline.live_ratio.intraday":0.9163,"pipeline.sync.duration_sec":17.82643699645996}}}

[Done] Synchronization complete in 17.83 seconds.
2026-05-17 13:59:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:59:31 EEST)" (scheduled at 2026-05-17 13:59:01.625095+03:00)
2026-05-17 13:59:01,639 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T13:58:44.242304). Version incremented to 21.
2026-05-17 13:59:01,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 13:59:31 EEST)" executed successfully
2026-05-17 13:59:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:00:01 EEST)" (scheduled at 2026-05-17 13:59:31.625095+03:00)
2026-05-17 13:59:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:00:01 EEST)" executed successfully
2026-05-17 14:00:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:00:31 EEST)" (scheduled at 2026-05-17 14:00:01.625095+03:00)
2026-05-17 14:00:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:00:31 EEST)" executed successfully
2026-05-17 14:00:31,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:01:01 EEST)" (scheduled at 2026-05-17 14:00:31.625095+03:00)
2026-05-17 14:00:31,649 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:01:01 EEST)" executed successfully
2026-05-17 14:01:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:01:31 EEST)" (scheduled at 2026-05-17 14:01:01.625095+03:00)
2026-05-17 14:01:01,649 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:01:31 EEST)" executed successfully
INFO:     127.0.0.1:60802 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:59437 - "GET /api/v1/data/status HTTP/1.1" 200 OK
2026-05-17 14:01:31,633 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:06:31 EEST)" (scheduled at 2026-05-17 14:01:31.618104+03:00)
2026-05-17 14:01:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:02:01 EEST)" (scheduled at 2026-05-17 14:01:31.625095+03:00)
2026-05-17 14:01:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:06:31 EEST)" (scheduled at 2026-05-17 14:01:31.622651+03:00)
2026-05-17 14:01:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 14:11:31 EEST)" (scheduled at 2026-05-17 14:01:31.627072+03:00)
2026-05-17 14:01:31,635 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:06:31 EEST)" executed successfully
2026-05-17 14:01:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:02:01 EEST)" executed successfully
2026-05-17 14:01:31,640 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 14:01:31,644 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 14:11:31 EEST)" executed successfully
2026-05-17 14:01:32,796 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 14:01:36,161 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 14:01:36,167 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 4 signals across 272 tickers.
2026-05-17 14:01:36,168 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 4 signals. Regime: BULLISH (57.8%)
2026-05-17 14:01:36,171 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 4 signals (regime=BULLISH).
2026-05-17 14:01:37,146 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=50
2026-05-17 14:01:37,196 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=50
2026-05-17 14:01:37,197 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=4 counts_by_reason={'repeat_cooldown': 4} dropped_tickers=['FAIT', 'BONY', 'COPR', 'SUGR']
2026-05-17 14:01:37,198 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 4/4 signals.
2026-05-17 14:01:37,247 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 4 signals; nothing to broadcast.
2026-05-17 14:01:38,161 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 14:01:38,217 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:06:31 EEST)" executed successfully
2026-05-17 14:02:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:02:31 EEST)" (scheduled at 2026-05-17 14:02:01.625095+03:00)
2026-05-17 14:02:01,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:02:31 EEST)" executed successfully
2026-05-17 14:02:31,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:03:01 EEST)" (scheduled at 2026-05-17 14:02:31.625095+03:00)
2026-05-17 14:02:31,634 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:03:01 EEST)" executed successfully
2026-05-17 14:03:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:03:31 EEST)" (scheduled at 2026-05-17 14:03:01.625095+03:00)
2026-05-17 14:03:01,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:03:31 EEST)" executed successfully
2026-05-17 14:03:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:04:01 EEST)" (scheduled at 2026-05-17 14:03:31.625095+03:00)
2026-05-17 14:03:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:04:01 EEST)" executed successfully
2026-05-17 14:04:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:04:31 EEST)" (scheduled at 2026-05-17 14:04:01.625095+03:00)
2026-05-17 14:04:01,634 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T14:03:45.426761). Version incremented to 22.
2026-05-17 14:04:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:04:31 EEST)" executed successfully
2026-05-17 14:04:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:05:01 EEST)" (scheduled at 2026-05-17 14:04:31.625095+03:00)
2026-05-17 14:04:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:05:01 EEST)" executed successfully
2026-05-17 14:05:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:05:31 EEST)" (scheduled at 2026-05-17 14:05:01.625095+03:00)
2026-05-17 14:05:01,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:05:31 EEST)" executed successfully
2026-05-17 14:05:31,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:06:01 EEST)" (scheduled at 2026-05-17 14:05:31.625095+03:00)
2026-05-17 14:05:31,650 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:06:01 EEST)" executed successfully
2026-05-17 14:06:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:06:31 EEST)" (scheduled at 2026-05-17 14:06:01.625095+03:00)
2026-05-17 14:06:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:06:31 EEST)" executed successfully
2026-05-17 14:06:31,632 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:11:31 EEST)" (scheduled at 2026-05-17 14:06:31.618104+03:00)
2026-05-17 14:06:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:11:31 EEST)" (scheduled at 2026-05-17 14:06:31.622651+03:00)
2026-05-17 14:06:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:07:01 EEST)" (scheduled at 2026-05-17 14:06:31.625095+03:00)
2026-05-17 14:06:31,633 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:11:31 EEST)" executed successfully
2026-05-17 14:06:31,635 - SignalExecutor - WARNING - [SignalExecutor] Pending entries blocked by live execution guard.
2026-05-17 14:06:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:07:01 EEST)" executed successfully
2026-05-17 14:06:33,581 - DailyScanner - INFO - Intraday sync skipped: freshness already OK.
2026-05-17 14:06:33,584 - DailyScanner - INFO - Scanning 272 tickers. Intraday=True PreClose=False
2026-05-17 14:06:36,100 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 14:06:36,106 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 4 signals across 272 tickers.
2026-05-17 14:06:36,107 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 4 signals. Regime: BULLISH (57.8%)
2026-05-17 14:06:36,110 - horus.scheduling - INFO - [Scheduler] Intraday: scanner returned 4 signals (regime=BULLISH).
2026-05-17 14:06:37,055 - horus.scheduling - INFO - [Scheduler] Intraday: persisted signal run status=completed scan_type=INTRADAY run_id=51
2026-05-17 14:06:37,105 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=51
2026-05-17 14:06:37,107 - horus.alerts - INFO - [Deduplicator] label=INTRADAY kept=0 dropped=4 counts_by_reason={'repeat_cooldown': 4} dropped_tickers=['FAIT', 'COPR', 'BONY', 'SUGR']
2026-05-17 14:06:37,108 - horus.scheduling - INFO - [Scheduler] Intraday: dedup dropped 4/4 signals.
2026-05-17 14:06:37,157 - horus.scheduling - INFO - [Scheduler] Intraday: dedup filtered all 4 signals; nothing to broadcast.
2026-05-17 14:06:38,013 - horus.scheduling - INFO - [Scheduler] Intraday: broadcasted dedup status update.
2026-05-17 14:06:38,070 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:11:31 EEST)" executed successfully
2026-05-17 14:07:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:07:31 EEST)" (scheduled at 2026-05-17 14:07:01.625095+03:00)
2026-05-17 14:07:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:07:31 EEST)" executed successfully
2026-05-17 14:07:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:08:01 EEST)" (scheduled at 2026-05-17 14:07:31.625095+03:00)
2026-05-17 14:07:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:08:01 EEST)" executed successfully
2026-05-17 14:08:01,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:08:31 EEST)" (scheduled at 2026-05-17 14:08:01.625095+03:00)
2026-05-17 14:08:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:08:31 EEST)" executed successfully
2026-05-17 14:08:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:09:01 EEST)" (scheduled at 2026-05-17 14:08:31.625095+03:00)
2026-05-17 14:08:31,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:09:01 EEST)" executed successfully
2026-05-17 14:09:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:09:31 EEST)" (scheduled at 2026-05-17 14:09:01.625095+03:00)
2026-05-17 14:09:01,639 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T14:08:46.414930). Version incremented to 23.
2026-05-17 14:09:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:09:31 EEST)" executed successfully
2026-05-17 14:09:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:10:01 EEST)" (scheduled at 2026-05-17 14:09:31.625095+03:00)
2026-05-17 14:09:31,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:10:01 EEST)" executed successfully
2026-05-17 14:10:00,005 - apscheduler.executors.default - INFO - Running job "scheduled_pre_close_scan (trigger: cron[hour='14', minute='10'], next run at: 2026-05-18 14:10:00 EEST)" (scheduled at 2026-05-17 14:10:00+03:00)
2026-05-17 14:10:01,346 - DailyScanner - INFO - Scanning 272 tickers. Intraday=False PreClose=True
2026-05-17 14:10:01,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:10:31 EEST)" (scheduled at 2026-05-17 14:10:01.625095+03:00)
2026-05-17 14:10:01,646 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:10:31 EEST)" executed successfully
2026-05-17 14:10:04,463 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 14:10:04,472 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 4 signals across 272 tickers.
2026-05-17 14:10:04,473 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 4 signals. Regime: BULLISH (57.8%)
2026-05-17 14:10:04,475 - horus.scheduling - INFO - [Scheduler] Pre-Close/Daily: scanner returned 4 signals (regime=BULLISH).
2026-05-17 14:10:05,627 - horus.scheduling - INFO - [Scheduler] Pre-Close/Daily: persisted signal run status=completed scan_type=PRE_CLOSE run_id=52
2026-05-17 14:10:05,684 - SignalExecutor - WARNING - [SignalExecutor] Live execution guard blocked run_id=52
2026-05-17 14:10:05,688 - horus.scheduling - INFO - [Scheduler] Pre-Close/Daily: broadcasting 4 signals after dedup.
2026-05-17 14:10:12,302 - horus.scheduling - INFO - [Scheduler] Pre-Close/Daily: broadcast completed (cards=4, summary_signals=4).
2026-05-17 14:10:12,368 - apscheduler.executors.default - INFO - Job "scheduled_pre_close_scan (trigger: cron[hour='14', minute='10'], next run at: 2026-05-18 14:10:00 EEST)" executed successfully
2026-05-17 14:10:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:11:01 EEST)" (scheduled at 2026-05-17 14:10:31.625095+03:00)
2026-05-17 14:10:31,648 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:11:01 EEST)" executed successfully
2026-05-17 14:11:01,639 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:11:31 EEST)" (scheduled at 2026-05-17 14:11:01.625095+03:00)
2026-05-17 14:11:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:11:31 EEST)" executed successfully
2026-05-17 14:11:31,629 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:16:31 EEST)" (scheduled at 2026-05-17 14:11:31.618104+03:00)
2026-05-17 14:11:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:16:31 EEST)" (scheduled at 2026-05-17 14:11:31.622651+03:00)
2026-05-17 14:11:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 14:21:31 EEST)" (scheduled at 2026-05-17 14:11:31.627072+03:00)
2026-05-17 14:11:31,632 - horus.scheduling - INFO - [Scheduler] Intraday scan skipped: within 20 min of market close.
2026-05-17 14:11:31,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:12:01 EEST)" (scheduled at 2026-05-17 14:11:31.625095+03:00)
2026-05-17 14:11:31,631 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:16:31 EEST)" executed successfully
2026-05-17 14:11:31,634 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 14:21:31 EEST)" executed successfully
2026-05-17 14:11:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:12:01 EEST)" executed successfully
2026-05-17 14:11:31,690 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:16:31 EEST)" executed successfully
2026-05-17 14:12:01,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:12:31 EEST)" (scheduled at 2026-05-17 14:12:01.625095+03:00)
2026-05-17 14:12:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:12:31 EEST)" executed successfully
2026-05-17 14:12:31,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:13:01 EEST)" (scheduled at 2026-05-17 14:12:31.625095+03:00)
2026-05-17 14:12:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:13:01 EEST)" executed successfully
2026-05-17 14:13:01,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:13:31 EEST)" (scheduled at 2026-05-17 14:13:01.625095+03:00)
2026-05-17 14:13:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:13:31 EEST)" executed successfully
2026-05-17 14:13:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:14:01 EEST)" (scheduled at 2026-05-17 14:13:31.625095+03:00)
2026-05-17 14:13:31,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:14:01 EEST)" executed successfully
2026-05-17 14:14:01,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:14:31 EEST)" (scheduled at 2026-05-17 14:14:01.625095+03:00)
2026-05-17 14:14:01,648 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T14:13:47.389781). Version incremented to 24.
2026-05-17 14:14:01,654 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:14:31 EEST)" executed successfully
2026-05-17 14:14:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:15:01 EEST)" (scheduled at 2026-05-17 14:14:31.625095+03:00)
2026-05-17 14:14:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:15:01 EEST)" executed successfully
2026-05-17 14:15:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:15:31 EEST)" (scheduled at 2026-05-17 14:15:01.625095+03:00)
2026-05-17 14:15:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:15:31 EEST)" executed successfully
2026-05-17 14:15:31,637 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:16:01 EEST)" (scheduled at 2026-05-17 14:15:31.625095+03:00)
2026-05-17 14:15:31,653 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:16:01 EEST)" executed successfully
2026-05-17 14:16:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:16:31 EEST)" (scheduled at 2026-05-17 14:16:01.625095+03:00)
2026-05-17 14:16:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:16:31 EEST)" executed successfully
2026-05-17 14:16:31,631 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:21:31 EEST)" (scheduled at 2026-05-17 14:16:31.618104+03:00)
2026-05-17 14:16:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:21:31 EEST)" (scheduled at 2026-05-17 14:16:31.622651+03:00)
2026-05-17 14:16:31,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:17:01 EEST)" (scheduled at 2026-05-17 14:16:31.625095+03:00)
2026-05-17 14:16:31,634 - horus.scheduling - INFO - [Scheduler] Intraday scan skipped: within 20 min of market close.
2026-05-17 14:16:31,633 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:21:31 EEST)" executed successfully
2026-05-17 14:16:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:17:01 EEST)" executed successfully
2026-05-17 14:16:31,684 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:21:31 EEST)" executed successfully
2026-05-17 14:17:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:17:31 EEST)" (scheduled at 2026-05-17 14:17:01.625095+03:00)
2026-05-17 14:17:01,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:17:31 EEST)" executed successfully
2026-05-17 14:17:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:18:01 EEST)" (scheduled at 2026-05-17 14:17:31.625095+03:00)
2026-05-17 14:17:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:18:01 EEST)" executed successfully
2026-05-17 14:18:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:18:31 EEST)" (scheduled at 2026-05-17 14:18:01.625095+03:00)
2026-05-17 14:18:01,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:18:31 EEST)" executed successfully
2026-05-17 14:18:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:19:01 EEST)" (scheduled at 2026-05-17 14:18:31.625095+03:00)
2026-05-17 14:18:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:19:01 EEST)" executed successfully
2026-05-17 14:19:01,630 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:19:31 EEST)" (scheduled at 2026-05-17 14:19:01.625095+03:00)
2026-05-17 14:19:01,638 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T14:18:48.419438). Version incremented to 25.
2026-05-17 14:19:01,649 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:19:31 EEST)" executed successfully
2026-05-17 14:19:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:20:01 EEST)" (scheduled at 2026-05-17 14:19:31.625095+03:00)
2026-05-17 14:19:31,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:20:01 EEST)" executed successfully
2026-05-17 14:20:01,634 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:20:31 EEST)" (scheduled at 2026-05-17 14:20:01.625095+03:00)
2026-05-17 14:20:01,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:20:31 EEST)" executed successfully
2026-05-17 14:20:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:21:01 EEST)" (scheduled at 2026-05-17 14:20:31.625095+03:00)
2026-05-17 14:20:31,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:21:01 EEST)" executed successfully
2026-05-17 14:21:01,632 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:21:31 EEST)" (scheduled at 2026-05-17 14:21:01.625095+03:00)
2026-05-17 14:21:01,647 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:21:31 EEST)" executed successfully
INFO:     127.0.0.1:51349 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 14:21:31,633 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:26:31 EEST)" (scheduled at 2026-05-17 14:21:31.618104+03:00)
2026-05-17 14:21:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:26:31 EEST)" (scheduled at 2026-05-17 14:21:31.622651+03:00)
2026-05-17 14:21:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:22:01 EEST)" (scheduled at 2026-05-17 14:21:31.625095+03:00)
2026-05-17 14:21:31,636 - horus.scheduling - INFO - [Scheduler] Intraday scan skipped: within 20 min of market close.
2026-05-17 14:21:31,633 - apscheduler.executors.default - INFO - Running job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 14:31:31 EEST)" (scheduled at 2026-05-17 14:21:31.627072+03:00)
2026-05-17 14:21:31,634 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:26:31 EEST)" executed successfully
2026-05-17 14:21:31,640 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:22:01 EEST)" executed successfully
2026-05-17 14:21:31,643 - apscheduler.executors.default - INFO - Job "scheduled_failed_delivery_retry (trigger: interval[0:10:00], next run at: 2026-05-17 14:31:31 EEST)" executed successfully
2026-05-17 14:21:31,692 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:26:31 EEST)" executed successfully
2026-05-17 14:22:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:22:31 EEST)" (scheduled at 2026-05-17 14:22:01.625095+03:00)
2026-05-17 14:22:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:22:31 EEST)" executed successfully
2026-05-17 14:22:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:23:01 EEST)" (scheduled at 2026-05-17 14:22:31.625095+03:00)
2026-05-17 14:22:31,639 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:23:01 EEST)" executed successfully
2026-05-17 14:23:01,640 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:23:31 EEST)" (scheduled at 2026-05-17 14:23:01.625095+03:00)
2026-05-17 14:23:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:23:31 EEST)" executed successfully
2026-05-17 14:23:31,641 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:24:01 EEST)" (scheduled at 2026-05-17 14:23:31.625095+03:00)
2026-05-17 14:23:31,645 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:24:01 EEST)" executed successfully
2026-05-17 14:24:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:24:31 EEST)" (scheduled at 2026-05-17 14:24:01.625095+03:00)
2026-05-17 14:24:01,639 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T14:23:49.442983). Version incremented to 26.
2026-05-17 14:24:01,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:24:31 EEST)" executed successfully
2026-05-17 14:24:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:25:01 EEST)" (scheduled at 2026-05-17 14:24:31.625095+03:00)
2026-05-17 14:24:31,637 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:25:01 EEST)" executed successfully
2026-05-17 14:25:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:25:31 EEST)" (scheduled at 2026-05-17 14:25:01.625095+03:00)
2026-05-17 14:25:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:25:31 EEST)" executed successfully
2026-05-17 14:25:31,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:26:01 EEST)" (scheduled at 2026-05-17 14:25:31.625095+03:00)
2026-05-17 14:25:31,630 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:26:01 EEST)" executed successfully
2026-05-17 14:26:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:26:31 EEST)" (scheduled at 2026-05-17 14:26:01.625095+03:00)
2026-05-17 14:26:01,632 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:26:31 EEST)" executed successfully
2026-05-17 14:26:31,621 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:31:31 EEST)" (scheduled at 2026-05-17 14:26:31.618104+03:00)
2026-05-17 14:26:31,625 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:31:31 EEST)" executed successfully
2026-05-17 14:26:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:31:31 EEST)" (scheduled at 2026-05-17 14:26:31.622651+03:00)
2026-05-17 14:26:31,636 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:27:01 EEST)" (scheduled at 2026-05-17 14:26:31.625095+03:00)
2026-05-17 14:26:31,638 - horus.scheduling - INFO - [Scheduler] Intraday scan skipped: within 20 min of market close.
2026-05-17 14:26:31,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:27:01 EEST)" executed successfully
2026-05-17 14:26:31,694 - apscheduler.executors.default - INFO - Job "scheduled_intraday_scan (trigger: interval[0:05:00], next run at: 2026-05-17 14:31:31 EEST)" executed successfully
2026-05-17 14:27:01,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:27:31 EEST)" (scheduled at 2026-05-17 14:27:01.625095+03:00)
2026-05-17 14:27:01,641 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:27:31 EEST)" executed successfully
2026-05-17 14:27:31,638 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:28:01 EEST)" (scheduled at 2026-05-17 14:27:31.625095+03:00)
2026-05-17 14:27:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:28:01 EEST)" executed successfully
2026-05-17 14:28:01,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:28:31 EEST)" (scheduled at 2026-05-17 14:28:01.625095+03:00)
2026-05-17 14:28:01,643 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:28:31 EEST)" executed successfully
2026-05-17 14:28:31,635 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:29:01 EEST)" (scheduled at 2026-05-17 14:28:31.625095+03:00)
2026-05-17 14:28:31,642 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:29:01 EEST)" executed successfully
2026-05-17 14:29:01,626 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:29:31 EEST)" (scheduled at 2026-05-17 14:29:01.625095+03:00)
2026-05-17 14:29:01,628 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T14:28:50.403883). Version incremented to 27.
2026-05-17 14:29:01,631 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:29:31 EEST)" executed successfully
2026-05-17 14:29:31,628 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:30:01 EEST)" (scheduled at 2026-05-17 14:29:31.625095+03:00)
2026-05-17 14:29:31,636 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:30:01 EEST)" executed successfully
2026-05-17 14:30:00,012 - apscheduler.executors.default - INFO - Running job "scheduled_enter_analysis_mode (trigger: cron[hour='14', minute='30'], next run at: 2026-05-18 14:30:00 EEST)" (scheduled at 2026-05-17 14:30:00+03:00)
2026-05-17 14:30:00,014 - horus.session_mode - INFO - [SessionMode] Transitioning LIVE → ANALYSIS
2026-05-17 14:30:00,464 - LiveFeedManager - INFO - [LiveFeed] ZMQ listener terminated.
2026-05-17 14:30:00,465 - LiveFeedManager - INFO - [LiveFeed] ZMQ monitoring stopped
2026-05-17 14:30:00,467 - horus.session_mode - INFO - [SessionMode] LiveFeedManager stopped.
2026-05-17 14:30:00,468 - horus.session_mode - INFO - [SessionMode] Session mode transitioned from LIVE to ANALYSIS.
2026-05-17 14:30:00,470 - horus.session_mode - INFO - [SessionMode] scheduled_enter_analysis_mode result: {'status': 'transitioned', 'from': 'LIVE', 'to': 'ANALYSIS', 'message': 'Session mode transitioned from LIVE to ANALYSIS.'}
2026-05-17 14:30:00,472 - apscheduler.executors.default - INFO - Job "scheduled_enter_analysis_mode (trigger: cron[hour='14', minute='30'], next run at: 2026-05-18 14:30:00 EEST)" executed successfully
2026-05-17 14:30:01,631 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:30:31 EEST)" (scheduled at 2026-05-17 14:30:01.625095+03:00)
2026-05-17 14:30:01,638 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:30:31 EEST)" executed successfully
2026-05-17 14:30:17,812 - TelegramBot - WARNING - Telegram polling error (retry in 300s): HTTPSConnectionPool(host='api.telegram.org', port=443): Max retries exceeded with url: /bottoken/getUpdates?offset=1&timeout=30 (Caused by ConnectTimeoutError(<HTTPSConnection(host='api.telegram.org', port=443) at 0x1daf232dd10>, 'Connection to api.telegram.org timed out. (connect timeout=35)'))
2026-05-17 14:30:31,627 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:31:01 EEST)" (scheduled at 2026-05-17 14:30:31.625095+03:00)
2026-05-17 14:30:31,633 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:31:01 EEST)" executed successfully
2026-05-17 14:31:01,629 - apscheduler.executors.default - INFO - Running job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:31:31 EEST)" (scheduled at 2026-05-17 14:31:01.625095+03:00)
2026-05-17 14:31:01,631 - horus.scheduling - INFO - [Monitor] skipped: market is closed.
2026-05-17 14:31:01,677 - apscheduler.executors.default - INFO - Job "scheduled_trade_monitor (trigger: interval[0:00:30], next run at: 2026-05-17 14:31:31 EEST)" executed successfully
2026-05-17 14:31:31,621 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:36:31 EEST)" (scheduled at 2026-05-17 14:31:31.618104+03:00)
2026-05-17 14:31:31,625 - horus.api - INFO - [Watchdog] Market closed. Heavy background tasks paused.
2026-05-17 14:31:31,673 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:36:31 EEST)" executed successfully
2026-05-17 14:33:51,377 - horus.api - INFO - [SyncWorker] Closed session detected with complete history. Running one verification sync pass before idling.
--- Starting Data Lake Synchronization ---
{"ts":"2026-05-17T11:33:51+00:00","event":"pipeline.sync.start","realm":"EGX","intraday_provider":"CSV","intraday_provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"}},"history_provider":"CSV","history_provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"}},"ticks_provider":"MUBASHER_DB","ticks_provider_context":{"provider":"MUBASHER_DB","reason":"configured_ticks_provider","fallback_from":null,"evidence":{"configured_provider":"MUBASHER_DB"}}}
[LocalFeed] Provider policy intraday=CSV, history=CSV

[Parallel] Dispatching Intraday, History, and Ticks sync stages...

[1/3] Syncing Intraday (1min)...
[2/3] Syncing History (Daily)...
[3/3] Market is CLOSED. Skipping Tick Sync.


[Info] Found 273 intraday CSV files to ingest.[Info] Found 312 history CSV files to ingest.

[Success] Saved 2725 total rows for AALR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AALR.parquet
[Success] Saved 5230 total rows for ABUK to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ABUK.parquet
[Success] Saved 1906 total rows for ACAMD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACAMD.parquet
[Success] Saved 718 total rows for ACAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACAP.parquet
[Success] Saved 5453 total rows for ACGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACGC.parquet
[Success] Saved 4302 total rows for ACRO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACRO.parquet
[Success] Saved 437 total rows for ACTF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACTF.parquet
[Success] Saved 4497 total rows for ADCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADCI.parquet
[Success] Saved 5386 total rows for ADIB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADIB.parquet
[Success] Saved 2386 total rows for ADPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADPC.parquet
[Success] Saved 2555 total rows for ADRI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADRI.parquet
[Success] Saved 5393 total rows for AFDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AFDI.parquet
[Success] Saved 5158 total rows for AFMC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AFMC.parquet
[Success] Saved 188 total rows for AIDC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AIDC.parquet
[Success] Saved 3207 total rows for AIFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AIFI.parquet
[Success] Saved 1210 total rows for AIHC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AIHC.parquet
[Success] Saved 3691 total rows for AJWA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AJWA.parquet
[Success] Saved 4819 total rows for ALCN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ALCN.parquet
[Success] Saved 3353 total rows for ALEX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ALEX.parquet
[Success] Saved 4300 total rows for ALUM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ALUM.parquet
[Success] Saved 3710 total rows for AMER to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMER.parquet
[Success] Saved 2647 total rows for AMES to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMES.parquet
[Success] Saved 10 total rows for AMES_R2 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMES_R2.parquet
[Success] Saved 3909 total rows for AMIA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMIA.parquet
[Success] Saved 4986 total rows for AMOC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMOC.parquet
[Success] Saved 3089 total rows for AMPI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMPI.parquet
[Success] Saved 2106 total rows for ANFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ANFI.parquet
[Success] Saved 1258 total rows for APPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\APPC.parquet
[Success] Saved 2958 total rows for APSW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\APSW.parquet
[Success] Saved 2569 total rows for ARAB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARAB.parquet
[Success] Saved 5 total rows for ARAB_R2 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARAB_R2.parquet
[Success] Saved 2903 total rows for ARCC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARCC.parquet
[Success] Saved 4428 total rows for AREH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AREH.parquet
[Success] Saved 3783 total rows for ARVA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARVA.parquet
[Success] Saved 4642 total rows for ASCM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ASCM.parquet
[Success] Saved 4306 total rows for ASPI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ASPI.parquet
[Success] Saved 1944 total rows for ATLC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ATLC.parquet
[Success] Saved 2766 total rows for ATQA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ATQA.parquet
[Success] Saved 4566 total rows for AXPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AXPH.parquet
[Success] Saved 2219 total rows for BIDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BIDI.parquet
{"ts":"2026-05-17T11:34:06+00:00","event":"pipeline.stage.complete","stage":"intraday","provider":"CSV","provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":238,"status":"completed"}},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":238,"status":"completed"},"updated_symbols":238}
[Success] Saved 3549 total rows for BIGP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BIGP.parquet
[Success] Saved 1914 total rows for BINV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BINV.parquet
[Success] Saved 3834 total rows for BIOC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BIOC.parquet
[Success] Saved 201 total rows for BONY to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BONY.parquet
[Success] Saved 3334 total rows for BTFH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BTFH.parquet
[Success] Saved 2422 total rows for CAED to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CAED.parquet
[Success] Saved 5172 total rows for CANA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CANA.parquet
[Success] Saved 3067 total rows for CCAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CCAP.parquet
[Success] Saved 2980 total rows for CCRS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CCRS.parquet
[Success] Saved 5140 total rows for CEFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CEFM.parquet
[Success] Saved 4796 total rows for CERA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CERA.parquet
[Success] Saved 1068 total rows for CFGH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CFGH.parquet
[Success] Saved 1943 total rows for CICH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CICH.parquet
[Success] Saved 4827 total rows for CIEB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CIEB.parquet
[Success] Saved 3493 total rows for CIRA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CIRA.parquet
[Success] Saved 2402 total rows for CLHO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CLHO.parquet
[Success] Saved 1570 total rows for CNFN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CNFN.parquet
[Success] Saved 5453 total rows for COMI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\COMI.parquet
[Success] Saved 4211 total rows for COPR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\COPR.parquet
[Success] Saved 4499 total rows for COSG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\COSG.parquet
[Success] Saved 4560 total rows for CPCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CPCI.parquet
[Success] Saved 52 total rows for CPME to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CPME.parquet
[Success] Saved 1213 total rows for CRST to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CRST.parquet
[Success] Saved 3069 total rows for CSAG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CSAG.parquet
[Success] Saved 4870 total rows for DAPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DAPH.parquet
[Success] Saved 4304 total rows for DCRC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DCRC.parquet
[Success] Saved 3423 total rows for DEIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DEIN.parquet
[Success] Saved 622 total rows for DGTZ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DGTZ.parquet
[Success] Saved 774 total rows for DIFC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DIFC.parquet
[Success] Saved 2382 total rows for DOMT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DOMT.parquet
[Success] Saved 1999 total rows for DSCW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DSCW.parquet
[Success] Saved 3107 total rows for DTPP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DTPP.parquet
[Success] Saved 2398 total rows for EALR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EALR.parquet
[Success] Saved 3626 total rows for EASB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EASB.parquet
[Success] Saved 5046 total rows for EAST to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EAST.parquet
[Success] Saved 1493 total rows for EBSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EBSC.parquet
[Success] Saved 5431 total rows for ECAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ECAP.parquet
[Success] Saved 2650 total rows for EDFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EDFM.parquet
[Success] Saved 3255 total rows for EEII to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EEII.parquet
[Success] Saved 5424 total rows for EFIC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EFIC.parquet
[Success] Saved 2491 total rows for EFID to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EFID.parquet
[Success] Saved 1108 total rows for EFIH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EFIH.parquet
[Success] Saved 5026 total rows for EGAL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGAL.parquet
[Success] Saved 5026 total rows for EGAS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGAS.parquet
[Success] Saved 5153 total rows for EGBE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGBE.parquet
[Success] Saved 5055 total rows for EGCH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGCH.parquet
[Success] Saved 743 total rows for EGREF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGREF.parquet
[Success] Saved 4417 total rows for EGSA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGSA.parquet
[Success] Saved 3057 total rows for EGTS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGTS.parquet
[Success] Saved 4922 total rows for EGX100 EWI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX100 EWI.parquet
[Success] Saved 3250 total rows for EGX30 CAPPED to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30 CAPPED.parquet
[Success] Saved 4172 total rows for EGX30 TR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30 TR.parquet
[Success] Saved 3073 total rows for EGX30 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30.parquet
[Success] Saved 1789 total rows for EGX30ETF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30ETF.parquet
[Success] Saved 194 total rows for EGX35-LV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX35-LV.parquet
[Success] Saved 4434 total rows for EGX70 EWI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX70 EWI.parquet
[Success] Saved 4710 total rows for EHDR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EHDR.parquet
[Success] Saved 1272 total rows for EITP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EITP.parquet
[Success] Saved 5435 total rows for ELEC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELEC.parquet
[Success] Saved 5144 total rows for ELKA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELKA.parquet
[Success] Saved 2576 total rows for ELNA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELNA.parquet
[Success] Saved 5447 total rows for ELSH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELSH.parquet
[Success] Saved 3235 total rows for ELWA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELWA.parquet
[Success] Saved 2639 total rows for EMFD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EMFD.parquet
[Success] Saved 5116 total rows for ENGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ENGC.parquet
[Success] Saved 1569 total rows for EOSB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EOSB.parquet
[Success] Saved 5281 total rows for EPCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EPCO.parquet
[Success] Saved 2493 total rows for EPPK to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EPPK.parquet
[Success] Saved 1211 total rows for ESAC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ESAC.parquet
[Success] Saved 5277 total rows for ESRS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ESRS.parquet
[Success] Saved 3074 total rows for ETEL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ETEL.parquet
[Success] Saved 4663 total rows for ETRS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ETRS.parquet
[Success] Saved 5411 total rows for EXPA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EXPA.parquet
[Success] Saved 4829 total rows for FAIT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FAIT.parquet
[Success] Saved 5121 total rows for FAITA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FAITA.parquet
[Success] Saved 26 total rows for FCMD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FCMD.parquet
[Success] Saved 683 total rows for FERC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FERC.parquet
[Success] Saved 1638 total rows for FIRE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FIRE.parquet
[Success] Saved 2012 total rows for FNAR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FNAR.parquet
[Success] Saved 585 total rows for FTNS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FTNS.parquet
[Success] Saved 1643 total rows for FWRY to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FWRY.parquet
[Success] Saved 3011 total rows for GBCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GBCO.parquet
[Success] Saved 1115 total rows for GDWA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GDWA.parquet
[Success] Saved 5224 total rows for GGCC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GGCC.parquet
[Success] Saved 296 total rows for GGRN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GGRN.parquet
[Success] Saved 4426 total rows for GIHD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GIHD.parquet
[Success] Saved 2661 total rows for GMCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GMCI.parquet
[Success] Saved 62 total rows for GOUR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GOUR.parquet
[Success] Saved 1193 total rows for GPIM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GPIM.parquet
[Success] Saved 567 total rows for GPPL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GPPL.parquet
[Success] Saved 2116 total rows for GRCA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GRCA.parquet
[Success] Saved 5095 total rows for GSSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GSSC.parquet
[Success] Saved 461 total rows for GTEX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GTEX.parquet
[Success] Saved 1962 total rows for GTHE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GTHE.parquet
[Success] Saved 2323 total rows for GTWL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GTWL.parquet
[Success] Saved 333 total rows for HBCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HBCO.parquet
[Success] Saved 1106 total rows for HCFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HCFI.parquet
[Success] Saved 5297 total rows for HDBK to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HDBK.parquet
[Success] Saved 5238 total rows for HELI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HELI.parquet
[Success] Saved 5455 total rows for HRHO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HRHO.parquet
[Success] Saved 1419 total rows for IBCT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IBCT.parquet
[Success] Saved 2663 total rows for ICFC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ICFC.parquet
[Success] Saved 4077 total rows for ICID to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ICID.parquet
INFO:     127.0.0.1:52998 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
[Success] Saved 219 total rows for ICLE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ICLE.parquet
[Success] Saved 2930 total rows for IDRE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IDRE.parquet
[Success] Saved 1780 total rows for IEEC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IEEC.parquet
[Success] Saved 3119 total rows for IFAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IFAP.parquet
[Success] Saved 2214 total rows for INEG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\INEG.parquet
[Success] Saved 4412 total rows for INFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\INFI.parquet
[Success] Saved 4604 total rows for IRAX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IRAX.parquet
[Success] Saved 4958 total rows for IRON to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IRON.parquet
[Success] Saved 4326 total rows for ISMA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ISMA.parquet
[Success] Saved 1204 total rows for ISMQ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ISMQ.parquet
[Success] Saved 2044 total rows for ISPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ISPH.parquet
[Success] Saved 3777 total rows for JUFO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\JUFO.parquet
[Success] Saved 5371 total rows for KABO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KABO.parquet
[Success] Saved 230 total rows for KASABF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KASABF.parquet
[Success] Saved 1040 total rows for KRDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KRDI.parquet
[Success] Saved 10 total rows for KRDI_R1 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KRDI_R1.parquet
[Success] Saved 1860 total rows for KWIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KWIN.parquet
[Success] Saved 4559 total rows for KZPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KZPC.parquet
[Success] Saved 4233 total rows for LCSW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\LCSW.parquet
[Success] Saved 715 total rows for LUTS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\LUTS.parquet
[Success] Saved 2313 total rows for MAAL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MAAL.parquet
[Success] Saved 3098 total rows for MASR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MASR.parquet
[Success] Saved 1167 total rows for MBEG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MBEG.parquet
[Success] Saved 5042 total rows for MBSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MBSC.parquet
[Success] Saved 5215 total rows for MCQE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MCQE.parquet
[Success] Saved 1030 total rows for MCRO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MCRO.parquet
[Success] Saved 20 total rows for MEGM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MEGM.parquet
[Success] Saved 5358 total rows for MENA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MENA.parquet
[Success] Saved 3491 total rows for MEPA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MEPA.parquet
[Success] Saved 2343 total rows for MFPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MFPC.parquet
[Success] Saved 5014 total rows for MFSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MFSC.parquet
[Success] Saved 4237 total rows for MHOT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MHOT.parquet
[Success] Saved 5437 total rows for MICH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MICH.parquet
[Success] Saved 2945 total rows for MILS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MILS.parquet
[Success] Saved 2656 total rows for MIPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MIPH.parquet
[Success] Saved 342 total rows for MISR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MISR.parquet
[Success] Saved 1212 total rows for MKIT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MKIT.parquet
[Success] Saved 2407 total rows for MMAT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MMAT.parquet
[Success] Saved 3005 total rows for MOED to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOED.parquet
[Success] Saved 4356 total rows for MOIL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOIL.parquet
[Success] Saved 4000 total rows for MOIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOIN.parquet
[Success] Saved 1816 total rows for MOSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOSC.parquet
[Success] Saved 2633 total rows for MPCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MPCI.parquet
[Success] Saved 4654 total rows for MPCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MPCO.parquet
[Success] Saved 5442 total rows for MPRC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MPRC.parquet
[Success] Saved 2125 total rows for MTIE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MTIE.parquet
[Success] Saved 4597 total rows for NAHO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NAHO.parquet
[Success] Saved 192 total rows for NAPR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NAPR.parquet
[Success] Saved 1193 total rows for NARE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NARE.parquet
[Success] Saved 3560 total rows for NBKE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NBKE.parquet
[Success] Saved 4695 total rows for NCCW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NCCW.parquet
[Success] Saved 241 total rows for NCGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NCGC.parquet
[Success] Saved 107 total rows for NDRL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NDRL.parquet
[Success] Saved 4671 total rows for NEDA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NEDA.parquet
[Success] Saved 1773 total rows for NHPS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NHPS.parquet
[Success] Saved 3419 total rows for NINH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NINH.parquet
[Success] Saved 4009 total rows for NIPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NIPH.parquet
[Success] Saved 3131 total rows for OBRI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OBRI.parquet
[Success] Saved 5378 total rows for OCDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OCDI.parquet
[Success] Saved 1126 total rows for OCPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OCPH.parquet
[Success] Saved 4985 total rows for ODIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ODIN.parquet
[Success] Saved 1270 total rows for OFH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OFH.parquet
[Success] Saved 3474 total rows for OIH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OIH.parquet
[Success] Saved 2155 total rows for OLFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OLFI.parquet
[Success] Saved 2708 total rows for ORAS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ORAS.parquet
[Success] Saved 4185 total rows for ORHD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ORHD.parquet
[Success] Saved 5394 total rows for ORWE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ORWE.parquet
[Success] Saved 4597 total rows for PACH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PACH.parquet
[Success] Saved 4887 total rows for PHAR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHAR.parquet
[Success] Saved 4353 total rows for PHDC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHDC.parquet
[Success] Saved 502 total rows for PHGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHGC.parquet
[Success] Saved 3795 total rows for PHTV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHTV.parquet
[Success] Saved 5018 total rows for POUL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\POUL.parquet
[Success] Saved 4860 total rows for PRCL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PRCL.parquet
[Success] Saved 1115 total rows for PRDC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PRDC.parquet
[Success] Saved 3900 total rows for PRMH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PRMH.parquet
[Success] Saved 1200 total rows for QNBE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\QNBE.parquet
[Success] Saved 1938 total rows for RACC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RACC.parquet
[Success] Saved 3047 total rows for RAKT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RAKT.parquet
[Success] Saved 5018 total rows for RAYA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RAYA.parquet
[Success] Saved 1753 total rows for RKAZ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RKAZ.parquet
[Success] Saved 1558 total rows for RMDA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RMDA.parquet
[Success] Saved 1 total rows for RMTV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RMTV.parquet
[Success] Saved 4318 total rows for ROTO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ROTO.parquet
[Success] Saved 3074 total rows for RREI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RREI.parquet
[Success] Saved 4607 total rows for RTVC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RTVC.parquet
[Success] Saved 4204 total rows for RUBX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RUBX.parquet
[Success] Saved 501 total rows for SAIB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SAIB.parquet
[Success] Saved 5236 total rows for SAUD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SAUD.parquet
[Success] Saved 5107 total rows for SCEM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SCEM.parquet
[Success] Saved 4025 total rows for SCFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SCFM.parquet
[Success] Saved 1960 total rows for SCTS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SCTS.parquet
[Success] Saved 4733 total rows for SDTI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SDTI.parquet
[Success] Saved 3747 total rows for SEIG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SEIG.parquet
[Success] Saved 1058 total rows for SHARIAH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SHARIAH.parquet
[Success] Saved 2685 total rows for SIPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SIPC.parquet
[Success] Saved 5057 total rows for SKPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SKPC.parquet
[Success] Saved 5205 total rows for SMFR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SMFR.parquet
[Success] Saved 2683 total rows for SMPP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SMPP.parquet
[Success] Saved 4430 total rows for SNFC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SNFC.parquet
[Success] Saved 2101 total rows for SNFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SNFI.parquet
[Success] Saved 64 total rows for SPHT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SPHT.parquet
[Success] Saved 5047 total rows for SPIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SPIN.parquet
[Success] Saved 1713 total rows for SPMD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SPMD.parquet
[Success] Saved 2109 total rows for SUCE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SUCE.parquet
[Success] Saved 4933 total rows for SUGR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SUGR.parquet
[Success] Saved 3069 total rows for SVCE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SVCE.parquet
[Success] Saved 9 total rows for SVCE_R1 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SVCE_R1.parquet
[Success] Saved 4805 total rows for SWDY to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SWDY.parquet
[Success] Saved 1230 total rows for TALM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TALM.parquet
[Success] Saved 1788 total rows for TAMAYUZ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TAMAYUZ.parquet
[Success] Saved 1184 total rows for TANM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TANM.parquet
[Success] Saved 692 total rows for TAQA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TAQA.parquet
[Success] Saved 4459 total rows for TMGH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TMGH.parquet
[Success] Saved 2097 total rows for TORA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TORA.parquet
[Success] Saved 3764 total rows for TRTO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TRTO.parquet
[Success] Saved 122 total rows for TWSA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TWSA.parquet
[Success] Saved 9 total rows for TWSA_R1 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TWSA_R1.parquet
[Success] Saved 969 total rows for TYCN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TYCN.parquet
[Success] Saved 2848 total rows for UASG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UASG.parquet
[Success] Saved 345 total rows for UBEE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UBEE.parquet
[Success] Saved 2442 total rows for UEFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UEFM.parquet
[Success] Saved 5142 total rows for UEGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UEGC.parquet
[Success] Saved 4444 total rows for UNIP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UNIP.parquet
[Success] Saved 5434 total rows for UNIT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UNIT.parquet
[Success] Saved 1415 total rows for UPMS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UPMS.parquet
[Success] Saved 2238 total rows for UTOP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UTOP.parquet
[Success] Saved 219 total rows for VALU to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VALU.parquet
[Success] Saved 1313 total rows for VERT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VERT.parquet
[Success] Saved 1215 total rows for VLMR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VLMR.parquet
[Success] Saved 1130 total rows for VLMRA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VLMRA.parquet
[Success] Saved 1797 total rows for WATP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\WATP.parquet
[Success] Saved 2739 total rows for WCDF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\WCDF.parquet
[Success] Saved 2586 total rows for WKOL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\WKOL.parquet
[Success] Saved 5444 total rows for ZEOT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ZEOT.parquet
[Success] Saved 4109 total rows for ZMID to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ZMID.parquet
{"ts":"2026-05-17T11:34:41+00:00","event":"pipeline.stage.complete","stage":"history","provider":"CSV","provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":279,"status":"completed"}},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":279,"status":"completed"},"updated_symbols":279}
{"ts":"2026-05-17T11:34:41+00:00","event":"pipeline.compaction.complete","realm":"EGX","folder":"history","compacted":0,"scanned":0}
{"ts":"2026-05-17T11:34:41+00:00","event":"pipeline.compaction.complete","realm":"EGX","folder":"intraday","compacted":0,"scanned":0}
{"ts":"2026-05-17T11:34:41+00:00","event":"pipeline.sync.complete","realm":"EGX","duration_sec":50.46,"metrics":{"counters":{"dq.input_rows.total":1355206.0,"dq.input_rows.history":835966.0,"dq.valid_rows.total":1354579.0,"dq.valid_rows.history":835339.0,"dq.input_rows.intraday_store":519240.0,"dq.valid_rows.intraday_store":519240.0,"dq.rejected_rows.total":627.0,"dq.rejected_rows.history":627.0,"pipeline.stage.success.intraday":4.0},"gauges":{"pipeline.stage.updated_symbols.intraday":238.0,"pipeline.compaction.compacted.history":0.0,"pipeline.compaction.compacted.intraday":0.0,"pipeline.fresh_ratio.history":0.924,"pipeline.live_ratio.intraday":0.0076,"pipeline.sync.duration_sec":50.4589958190918}}}

[Done] Synchronization complete in 50.46 seconds.
2026-05-17 14:36:31,624 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:41:31 EEST)" (scheduled at 2026-05-17 14:36:31.618104+03:00)
2026-05-17 14:36:31,625 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:41:31 EEST)" executed successfully
2026-05-17 14:41:31,623 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:46:31 EEST)" (scheduled at 2026-05-17 14:41:31.618104+03:00)
2026-05-17 14:41:31,628 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:46:31 EEST)" executed successfully
INFO:     127.0.0.1:54686 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 14:44:09,229 - horus.pipeline - INFO - [Pipeline] Data change detected (2026-05-17T14:34:42.969836). Version incremented to 28.
INFO:     127.0.0.1:54686 - "HEAD /status HTTP/1.1" 200 OK
INFO:     127.0.0.1:53438 - "HEAD / HTTP/1.1" 200 OK
INFO:     127.0.0.1:54686 - "GET /status/__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:53438 - "GET /__next._tree.txt?_rsc=DQxjArDrgutTG17x HTTP/1.1" 200 OK
INFO:     127.0.0.1:54686 - "GET /status/__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53438 - "GET /status/__next._index.txt?_rsc=ERfXn7tGRj5EupPH HTTP/1.1" 200 OK
INFO:     127.0.0.1:54686 - "GET /status/__next.status.txt?_rsc=s0FEf9OOxbpuBOef HTTP/1.1" 200 OK
INFO:     127.0.0.1:53438 - "GET /status/__next.status.__PAGE__.txt?_rsc=ESW-ijXE9EWSHgP1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54686 - "GET /__next._head.txt?_rsc=aSNK_J6MSRxpxu_0 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54061 - "GET /__next.__PAGE__.txt?_rsc=cdk-OvPaaQdzy3F4 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53438 - "GET /api/v1/data/sync/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54686 - "GET /api/v1/data/runtime-universe HTTP/1.1" 200 OK
INFO:     127.0.0.1:54061 - "GET /api/v1/system/full-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54061 - "POST /api/v1/data/sync/start HTTP/1.1" 200 OK
--- Starting Data Lake Synchronization ---
{"ts":"2026-05-17T11:44:16+00:00","event":"pipeline.sync.start","realm":"EGX","intraday_provider":"CSV","intraday_provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"}},"history_provider":"CSV","history_provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"}},"ticks_provider":"MUBASHER_DB","ticks_provider_context":{"provider":"MUBASHER_DB","reason":"configured_ticks_provider","fallback_from":null,"evidence":{"configured_provider":"MUBASHER_DB"}}}
[LocalFeed] Provider policy intraday=CSV, history=CSV

[Parallel] Dispatching Intraday, History, and Ticks sync stages...

[1/3] Syncing Intraday (1min)...
[2/3] Syncing History (Daily)...
[3/3] Market is CLOSED. Skipping Tick Sync.


INFO:     127.0.0.1:54061 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:61870 - "HEAD /sectors HTTP/1.1" 200 OK
INFO:     127.0.0.1:54061 - "HEAD /seasonality HTTP/1.1" 200 OK
INFO:     127.0.0.1:65041 - "HEAD /live HTTP/1.1" 200 OK
[Info] Found 273 intraday CSV files to ingest.[Info] Found 312 history CSV files to ingest.INFO:     127.0.0.1:64748 - "HEAD /news HTTP/1.1" 200 OK


INFO:     127.0.0.1:54061 - "GET /seasonality/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:65041 - "GET /live/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
[Success] Saved 2726 total rows for AALR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AALR.parquetINFO:     127.0.0.1:61870 - "GET /sectors/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK

INFO:     127.0.0.1:64748 - "GET /news/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
[Success] Saved 5231 total rows for ABUK to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ABUK.parquetINFO:     127.0.0.1:59203 - "GET /api/v1/data/sync/status HTTP/1.1" 200 OK

[Success] Saved 1907 total rows for ACAMD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACAMD.parquet
[Success] Saved 719 total rows for ACAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACAP.parquet
[Success] Saved 5454 total rows for ACGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACGC.parquet
[Success] Saved 4302 total rows for ACRO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACRO.parquet
[Success] Saved 438 total rows for ACTF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ACTF.parquet
[Success] Saved 4498 total rows for ADCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADCI.parquet
[Success] Saved 5387 total rows for ADIB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADIB.parquet
[Success] Saved 2387 total rows for ADPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADPC.parquet
[Success] Saved 2556 total rows for ADRI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ADRI.parquet
[Success] Saved 5394 total rows for AFDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AFDI.parquet
[Success] Saved 5159 total rows for AFMC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AFMC.parquet
[Success] Saved 189 total rows for AIDC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AIDC.parquet
[Success] Saved 3208 total rows for AIFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AIFI.parquet
[Success] Saved 1211 total rows for AIHC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AIHC.parquet
{"ts":"2026-05-17T11:44:29+00:00","event":"pipeline.stage.complete","stage":"intraday","provider":"CSV","provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":2,"status":"completed"}},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":2,"status":"completed"},"updated_symbols":2}
[Success] Saved 3692 total rows for AJWA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AJWA.parquet
[Success] Saved 4820 total rows for ALCN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ALCN.parquet
[Success] Saved 3353 total rows for ALEX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ALEX.parquet
[Success] Saved 4301 total rows for ALUM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ALUM.parquet
[Success] Saved 3711 total rows for AMER to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMER.parquet
[Success] Saved 2648 total rows for AMES to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMES.parquet
[Success] Saved 11 total rows for AMES_R2 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMES_R2.parquet
[Success] Saved 3910 total rows for AMIA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMIA.parquet
[Success] Saved 4987 total rows for AMOC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMOC.parquet
[Success] Saved 3090 total rows for AMPI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AMPI.parquet
[Success] Saved 2106 total rows for ANFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ANFI.parquet
[Success] Saved 1258 total rows for APPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\APPC.parquet
[Success] Saved 2959 total rows for APSW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\APSW.parquet
[Success] Saved 2570 total rows for ARAB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARAB.parquet
[Success] Saved 5 total rows for ARAB_R2 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARAB_R2.parquet
[Success] Saved 2904 total rows for ARCC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARCC.parquet
[Success] Saved 4429 total rows for AREH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AREH.parquet
[Success] Saved 3784 total rows for ARVA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ARVA.parquet
[Success] Saved 4643 total rows for ASCM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ASCM.parquet
[Success] Saved 4307 total rows for ASPI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ASPI.parquet
[Success] Saved 1945 total rows for ATLC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ATLC.parquet
[Success] Saved 2767 total rows for ATQA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ATQA.parquet
[Success] Saved 4567 total rows for AXPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\AXPH.parquet
[Success] Saved 2220 total rows for BIDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BIDI.parquet
[Success] Saved 3550 total rows for BIGP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BIGP.parquet
[Success] Saved 1915 total rows for BINV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BINV.parquet
[Success] Saved 3835 total rows for BIOC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BIOC.parquet
[Success] Saved 202 total rows for BONY to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BONY.parquet
[Success] Saved 3335 total rows for BTFH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\BTFH.parquet
[Success] Saved 2423 total rows for CAED to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CAED.parquet
[Success] Saved 5173 total rows for CANA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CANA.parquet
[Success] Saved 3068 total rows for CCAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CCAP.parquet
[Success] Saved 2981 total rows for CCRS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CCRS.parquet
[Success] Saved 5141 total rows for CEFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CEFM.parquet
[Success] Saved 4797 total rows for CERA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CERA.parquet
[Success] Saved 1069 total rows for CFGH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CFGH.parquet
[Success] Saved 1944 total rows for CICH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CICH.parquet
[Success] Saved 4828 total rows for CIEB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CIEB.parquet
[Success] Saved 3494 total rows for CIRA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CIRA.parquet
[Success] Saved 2403 total rows for CLHO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CLHO.parquet
[Success] Saved 1571 total rows for CNFN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CNFN.parquet
[Success] Saved 5454 total rows for COMI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\COMI.parquet
[Success] Saved 4212 total rows for COPR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\COPR.parquet
[Success] Saved 4500 total rows for COSG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\COSG.parquet
[Success] Saved 4561 total rows for CPCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CPCI.parquet
[Success] Saved 53 total rows for CPME to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CPME.parquet
[Success] Saved 1214 total rows for CRST to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CRST.parquet
[Success] Saved 3070 total rows for CSAG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\CSAG.parquet
[Success] Saved 4871 total rows for DAPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DAPH.parquet
[Success] Saved 4304 total rows for DCRC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DCRC.parquet
[Success] Saved 3423 total rows for DEIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DEIN.parquet
[Success] Saved 623 total rows for DGTZ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DGTZ.parquet
[Success] Saved 774 total rows for DIFC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DIFC.parquet
[Success] Saved 2383 total rows for DOMT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DOMT.parquet
[Success] Saved 2000 total rows for DSCW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DSCW.parquet
[Success] Saved 3108 total rows for DTPP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\DTPP.parquet
[Success] Saved 2399 total rows for EALR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EALR.parquet
[Success] Saved 3627 total rows for EASB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EASB.parquet
[Success] Saved 5047 total rows for EAST to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EAST.parquet
[Success] Saved 1494 total rows for EBSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EBSC.parquet
[Success] Saved 5432 total rows for ECAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ECAP.parquet
[Success] Saved 2651 total rows for EDFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EDFM.parquet
[Success] Saved 3256 total rows for EEII to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EEII.parquet
[Success] Saved 5425 total rows for EFIC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EFIC.parquet
[Success] Saved 2492 total rows for EFID to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EFID.parquet
[Success] Saved 1109 total rows for EFIH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EFIH.parquet
[Success] Saved 5027 total rows for EGAL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGAL.parquet
[Success] Saved 5027 total rows for EGAS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGAS.parquet
[Success] Saved 5154 total rows for EGBE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGBE.parquet
[Success] Saved 5056 total rows for EGCH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGCH.parquet
[Success] Saved 744 total rows for EGREF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGREF.parquet
[Success] Saved 4418 total rows for EGSA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGSA.parquet
[Success] Saved 3058 total rows for EGTS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGTS.parquet
[Success] Saved 4923 total rows for EGX100 EWI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX100 EWI.parquet
[Success] Saved 3251 total rows for EGX30 CAPPED to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30 CAPPED.parquet
[Success] Saved 4173 total rows for EGX30 TR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30 TR.parquet
[Success] Saved 3074 total rows for EGX30 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30.parquet
[Success] Saved 1790 total rows for EGX30ETF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX30ETF.parquet
[Success] Saved 195 total rows for EGX35-LV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX35-LV.parquet
[Success] Saved 4435 total rows for EGX70 EWI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EGX70 EWI.parquet
[Success] Saved 4711 total rows for EHDR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EHDR.parquet
[Success] Saved 1272 total rows for EITP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EITP.parquet
[Success] Saved 5436 total rows for ELEC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELEC.parquet
[Success] Saved 5145 total rows for ELKA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELKA.parquet
[Success] Saved 2577 total rows for ELNA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELNA.parquet
[Success] Saved 5448 total rows for ELSH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELSH.parquet
[Success] Saved 3236 total rows for ELWA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ELWA.parquet
[Success] Saved 2640 total rows for EMFD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EMFD.parquet
[Success] Saved 5117 total rows for ENGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ENGC.parquet
[Success] Saved 1570 total rows for EOSB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EOSB.parquet
[Success] Saved 5282 total rows for EPCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EPCO.parquet
[Success] Saved 2494 total rows for EPPK to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EPPK.parquet
[Success] Saved 1211 total rows for ESAC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ESAC.parquet
[Success] Saved 5277 total rows for ESRS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ESRS.parquet
[Success] Saved 3075 total rows for ETEL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ETEL.parquet
[Success] Saved 4664 total rows for ETRS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ETRS.parquet
[Success] Saved 5412 total rows for EXPA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\EXPA.parquet
[Success] Saved 4830 total rows for FAIT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FAIT.parquet
[Success] Saved 5122 total rows for FAITA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FAITA.parquet
[Success] Saved 26 total rows for FCMD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FCMD.parquet
[Success] Saved 684 total rows for FERC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FERC.parquet
[Success] Saved 1639 total rows for FIRE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FIRE.parquet
[Success] Saved 2013 total rows for FNAR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FNAR.parquet
[Success] Saved 586 total rows for FTNS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FTNS.parquet
[Success] Saved 1644 total rows for FWRY to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\FWRY.parquet
[Success] Saved 3012 total rows for GBCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GBCO.parquet
[Success] Saved 1116 total rows for GDWA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GDWA.parquet
[Success] Saved 5225 total rows for GGCC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GGCC.parquet
[Success] Saved 297 total rows for GGRN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GGRN.parquet
[Success] Saved 4427 total rows for GIHD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GIHD.parquet
[Success] Saved 2662 total rows for GMCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GMCI.parquet
[Success] Saved 63 total rows for GOUR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GOUR.parquet
[Success] Saved 1194 total rows for GPIM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GPIM.parquet
[Success] Saved 567 total rows for GPPL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GPPL.parquet
[Success] Saved 2117 total rows for GRCA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GRCA.parquet
[Success] Saved 5096 total rows for GSSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GSSC.parquet
[Success] Saved 462 total rows for GTEX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GTEX.parquet
[Success] Saved 1962 total rows for GTHE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GTHE.parquet
[Success] Saved 2324 total rows for GTWL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\GTWL.parquet
[Success] Saved 334 total rows for HBCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HBCO.parquet
[Success] Saved 1106 total rows for HCFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HCFI.parquet
[Success] Saved 5298 total rows for HDBK to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HDBK.parquet
[Success] Saved 5239 total rows for HELI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HELI.parquet
[Success] Saved 5456 total rows for HRHO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\HRHO.parquet
[Success] Saved 1420 total rows for IBCT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IBCT.parquet
[Success] Saved 2664 total rows for ICFC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ICFC.parquet
[Success] Saved 4078 total rows for ICID to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ICID.parquet
[Success] Saved 219 total rows for ICLE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ICLE.parquet
[Success] Saved 2931 total rows for IDRE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IDRE.parquet
[Success] Saved 1781 total rows for IEEC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IEEC.parquet
[Success] Saved 3120 total rows for IFAP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IFAP.parquet
[Success] Saved 2215 total rows for INEG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\INEG.parquet
[Success] Saved 4413 total rows for INFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\INFI.parquet
[Success] Saved 4604 total rows for IRAX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IRAX.parquet
[Success] Saved 4959 total rows for IRON to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\IRON.parquet
[Success] Saved 4327 total rows for ISMA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ISMA.parquet
[Success] Saved 1205 total rows for ISMQ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ISMQ.parquet
[Success] Saved 2045 total rows for ISPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ISPH.parquet
[Success] Saved 3778 total rows for JUFO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\JUFO.parquet
[Success] Saved 5372 total rows for KABO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KABO.parquet
[Success] Saved 231 total rows for KASABF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KASABF.parquet
[Success] Saved 1041 total rows for KRDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KRDI.parquet
[Success] Saved 10 total rows for KRDI_R1 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KRDI_R1.parquet
[Success] Saved 1861 total rows for KWIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KWIN.parquet
[Success] Saved 4560 total rows for KZPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\KZPC.parquet
[Success] Saved 4234 total rows for LCSW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\LCSW.parquet
[Success] Saved 716 total rows for LUTS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\LUTS.parquet
[Success] Saved 2314 total rows for MAAL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MAAL.parquet
[Success] Saved 3099 total rows for MASR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MASR.parquet
[Success] Saved 1168 total rows for MBEG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MBEG.parquet
[Success] Saved 5043 total rows for MBSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MBSC.parquet
[Success] Saved 5216 total rows for MCQE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MCQE.parquet
[Success] Saved 1031 total rows for MCRO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MCRO.parquet
[Success] Saved 20 total rows for MEGM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MEGM.parquet
[Success] Saved 5359 total rows for MENA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MENA.parquet
[Success] Saved 3492 total rows for MEPA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MEPA.parquet
[Success] Saved 2344 total rows for MFPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MFPC.parquet
[Success] Saved 5015 total rows for MFSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MFSC.parquet
[Success] Saved 4238 total rows for MHOT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MHOT.parquet
[Success] Saved 5438 total rows for MICH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MICH.parquet
[Success] Saved 2946 total rows for MILS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MILS.parquet
[Success] Saved 2657 total rows for MIPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MIPH.parquet
[Success] Saved 342 total rows for MISR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MISR.parquet
[Success] Saved 1213 total rows for MKIT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MKIT.parquet
[Success] Saved 2407 total rows for MMAT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MMAT.parquet
[Success] Saved 3006 total rows for MOED to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOED.parquet
[Success] Saved 4357 total rows for MOIL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOIL.parquet
[Success] Saved 4001 total rows for MOIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOIN.parquet
[Success] Saved 1817 total rows for MOSC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MOSC.parquet
[Success] Saved 2634 total rows for MPCI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MPCI.parquet
[Success] Saved 4655 total rows for MPCO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MPCO.parquet
[Success] Saved 5443 total rows for MPRC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MPRC.parquet
[Success] Saved 2126 total rows for MTIE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\MTIE.parquet
[Success] Saved 4598 total rows for NAHO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NAHO.parquet
[Success] Saved 193 total rows for NAPR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NAPR.parquet
[Success] Saved 1194 total rows for NARE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NARE.parquet
[Success] Saved 3560 total rows for NBKE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NBKE.parquet
[Success] Saved 4696 total rows for NCCW to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NCCW.parquet
[Success] Saved 241 total rows for NCGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NCGC.parquet
[Success] Saved 107 total rows for NDRL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NDRL.parquet
[Success] Saved 4672 total rows for NEDA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NEDA.parquet
[Success] Saved 1774 total rows for NHPS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NHPS.parquet
[Success] Saved 3420 total rows for NINH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NINH.parquet
[Success] Saved 4010 total rows for NIPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\NIPH.parquet
[Success] Saved 3132 total rows for OBRI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OBRI.parquet
[Success] Saved 5379 total rows for OCDI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OCDI.parquet
[Success] Saved 1127 total rows for OCPH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OCPH.parquet
[Success] Saved 4986 total rows for ODIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ODIN.parquet
[Success] Saved 1271 total rows for OFH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OFH.parquet
[Success] Saved 3475 total rows for OIH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OIH.parquet
[Success] Saved 2156 total rows for OLFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\OLFI.parquet
[Success] Saved 2709 total rows for ORAS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ORAS.parquet
[Success] Saved 4186 total rows for ORHD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ORHD.parquet
[Success] Saved 5395 total rows for ORWE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ORWE.parquet
[Success] Saved 4597 total rows for PACH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PACH.parquet
[Success] Saved 4888 total rows for PHAR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHAR.parquet
[Success] Saved 4354 total rows for PHDC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHDC.parquet
[Success] Saved 503 total rows for PHGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHGC.parquet
[Success] Saved 3796 total rows for PHTV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PHTV.parquet
[Success] Saved 5019 total rows for POUL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\POUL.parquet
[Success] Saved 4861 total rows for PRCL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PRCL.parquet
[Success] Saved 1116 total rows for PRDC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PRDC.parquet
[Success] Saved 3901 total rows for PRMH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\PRMH.parquet
[Success] Saved 1201 total rows for QNBE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\QNBE.parquet
2026-05-17 14:45:00,016 - apscheduler.executors.default - INFO - Running job "scheduled_daily_signal_pipeline (trigger: cron[hour='14', minute='45'], next run at: 2026-05-18 14:45:00 EEST)" (scheduled at 2026-05-17 14:45:00+03:00)
[Success] Saved 1939 total rows for RACC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RACC.parquet
[Success] Saved 3048 total rows for RAKT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RAKT.parquet
[Success] Saved 5019 total rows for RAYA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RAYA.parquet
[Success] Saved 1754 total rows for RKAZ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RKAZ.parquet
[Success] Saved 1559 total rows for RMDA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RMDA.parquet
[Success] Saved 1 total rows for RMTV to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RMTV.parquet
[Success] Saved 4319 total rows for ROTO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ROTO.parquet
[Success] Saved 3075 total rows for RREI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RREI.parquet2026-05-17 14:45:03,589 - DailyScanner - INFO - Scanning 272 tickers. Intraday=False PreClose=False

[Success] Saved 4608 total rows for RTVC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RTVC.parquet
[Success] Saved 4205 total rows for RUBX to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\RUBX.parquet
[Success] Saved 501 total rows for SAIB to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SAIB.parquet
[Success] Saved 5237 total rows for SAUD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SAUD.parquet2026-05-17 14:45:05,455 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 14:45:05,466 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 7 signals across 272 tickers.
2026-05-17 14:45:05,469 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 7 signals. Regime: BULLISH (57.0%)
2026-05-17 14:45:05,495 - horus.scheduling - INFO - [Signals] Daily run status=completed run_id=53 date=2026-05-17

2026-05-17 14:45:05,632 - horus.scheduling - INFO - [Signals] Desk autopilot status=blocked run_id=53
[Success] Saved 5108 total rows for SCEM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SCEM.parquet2026-05-17 14:45:05,755 - apscheduler.executors.default - INFO - Job "scheduled_daily_signal_pipeline (trigger: cron[hour='14', minute='45'], next run at: 2026-05-18 14:45:00 EEST)" executed successfully

[Success] Saved 4026 total rows for SCFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SCFM.parquet
[Success] Saved 1961 total rows for SCTS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SCTS.parquet
[Success] Saved 4734 total rows for SDTI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SDTI.parquet
[Success] Saved 3748 total rows for SEIG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SEIG.parquet
[Success] Saved 1059 total rows for SHARIAH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SHARIAH.parquet
[Success] Saved 2686 total rows for SIPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SIPC.parquet
[Success] Saved 5058 total rows for SKPC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SKPC.parquet
[Success] Saved 5206 total rows for SMFR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SMFR.parquet
[Success] Saved 2683 total rows for SMPP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SMPP.parquet
[Success] Saved 4431 total rows for SNFC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SNFC.parquet
[Success] Saved 2101 total rows for SNFI to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SNFI.parquet
[Success] Saved 64 total rows for SPHT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SPHT.parquet
[Success] Saved 5048 total rows for SPIN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SPIN.parquet
[Success] Saved 1714 total rows for SPMD to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SPMD.parquet
[Success] Saved 2109 total rows for SUCE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SUCE.parquet
[Success] Saved 4934 total rows for SUGR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SUGR.parquet
[Success] Saved 3070 total rows for SVCE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SVCE.parquet
[Success] Saved 9 total rows for SVCE_R1 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SVCE_R1.parquet
[Success] Saved 4806 total rows for SWDY to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\SWDY.parquet
[Success] Saved 1231 total rows for TALM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TALM.parquet
[Success] Saved 1789 total rows for TAMAYUZ to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TAMAYUZ.parquet
[Success] Saved 1185 total rows for TANM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TANM.parquet
[Success] Saved 693 total rows for TAQA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TAQA.parquet
[Success] Saved 4460 total rows for TMGH to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TMGH.parquet
[Success] Saved 2097 total rows for TORA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TORA.parquet
[Success] Saved 3765 total rows for TRTO to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TRTO.parquet
[Success] Saved 123 total rows for TWSA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TWSA.parquet
[Success] Saved 9 total rows for TWSA_R1 to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TWSA_R1.parquet
[Success] Saved 970 total rows for TYCN to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\TYCN.parquet
[Success] Saved 2848 total rows for UASG to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UASG.parquet
[Success] Saved 346 total rows for UBEE to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UBEE.parquet
[Success] Saved 2443 total rows for UEFM to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UEFM.parquet
[Success] Saved 5143 total rows for UEGC to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UEGC.parquet
[Success] Saved 4445 total rows for UNIP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UNIP.parquet
[Success] Saved 5435 total rows for UNIT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UNIT.parquet
[Success] Saved 1416 total rows for UPMS to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UPMS.parquet
[Success] Saved 2239 total rows for UTOP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\UTOP.parquet
[Success] Saved 220 total rows for VALU to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VALU.parquet
[Success] Saved 1314 total rows for VERT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VERT.parquet
[Success] Saved 1216 total rows for VLMR to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VLMR.parquet
[Success] Saved 1131 total rows for VLMRA to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\VLMRA.parquet
[Success] Saved 1797 total rows for WATP to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\WATP.parquet
[Success] Saved 2740 total rows for WCDF to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\WCDF.parquet
[Success] Saved 2587 total rows for WKOL to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\WKOL.parquet
[Success] Saved 5445 total rows for ZEOT to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ZEOT.parquet
[Success] Saved 4110 total rows for ZMID to C:\Users\TSabr\Horus\Horus-Analytics-II\dist\HorusApp\data\EGX\history\ZMID.parquet
{"ts":"2026-05-17T11:45:13+00:00","event":"pipeline.stage.complete","stage":"history","provider":"CSV","provider_context":{"provider":"CSV","reason":"explicit_timeframe_policy","fallback_from":null,"evidence":{"configured_provider":"CSV"},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":279,"status":"completed"}},"ingest_summary":{"requested_provider":"CSV","used_provider":"CSV","fallback_from":null,"failure_mode":null,"updated":279,"status":"completed"},"updated_symbols":279}
{"ts":"2026-05-17T11:45:13+00:00","event":"pipeline.compaction.complete","realm":"EGX","folder":"history","compacted":0,"scanned":0}
{"ts":"2026-05-17T11:45:13+00:00","event":"pipeline.compaction.complete","realm":"EGX","folder":"intraday","compacted":0,"scanned":0}
{"ts":"2026-05-17T11:45:14+00:00","event":"pipeline.sync.complete","realm":"EGX","duration_sec":58.23,"metrics":{"counters":{"dq.input_rows.total":1355977.0,"dq.input_rows.history":836735.0,"dq.valid_rows.total":1355350.0,"dq.valid_rows.history":836108.0,"dq.input_rows.intraday_store":519242.0,"dq.valid_rows.intraday_store":519242.0,"dq.rejected_rows.total":627.0,"dq.rejected_rows.history":627.0,"pipeline.stage.success.intraday":5.0},"gauges":{"pipeline.stage.updated_symbols.intraday":2.0,"pipeline.compaction.compacted.history":0.0,"pipeline.compaction.compacted.intraday":0.0,"pipeline.fresh_ratio.history":0.9202,"pipeline.live_ratio.intraday":0.9202,"pipeline.sync.duration_sec":58.227845430374146}}}

[Done] Synchronization complete in 58.23 seconds.
2026-05-17 14:46:31,631 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:51:31 EEST)" (scheduled at 2026-05-17 14:46:31.618104+03:00)
2026-05-17 14:46:31,636 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:51:31 EEST)" executed successfully
2026-05-17 14:51:31,624 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:56:31 EEST)" (scheduled at 2026-05-17 14:51:31.618104+03:00)
2026-05-17 14:51:31,629 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 14:56:31 EEST)" executed successfully
INFO:     127.0.0.1:51580 - "GET /api/v1/data/sync/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58979 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51143 - "HEAD /settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:51580 - "HEAD /portfolio HTTP/1.1" 200 OK
INFO:     127.0.0.1:51580 - "GET /settings/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:51580 - "GET /portfolio/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:62688 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:58979 - "GET /api/v1/system/full-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51143 - "GET /api/v1/data/runtime-universe HTTP/1.1" 200 OK
INFO:     127.0.0.1:51143 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:51143 - "GET /settings/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:62688 - "GET /settings/__next.settings.txt?_rsc=bypY-lgJtWE1htkG HTTP/1.1" 200 OK
INFO:     127.0.0.1:58979 - "GET /settings/__next._index.txt?_rsc=4MEx1ygTCVrtW97z HTTP/1.1" 200 OK
INFO:     127.0.0.1:51143 - "GET /settings/__next.settings.__PAGE__.txt?_rsc=Dy7bFjl2J4dryOJp HTTP/1.1" 200 OK
INFO:     127.0.0.1:58558 - "HEAD /arbitrage HTTP/1.1" 200 OK
INFO:     127.0.0.1:58558 - "HEAD /simulation HTTP/1.1" 200 OK
INFO:     127.0.0.1:58558 - "HEAD /optimization HTTP/1.1" 200 OK
INFO:     127.0.0.1:58558 - "HEAD /strategy HTTP/1.1" 200 OK
INFO:     127.0.0.1:56419 - "GET /optimization/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:55851 - "GET /simulation/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:58558 - "GET /strategy/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:57649 - "GET /arbitrage/__next._tree.txt?_rsc=aPBTvDumw6yNXDVK HTTP/1.1" 200 OK
INFO:     127.0.0.1:55851 - "GET /portfolio/__next._head.txt?_rsc=86wmhON3lfYeFbzN HTTP/1.1" 200 OK
INFO:     127.0.0.1:56419 - "GET /portfolio/__next.portfolio.txt?_rsc=jMDDsYmCMTF2sLQP HTTP/1.1" 200 OK
INFO:     127.0.0.1:57649 - "GET /portfolio/__next.portfolio.__PAGE__.txt?_rsc=d_Fwz1zmRCOVzyzG HTTP/1.1" 200 OK
INFO:     127.0.0.1:57649 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:55195 - "GET /api/v1/data/runtime-universe HTTP/1.1" 200 OK
INFO:     127.0.0.1:52224 - "GET /api/v1/system/full-status HTTP/1.1" 200 OK
INFO:     127.0.0.1:63954 - "GET /api/v1/data/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:54121 - "GET /api/v1/simulate/status HTTP/1.1" 200 OK
2026-05-17 14:56:31,619 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 15:01:31 EEST)" (scheduled at 2026-05-17 14:56:31.618104+03:00)
2026-05-17 14:56:31,621 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 15:01:31 EEST)" executed successfully
2026-05-17 15:00:00,009 - apscheduler.executors.default - INFO - Running job "scheduled_daily_ai_report_dispatch (trigger: cron[hour='15', minute='0'], next run at: 2026-05-18 15:00:00 EEST)" (scheduled at 2026-05-17 15:00:00+03:00)
2026-05-17 15:00:00,009 - apscheduler.executors.default - INFO - Running job "scheduled_daily_signal_scan (trigger: cron[hour='15', minute='0'], next run at: 2026-05-18 15:00:00 EEST)" (scheduled at 2026-05-17 15:00:00+03:00)
2026-05-17 15:00:01,600 - DailyScanner - INFO - Scanning 272 tickers. Intraday=False PreClose=True
2026-05-17 15:00:02,426 - httpx - INFO - HTTP Request: GET https://english.mubasher.info/markets/EGX "HTTP/1.1 200 OK"
2026-05-17 15:00:02,670 - httpx - INFO - HTTP Request: GET https://enterpriseam.com/egypt/ "HTTP/1.1 200 OK"
2026-05-17 15:00:03,068 - httpx - INFO - HTTP Request: GET https://www.argaam.com/en "HTTP/1.1 200 OK"
2026-05-17 15:00:03,617 - httpx - INFO - HTTP Request: GET https://www.mubasher.info/news/eg/now/latest "HTTP/1.1 200 OK"
2026-05-17 15:00:05,388 - DailyScanner - INFO - Parallel scoring 9 candidates...
2026-05-17 15:00:05,396 - DailyScanner - INFO - [DailyScanner] Scan complete. Found 5 signals across 272 tickers.
2026-05-17 15:00:05,398 - horus.audit - INFO - Audit [SIGNAL] SCAN_COMPLETE: Found 5 signals. Regime: BULLISH (55.5%)
2026-05-17 15:00:05,400 - horus.scheduling - INFO - [Scheduler] Pre-Close/Daily: scanner returned 5 signals (regime=BULLISH).
2026-05-17 15:00:05,453 - horus.scheduling - INFO - [Scheduler] Pre-Close/Daily: stale filter dropped 0 signals; remaining=5.
2026-05-17 15:00:05,524 - horus.scheduling - INFO - [Scheduler] Pre-Close/Daily: persisted signal run status=existing scan_type=DAILY run_id=53
2026-05-17 15:00:05,585 - horus.alerts - INFO - [Deduplicator] label=DAILY_CONFIRMED kept=1 dropped=4 counts_by_reason={'repeat_cooldown': 4} dropped_tickers=['BONY', 'FAIT', 'COPR', 'SUGR']
2026-05-17 15:00:05,587 - horus.scheduling - INFO - [Scheduler] Pre-Close/Daily: dedup dropped 4/5 signals.
2026-05-17 15:00:05,653 - horus.scheduling - INFO - [Scheduler] Pre-Close/Daily: broadcasting 1 signals after dedup.
2026-05-17 15:00:08,726 - horus.scheduling - INFO - [Scheduler] Pre-Close/Daily: broadcast completed (cards=1, summary_signals=1).
2026-05-17 15:00:08,790 - apscheduler.executors.default - INFO - Job "scheduled_daily_signal_scan (trigger: cron[hour='15', minute='0'], next run at: 2026-05-18 15:00:00 EEST)" executed successfully
2026-05-17 15:00:12,732 - httpx - INFO - HTTP Request: GET https://www.mubasher.info/news/eg/pulse/stocks "HTTP/1.1 200 OK"
[Info] Found 273 intraday CSV files to ingest.
[Jotunheim] Scoring 101 tickers for liquidity (EGX100 default universe)...
  ... processed 50/101 ...
  ... processed 100/101 ...
[THE CANARY] Calculating Market Breadth...

[MACRO PREDICTION] (EGX30):
Correlation (Price vs Internal Strength): 0.96
[THE COIL] Hunting for explosive moves...
2026-05-17 15:00:51,033 - horus.confluence - INFO - Confluence: Analyzing Sovereign Hedge signals...
2026-05-17 15:01:31,629 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 15:06:31 EEST)" (scheduled at 2026-05-17 15:01:31.618104+03:00)
2026-05-17 15:01:31,630 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 15:06:31 EEST)" executed successfully
2026-05-17 15:01:33,188 - horus.scheduling - INFO - [Scheduler] AI daily report dispatched to Telegram.
2026-05-17 15:01:33,238 - apscheduler.executors.default - INFO - Job "scheduled_daily_ai_report_dispatch (trigger: cron[hour='15', minute='0'], next run at: 2026-05-18 15:00:00 EEST)" executed successfully
2026-05-17 15:06:31,625 - apscheduler.executors.default - INFO - Running job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 15:11:31 EEST)" (scheduled at 2026-05-17 15:06:31.618104+03:00)
2026-05-17 15:06:31,626 - apscheduler.executors.default - INFO - Job "lifespan.<locals>.background_startup.<locals>.scheduled_market_watchdog (trigger: interval[0:05:00], next run at: 2026-05-17 15:11:31 EEST)" executed successfully
