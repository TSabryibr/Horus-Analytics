import pytest
import pandas as pd
import numpy as np
from core.SignalEngine import add_indicators, check_buy_signal, check_trickster_signal

def test_add_indicators():
    # Create sample data
    df = pd.DataFrame({
        'Open': [10.0] * 35,
        'High': [11.0] * 35,
        'Low': [9.0] * 35,
        'Close': [10.5] * 35,
        'Volume': [1000] * 35
    })
    
    df = add_indicators(df, lookback=30)
    
    assert 'ATR' in df.columns
    assert 'RSI' in df.columns
    assert 'EMA9' in df.columns
    assert 'Res_30' in df.columns
    assert not pd.isna(df['Res_30'].iloc[-1])

def test_check_buy_signal_success():
    # Mock settings
    class Settings:
        MIN_TURNOVER = 1000
        VOL_SPIKE = 1.1
        MOMENTUM = 1.0
        RSI_MIN = 30
        RSI_MAX = 75
        SL_PCT = 5
        TP1_PCT = 10
    
    # Create a row that should trigger a signal
    # Breakout: Close > Res_30
    # Momentum: Move >= 1.0
    # Rel_Vol: Rel_Vol > 1.1
    # RSI: 30 < 50 < 75
    # Liquid: Avg_Turnover > 1000
    
    row = pd.Series({
        'Close': 110.0,
        'Open': 105.0,
        'Res_30': 100.0,
        'RSI': 50.0,
        'Avg_Turnover': 20000.0,
        'Rel_Vol': 2.0,
        'Move': 4.76, # (110-105)/105 * 100
        'EFI': 10.0,
        'EMA9': 105.0
    })
    
    res = check_buy_signal(row, Settings(), resistance_col='Res_30')
    
    assert res is not None
    assert res['Signal_Type'] == 'BUY'
    assert res['Entry_Price'] == 110.0
    assert res['Score'] > 0

def test_check_buy_signal_no_breakout():
    class Settings:
        MIN_TURNOVER = 1000
        VOL_SPIKE = 1.1
        MOMENTUM = 1.0
        RSI_MIN = 30
        RSI_MAX = 75
    
    # Close < Res_30
    row = pd.Series({
        'Close': 95.0,
        'Open': 90.0,
        'Res_30': 100.0,
        'RSI': 50.0,
        'Avg_Turnover': 20000.0,
        'Rel_Vol': 2.0,
        'Move': 5.5
    })
    
    res = check_buy_signal(row, Settings(), resistance_col='Res_30')
    assert res is None

def test_check_trickster_signal_success():
    class Settings:
        USE_ATR_EXITS = True
        ATR_SL_MULTIPLIER = 1.5
        SL_PCT = 1.5

    df = pd.DataFrame([{
        'Open': 88.0,
        'Close': 90.0,
        'EMA9': 100.0,
        'ATR': 4.0,
        'RSI': 24.0,
        'Rel_Vol': 1.4
    }])

    res = check_trickster_signal(df, settings=Settings())

    assert res is not None
    assert res['Signal_Type'] == 'BUY'
    assert res['Signal_Setup'] == 'TRICKSTER_REVERSAL'
    assert res['Target_Price'] == 100.0
    assert res['Stop_Loss'] < res['Entry_Price']

def test_check_trickster_signal_not_stretched():
    df = pd.DataFrame([{
        'Open': 88.0,
        'Close': 90.0,
        'EMA9': 96.0,   # (96 - 90) / 4 = 1.5 -> not stretched enough
        'ATR': 4.0,
        'RSI': 24.0,
        'Rel_Vol': 1.4
    }])

    res = check_trickster_signal(df)
    assert res is None


def test_check_trickster_signal_high_conviction_when_rsi_below_20():
    class Settings:
        USE_ATR_EXITS = True
        ATR_SL_MULTIPLIER = 1.5
        SL_PCT = 1.5

    df = pd.DataFrame([{
        'Open': 88.0,
        'Close': 90.0,
        'EMA9': 102.0,
        'ATR': 4.0,
        'RSI': 18.0,
        'Rel_Vol': 1.1
    }])

    res = check_trickster_signal(df, settings=Settings())
    assert res is not None
    assert res['Conviction'] == 'High'


def test_check_trickster_signal_returns_none_when_atr_non_positive():
    df = pd.DataFrame([{
        'Open': 88.0,
        'Close': 90.0,
        'EMA9': 102.0,
        'ATR': 0.0,
        'RSI': 18.0,
        'Rel_Vol': 1.1
    }])
    assert check_trickster_signal(df) is None


def test_check_trickster_signal_stop_loss_guard_when_multiplier_invalid():
    class Settings:
        USE_ATR_EXITS = True
        ATR_SL_MULTIPLIER = -1.0  # Invalid, would place SL above entry without guard
        SL_PCT = 1.5

    df = pd.DataFrame([{
        'Open': 88.0,
        'Close': 90.0,
        'EMA9': 102.0,
        'ATR': 4.0,
        'RSI': 24.0,
        'Rel_Vol': 1.4
    }])

    res = check_trickster_signal(df, settings=Settings())
    assert res is not None
    assert res['Stop_Loss'] < res['Entry_Price']


def test_check_trickster_signal_uses_evolved_thresholds():
    # Evolved breakout settings should influence trickster gating.
    settings = {
        "RSI_MIN": 48,            # -> default Trickster RSI cap becomes 28
        "VOL_SPIKE": 2.0,         # -> default Trickster rel-vol min becomes 1.4
        "MOMENTUM": 2.4,          # -> default stretch threshold ~2.4 ATR
        "USE_ATR_EXITS": True,
        "ATR_SL_MULTIPLIER": 1.5,
        "SL_PCT": 1.5,
    }

    df_fail = pd.DataFrame([{
        "Open": 88.0,
        "Close": 90.0,
        "EMA9": 100.0,            # gap 2.5 ATR
        "ATR": 4.0,
        "RSI": 29.0,              # fails adapted RSI cap (<28)
        "Rel_Vol": 1.5,
    }])
    assert check_trickster_signal(df_fail, settings=settings) is None

    df_pass = pd.DataFrame([{
        "Open": 88.0,
        "Close": 90.0,
        "EMA9": 100.0,
        "ATR": 4.0,
        "RSI": 24.0,
        "Rel_Vol": 1.6,
    }])
    res = check_trickster_signal(df_pass, settings=settings)
    assert res is not None
    assert res["Trickster_RSI_Max"] < 30.0
    assert res["Trickster_RelVol_Min"] >= 1.3
