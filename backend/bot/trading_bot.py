"""
Automated Paper Trading Bot v2
With risk management, trailing stops, and multi-timeframe confirmation
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
import ccxt
import pandas as pd
import ta

# Config
INITIAL_CAPITAL = 10000
POSITION_SIZE_PCT = 15  # Reduced from 20% - less risk per trade
MAX_POSITIONS = 3  # Don't put all eggs in one basket
FEE_PCT = 0.1
CHECK_INTERVAL_MINUTES = 0.5  # Check every 30 seconds

# Risk Management
STOP_LOSS_PCT = 5  # Exit if down 5%
TAKE_PROFIT_PCT = 10  # Take profits at 10%
TRAILING_STOP_PCT = 3  # Trail by 3% from highs

SYMBOLS = [
    # Majors
    "BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD", "ADA/USD",
    # Large caps
    "DOGE/USD", "AVAX/USD", "LINK/USD", "DOT/USD", "POL/USD",
    "LTC/USD", "UNI/USD", "ATOM/USD", "NEAR/USD",
    # Mid caps
    "APT/USD", "ARB/USD", "OP/USD", "INJ/USD", "SUI/USD",
    "AAVE/USD", "FET/USD", "PEPE/USD",
]
TIMEFRAME = "1h"
CONFIRM_TIMEFRAME = "4h"  # Higher timeframe for trend confirmation

STATE_FILE = Path(__file__).parent / "bot_state.json"
LOG_FILE = Path(__file__).parent / "bot_log.json"

# Initialize exchange (public data only)
exchange = ccxt.kraken({"enableRateLimit": True})


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "cash": INITIAL_CAPITAL,
        "positions": {},
        "trades": [],
        "started_at": datetime.now().isoformat(),
        "total_pnl": 0
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def log_event(event_type, data):
    logs = []
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            logs = json.load(f)
    
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    })
    
    # Keep last 500 events
    logs = logs[-500:]
    
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2, default=str)


def get_ohlcv(symbol, timeframe=TIMEFRAME, limit=100):
    """Fetch OHLCV data"""
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


def get_trend_bias(symbol):
    """Check higher timeframe for trend direction"""
    try:
        df = get_ohlcv(symbol, CONFIRM_TIMEFRAME, 50)
        ema_20 = ta.trend.ema_indicator(df["close"], window=20).iloc[-1]
        ema_50 = ta.trend.ema_indicator(df["close"], window=50).iloc[-1]
        price = df["close"].iloc[-1]
        
        if price > ema_20 > ema_50:
            return "bullish", "Price above EMAs, uptrend"
        elif price < ema_20 < ema_50:
            return "bearish", "Price below EMAs, downtrend"
        else:
            return "neutral", "Mixed signals"
    except:
        return "neutral", "Could not determine"


def check_volume_breakout(df, trend_bias):
    """Volume Breakout Strategy - loosened criteria"""
    vol_sma = df["volume"].rolling(20).mean()
    vol_spike = df["volume"].iloc[-1] > (vol_sma.iloc[-1] * 1.2)  # Lowered from 1.5x to 1.2x
    
    high_10 = df["high"].rolling(10).max().shift(1).iloc[-1]  # 10-period instead of 20
    breakout = df["close"].iloc[-1] > high_10
    
    rsi = ta.momentum.rsi(df["close"], window=14).iloc[-1]
    
    # Buy breakouts in any trend except strong bearish
    if vol_spike and breakout and rsi < 72:
        return "buy", 75, f"Volume breakout, RSI={rsi:.1f}"
    elif rsi > 75:
        return "sell", 70, f"RSI overbought at {rsi:.1f}"
    return "hold", 0, f"No signal (RSI={rsi:.1f})"


def check_support_bounce(df, trend_bias):
    """Support Bounce Strategy - loosened criteria"""
    low_20 = df["low"].rolling(20).min().iloc[-1]
    price = df["close"].iloc[-1]
    near_support = price < (low_20 * 1.05)  # Within 5% of support (was 2%)
    
    rsi = ta.momentum.rsi(df["close"], window=14).iloc[-1]
    bullish_candle = df["close"].iloc[-1] > df["open"].iloc[-1]
    
    # Loosened RSI threshold
    if near_support and rsi < 45 and bullish_candle:  # RSI < 45 instead of 35
        return "buy", 70, f"Support bounce, RSI={rsi:.1f}"
    elif rsi > 65:
        return "sell", 60, f"Take profit, RSI={rsi:.1f}"
    return "hold", 0, f"No signal (RSI={rsi:.1f})"


def check_mean_reversion(df, trend_bias):
    """Mean Reversion Strategy - loosened criteria"""
    sma_20 = ta.trend.sma_indicator(df["close"], window=20).iloc[-1]
    std_20 = df["close"].rolling(20).std().iloc[-1]
    price = df["close"].iloc[-1]
    z_score = (price - sma_20) / std_20
    
    # Loosened z-score threshold
    if z_score < -1.5:  # Was -2
        return "buy", 70, f"Z-score={z_score:.2f}, below mean"
    elif z_score > 0.5:
        return "sell", 60, f"Z-score={z_score:.2f}, returned to mean"
    return "hold", 0, f"Z-score={z_score:.2f}"


def check_momentum_surge(df, trend_bias):
    """Momentum surge - loosened criteria"""
    roc = ta.momentum.roc(df["close"], window=5).iloc[-1]
    vol_sma = df["volume"].rolling(10).mean().iloc[-1]
    vol_ratio = df["volume"].iloc[-1] / vol_sma
    rsi = ta.momentum.rsi(df["close"], window=14).iloc[-1]
    
    # Loosened: lower ROC threshold, any trend
    if roc > 2 and vol_ratio > 1.1 and rsi < 68:  # Was roc>3, vol>1.3, rsi<65
        return "buy", 70, f"Momentum surge {roc:.1f}%, vol {vol_ratio:.1f}x"
    elif roc < -5 or rsi > 75:
        return "sell", 65, f"Momentum fading or overbought"
    return "hold", 0, f"ROC={roc:.1f}%"


def check_ema_crossover(df, trend_bias):
    """NEW: Simple EMA crossover - more frequent signals"""
    ema_9 = ta.trend.ema_indicator(df["close"], window=9)
    ema_21 = ta.trend.ema_indicator(df["close"], window=21)
    rsi = ta.momentum.rsi(df["close"], window=14).iloc[-1]
    
    # Just crossed above
    if ema_9.iloc[-1] > ema_21.iloc[-1] and ema_9.iloc[-2] <= ema_21.iloc[-2] and rsi < 65:
        return "buy", 70, f"EMA 9/21 bullish cross, RSI={rsi:.1f}"
    # Just crossed below
    elif ema_9.iloc[-1] < ema_21.iloc[-1] and ema_9.iloc[-2] >= ema_21.iloc[-2]:
        return "sell", 65, f"EMA 9/21 bearish cross"
    return "hold", 0, f"No crossover"


def check_stop_loss_take_profit(position, current_price):
    """Check if we should exit based on risk management rules"""
    entry_price = position["entry_price"]
    highest_price = position.get("highest_price", entry_price)
    
    # Update highest price for trailing stop
    if current_price > highest_price:
        position["highest_price"] = current_price
        highest_price = current_price
    
    pnl_pct = ((current_price - entry_price) / entry_price) * 100
    trail_pct = ((current_price - highest_price) / highest_price) * 100
    
    # Stop loss
    if pnl_pct <= -STOP_LOSS_PCT:
        return "sell", f"STOP LOSS triggered at {pnl_pct:.1f}%"
    
    # Take profit
    if pnl_pct >= TAKE_PROFIT_PCT:
        return "sell", f"TAKE PROFIT triggered at {pnl_pct:.1f}%"
    
    # Trailing stop (only if in profit)
    if pnl_pct > 3 and trail_pct <= -TRAILING_STOP_PCT:
        return "sell", f"TRAILING STOP triggered, dropped {abs(trail_pct):.1f}% from high"
    
    return "hold", f"PnL: {pnl_pct:.1f}%, Trail: {trail_pct:.1f}%"


def execute_paper_trade(state, symbol, side, price, reason, confidence=0):
    """Execute a paper trade"""
    now = datetime.now().isoformat()
    
    if side == "buy":
        if symbol in state["positions"]:
            return state, None  # Already have position
        
        if len(state["positions"]) >= MAX_POSITIONS:
            return state, None  # Too many positions
        
        # Calculate position size
        trade_amount_usd = state["cash"] * (POSITION_SIZE_PCT / 100)
        if trade_amount_usd < 10:
            return state, None  # Not enough cash
        
        fee = trade_amount_usd * (FEE_PCT / 100)
        crypto_amount = (trade_amount_usd - fee) / price
        
        state["cash"] -= trade_amount_usd
        state["positions"][symbol] = {
            "amount": crypto_amount,
            "entry_price": price,
            "entry_time": now,
            "highest_price": price,  # For trailing stop
            "confidence": confidence
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
            return state, None  # No position to sell
        
        position = state["positions"][symbol]
        gross = position["amount"] * price
        fee = gross * (FEE_PCT / 100)
        net = gross - fee
        
        # Calculate PnL
        cost_basis = position["amount"] * position["entry_price"]
        pnl = net - cost_basis
        pnl_pct = (pnl / cost_basis) * 100
        
        state["cash"] += net
        state["total_pnl"] += pnl
        
        # Track wins/losses
        if "wins" not in state:
            state["wins"] = 0
            state["losses"] = 0
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
    """Run one cycle of the bot"""
    state = load_state()
    wins = state.get("wins", 0)
    losses = state.get("losses", 0)
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"Bot Cycle: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Cash: ${state['cash']:.2f} | Positions: {len(state['positions'])}/{MAX_POSITIONS} | PnL: ${state['total_pnl']:.2f}")
    print(f"Win Rate: {wins}W/{losses}L ({win_rate:.0f}%)")
    print(f"{'='*60}")
    
    strategies = [
        ("Volume Breakout", check_volume_breakout),
        ("Support Bounce", check_support_bounce),
        ("Mean Reversion", check_mean_reversion),
        ("Momentum Surge", check_momentum_surge),
        ("EMA Crossover", check_ema_crossover),
    ]
    
    # First, check existing positions for stop loss / take profit
    for symbol in list(state["positions"].keys()):
        try:
            ticker = exchange.fetch_ticker(symbol)
            price = ticker["last"]
            position = state["positions"][symbol]
            
            action, reason = check_stop_loss_take_profit(position, price)
            
            if action == "sell":
                print(f"\n⚠️  {symbol} @ ${price:,.2f}")
                print(f"  � {reason}i")
                state, trade = execute_paper_trade(state, symbol, "sell", price, reason)
                if trade:
                    print(f"  SOLD: PnL ${trade['pnl']:.2f} ({trade['pnl_pct']:.1f}%)")
                    log_event("trade", trade)
            else:
                pnl_pct = ((price - position["entry_price"]) / position["entry_price"]) * 100
                print(f"\n📍 {symbol} @ ${price:,.2f} (entry: ${position['entry_price']:,.2f}, {pnl_pct:+.1f}%)")
                # Update highest price for trailing stop
                if price > position.get("highest_price", 0):
                    state["positions"][symbol]["highest_price"] = price
        except Exception as e:
            print(f"  Error checking {symbol}: {e}")
    
    # Then look for new entries
    for symbol in SYMBOLS:
        if symbol in state["positions"]:
            continue  # Already have position
        
        if len(state["positions"]) >= MAX_POSITIONS:
            print(f"\n⏸️  Max positions reached, skipping new entries")
            break
        
        try:
            df = get_ohlcv(symbol)
            price = df["close"].iloc[-1]
            
            # Get higher timeframe trend
            trend_bias, trend_reason = get_trend_bias(symbol)
            
            print(f"\n{symbol} @ ${price:,.2f} [{trend_bias}]")
            
            best_signal = None
            best_confidence = 0
            best_reason = ""
            
            # Check each strategy
            for strat_name, strat_fn in strategies:
                signal, confidence, reason = strat_fn(df, trend_bias)
                
                if signal == "buy" and confidence > best_confidence:
                    best_signal = signal
                    best_confidence = confidence
                    best_reason = f"{strat_name}: {reason}"
                
                if signal != "hold":
                    print(f"  [{strat_name}] {signal.upper()} ({confidence}%): {reason}")
            
            # Only execute if confidence is high enough
            if best_signal == "buy" and best_confidence >= 70:
                state, trade = execute_paper_trade(state, symbol, "buy", price, best_reason, best_confidence)
                
                if trade:
                    print(f"  🟢 BOUGHT: {trade['amount']:.6f} @ ${price:,.2f} (${trade['usd_value']:.2f})")
                    log_event("trade", trade)
        
        except Exception as e:
            print(f"  Error: {e}")
            log_event("error", {"symbol": symbol, "error": str(e)})
    
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
    print(f"\n{'='*60}")
    print(f"📊 Portfolio: ${total_value:,.2f} ({returns:+.2f}%) | Realized PnL: ${state['total_pnl']:.2f}")
    print(f"{'='*60}")
    
    log_event("cycle", {
        "cash": state["cash"],
        "positions": len(state["positions"]),
        "total_value": total_value,
        "returns_pct": returns,
        "wins": wins,
        "losses": losses
    })
    
    return state


def run_continuous():
    """Run the bot continuously"""
    print("🤖 Starting Paper Trading Bot v2")
    print(f"   Capital: ${INITIAL_CAPITAL}")
    print(f"   Symbols: {', '.join(SYMBOLS)}")
    print(f"   Check interval: {CHECK_INTERVAL_MINUTES} minutes")
    print(f"   Position size: {POSITION_SIZE_PCT}% per trade (max {MAX_POSITIONS} positions)")
    print(f"   Risk Management: {STOP_LOSS_PCT}% stop loss, {TAKE_PROFIT_PCT}% take profit, {TRAILING_STOP_PCT}% trailing")
    print()
    
    while True:
        try:
            run_bot_cycle()
        except Exception as e:
            print(f"❌ Cycle error: {e}")
            log_event("error", {"error": str(e)})
        
        print(f"\n⏰ Next check in {CHECK_INTERVAL_MINUTES} minutes...")
        time.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run single cycle
        run_bot_cycle()
    else:
        # Run continuously
        run_continuous()
