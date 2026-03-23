"""
indicators.py - Technical analysis engine
Computes all indicators needed by the scalping strategy.
Uses the `ta` library (compatible with Python 3.10+).
"""

import pandas as pd
import numpy as np
import ta
import ta.trend
import ta.momentum
import ta.volatility
import ta.volume

from .config import Config
from .logger import get_logger

log = get_logger("indicators", Config.LOG_LEVEL)


def ohlcv_to_df(ohlcv: list[list]) -> pd.DataFrame:
    """Convert raw ccxt OHLCV list → clean DataFrame."""
    df = pd.DataFrame(
        ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df.set_index("timestamp", inplace=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all strategy indicators to the dataframe.
    Returns the enriched DataFrame (leading NaN rows stripped).
    Requires at least 60 bars (warm-up for slowest indicator).
    """
    c = Config

    if len(df) < 60:
        log.debug(f"compute_indicators: only {len(df)} bars, need ≥60 — returning empty")
        return df.iloc[0:0]  # empty but typed

    # ── EMAs ────────────────────────────────────────────────────────────────────
    df["ema_fast"]  = ta.trend.EMAIndicator(df["close"], window=c.EMA_FAST).ema_indicator()
    df["ema_slow"]  = ta.trend.EMAIndicator(df["close"], window=c.EMA_SLOW).ema_indicator()
    df["ema_trend"] = ta.trend.EMAIndicator(df["close"], window=c.EMA_TREND).ema_indicator()

    # ── RSI ─────────────────────────────────────────────────────────────────────
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=c.RSI_PERIOD).rsi()

    # ── Bollinger Bands ─────────────────────────────────────────────────────────
    bb = ta.volatility.BollingerBands(df["close"], window=c.BB_PERIOD, window_dev=c.BB_STD)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_mid"]   = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]

    # ── ATR (for dynamic SL/TP sizing) ───────────────────────────────────────────
    df["atr"] = ta.volatility.AverageTrueRange(
        df["high"], df["low"], df["close"], window=c.ATR_PERIOD
    ).average_true_range()

    # ── VWAP ────────────────────────────────────────────────────────────────────
    df["vwap"] = ta.volume.VolumeWeightedAveragePrice(
        df["high"], df["low"], df["close"], df["volume"], window=14
    ).volume_weighted_average_price()

    # ── Volume filter ────────────────────────────────────────────────────────────
    df["vol_ma"]    = df["volume"].rolling(20).mean()
    df["vol_spike"] = df["volume"] > (df["vol_ma"] * c.VOLUME_THRESHOLD)

    # ── EMA crossover signals ────────────────────────────────────────────────────
    df["ema_bullish"]    = df["ema_fast"] > df["ema_slow"]
    df["ema_cross_up"]   = (df["ema_fast"] > df["ema_slow"]) & (
        df["ema_fast"].shift(1) <= df["ema_slow"].shift(1)
    )
    df["ema_cross_down"] = (df["ema_fast"] < df["ema_slow"]) & (
        df["ema_fast"].shift(1) >= df["ema_slow"].shift(1)
    )

    # Drop leading NaN rows (warm-up period)
    df.dropna(inplace=True)

    return df


def compute_trend_bias(df_5m: pd.DataFrame) -> str:
    """
    Returns 'bull', 'bear', or 'neutral' based on 5m 50-EMA vs price.
    Used as a higher-timeframe filter to avoid counter-trend entries.
    """
    if df_5m.empty or "ema_trend" not in df_5m.columns:
        return "neutral"

    last  = df_5m.iloc[-1]
    price = last["close"]
    ema   = last["ema_trend"]

    if price > ema * 1.001:   # 0.1% buffer to filter noise
        return "bull"
    elif price < ema * 0.999:
        return "bear"
    return "neutral"


class SignalResult:
    __slots__ = ("signal", "entry_price", "stop_loss", "take_profit", "atr", "reason")

    def __init__(
        self,
        signal: str,            # 'long' | 'short' | 'none'
        entry_price: float = 0.0,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        atr: float = 0.0,
        reason: str = "",
    ):
        self.signal      = signal
        self.entry_price = entry_price
        self.stop_loss   = stop_loss
        self.take_profit = take_profit
        self.atr         = atr
        self.reason      = reason

    def __repr__(self):
        if self.signal == "none":
            return f"SignalResult(none | {self.reason})"
        return (
            f"SignalResult({self.signal.upper()} | entry={self.entry_price:.4f} "
            f"SL={self.stop_loss:.4f} TP={self.take_profit:.4f} | {self.reason})"
        )


def generate_signal(df_1m: pd.DataFrame, df_5m: pd.DataFrame) -> SignalResult:
    """
    Core signal generator — multi-confluence scalping strategy.

    LONG conditions:
      1. 5m trend = bull (price above 5m 50-EMA)
      2. 1m EMA9 crossed above EMA21 in last 2 bars
      3. RSI(7) between 40–65 (momentum, not overbought)
      4. Volume spike confirms
      5. Price above VWAP
      6. Price not extended above BB midline

    SHORT conditions: mirror image.

    Secondary: Bollinger Band touch reversal.

    SL = entry ± (ATR × 1.5)
    TP = entry ± (ATR × 2.5)  →  1:1.67 R:R
    """
    c = Config

    if len(df_1m) < 3:
        return SignalResult("none", reason="insufficient data")

    trend = compute_trend_bias(df_5m)
    last  = df_1m.iloc[-1]

    price      = float(last["close"])
    rsi        = float(last["rsi"])
    atr        = float(last["atr"])
    vol_spike  = bool(last["vol_spike"])
    vwap       = float(last["vwap"])
    bb_lower   = float(last["bb_lower"])
    bb_upper   = float(last["bb_upper"])
    bb_mid     = float(last["bb_mid"])
    ema_bull   = bool(last["ema_bullish"])

    # Crossover in last 2 bars
    cross_up   = bool(df_1m["ema_cross_up"].iloc[-2:].any())
    cross_down = bool(df_1m["ema_cross_down"].iloc[-2:].any())

    sl_dist = atr * c.ATR_SL_MULT
    tp_dist = atr * c.ATR_TP_MULT

    # ── Primary LONG signal ──────────────────────────────────────────────────────
    if (
        trend == "bull"
        and cross_up
        and 40 < rsi < (c.RSI_OVERBOUGHT - 5)  # 40–65
        and vol_spike
        and price > vwap
        and price <= bb_mid * 1.005
    ):
        entry = price
        sl    = round(entry - sl_dist, 6)
        tp    = round(entry + tp_dist, 6)
        return SignalResult(
            "long", entry, sl, tp, atr,
            reason=f"EMA cross↑ | RSI={rsi:.1f} | trend=bull | vol✓ | VWAP✓"
        )

    # ── Primary SHORT signal ─────────────────────────────────────────────────────
    if (
        trend == "bear"
        and cross_down
        and (c.RSI_OVERSOLD + 5) < rsi < 60    # 35–60
        and vol_spike
        and price < vwap
        and price >= bb_mid * 0.995
    ):
        entry = price
        sl    = round(entry + sl_dist, 6)
        tp    = round(entry - tp_dist, 6)
        return SignalResult(
            "short", entry, sl, tp, atr,
            reason=f"EMA cross↓ | RSI={rsi:.1f} | trend=bear | vol✓ | VWAP✓"
        )

    # ── Secondary: BB lower bounce (LONG) ───────────────────────────────────────
    if (
        trend in ("bull", "neutral")
        and price <= bb_lower * 1.001
        and rsi < (c.RSI_OVERSOLD + 5)
        and vol_spike
        and ema_bull
    ):
        entry = price
        sl    = round(entry - sl_dist, 6)
        tp    = round(entry + tp_dist, 6)
        return SignalResult(
            "long", entry, sl, tp, atr,
            reason=f"BB lower bounce | RSI={rsi:.1f} | trend={trend} | vol✓"
        )

    # ── Secondary: BB upper rejection (SHORT) ───────────────────────────────────
    if (
        trend in ("bear", "neutral")
        and price >= bb_upper * 0.999
        and rsi > (c.RSI_OVERBOUGHT - 5)
        and vol_spike
        and not ema_bull
    ):
        entry = price
        sl    = round(entry + sl_dist, 6)
        tp    = round(entry - tp_dist, 6)
        return SignalResult(
            "short", entry, sl, tp, atr,
            reason=f"BB upper rejection | RSI={rsi:.1f} | trend={trend} | vol✓"
        )

    # ── No signal ───────────────────────────────────────────────────────────────
    reasons = []
    if trend == "neutral":
        reasons.append("no trend")
    if not vol_spike:
        reasons.append("low vol")
    if not (cross_up or cross_down):
        reasons.append("no EMA cross")

    return SignalResult("none", reason=" | ".join(reasons) or "no setup")
