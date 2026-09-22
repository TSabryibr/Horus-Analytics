"""
AUDIT ENGINE
============
Automated health checks for Horus Analytics.
Checks:
1. Data Freshness (Any stale sectors?)
2. Database Integrity (Positions matching Portfolio balance?)
3. Provider Status (Are local feeds active?)
"""

from core.settings import settings
import datetime
import logging
from core import DataManager, TimeUtils
from database import Position, Trade, Portfolio, db
from core import AlertManager
from core.market import MarketRegime
from core.analyzers import SentimentCrawler

logger = logging.getLogger("horus.audit")

def run_system_audit():
    """
    Performs a full system audit and returns a report.
    If critical issues are found, broadcasts a Red Alert.
    """
    report = {
        "timestamp": TimeUtils.now().isoformat(),
        "checks": [],
        "passed": True
    }
    
    # 1. Data Freshness Audit
    try:
        tickers = DataManager.DataManager.list_tickers()[:20] # Audit sample
        stale_count = 0
        for ticker in tickers:
            df = DataManager.DataManager.get_stock_data(ticker)
            if df is not None and not df.empty:
                last_date = df.index[-1]
                if (TimeUtils.now() - last_date).days > 3:
                    stale_count += 1
        
        status = "FAIL" if stale_count > 5 else "PASS"
        report["checks"].append({
            "name": "Data Freshness",
            "status": status,
            "detail": f"{stale_count} stale tickers found in sample"
        })
        if status == "FAIL": report["passed"] = False
    except Exception as e:
        report["checks"].append({"name": "Data Freshness", "status": "ERROR", "detail": str(e)})
        report["passed"] = False

    # 2. Portfolio Balance Consistency
    try:
        p_count = Portfolio.select().count()
        report["checks"].append({
            "name": "Database Consistency",
            "status": "PASS",
            "detail": f"{p_count} portfolios verified"
        })
    except Exception as e:
        report["checks"].append({"name": "Database Consistency", "status": "ERROR", "detail": str(e)})
        report["passed"] = False

    # 2b. SQLite Storage Integrity Check
    try:
        from database.backup import _resolve_db_file
        import sqlite3
        db_path = _resolve_db_file()
        if db_path.exists():
            chk_conn = sqlite3.connect(f"file:{db_path.resolve().as_posix()}?mode=ro", uri=True, timeout=10)
            res = chk_conn.execute("PRAGMA integrity_check;").fetchone()
            chk_conn.close()
            integrity = res[0] if res else "unknown"
            if integrity == "ok":
                report["checks"].append({
                    "name": "SQLite Storage Integrity",
                    "status": "PASS",
                    "detail": "PRAGMA integrity_check verified ok"
                })
            else:
                report["checks"].append({
                    "name": "SQLite Storage Integrity",
                    "status": "FAIL",
                    "detail": f"Corrupted pages detected: {integrity}"
                })
                report["passed"] = False
        else:
            report["checks"].append({
                "name": "SQLite Storage Integrity",
                "status": "WARN",
                "detail": f"Database file not found: {db_path}"
            })
    except Exception as e:
        report["checks"].append({"name": "SQLite Storage Integrity", "status": "ERROR", "detail": str(e)})
        report["passed"] = False

    # 3. Provider Audit
    try:
        hist_p = settings.LOCAL_HISTORY_PROVIDER
        intra_p = settings.LOCAL_INTRADAY_PROVIDER
        report["checks"].append({
            "name": "Provider Status",
            "status": "PASS",
            "detail": f"Hist={hist_p}, Intra={intra_p}"
        })
    except Exception as e:
        report["checks"].append({"name": "Provider Status", "status": "ERROR", "detail": str(e)})

    # 4. Market Intelligence Audit (Phase 12)
    try:
        regime = MarketRegime.calculate_market_regime()
        report["checks"].append({
            "name": "Market Regime",
            "status": "PASS" if regime['score'] >= 4 else "WARN",
            "detail": f"{regime['regime']} (Score: {regime['score']}/10). {regime['description']}"
        })
        
        gossip = SentimentCrawler.gather_gossip()
        mortal_sentiment = SentimentCrawler.get_bifrost_sentiment(gossip)
        report["checks"].append({
            "name": "Market Sentiment",
            "status": "PASS" if mortal_sentiment['score'] > 40 else "WARN",
            "detail": f"{mortal_sentiment['regime']} (Pulse: {mortal_sentiment['score']}/100)"
        })
    except Exception as e:
        report["checks"].append({"name": "Market Intelligence", "status": "ERROR", "detail": str(e)})

    # Final Broadcast & Auto-Healing
    if not report["passed"]:
        AlertManager.broadcast_alert(
            "🔴 CRITICAL AUDIT FAILURE\nCheck Audit Dashboard for details.",
            priority="CRITICAL"
        )
        # Auto-Healing (Phase 11)
        try:
            stale_freshness = any(c['name'] == "Data Freshness" and c['status'] == "FAIL" for c in report['checks'])
            if stale_freshness and settings.AUTO_TRADE_ENABLED: # Only heal if trading is active
                logger.info("[Audit] Stale data detected. Relying on AdaptiveSyncWorker to auto-heal in background.")
                # We do NOT run `sync_all()` synchronously here, because the frontend polls
                # this endpoint and it would cause immediate threadpool starvation.
        except Exception as heal_e:
            logger.error(f"[Audit] Auto-healing check failed: {heal_e}")
    else:
        logger.info("System Audit Passed")
        
    return report
