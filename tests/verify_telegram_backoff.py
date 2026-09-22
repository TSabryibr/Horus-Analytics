
import unittest
from unittest.mock import patch, MagicMock
import requests
import time
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import TelegramBot_Alerts
class TestTelegramBackoff(unittest.TestCase):
    @patch('core.TelegramBot_Alerts.requests.get')
    @patch('core.TelegramBot_Alerts.time.sleep')
    @patch('core.TelegramBot_Alerts._current_telegram_config')
    def test_backoff_logic(self, mock_config, mock_sleep, mock_get):
        mock_config.return_value = ("test_token", "test_chat_id")
        
        # Simulate multiple consecutive failures
        mock_get.side_effect = requests.exceptions.ConnectionError("DNS failure")
        
        # We need to break the infinite loop in handle_commands for testing
        # One way is to raise an exception after a few iterations
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 3:
                raise KeyboardInterrupt("Stop for test")
            raise requests.exceptions.ConnectionError("DNS failure")
        
        call_count = 0
        mock_get.side_effect = side_effect
        
        try:
            TelegramBot_Alerts.handle_commands()
        except KeyboardInterrupt:
            pass
            
        # Verify sleep times: 10 * 2^0, 10 * 2^1, 10 * 2^2
        expected_sleeps = [10, 20, 40]
        actual_sleeps = [call.args[0] for call in mock_sleep.call_args_list]
        
        print(f"Actual sleeps: {actual_sleeps}")
        self.assertEqual(actual_sleeps[:3], expected_sleeps)

if __name__ == '__main__':
    unittest.main()
