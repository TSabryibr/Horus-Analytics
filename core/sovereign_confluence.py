"""
SOVEREIGN CONFLUENCE ENGINE
===========================
The "Sovereign Hedge" Engine.
Correlates sentiment data from SentimentCrawler with whale flow from Vanaheim.
Detects institutional traps (Sovereign Bear Trap / Sovereign Bull Dive).
"""
import logging
import asyncio
import datetime
from typing import List, Dict, Any, Optional
from core import audit
from core import TimeUtils
from database import SovereignState

logger = logging.getLogger("horus.sovereign_confluence")


class SovereignConfluenceEngine:
    """
    The Sovereign Hedge Engine.
    Correlates sentiment data from SentimentCrawler with whale flow from Vanaheim.
    """

    @staticmethod
    async def analyze_sovereign_confluence(processed_news: Dict[str, Any], whale_data: Dict[str, Any]):
        """
        Analyzes the intersection of sentiment and volume.
        """
        logger.info("SovereignConfluence: Analyzing Sovereign Hedge signals...")

        stories = processed_news.get("stories", []) if isinstance(processed_news, dict) else (processed_news if isinstance(processed_news, list) else [])
        whales = whale_data.get("candidates", []) if isinstance(whale_data, dict) else (whale_data if isinstance(whale_data, list) else [])

        # 1. Calculate Ticker-Specific Sentiment
        ticker_sentiment = {}
        for story in stories:
            for ticker in story.get("tickers", []):
                ticker_sentiment.setdefault(ticker, []).append(story.get("gossip_score", 0))

        # Average it out
        ticker_avg_sentiment = {t: sum(scores)/len(scores) for t, scores in ticker_sentiment.items() if scores}

        confluence_alerts = []

        # 2. Check for "Sovereign" Intersection
        for whale in whales:
            ticker = whale["Ticker"]
            sentiment_score = ticker_avg_sentiment.get(ticker, 0)

            # --- THE SOVEREIGN BEAR TRAP ---
            # Sentiment is high (Exuberant Greed) BUT Whales are in DISTRIBUTION
            if sentiment_score > 3 and whale["Signal"] == "DISTRIBUTION":
                alert = {
                    "Ticker": ticker,
                    "Type": "SOVEREIGN_BEAR_TRAP",
                    "Conviction": "HIGH",
                    "Sentiment_Score": round(sentiment_score, 2),
                    "Whale_Strength": whale["Strength"],
                    "Message": f"🚨 SOVEREIGN WARNING: {ticker} news is highly bullish ({sentiment_score:.1f}), BUT institutional distribution is detected. Retail is being exit-liquidity."
                }
                confluence_alerts.append(alert)

            # --- THE SOVEREIGN BULL TRAP (Rare but possible: Stealth accumulation during panic) ---
            elif sentiment_score < -3 and whale["Signal"] == "ACCUMULATION":
                alert = {
                    "Ticker": ticker,
                    "Type": "SOVEREIGN_BULL_DIVE",
                    "Conviction": "HIGH",
                    "Sentiment_Score": round(sentiment_score, 2),
                    "Whale_Strength": whale["Strength"],
                    "Message": f"🛡️ SOVEREIGN SHIELD: {ticker} news is panic-driven ({sentiment_score:.1f}), BUT smart money is stealthily accumulating. Possible bottom."
                }
                confluence_alerts.append(alert)

        # 3. Log, Save to DB, and Broadcast
        try:
            sovereign_confluence_engine.clear_stale_traps()
        except Exception:
            pass

        now_dt = TimeUtils.now()

        for alert in confluence_alerts:
            # Upsert into Database
            try:
                trap, created = SovereignState.get_or_create(ticker=alert["Ticker"], defaults={
                    'trap_type': alert["Type"],
                    'confidence': alert["Conviction"],
                    'message': alert["Message"],
                    'created_at': now_dt,
                })
                if not created:
                    trap.trap_type = alert["Type"]
                    trap.confidence = alert["Conviction"]
                    trap.message = alert["Message"]
                    trap.created_at = now_dt
                    trap.save()
            except Exception as e:
                logger.error(f"Failed to save SovereignState for {alert['Ticker']}: {e}")

            audit.log_event(
                category="CONFLUENCE",
                event=alert["Type"],
                message=alert["Message"],
                level="WARNING",
                ticker=alert["Ticker"],
                meta=alert
            )

            # Broadcast via WebSocket
            from core.websocket import ws_manager
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(ws_manager.broadcast(alert, event_type="sovereign"))
            except RuntimeError:
                pass

        return confluence_alerts

    def get_active_trap(self, ticker: str, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
        """
        Retrieves an active sovereign trap for a ticker from the database.
        Returns a dict e.g. {"type": "SOVEREIGN_BEAR_TRAP"} or None if none/stale.
        """
        try:
            cutoff = TimeUtils.now() - datetime.timedelta(hours=max_age_hours)
            trap = SovereignState.get_or_none(
                (SovereignState.ticker == ticker) & 
                (SovereignState.created_at >= cutoff)
            )
            if trap:
                return {"type": trap.trap_type, "confidence": trap.confidence, "message": trap.message}
        except Exception as e:
            logger.error(f"Error reading sovereign trap for {ticker}: {e}")
        return None

    def clear_stale_traps(self, max_age_hours: int = 24):
        """Cleans up old traps to keep the DB fast"""
        try:
            cutoff = TimeUtils.now() - datetime.timedelta(hours=max_age_hours)
            query = SovereignState.delete().where(SovereignState.created_at < cutoff)
            deleted = query.execute()
            if deleted > 0:
                logger.debug(f"Cleared {deleted} stale sovereign traps from DB.")
        except Exception:
            pass


# Singleton
sovereign_confluence_engine = SovereignConfluenceEngine()

# Backward-compatible aliases within this module
ConfluenceEngine = SovereignConfluenceEngine
confluence_engine = sovereign_confluence_engine
