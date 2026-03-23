#!/usr/bin/env python3
"""
main.py - Entry point for the Scalping Bot
Usage:
    python main.py            # run the bot
    python main.py --dry-run  # signal-only (no orders placed)
    python main.py --backtest # not yet implemented (planned)
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Ensure bot package is importable
sys.path.insert(0, str(Path(__file__).parent))

from bot.engine import TradingEngine
from bot.config import Config
from bot.logger import get_logger

log = get_logger("main", Config.LOG_LEVEL)


def parse_args():
    parser = argparse.ArgumentParser(description="Crypto Scalping Bot")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log signals only — no real orders placed",
    )
    return parser.parse_args()


def check_config():
    """Warn user if keys look like placeholders."""
    if not Config.API_KEY or Config.API_KEY == "your_testnet_api_key_here":
        print(
            "\n⚠️  WARNING: API key not set.\n"
            "   The bot needs Binance Testnet API keys to place orders.\n"
            "   1. Go to: https://testnet.binancefuture.com\n"
            "   2. Register and generate API keys\n"
            "   3. Copy .env.example → .env and fill in your keys\n"
            "   4. Re-run the bot\n"
            "\n   Running in DRY-RUN (signal-only) mode until keys are set.\n"
        )
        return False
    return True


async def main():
    args = parse_args()
    has_keys = check_config()

    if args.dry_run or not has_keys:
        log.info("🧪 DRY-RUN mode: signals will be logged but no orders placed")
        # Patch exchange to skip order placement
        from bot import exchange as ex_mod
        original_place = ex_mod.ExchangeClient.place_market_order

        async def dry_run_order(self, symbol, side, quantity):
            log.info(f"[DRY-RUN] Would place: {side.upper()} {quantity} {symbol}")
            return {"id": "dry-run", "status": "filled"}

        ex_mod.ExchangeClient.place_market_order      = dry_run_order
        ex_mod.ExchangeClient.place_stop_order        = dry_run_order
        ex_mod.ExchangeClient.place_take_profit_order = dry_run_order

        async def noop_cancel(*a, **kw): pass
        async def noop_positions(*a, **kw): return []
        async def fake_balance(*a, **kw): return Config.INITIAL_BALANCE
        async def noop_leverage(*a, **kw): pass

        ex_mod.ExchangeClient.cancel_all_orders    = noop_cancel
        ex_mod.ExchangeClient.fetch_open_positions = noop_positions
        ex_mod.ExchangeClient.get_usdt_balance     = fake_balance
        ex_mod.ExchangeClient.set_leverage         = noop_leverage

    engine = TradingEngine()
    await engine.start()


if __name__ == "__main__":
    asyncio.run(main())
