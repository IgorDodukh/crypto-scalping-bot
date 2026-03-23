"""
exchange.py - Exchange connectivity layer (Binance Futures Testnet / Live)
Wraps ccxt with helpers used by the rest of the bot.
"""

import asyncio
from typing import Optional

import ccxt.async_support as ccxt

from .config import Config
from .logger import get_logger

log = get_logger("exchange", Config.LOG_LEVEL)


class ExchangeClient:
    """Thin async wrapper around ccxt binanceusdm."""

    def __init__(self):
        params: dict = {
            "apiKey": Config.API_KEY,
            "secret": Config.API_SECRET,
            "enableRateLimit": True,
            "options": {
                "defaultType": "future",
                "adjustForTimeDifference": True,
                # Skip spot/margin currency fetch — testnet keys are futures-only
                "fetchCurrencies": False,
            },
        }

        if Config.TESTNET:
            params["urls"] = {
                "api": {
                    "public":        "https://testnet.binancefuture.com/fapi/v1",
                    "private":       "https://testnet.binancefuture.com/fapi/v1",
                    "fapiPublic":    "https://testnet.binancefuture.com/fapi/v1",
                    "fapiPrivate":   "https://testnet.binancefuture.com/fapi/v1",
                    "fapiPrivateV2": "https://testnet.binancefuture.com/fapi/v2",
                    "fapiPrivateV3": "https://testnet.binancefuture.com/fapi/v3",
                    "fapiData":      "https://testnet.binancefuture.com/futures/data",
                }
            }

        self.exchange = ccxt.binanceusdm(params)
        self._markets_loaded = False

    # ── Lifecycle ────────────────────────────────────────────────────────────────

    async def connect(self):
        await self.exchange.load_markets()
        self._markets_loaded = True
        mode = "TESTNET" if Config.TESTNET else "LIVE"
        log.info(f"Connected to Binance Futures [{mode}]")

    async def close(self):
        await self.exchange.close()

    # ── Market data ──────────────────────────────────────────────────────────────

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str, limit: int = 200
    ) -> list[list]:
        """Returns list of [ts, open, high, low, close, volume]."""
        return await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

    async def fetch_ticker(self, symbol: str) -> dict:
        return await self.exchange.fetch_ticker(symbol)

    async def fetch_order_book(self, symbol: str, limit: int = 5) -> dict:
        return await self.exchange.fetch_order_book(symbol, limit=limit)

    # ── Account ──────────────────────────────────────────────────────────────────

    async def fetch_balance(self) -> dict:
        bal = await self.exchange.fetch_balance()
        return bal

    async def get_usdt_balance(self) -> float:
        bal = await self.fetch_balance()
        return float(bal.get("USDT", {}).get("free", 0.0))

    # ── Orders ───────────────────────────────────────────────────────────────────

    async def set_leverage(self, symbol: str, leverage: int):
        try:
            await self.exchange.set_leverage(leverage, symbol)
            log.debug(f"Leverage set to {leverage}x for {symbol}")
        except Exception as e:
            log.warning(f"Could not set leverage for {symbol}: {e}")

    async def place_market_order(
        self, symbol: str, side: str, quantity: float
    ) -> dict:
        """side: 'buy' | 'sell'"""
        order = await self.exchange.create_order(
            symbol, "market", side, quantity
        )
        log.info(f"Market order placed: {side.upper()} {quantity} {symbol}")
        return order

    async def place_limit_order(
        self, symbol: str, side: str, quantity: float, price: float
    ) -> dict:
        order = await self.exchange.create_order(
            symbol, "limit", side, quantity, price
        )
        log.info(f"Limit order placed: {side.upper()} {quantity} {symbol} @ {price}")
        return order

    async def place_stop_order(
        self, symbol: str, side: str, quantity: float, stop_price: float
    ) -> dict:
        """Stop-market for stop-loss."""
        order = await self.exchange.create_order(
            symbol,
            "STOP_MARKET",
            side,
            quantity,
            params={"stopPrice": stop_price, "closePosition": True},
        )
        log.info(f"Stop order placed: {side.upper()} {symbol} trigger={stop_price}")
        return order

    async def place_take_profit_order(
        self, symbol: str, side: str, quantity: float, tp_price: float
    ) -> dict:
        order = await self.exchange.create_order(
            symbol,
            "TAKE_PROFIT_MARKET",
            side,
            quantity,
            params={"stopPrice": tp_price, "closePosition": True},
        )
        log.info(f"Take-profit order placed: {side.upper()} {symbol} trigger={tp_price}")
        return order

    async def cancel_all_orders(self, symbol: str):
        try:
            await self.exchange.cancel_all_orders(symbol)
            log.info(f"All open orders cancelled for {symbol}")
        except Exception as e:
            log.warning(f"Cancel orders error for {symbol}: {e}")

    async def fetch_open_positions(self) -> list[dict]:
        positions = await self.exchange.fetch_positions()
        return [p for p in positions if float(p.get("contracts", 0)) != 0]

    async def close_position(self, symbol: str, side: str, quantity: float):
        """Close an open position with a market order in the opposite direction."""
        close_side = "sell" if side == "long" else "buy"
        await self.place_market_order(symbol, close_side, quantity)
        log.info(f"Position closed: {symbol} {side}")
