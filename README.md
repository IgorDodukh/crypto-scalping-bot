# 🤖 Crypto Scalping Bot

High-frequency scalping bot for Binance Futures Testnet (and live).
Targets BTC/USDT · ETH/USDT · SOL/USDT with a multi-confluence entry strategy.

---

## Strategy Overview

| Component | Detail |
|-----------|--------|
| Entry TF | 1-minute candles |
| Trend filter | 5-minute 50-EMA |
| Entry signal | EMA 9/21 crossover + RSI(7) + Volume confirmation |
| Secondary signal | Bollinger Band reversal (lower/upper touch) |
| VWAP filter | Trade only on correct side of intraday VWAP |
| Stop-loss | 1.5× ATR below/above entry |
| Take-profit | 2.5× ATR from entry (1:1.67 R:R) |
| Trailing stop | Activates after 1 ATR in profit, trails at 1× ATR |
| Leverage | 10× (configurable) |
| Risk/trade | 2% of account |
| Daily halt | −15% daily drawdown or −25% from equity peak |
| Max positions | 3 concurrent |

---

## Quick Start

### 1. Get Testnet API Keys (No real account needed!)

1. Open **https://testnet.binancefuture.com**
2. Click **Register** (free, instant, no KYC)
3. Go to **API Management** → click **Generate HMAC_SHA256 Key**
4. Copy your **API Key** and **Secret Key**

### 2. Install Dependencies

```bash
cd scalping-bot
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env and paste your testnet keys
nano .env   # or use any text editor
```

Key settings in `.env`:
```
BINANCE_API_KEY=<your key>
BINANCE_API_SECRET=<your secret>
BINANCE_TESTNET=true       ← keep this true until you're confident
INITIAL_BALANCE_USDT=100
LEVERAGE=10
```

### 4. Run

```bash
# Dry-run (signals only, no orders)
python main.py --dry-run

# Full testnet trading
python main.py
```

---

## File Structure

```
scalping-bot/
├── main.py                  # Entry point
├── requirements.txt
├── .env.example             # Config template
├── .env                     # Your config (never commit this!)
├── bot/
│   ├── config.py            # All settings
│   ├── logger.py            # Colored logging
│   ├── exchange.py          # Binance API wrapper (ccxt)
│   ├── indicators.py        # TA engine (EMA, RSI, BB, ATR, VWAP)
│   ├── risk.py              # Risk manager + trade journal
│   ├── position_manager.py  # Open position tracking + trailing stops
│   └── engine.py            # Main trading loop
├── data/
│   └── journal_YYYY-MM-DD.json   # Daily trade log
└── logs/
    └── bot_YYYY-MM-DD.log         # Full session logs
```

---

## Risk Management Details

### Per-Trade Risk
- Max **2%** of account per trade
- Position size = `(balance × 0.02) / |entry − stop_loss|`
- Absolute minimum: $5 notional (skip otherwise)

### Account-Level Guards
- **Daily drawdown halt**: if daily losses exceed 15% of starting balance → stop new entries
- **Peak drawdown halt**: if account drops 25% from its equity peak → stop new entries
- **Max 3 concurrent positions** across all pairs

### Trailing Stop
- Activates once price moves **1× ATR** in your favour
- Trails at **1× ATR** behind the running peak/trough
- Ensures you always lock in partial profit on strong moves

---

## Going Live (When Ready)

1. Open a real Binance Futures account at **https://www.binance.com**
2. Complete KYC verification
3. Generate API keys (enable Futures trading, disable withdrawals)
4. In `.env`: set `BINANCE_TESTNET=false` and update your keys
5. Start with small capital to verify everything works as expected

⚠️ **Always start small on live. Testnet performance ≠ live performance due to slippage and liquidity differences.**

---

## Tuning Tips

| Goal | Change |
|------|--------|
| More trades | Lower `VOLUME_THRESHOLD` (1.1) or use tighter RSI bands |
| Fewer but better trades | Raise `VOLUME_THRESHOLD` (1.5+) |
| Tighter stops | Lower `ATR_SL_MULT` (1.0–1.2) |
| More room to breathe | Raise `ATR_SL_MULT` (2.0) |
| Higher aggression | Raise `LEVERAGE` (15–20) + raise `MAX_RISK_PER_TRADE` (0.03) |
| Lower risk | Lower `LEVERAGE` (5) + lower `MAX_RISK_PER_TRADE` (0.01) |

---

## ⚠️ Disclaimer

This bot is for educational and competition purposes. Crypto trading carries
substantial risk of loss. The $100→$10k target requires a sustained run of 
profitable trades at leverage — this is achievable but not guaranteed. 
Never risk money you cannot afford to lose.
