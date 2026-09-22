from core.settings import settings
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import unittest
from unittest.mock import patch, MagicMock
from core import AutoTrader
from core import RiskManager
import pandas as pd

class TestAutoTraderMechanisms(unittest.TestCase):
    @patch('core.AutoTrader.Portfolio')
    @patch('core.RiskManager.calculate_portfolio_heat', create=True)
    @patch('core.RiskManager.check_correlation', create=True)
    def test_portfolio_heat_deadbolt(self, mock_check_correlation, mock_calc_heat, mock_portfolio):
        # Mock global settings
        settings.AUTO_TRADE_ENABLED = True
        settings.MAX_PORTFOLIO_HEAT = 5.0
        
        # Mock portfolio
        mock_port = MagicMock()
        mock_port.id = 1
        mock_portfolio.get.return_value = mock_port
        
        # Mock risk manager to return a heat exceeding max heat
        mock_calc_heat.return_value = 6.5
        
        # Mock signals
        signals = [{'Ticker': 'CIB', 'Entry_Price': 100, 'Stop_Loss': 90, 'Target_Price': 120}]
        
        # Act
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning, message="AutoTrader.process_scanner_signals is deprecated")
            AutoTrader.process_scanner_signals(signals)
        
        # Assert correlation check should not be called since heat deadbolt blocked it
        mock_check_correlation.assert_not_called()

    @patch('core.AutoTrader.Portfolio')
    @patch('core.AutoTrader.PositionTracker')
    @patch('core.AutoTrader._check_entry_gate')
    @patch('core.RiskManager.calculate_portfolio_heat', create=True)
    @patch('core.RiskManager.check_new_trade_correlation', create=True)
    def test_correlation_deadbolt(self, mock_check_correlation, mock_calc_heat, mock_check_entry_gate, mock_position_tracker, mock_portfolio):
        # Mock global settings
        settings.AUTO_TRADE_ENABLED = True
        settings.MAX_PORTFOLIO_HEAT = 6.0
        settings.ACCOUNT_BALANCE = 100000
        settings.RISK_PER_TRADE = 1.0
        
        # Mock portfolio
        mock_port = MagicMock()
        mock_port.id = 1
        mock_portfolio.get.return_value = mock_port
        
        # Mock risk manager
        mock_calc_heat.return_value = 2.0
        # Correlation returns is_safe: False
        mock_check_correlation.return_value = {'is_safe': False, 'most_correlated_with': 'FAIRY'}
        
        # Mock entry gate
        mock_check_entry_gate.return_value = (True, "allowed", {})
        
        # Mock signals
        signals = [{'Ticker': 'CIB', 'Entry_Price': 100, 'Stop_Loss': 90, 'Target_Price': 120, 'Sector': 'Banks'}]
        
        # Act
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning, message="AutoTrader.process_scanner_signals is deprecated")
            AutoTrader.process_scanner_signals(signals)
        
        # Assert position tracker should not be called since correlation deadbolt blocked it
        mock_position_tracker.add_position.assert_not_called()

if __name__ == '__main__':
    unittest.main()
