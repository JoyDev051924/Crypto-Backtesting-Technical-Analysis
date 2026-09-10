"""
Trading Bot v3 - Improved with better trend detection
"""

import json
import time
from datetime import datetime
from pathlib import Path
import ccxt
import pandas as pd
import ta

# Config - More conservative
INITIAL_CAPITAL = 10000
POSITION_SIZE_PCT = 10  # Reduced from 15%
MAX_POSITIONS = 2  # Reduced from 3 - more selective
FEE_PCT = 0.1
CHECK_INTERVAL_MINUTES = 1  # Check every minute

# Stricter risk management
STOP_LOSS_PCT = 4  # Tighter stop
TAKE_PROFIT_PCT = 8  # Lower target (take profits faster)
TRAILING_STOP_PCT = 2

SYMBOLS = [
    "BTC/USD", "ETH/USD", "SOL/USD", "LINK/USD", "AVAX/USD",
    "DOT/USD", "AAVE/USD", "UNI/USD", "ATOM/USD",
]
TIMEFRAME = "1h"

STATE_FILE = Path(__file__).parent / "bot_v3_state.json"
LOG_FILE = Path(__file__).parent / "bot_v3_log.json"

exchange = ccxt.kraken({"enableRateLimit": True})


def get_fear_greed_index():
    """Get crypto Fear & Greed Index (0-100)"""
    try:
        import requests
        response = requests.get("https://api.alternative.me/fng/", timeout=5)
        data = response.json()
        value = int(data["data"][0]["value"])
        classification = data["data"][0]["value_classification"]
        return value, classification
    except Exception as e:
        print(f"   Warning: Could not fetch Fear & Greed Index: {e}")
        return 50, "neutral"  # Default to neutral if API fails


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "cash": INITIAL_CAPITAL,
        "positions": {},
        "trades": [],
        "started_at": datetime.now().isoformat(),
        "total_pnl": 0,
        "wins": 0,
        "losses": 0,
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def log_event(event_type, data):
    logs = []
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            logs = json.load(f)
    logs.append({"timestamp": datetime.now().isoformat(), "type": event_type, "data": data})
    with open(LOG_FILE, "w") as f:
        json.dump(logs[-500:], f, indent=2, default=str)


def get_ohlcv(symbol, timeframe=TIMEFRAME, limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


def check_market_regime(df):
    """Determine if market is trending up, down, or ranging"""
    # Multiple timeframe EMAs
    ema_20 = ta.trend.ema_indicator(df["close"], window=20).iloc[-1]
    ema_50 = ta.trend.ema_indicator(df["close"], window=50).iloc[-1]
    ema_100 = ta.trend.ema_indicator(df["close"], window=100).iloc[-1]
    price = df["close"].iloc[-1]
    
    # ADX for trend strength
    adx = ta.trend.adx(df["high"], df["low"], df["close"], window=14).iloc[-1]
    
    # Get Fear & Greed sentiment
    fear_greed, sentiment = get_fear_greed_index()
    
    # Adjust confidence based on sentiment
    sentiment_boost = 0
    if fear_greed < 25:  # Extreme fear - contrarian buy signal
        sentiment_boost = 15
    elif fear_greed > 75:  # Extreme greed - reduce confidence
        sentiment_boost = -15
    
    # Strong uptrend
    if price > ema_20 > ema_50 > ema_100 and adx > 25:
        return "strong_uptrend", min(90 + sentiment_boost, 100), fear_greed
    # Uptrend
    elif price > ema_20 > ema_50 and adx > 20:
        return "uptrend", min(75 + sentiment_boost, 100), fear_greed
    # Strong downtrend - AVOID
    elif price < ema_20 < ema_50 < ema_100 and adx > 25:
        # Exception: extreme fear can signal bottom
        if fear_greed < 20:
            return "downtrend_but_oversold", 60, fear_greed
        return "strong_downtrend", 0, fear_greed
    # Downtrend - AVOID
    elif price < ema_20 < ema_50:
        if fear_greed < 20:
            return "downtrend_but_oversold", 50, fear_greed
        return "downtrend", 0, fear_greed
    # Ranging
    else:
        return "ranging", 50 + sentiment_boost, fear_greed


def check_reversal_signal(df):
    """Look for reversal after pullback in uptrend"""
    regime, confidence, fear_greed = check_market_regime(df)
    
    # Only trade in uptrends or if extreme fear signals bottom
    if regime not in ["uptrend", "strong_uptrend", "downtrend_but_oversold"]:
        return "hold", 0, f"Market regime: {regime}, F&G: {fear_greed}"
    
    rsi = ta.momentum.rsi(df["close"], window=14).iloc[-1]
    macd = ta.trend.MACD(df["close"])
    macd_line = macd.macd().iloc[-1]
    signal_line = macd.macd_signal().iloc[-1]
    
    # Pullback in uptrend (RSI oversold but trend still up)
    if rsi < 40 and macd_line > signal_line:
        return "buy", confidence, f"Pullback in {regime}, RSI={rsi:.0f}, F&G={fear_greed}"
    
    # Exit signals
    if rsi > 70 or macd_line < signal_line:
        return "sell", 70, f"Overbought or momentum fading"
    
    return "hold", 0, f"No signal, RSI={rsi:.0f}, F&G={fear_greed}"


def check_breakout_signal(df):
    """Breakout strategy - only in uptrends"""
    regime, confidence, fear_greed = check_market_regime(df)
    
    if regime not in ["uptrend", "strong_uptrend", "downtrend_but_oversold"]:
        return "hold", 0, f"Market regime: {regime}, F&G: {fear_greed}"
    
    # Volume confirmation
    vol_sma = df["volume"].rolling(20).mean().iloc[-1]
    vol_ratio = df["volume"].iloc[-1] / vol_sma
    
    # Price breakout
    high_20 = df["high"].rolling(20).max().shift(1).iloc[-1]
    price = df["close"].iloc[-1]
    breakout = price > high_20
    
    rsi = ta.momentum.rsi(df["close"], window=14).iloc[-1]
    
    if breakout and vol_ratio > 1.3 and rsi < 70:
        return "buy", confidence, f"Breakout in {regime}, vol={vol_ratio:.1f}x, F&G={fear_greed}"
    
    if rsi > 75:
        return "sell", 70, "Overbought"
    
    return "hold", 0, f"No breakout, F&G={fear_greed}"


def check_stop_loss_take_profit(position, current_price):
    entry_price = position["entry_price"]
    highest_price = position.get("highest_price", entry_price)
    
    if current_price > highest_price:
        position["highest_price"] = current_price
        highest_price = current_price
    
    pnl_pct = ((current_price - entry_price) / entry_price) * 100
    trail_pct = ((current_price - highest_price) / highest_price) * 100
    
    if pnl_pct <= -STOP_LOSS_PCT:
        return "sell", f"STOP LOSS {pnl_pct:.1f}%"
    
    if pnl_pct >= TAKE_PROFIT_PCT:
        return "sell", f"TAKE PROFIT {pnl_pct:.1f}%"
    
    if pnl_pct > 2 and trail_pct <= -TRAILING_STOP_PCT:
        return "sell", f"TRAILING STOP {pnl_pct:.1f}%"
    
    return "hold", f"PnL: {pnl_pct:.1f}%"


def execute_paper_trade(state, symbol, side, price, reason, confidence=0):
    now = datetime.now().isoformat()
    
    if side == "buy":
        if symbol in state["positions"] or len(state["positions"]) >= MAX_POSITIONS:
            return state, None
        
        trade_amount_usd = state["cash"] * (POSITION_SIZE_PCT / 100)
        if trade_amount_usd < 10:
            return state, None
        
        fee = trade_amount_usd * (FEE_PCT / 100)
        crypto_amount = (trade_amount_usd - fee) / price
        
        state["cash"] -= trade_amount_usd
        state["positions"][symbol] = {
            "amount": crypto_amount,
            "entry_price": price,
            "entry_time": now,
            "highest_price": price,
            "confidence": confidence,
            "reason": reason
        }
        
        trade = {
            "type": "buy",
            "symbol": symbol,
            "price": price,
            "amount": crypto_amount,
            "usd_value": trade_amount_usd,
            "fee": fee,
            "reason": reason,
            "confidence": confidence,
            "timestamp": now
        }
        state["trades"].append(trade)
        return state, trade
    
    elif side == "sell":
        if symbol not in state["positions"]:
            return state, None
        
        position = state["positions"][symbol]
        gross = position["amount"] * price
        fee = gross * (FEE_PCT / 100)
        net = gross - fee
        
        cost_basis = position["amount"] * position["entry_price"]
        pnl = net - cost_basis
        pnl_pct = (pnl / cost_basis) * 100
        
        state["cash"] += net
        state["total_pnl"] += pnl
        
        if pnl > 0:
            state["wins"] += 1
        else:
            state["losses"] += 1
        
        del state["positions"][symbol]
        
        trade = {
            "type": "sell",
            "symbol": symbol,
            "price": price,
            "amount": position["amount"],
            "usd_value": net,
            "fee": fee,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "reason": reason,
            "timestamp": now
        }
        state["trades"].append(trade)
        return state, trade
    
    return state, None


def run_bot_cycle():
    state = load_state()
    wins = state.get("wins", 0)
    losses = state.get("losses", 0)
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    # Get market sentiment
    fear_greed, sentiment = get_fear_greed_index()
    
    print(f"\n{'='*70}")
    print(f"Bot v3: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"💰 ${state['cash']:.2f} | 📊 {len(state['positions'])}/{MAX_POSITIONS} positions | PnL: ${state['total_pnl']:.2f}")
    print(f"📈 {wins}W/{losses}L ({win_rate:.0f}%) | 😱 Fear & Greed: {fear_greed} ({sentiment})")
    print(f"{'='*70}")
    
    strategies = [
        ("Reversal", check_reversal_signal),
        ("Breakout", check_breakout_signal),
    ]
    
    # Check existing positions
    for symbol in list(state["positions"].keys()):
        try:
            ticker = exchange.fetch_ticker(symbol)
            price = ticker["last"]
            position = state["positions"][symbol]
            
            action, reason = check_stop_loss_take_profit(position, price)
            
            if action == "sell":
                print(f"\n🔴 {symbol} @ ${price:,.2f} - {reason}")
                state, trade = execute_paper_trade(state, symbol, "sell", price, reason)
                if trade:
                    emoji = "✅" if trade["pnl"] > 0 else "❌"
                    print(f"   {emoji} PnL: ${trade['pnl']:.2f} ({trade['pnl_pct']:.1f}%)")
                    log_event("trade", trade)
            else:
                pnl_pct = ((price - position["entry_price"]) / position["entry_price"]) * 100
                print(f"\n📍 {symbol} @ ${price:,.2f} ({pnl_pct:+.1f}%)")
                if price > position.get("highest_price", 0):
                    state["positions"][symbol]["highest_price"] = price
        except Exception as e:
            print(f"   Error: {e}")
    
    # Look for new entries
    if len(state["positions"]) < MAX_POSITIONS:
        for symbol in SYMBOLS:
            if symbol in state["positions"]:
                continue
            
            try:
                df = get_ohlcv(symbol)
                price = df["close"].iloc[-1]
                
                regime, _, fear_greed = check_market_regime(df)
                print(f"\n{symbol} @ ${price:,.2f} [{regime}]")
                
                best_signal = None
                best_confidence = 0
                best_reason = ""
                
                for strat_name, strat_fn in strategies:
                    signal, confidence, reason = strat_fn(df)
                    
                    if signal == "buy" and confidence > best_confidence:
                        best_signal = signal
                        best_confidence = confidence
                        best_reason = f"{strat_name}: {reason}"
                    
                    if signal != "hold":
                        print(f"   [{strat_name}] {signal.upper()} ({confidence}%): {reason}")
                
                # Only buy with 75%+ confidence
                if best_signal == "buy" and best_confidence >= 75:
                    state, trade = execute_paper_trade(state, symbol, "buy", price, best_reason, best_confidence)
                    if trade:
                        print(f"   🟢 BOUGHT ${trade['usd_value']:.2f}")
                        log_event("trade", trade)
                        break  # Only one entry per cycle
            
            except Exception as e:
                print(f"   Error: {e}")
    
    save_state(state)
    
    # Summary
    total_value = state["cash"]
    for sym, pos in state["positions"].items():
        try:
            ticker = exchange.fetch_ticker(sym)
            total_value += pos["amount"] * ticker["last"]
        except:
            total_value += pos["amount"] * pos["entry_price"]
    
    returns = ((total_value - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100
    print(f"\n{'='*70}")
    print(f"📊 Portfolio: ${total_value:,.2f} ({returns:+.2f}%)")
    print(f"{'='*70}")
    
    log_event("cycle", {"total_value": total_value, "returns_pct": returns})
    return state


def run_continuous():
    print("🚀 Trading Bot v3 - Improved Trend Detection")
    print(f"   Capital: ${INITIAL_CAPITAL}")
    print(f"   Position size: {POSITION_SIZE_PCT}% (max {MAX_POSITIONS})")
    print(f"   Risk: {STOP_LOSS_PCT}% stop, {TAKE_PROFIT_PCT}% target")
    print()
    
    while True:
        try:
            run_bot_cycle()
        except Exception as e:
            print(f"❌ Error: {e}")
            log_event("error", {"error": str(e)})
        
        print(f"\n⏰ Next check in {CHECK_INTERVAL_MINUTES} minute(s)...")
        time.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_bot_cycle()
    else:
        run_continuous()
