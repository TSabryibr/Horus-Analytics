import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import MagicMock
from core import RiskManager

def test_heat_with_mocks():
    print("\nTesting calculate_portfolio_heat with MagicMocks...")
    
    # Mock positions
    mock_pos = [
        {'ticker': 'COMI', 'entry': 50.0, 'sl': MagicMock(), 'shares': 100}, # SL is mock
        {'ticker': 'SWDY', 'entry': MagicMock(), 'sl': 15.0, 'shares': 200}, # Entry is mock
    ]
    
    # Mock account balance
    mock_balance = MagicMock()
    
    try:
        heat = RiskManager.calculate_portfolio_heat(mock_pos, mock_balance)
        print(f"Heat with all mocks: {heat}")
        
        # Partially mocked
        mock_pos_2 = [
            {'ticker': 'FWRY', 'entry': 10.0, 'sl': 9.0, 'shares': 500},
        ]
        heat_2 = RiskManager.calculate_portfolio_heat(mock_pos_2, 100000)
        print(f"Heat with valid data: {heat_2}")
        
        # Mixed
        mock_pos_3 = [
            {'ticker': 'FWRY', 'entry': 10.0, 'sl': 9.0, 'shares': 500},
            {'ticker': 'MOCK', 'entry': MagicMock(), 'sl': MagicMock(), 'shares': MagicMock()},
        ]
        heat_3 = RiskManager.calculate_portfolio_heat(mock_pos_3, 100000)
        print(f"Heat with mixed data: {heat_3}")
        
        print("✅ RiskManager type safety test passed!")
    except Exception as e:
        print(f"❌ RiskManager type safety test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_heat_with_mocks()
