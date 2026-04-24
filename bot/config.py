"""
config.py - Central configuration loader
All runtime settings flow from .env or environment variables.
"""

from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Exchange ────────────────────────────────────────────────────────────────
    API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    API_SECRET: str = os.getenv("BINANCE_API_SECRET", "")
    TESTNET: bool = os.getenv("BINANCE_TESTNET", "true").lower() == "true"

    # ── Capital & Risk ──────────────────────────────────────────────────────────
    INITIAL_BALANCE: float = float(os.getenv("INITIAL_BALANCE_USDT", 100))
    MAX_RISK_PER_TRADE: float = float(os.getenv("MAX_RISK_PER_TRADE", 0.02))   # 2%
    DAILY_DRAWDOWN_LIMIT: float = float(os.getenv("DAILY_DRAWDOWN_LIMIT", 0.15))  # 15%
    LEVERAGE: int = int(os.getenv("LEVERAGE", 10))

    # ── Strategy ────────────────────────────────────────────────────────────────
    PAIRS: list[str] = [
        p.strip() for p in os.getenv("TRADING_PAIRS", "BTC/USDT,ETH/USDT,SOL/USDT").split(",")
    ]
    ENTRY_TF: str = "1m"    # signal timeframe
    TREND_TF: str = "5m"    # trend filter timeframe

    # EMA
    EMA_FAST: int = 9
    EMA_SLOW: int = 21
    EMA_TREND: int = 50     # 5m 50-EMA = macro bias

    # RSI
    RSI_PERIOD: int = 7
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0

    # Bollinger Bands
    BB_PERIOD: int = 20
    BB_STD: float = 2.0

    # ATR (for dynamic SL/TP)
    ATR_PERIOD: int = 14
    
    # Grade A: High Confluence
    ATR_SL_MULT_A: float = float(os.getenv("ATR_SL_MULT_A", 1.5))
    ATR_TP_MULT_A: float = float(os.getenv("ATR_TP_MULT_A", 3.5))  # Higher target for A-grade
    
    # Grade B: RSI Reversal (Current default)
    ATR_SL_MULT_B: float = float(os.getenv("ATR_SL_MULT_B", 1.5))
    ATR_TP_MULT_B: float = float(os.getenv("ATR_TP_MULT_B", 2.5))
    
    # Grade C: Momentum Continuation
    ATR_SL_MULT_C: float = float(os.getenv("ATR_SL_MULT_C", 1.5))
    ATR_TP_MULT_C: float = float(os.getenv("ATR_TP_MULT_C", 2.0))  # Lower target for chasing
    
    # Trailing Stop / Break-even
    BREAKEVEN_ATR_TRIGGER: float = float(os.getenv("BREAKEVEN_ATR_TRIGGER", 1.0))
    TRAILING_ATR_DIST: float     = float(os.getenv("TRAILING_ATR_DIST", 1.0))

    # Volume: candle volume must be > N× 20-bar average
    VOLUME_THRESHOLD: float = 1.3

    # ── Operational ─────────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOOP_SLEEP_SECONDS: int = 30   # how often we poll for new candles
    MAX_OPEN_POSITIONS: int = 3    # never hold more than 3 concurrent positions
