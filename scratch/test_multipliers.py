
import pandas as pd
import numpy as np
from bot.config import Config
from bot.indicators import generate_signal, SignalResult

def mock_df(rows=10, price=100.0, atr=1.0):
    df = pd.DataFrame({
        "open": [price]*rows,
        "high": [price+atr]*rows,
        "low": [price-atr]*rows,
        "close": [price]*rows,
        "volume": [1000]*rows,
        "ema_fast": [price]*rows,
        "ema_slow": [price]*rows,
        "ema_trend": [price]*rows,
        "rsi": [50]*rows,
        "rsi_14": [50]*rows,
        "stoch_k": [50]*rows,
        "stoch_d": [50]*rows,
        "atr": [atr]*rows,
        "vol_spike": [False]*rows,
        "vol_ok": [True]*rows,
        "vwap": [price]*rows,
        "bb_lower": [price-2]*rows,
        "bb_upper": [price+2]*rows,
        "bb_mid": [price]*rows,
        "bb_pct": [0.5]*rows,
        "macd_bullish": [True]*rows,
        "macd_hist": [0.1]*rows,
        "ema_bullish": [True]*rows,
        "ema_cross_up": [False]*rows,
        "ema_cross_down": [False]*rows,
        "rsi_rising": [True]*rows,
        "rsi_falling": [False]*rows,
        "bullish_candle": [True]*rows,
        "bearish_candle": [False]*rows,
    })
    return df

def test_grade_multipliers():
    df_1m = mock_df(price=100.0, atr=1.0)
    df_5m = mock_df(price=100.0, atr=1.0)
    
    # Force Grade A Long
    df_5m.loc[df_5m.index[-1], "ema_trend"] = 90.0 # trend bull (price 100 > 90)
    df_1m.loc[df_1m.index[-1], "ema_cross_up"] = True
    df_1m.loc[df_1m.index[-1], "rsi"] = 50
    df_1m.loc[df_1m.index[-1], "vol_spike"] = True
    df_1m.loc[df_1m.index[-1], "vwap"] = 100.0
    
    sig_a = generate_signal(df_1m, df_5m)
    print(f"Grade A Signal: {sig_a}")
    expected_tp_a = 100.0 + (1.0 * Config.ATR_TP_MULT_A)
    assert abs(sig_a.take_profit - expected_tp_a) < 0.0001, f"Expected {expected_tp_a}, got {sig_a.take_profit}"

    # Force Grade B Long (RSI extreme)
    df_1m = mock_df(price=100.0, atr=1.0)
    df_1m.loc[df_1m.index[-1], "rsi"] = 15
    df_1m.loc[df_1m.index[-1], "rsi_14"] = 30
    df_1m.loc[df_1m.index[-1], "stoch_k"] = 10
    df_1m.loc[df_1m.index[-1], "bb_lower"] = 100.0
    df_1m.loc[df_1m.index[-1], "rsi_rising"] = True
    
    sig_b = generate_signal(df_1m, df_5m)
    print(f"Grade B Signal: {sig_b}")
    expected_tp_b = 100.0 + (1.0 * Config.ATR_TP_MULT_B)
    assert abs(sig_b.take_profit - expected_tp_b) < 0.0001, f"Expected {expected_tp_b}, got {sig_b.take_profit}"

    # Force Grade C Long (Momentum)
    df_1m = mock_df(price=100.0, atr=1.0)
    df_5m.loc[df_5m.index[-1], "ema_trend"] = 90.0 # trend bull
    df_1m.loc[df_1m.index[-1], "ema_bullish"] = True
    df_1m.loc[df_1m.index[-1], "macd_bullish"] = True
    df_1m.loc[df_1m.index[-1], "macd_hist"] = 0.5
    df_1m.loc[df_1m.index[-1], "rsi"] = 50
    df_1m.loc[df_1m.index[-1], "ema_fast"] = 99.0
    df_1m.loc[df_1m.index[-1], "bb_mid"] = 101.0
    df_1m.loc[df_1m.index[-1], "vol_ok"] = True
    
    sig_c = generate_signal(df_1m, df_5m)
    print(f"Grade C Signal: {sig_c}")
    expected_tp_c = 100.0 + (1.0 * Config.ATR_TP_MULT_C)
    assert abs(sig_c.take_profit - expected_tp_c) < 0.0001, f"Expected {expected_tp_c}, got {sig_c.take_profit}"

    print("All tests passed!")

if __name__ == "__main__":
    test_grade_multipliers()
