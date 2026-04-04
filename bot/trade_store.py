"""
trade_store.py - Persistent cross-session trade history.
Appends every closed trade to data/trades.json.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
TRADES_FILE = DATA_DIR / "trades.json"


def load_trades() -> list[dict]:
    """Load all historical trades."""
    if not TRADES_FILE.exists():
        return []
    try:
        with open(TRADES_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def append_trade(
    symbol: str,
    side: str,
    entry_price: float,
    exit_price: float,
    quantity: float,
    pnl: float,
    reason: str = "",
    opened_at: Optional[float] = None,  # unix timestamp
) -> dict:
    """Append a closed trade record. Returns the trade dict."""
    trades = load_trades()
    now = datetime.now(timezone.utc)
    trade = {
        "id":          len(trades) + 1,
        "ts":          now.isoformat(),
        "date":        now.strftime("%Y-%m-%d"),
        "symbol":      symbol,
        "side":        side,
        "entry":       round(entry_price, 6),
        "exit":        round(exit_price, 6),
        "qty":         round(quantity, 6),
        "pnl":         round(pnl, 4),
        "reason":      reason,
        "duration_s":  round(now.timestamp() - opened_at, 0) if opened_at else None,
    }
    trades.append(trade)
    with open(TRADES_FILE, "w") as f:
        json.dump(trades, f, indent=2)
    return trade


def get_stats() -> dict:
    """Aggregate stats across all trades."""
    trades = load_trades()
    if not trades:
        return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0,
                "total_pnl": 0, "best": 0, "worst": 0, "avg_pnl": 0}
    pnls   = [t["pnl"] for t in trades]
    wins   = sum(1 for p in pnls if p >= 0)
    losses = len(pnls) - wins
    return {
        "total":     len(trades),
        "wins":      wins,
        "losses":    losses,
        "win_rate":  wins / len(trades),
        "total_pnl": round(sum(pnls), 4),
        "best":      round(max(pnls), 4),
        "worst":     round(min(pnls), 4),
        "avg_pnl":   round(sum(pnls) / len(pnls), 4),
    }
