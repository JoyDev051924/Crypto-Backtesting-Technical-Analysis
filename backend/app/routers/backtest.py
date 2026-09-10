from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
import pandas as pd
import numpy as np
import ta

router = APIRouter()

class BacktestConfig(BaseModel):
    symbol: str
    initial_capital: float = 10000
    fee_percent: float = 0.1  # 0.1% per trade
    strategy: Literal["sma_crossover", "rsi", "macd", "bollinger_bounce"]
    # Strategy params
    sma_fast: int = 20
    sma_slow: int = 50
    rsi_oversold: int = 30
    rsi_overbought: int = 70

class OHLCVData(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class BacktestRequest(BaseModel):
    config: BacktestConfig
    data: List[OHLCVData]


class CompareRequest(BaseModel):
    data: List[OHLCVData]
    initial_capital: float = 10000
    fee_percent: float = 0.1


@router.post("/compare")
async def compare_strategies(request: CompareRequest):
    """Run all strategies and compare results"""
    try:
        df = pd.DataFrame([d.model_dump() for d in request.data])
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        strategies = [
            ("SMA 20/50", lambda d: _sma_crossover_strategy(d, 20, 50)),
            ("SMA 50/200", lambda d: _sma_crossover_strategy(d, 50, 200)),
            ("RSI 30/70", lambda d: _rsi_strategy(d, 30, 70)),
            ("RSI 20/80", lambda d: _rsi_strategy(d, 20, 80)),
            ("MACD", lambda d: _macd_strategy(d)),
            ("Bollinger", lambda d: _bollinger_strategy(d)),
            ("EMA 12/26", lambda d: _ema_crossover_strategy(d, 12, 26)),
            ("RSI + MACD", lambda d: _rsi_macd_combo(d)),
            ("Volume Breakout", lambda d: _volume_breakout_strategy(d)),
            ("Support Bounce", lambda d: _support_bounce_strategy(d)),
            ("Trend Filter", lambda d: _trend_filter_strategy(d)),
            ("Mean Reversion", lambda d: _mean_reversion_strategy(d)),
            ("Momentum", lambda d: _momentum_strategy(d)),
            ("Triple Confirm", lambda d: _triple_confirm_strategy(d)),
        ]

        results = []
        for name, strategy_fn in strategies:
            signals = strategy_fn(df)
            result = _simulate_trades(
                df, signals, request.initial_capital, request.fee_percent
            )
            results.append(
                {
                    "strategy": name,
                    "final_equity": result["final_equity"],
                    "total_return_pct": result["total_return_pct"],
                    "total_trades": result["total_trades"],
                    "win_rate": result["win_rate"],
                    "sharpe_ratio": result["sharpe_ratio"],
                    "max_drawdown_pct": result["max_drawdown_pct"],
                }
            )

        # Add buy & hold for comparison
        start_price = df["close"].iloc[0]
        end_price = df["close"].iloc[-1]
        buy_hold_return = ((end_price - start_price) / start_price) * 100
        results.append(
            {
                "strategy": "Buy & Hold",
                "final_equity": round(
                    request.initial_capital * (1 + buy_hold_return / 100), 2
                ),
                "total_return_pct": round(buy_hold_return, 2),
                "total_trades": 1,
                "win_rate": 100 if buy_hold_return > 0 else 0,
                "sharpe_ratio": 0,
                "max_drawdown_pct": 0,
            }
        )

        # Sort by return
        results.sort(key=lambda x: x["total_return_pct"], reverse=True)

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ScanRequest(BaseModel):
    symbols_data: List[dict]  # [{symbol: str, data: List[OHLCVData]}]
    initial_capital: float = 10000
    fee_percent: float = 0.1


@router.post("/scan")
async def scan_market(request: ScanRequest):
    """Find best strategy/symbol combinations across the market"""
    try:
        all_results = []
        
        strategies = [
            ("RSI 20/80", lambda d: _rsi_strategy(d, 20, 80)),
            ("Mean Reversion", lambda d: _mean_reversion_strategy(d)),
            ("Support Bounce", lambda d: _support_bounce_strategy(d)),
            ("Trend Filter", lambda d: _trend_filter_strategy(d)),
            ("Triple Confirm", lambda d: _triple_confirm_strategy(d)),
            ("Bollinger", lambda d: _bollinger_strategy(d)),
        ]
        
        for symbol_data in request.symbols_data:
            symbol = symbol_data["symbol"]
            data = symbol_data["data"]
            
            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            # Calculate buy & hold for this symbol
            start_price = df["close"].iloc[0]
            end_price = df["close"].iloc[-1]
            buy_hold_return = ((end_price - start_price) / start_price) * 100
            
            for name, strategy_fn in strategies:
                try:
                    signals = strategy_fn(df)
                    result = _simulate_trades(
                        df, signals, request.initial_capital, request.fee_percent
                    )
                    
                    # Only include if it beats buy & hold
                    beats_hold = result["total_return_pct"] > buy_hold_return
                    
                    all_results.append({
                        "symbol": symbol,
                        "strategy": name,
                        "return_pct": result["total_return_pct"],
                        "buy_hold_pct": round(buy_hold_return, 2),
                        "beats_hold": beats_hold,
                        "win_rate": result["win_rate"],
                        "trades": result["total_trades"],
                        "sharpe": result["sharpe_ratio"],
                    })
                except Exception:
                    continue
        
        # Sort by return
        all_results.sort(key=lambda x: x["return_pct"], reverse=True)
        
        # Get winners (beat buy & hold)
        winners = [r for r in all_results if r["beats_hold"]]
        
        return {
            "all_results": all_results[:20],  # Top 20
            "winners": winners[:10],  # Top 10 that beat buy & hold
            "total_tested": len(all_results),
            "total_winners": len(winners),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
async def run_backtest(request: BacktestRequest):
    """Run backtest with specified strategy"""
    try:
        df = pd.DataFrame([d.model_dump() for d in request.data])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        config = request.config
        
        # Generate signals based on strategy
        if config.strategy == "sma_crossover":
            signals = _sma_crossover_strategy(df, config.sma_fast, config.sma_slow)
        elif config.strategy == "rsi":
            signals = _rsi_strategy(df, config.rsi_oversold, config.rsi_overbought)
        elif config.strategy == "macd":
            signals = _macd_strategy(df)
        elif config.strategy == "bollinger_bounce":
            signals = _bollinger_strategy(df)
        else:
            raise HTTPException(status_code=400, detail="Unknown strategy")
        
        # Run simulation
        results = _simulate_trades(df, signals, config.initial_capital, config.fee_percent)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _sma_crossover_strategy(df: pd.DataFrame, fast: int, slow: int) -> pd.Series:
    """SMA crossover: buy when fast crosses above slow, sell when below"""
    sma_fast = ta.trend.sma_indicator(df["close"], window=fast)
    sma_slow = ta.trend.sma_indicator(df["close"], window=slow)
    
    signals = pd.Series(0, index=df.index)
    signals[sma_fast > sma_slow] = 1   # Buy signal
    signals[sma_fast < sma_slow] = -1  # Sell signal
    return signals

def _rsi_strategy(df: pd.DataFrame, oversold: int, overbought: int) -> pd.Series:
    """RSI: buy when oversold, sell when overbought"""
    rsi = ta.momentum.rsi(df["close"], window=14)
    
    signals = pd.Series(0, index=df.index)
    signals[rsi < oversold] = 1
    signals[rsi > overbought] = -1
    return signals

def _macd_strategy(df: pd.DataFrame) -> pd.Series:
    """MACD: buy when MACD crosses above signal, sell when below"""
    macd = ta.trend.MACD(df["close"])
    macd_line = macd.macd()
    signal_line = macd.macd_signal()
    
    signals = pd.Series(0, index=df.index)
    signals[macd_line > signal_line] = 1
    signals[macd_line < signal_line] = -1
    return signals

def _bollinger_strategy(df: pd.DataFrame) -> pd.Series:
    """Bollinger: buy at lower band, sell at upper band"""
    bb = ta.volatility.BollingerBands(df["close"])
    
    signals = pd.Series(0, index=df.index)
    signals[df["close"] < bb.bollinger_lband()] = 1
    signals[df["close"] > bb.bollinger_hband()] = -1
    return signals


def _ema_crossover_strategy(df: pd.DataFrame, fast: int, slow: int) -> pd.Series:
    """EMA crossover: buy when fast crosses above slow"""
    ema_fast = ta.trend.ema_indicator(df["close"], window=fast)
    ema_slow = ta.trend.ema_indicator(df["close"], window=slow)

    signals = pd.Series(0, index=df.index)
    signals[ema_fast > ema_slow] = 1
    signals[ema_fast < ema_slow] = -1
    return signals


def _rsi_macd_combo(df: pd.DataFrame) -> pd.Series:
    """Combined RSI + MACD: only buy when both agree"""
    rsi = ta.momentum.rsi(df["close"], window=14)
    macd = ta.trend.MACD(df["close"])
    macd_line = macd.macd()
    signal_line = macd.macd_signal()

    signals = pd.Series(0, index=df.index)
    # Buy when RSI < 40 AND MACD crosses above signal
    buy_condition = (rsi < 40) & (macd_line > signal_line)
    # Sell when RSI > 60 AND MACD crosses below signal
    sell_condition = (rsi > 60) & (macd_line < signal_line)

    signals[buy_condition] = 1
    signals[sell_condition] = -1
    return signals


def _volume_breakout_strategy(df: pd.DataFrame) -> pd.Series:
    """Buy on high volume breakouts above resistance"""
    # Volume spike = 2x average
    vol_sma = df["volume"].rolling(20).mean()
    vol_spike = df["volume"] > (vol_sma * 2)
    
    # Price breaking above recent high
    high_20 = df["high"].rolling(20).max().shift(1)
    breakout = df["close"] > high_20
    
    # RSI not overbought (avoid FOMO tops)
    rsi = ta.momentum.rsi(df["close"], window=14)
    
    signals = pd.Series(0, index=df.index)
    signals[(vol_spike) & (breakout) & (rsi < 70)] = 1
    signals[rsi > 75] = -1  # Take profit when overbought
    return signals


def _support_bounce_strategy(df: pd.DataFrame) -> pd.Series:
    """Buy at support levels with confirmation"""
    # Find support as recent lows
    low_20 = df["low"].rolling(20).min()
    near_support = df["close"] < (low_20 * 1.02)  # Within 2% of support
    
    # RSI oversold for confirmation
    rsi = ta.momentum.rsi(df["close"], window=14)
    
    # Bullish candle (close > open)
    bullish = df["close"] > df["open"]
    
    signals = pd.Series(0, index=df.index)
    signals[(near_support) & (rsi < 35) & (bullish)] = 1
    signals[rsi > 65] = -1
    return signals


def _trend_filter_strategy(df: pd.DataFrame) -> pd.Series:
    """Only trade in direction of major trend"""
    # Major trend: 100 EMA
    ema_100 = ta.trend.ema_indicator(df["close"], window=100)
    uptrend = df["close"] > ema_100
    
    # Entry: RSI oversold in uptrend only
    rsi = ta.momentum.rsi(df["close"], window=14)
    
    signals = pd.Series(0, index=df.index)
    signals[(uptrend) & (rsi < 35)] = 1  # Buy dips in uptrend
    signals[(~uptrend) | (rsi > 70)] = -1  # Exit if trend breaks or overbought
    return signals


def _mean_reversion_strategy(df: pd.DataFrame) -> pd.Series:
    """Buy when price deviates significantly from mean"""
    sma_20 = ta.trend.sma_indicator(df["close"], window=20)
    std_20 = df["close"].rolling(20).std()
    
    # Z-score: how many std devs from mean
    z_score = (df["close"] - sma_20) / std_20
    
    signals = pd.Series(0, index=df.index)
    signals[z_score < -2] = 1   # Buy when 2 std below mean
    signals[z_score > 0.5] = -1  # Sell when back to mean
    return signals


def _momentum_strategy(df: pd.DataFrame) -> pd.Series:
    """Ride momentum with trailing logic"""
    # Rate of change
    roc = ta.momentum.roc(df["close"], window=10)
    
    # ADX for trend strength
    adx = ta.trend.adx(df["high"], df["low"], df["close"], window=14)
    
    signals = pd.Series(0, index=df.index)
    # Buy strong upward momentum in trending market
    signals[(roc > 3) & (adx > 25)] = 1
    # Sell when momentum fades
    signals[(roc < 0) | (adx < 20)] = -1
    return signals


def _triple_confirm_strategy(df: pd.DataFrame) -> pd.Series:
    """Ultra conservative: need 3 indicators to agree"""
    rsi = ta.momentum.rsi(df["close"], window=14)
    macd = ta.trend.MACD(df["close"])
    macd_line = macd.macd()
    signal_line = macd.macd_signal()
    bb = ta.volatility.BollingerBands(df["close"])
    
    # All three must agree
    rsi_buy = rsi < 35
    macd_buy = macd_line > signal_line
    bb_buy = df["close"] < bb.bollinger_lband()
    
    rsi_sell = rsi > 65
    macd_sell = macd_line < signal_line
    bb_sell = df["close"] > bb.bollinger_hband()
    
    signals = pd.Series(0, index=df.index)
    signals[(rsi_buy) & (macd_buy) & (bb_buy)] = 1
    signals[(rsi_sell) | (macd_sell & bb_sell)] = -1
    return signals


def _simulate_trades(df: pd.DataFrame, signals: pd.Series, capital: float, fee_pct: float) -> dict:
    """Simulate trades and calculate performance"""
    cash = capital
    position = 0
    trades = []
    equity_curve = []
    
    for i in range(len(df)):
        price = df["close"].iloc[i]
        signal = signals.iloc[i]
        timestamp = str(df["timestamp"].iloc[i])
        
        # Buy signal and no position
        if signal == 1 and position == 0:
            fee = cash * (fee_pct / 100)
            position = (cash - fee) / price
            cash = 0
            trades.append({
                "type": "buy",
                "timestamp": timestamp,
                "price": price,
                "amount": position,
                "fee": fee
            })
        
        # Sell signal and have position
        elif signal == -1 and position > 0:
            gross = position * price
            fee = gross * (fee_pct / 100)
            cash = gross - fee
            trades.append({
                "type": "sell",
                "timestamp": timestamp,
                "price": price,
                "amount": position,
                "fee": fee,
                "pnl": cash - capital if len(trades) == 1 else None
            })
            position = 0
        
        # Track equity
        equity = cash + (position * price)
        equity_curve.append({
            "timestamp": timestamp,
            "equity": equity,
            "price": price
        })
    
    # Final equity
    final_equity = cash + (position * df["close"].iloc[-1])
    total_return = ((final_equity - capital) / capital) * 100
    
    # Calculate metrics
    equity_series = pd.Series([e["equity"] for e in equity_curve])
    returns = equity_series.pct_change().dropna()
    
    sharpe = (returns.mean() / returns.std()) * np.sqrt(365 * 24) if returns.std() > 0 else 0
    max_drawdown = ((equity_series.cummax() - equity_series) / equity_series.cummax()).max() * 100
    
    win_trades = len([t for t in trades if t["type"] == "sell" and trades[trades.index(t)-1]["price"] < t["price"]])
    total_trades = len([t for t in trades if t["type"] == "sell"])
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
    
    return {
        "initial_capital": capital,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(total_return, 2),
        "total_trades": len(trades),
        "win_rate": round(win_rate, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "trades": trades,
        "equity_curve": equity_curve
    }
