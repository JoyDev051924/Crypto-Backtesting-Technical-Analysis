"""
Multi-Strategy Bot System
Runs multiple independent strategy bots, each with their own capital allocation
"""

import json
import time
from datetime import datetime
from pathlib import Path
import ccxt
import pandas as pd
import ta

# Total capital split across strategies
TOTAL_CAPITAL = 10000
CHECK_INTERVAL_MINUTES = 30

# Top liquid coins on Kraken (high volume, tight spreads)
ALL_COINS = [
    # Majors
    "BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD", "ADA/USD",
    # Large caps
    "DOGE/USD", "AVAX/USD", "LINK/USD", "DOT/USD", "MATIC/USD",
    "LTC/USD", "UNI/USD", "ATOM/USD", "XLM/USD", "NEAR/USD",
    # Mid caps with good volume
    "APT/USD", "ARB/USD", "OP/USD", "INJ/USD", "SUI/USD",
    "FIL/USD", "AAVE/USD", "MKR/USD", "GRT/USD", "RENDER/USD",
    "FET/USD", "IMX/USD", "PEPE/USD", "SHIB/USD", "BONK/USD",
]

# Each bot gets equal share
BOTS = [
    {
        "name": "Breakout Hunter",
        "strategy": "volume_breakout",
        "coins": ALL_COINS[:15],  # Top 15 liquid
        "timeframe": "1h",
        "stop_loss": 5,
        "take_profit": 12,
    },
    {
        "name": "Dip Buyer",
        "strategy": "mean_reversion",
        "coins": ALL_COINS,  # All coins
        "timeframe": "4h",
        "stop_loss": 4,
        "take_profit": 8,
    },
    {
        "name": "Trend Rider",
        "strategy": "trend_follow",
        "coins": ALL_COINS[:10],  # Top 10 only
        "timeframe": "4h",
        "stop_loss": 6,
        "take_profit": 15,
    },
    {
        "name": "Scalper",
        "strategy": "rsi_extreme",
        "coins": ALL_COINS,  # All coins - more opportunities
        "timeframe": "1h",
        "stop_loss": 3,
        "take_profit": 5,
    },
]

STATE_FILE = Path(__file__).parent / "multi_bot_state.json"
exchange = ccxt.kraken({"enableRateLimit": True})


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    
    # Initialize each bot with equal capital
    capital_per_bot = TOTAL_CAPITAL / len(BOTS)
    return {
        "started_at": datetime.now().isoformat(),
        "bots": {
            bot["name"]: {
                "config": bot,
                "cash": capital_per_bot,
                "position": None,
                "trades": [],
                "pnl": 0,
                "wins": 0,
                "losses": 0,
            }
            for bot in BOTS
        }
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def get_ohlcv(symbol, timeframe, limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


# ============ STRATEGIES ============

def strategy_volume_breakout(df):
    """Buy breakouts with volume confirmation"""
    vol_sma = df["volume"].rolling(20).mean()
    vol_spike = df["volume"].iloc[-1] > (vol_sma.iloc[-1] * 1.5)
    high_20 = df["high"].rolling(20).max().shift(1).iloc[-1]
    breakout = df["close"].iloc[-1] > high_20
    rsi = ta.momentum.rsi(df["close"], window=14).iloc[-1]
    
    if vol_spike and breakout and rsi < 70:
        return "buy", 80, f"Breakout + volume, RSI {rsi:.0f}"
    elif rsi > 75:
        return "sell", 70, "RSI overbought"
    return "hold", 0, ""


def strategy_mean_reversion(df):
    """Buy when price deviates from mean"""
    sma = ta.trend.sma_indicator(df["close"], window=20).iloc[-1]
    std = df["close"].rolling(20).std().iloc[-1]
    price = df["close"].iloc[-1]
    z = (price - sma) / std
    
    if z < -2:
        return "buy", 75, f"Z-score {z:.1f}"
    elif z > 0.5:
        return "sell", 65, "Back to mean"
    return "hold", 0, ""


def strategy_trend_follow(df):
    """Follow the trend using EMAs"""
    ema_fast = ta.trend.ema_indicator(df["close"], window=12).iloc[-1]
    ema_slow = ta.trend.ema_indicator(df["close"], window=26).iloc[-1]
    ema_trend = ta.trend.ema_indicator(df["close"], window=50).iloc[-1]
    price = df["close"].iloc[-1]
    rsi = ta.momentum.rsi(df["close"], window=14).iloc[-1]
    
    # Buy when fast > slow and price > trend, RSI not overbought
    if ema_fast > ema_slow and price > ema_trend and rsi < 65:
        return "buy", 75, f"Uptrend confirmed"
    elif ema_fast < ema_slow or price < ema_trend:
        return "sell", 70, "Trend broken"
    return "hold", 0, ""


def strategy_rsi_extreme(df):
    """Quick trades on RSI extremes"""
    rsi = ta.momentum.rsi(df["close"], window=14).iloc[-1]
    rsi_prev = ta.momentum.rsi(df["close"], window=14).iloc[-2]
    
    # Buy when RSI crosses up from oversold
    if rsi > 30 and rsi_prev <= 30:
        return "buy", 70, f"RSI bounce from {rsi_prev:.0f}"
    elif rsi > 65:
        return "sell", 65, f"RSI elevated {rsi:.0f}"
    return "hold", 0, ""


STRATEGY_FUNCS = {
    "volume_breakout": strategy_volume_breakout,
    "mean_reversion": strategy_mean_reversion,
    "trend_follow": strategy_trend_follow,
    "rsi_extreme": strategy_rsi_extreme,
}


def check_exit(position, current_price, stop_loss_pct, take_profit_pct):
    """Check stop loss and take profit"""
    entry = position["entry_price"]
    high = position.get("highest", entry)
    
    if current_price > high:
        position["highest"] = current_price
        high = current_price
    
    pnl_pct = ((current_price - entry) / entry) * 100
    
    if pnl_pct <= -stop_loss_pct:
        return "sell", f"STOP LOSS {pnl_pct:.1f}%"
    if pnl_pct >= take_profit_pct:
        return "sell", f"TAKE PROFIT {pnl_pct:.1f}%"
    # Trailing stop at 50% of gains
    if pnl_pct > 3:
        trail = ((current_price - high) / high) * 100
        if trail < -2:
            return "sell", f"TRAILING STOP {pnl_pct:.1f}%"
    
    return "hold", f"PnL {pnl_pct:.1f}%"


def run_single_bot(bot_name, bot_state, config):
    """Run one bot's cycle"""
    strategy_fn = STRATEGY_FUNCS[config["strategy"]]
    
    # Check existing position first
    if bot_state["position"]:
        pos = bot_state["position"]
        try:
            ticker = exchange.fetch_ticker(pos["symbol"])
            price = ticker["last"]
            
            action, reason = check_exit(pos, price, config["stop_loss"], config["take_profit"])
            
            if action == "sell":
                # Execute sell
                gross = pos["amount"] * price
                fee = gross * 0.001
                net = gross - fee
                pnl = net - (pos["amount"] * pos["entry_price"])
                
                bot_state["cash"] += net
                bot_state["pnl"] += pnl
                if pnl > 0:
                    bot_state["wins"] += 1
                else:
                    bot_state["losses"] += 1
                
                bot_state["trades"].append({
                    "type": "sell",
                    "symbol": pos["symbol"],
                    "price": price,
                    "pnl": pnl,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                })
                bot_state["position"] = None
                
                emoji = "🟢" if pnl > 0 else "🔴"
                print(f"    {emoji} SOLD {pos['symbol']}: ${pnl:.2f} ({reason})")
                return bot_state
            else:
                pnl_pct = ((price - pos["entry_price"]) / pos["entry_price"]) * 100
                print(f"    📍 Holding {pos['symbol']} @ ${price:,.2f} ({pnl_pct:+.1f}%)")
                return bot_state
        except Exception as e:
            print(f"    ⚠️ Error checking position: {e}")
            return bot_state
    
    # Look for new entry
    for symbol in config["coins"]:
        try:
            df = get_ohlcv(symbol, config["timeframe"])
            price = df["close"].iloc[-1]
            
            signal, confidence, reason = strategy_fn(df)
            
            if signal == "buy" and confidence >= 70:
                # Execute buy
                trade_size = bot_state["cash"] * 0.9  # Use 90% of available
                if trade_size < 10:
                    continue
                
                fee = trade_size * 0.001
                amount = (trade_size - fee) / price
                
                bot_state["cash"] -= trade_size
                bot_state["position"] = {
                    "symbol": symbol,
                    "amount": amount,
                    "entry_price": price,
                    "highest": price,
                    "entry_time": datetime.now().isoformat()
                }
                bot_state["trades"].append({
                    "type": "buy",
                    "symbol": symbol,
                    "price": price,
                    "amount": amount,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                })
                
                print(f"    🟢 BOUGHT {symbol} @ ${price:,.2f} ({reason})")
                return bot_state
        except Exception as e:
            continue
    
    print(f"    No signals")
    return bot_state


def run_cycle():
    """Run all bots"""
    state = load_state()
    
    print(f"\n{'='*70}")
    print(f"Multi-Bot Cycle: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}")
    
    total_value = 0
    
    for bot_name, bot_state in state["bots"].items():
        config = bot_state["config"]
        w, l = bot_state["wins"], bot_state["losses"]
        wr = (w/(w+l)*100) if (w+l) > 0 else 0
        
        print(f"\n🤖 {bot_name} [{config['strategy']}] - {w}W/{l}L ({wr:.0f}%)")
        
        state["bots"][bot_name] = run_single_bot(bot_name, bot_state, config)
        
        # Calculate bot value
        bot_value = state["bots"][bot_name]["cash"]
        if state["bots"][bot_name]["position"]:
            try:
                pos = state["bots"][bot_name]["position"]
                ticker = exchange.fetch_ticker(pos["symbol"])
                bot_value += pos["amount"] * ticker["last"]
            except:
                bot_value += pos["amount"] * pos["entry_price"]
        
        total_value += bot_value
        print(f"    💰 Value: ${bot_value:,.2f} | PnL: ${bot_state['pnl']:.2f}")
    
    save_state(state)
    
    returns = ((total_value - TOTAL_CAPITAL) / TOTAL_CAPITAL) * 100
    print(f"\n{'='*70}")
    print(f"📊 TOTAL: ${total_value:,.2f} ({returns:+.2f}%)")
    print(f"{'='*70}")
    
    return state


def run_continuous():
    print("🚀 Starting Multi-Strategy Bot System")
    print(f"   Total Capital: ${TOTAL_CAPITAL}")
    print(f"   Bots: {len(BOTS)}")
    for bot in BOTS:
        print(f"   - {bot['name']}: {bot['strategy']} on {', '.join(bot['coins'])}")
    print()
    
    while True:
        try:
            run_cycle()
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print(f"\n⏰ Next check in {CHECK_INTERVAL_MINUTES} minutes...")
        time.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_cycle()
    else:
        run_continuous()
