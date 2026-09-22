"""
ALPHA SENTIMENT VALIDATION TEST
===============================
Verifies that SentimentCrawler news sentiment correctly influences 
AlphaIntelligence composite scores.
"""

import unittest
from unittest.mock import patch, MagicMock
from core.market import alpha_intelligence
from core.analyzers import SentimentCrawler

class TestAlphaSentiment(unittest.TestCase):

    def setUp(self):
        # Reset the gossip cache before each test
        alpha_intelligence._gossip_cache = None

    @patch('core.analyzers.SentimentCrawler.gather_gossip')
    @patch('core.Heimdall.diagnose_stock')
    @patch('database.TickerStrategyMetrics.get_or_none')
    def test_positive_sentiment_boost(self, mock_metrics, mock_heimdall, mock_gossip):
        # Setup: Positive Gossip for COMI
        mock_gossip.return_value = [
            {
                "source": "Test",
                "title": "COMI profit increase and acquisition",
                "tickers": ["COMI"],
                "gossip_score": 4.0 # (profit=2, increase=1, acquisition=2) -> max cap 10
            }
        ]
        mock_heimdall.return_value = {"status": "ok", "whale_activity": "NEUTRAL"}
        mock_metrics.return_value = None # No historical metrics
        
        # Test: Score with base 10
        # Expected composite: (10 * 4) + (4 * 1.5) = 40 + 6 = 46
        res = alpha_intelligence.get_composite_score("COMI", base_score=10)
        
        self.assertEqual(res['score'], 46.0)
        self.assertTrue(any("Gossip Sentiment: Positive" in r for r in res['rationale']))

    @patch('core.analyzers.SentimentCrawler.gather_gossip')
    @patch('core.Heimdall.diagnose_stock')
    @patch('database.TickerStrategyMetrics.get_or_none')
    def test_negative_sentiment_penalty(self, mock_metrics, mock_heimdall, mock_gossip):
        # Setup: Negative Gossip for EKHO
        mock_gossip.return_value = [
            {
                "source": "Test",
                "title": "EKHO default and bankruptcy probe",
                "tickers": ["EKHO"],
                "gossip_score": -8.0 
            }
        ]
        mock_heimdall.return_value = {"status": "ok", "whale_activity": "NEUTRAL"}
        mock_metrics.return_value = None
        
        # Test: Score with base 10
        # Expected composite: (10 * 4) + (-8 * 1.5) = 40 - 12 = 28
        res = alpha_intelligence.get_composite_score("EKHO", base_score=10)
        
        self.assertEqual(res['score'], 28.0)
        self.assertTrue(any("Gossip Sentiment: Negative" in r for r in res['rationale']))

    @patch('core.analyzers.SentimentCrawler.gather_gossip')
    def test_gossip_caching(self, mock_gossip):
        # Setup
        mock_gossip.return_value = []
        
        # Call multiple times
        alpha_intelligence.get_composite_score("COMI", 10)
        alpha_intelligence.get_composite_score("EKHO", 10)
        
        # gather_gossip should only be called once due to global cache
        self.assertEqual(mock_gossip.call_count, 1)

if __name__ == '__main__':
    unittest.main()
