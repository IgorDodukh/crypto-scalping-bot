
import json
from pathlib import Path

def analyze_trades():
    trades_path = Path("data/trades.json")
    if not trades_path.exists():
        print("No trades found.")
        return

    with open(trades_path) as f:
        trades = json.load(f)

    if not trades:
        print("No trades found in file.")
        return

    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] < 0]
    breakeven = [t for t in trades if t["pnl"] == 0]

    total_trades = len(trades)
    win_rate = len(wins) / total_trades if total_trades > 0 else 0

    avg_win = sum(t["pnl"] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t["pnl"] for t in losses) / len(losses) if losses else 0

    total_pnl = sum(t["pnl"] for t in trades)

    print(f"Total Trades: {total_trades}")
    print(f"Wins: {len(wins)} ({win_rate:.1%})")
    print(f"Losses: {len(losses)}")
    print(f"Breakeven: {len(breakeven)}")
    print(f"Average Win: {avg_win:.4f}")
    print(f"Average Loss: {avg_loss:.4f}")
    print(f"Total PnL: {total_pnl:.4f}")
    print(f"R:R (Actual): {abs(avg_win / avg_loss) if avg_loss != 0 else 0:.2f}")

    # Analyze by grade
    grades = ["A", "B", "C"]
    for g in grades:
        g_trades = [t for t in trades if f"[{g}]" in t["reason"]]
        if not g_trades:
            continue
        g_wins = [t for t in g_trades if t["pnl"] > 0]
        g_losses = [t for t in g_trades if t["pnl"] < 0]
        g_win_rate = len(g_wins) / len(g_trades)
        g_avg_win = sum(t["pnl"] for t in g_wins) / len(g_wins) if g_wins else 0
        g_avg_loss = sum(t["pnl"] for t in g_losses) / len(g_losses) if g_losses else 0
        g_pnl = sum(t["pnl"] for t in g_trades)
        print(f"\nGrade {g} Stats:")
        print(f"  Trades: {len(g_trades)}")
        print(f"  Win Rate: {g_win_rate:.1%}")
        print(f"  Avg Win: {g_avg_win:.4f}")
        print(f"  Avg Loss: {g_avg_loss:.4f}")
        print(f"  Total PnL: {g_pnl:.4f}")
        print(f"  Actual R:R: {abs(g_avg_win / g_avg_loss) if g_avg_loss != 0 else 0:.2f}")

if __name__ == "__main__":
    analyze_trades()
