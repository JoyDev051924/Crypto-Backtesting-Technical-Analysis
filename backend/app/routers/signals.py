from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import pandas as pd
import numpy as np
import ta

router = APIRouter()

class OHLCVData(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class SignalRequest(BaseModel):
    symbol: str
    data: List[OHLCVData]
    strategy: str = "volume_breakout"

@router.post("/check")
async def check_signals(request: SignalRequest):
    """Check if there's a current buy/sell signal for a strategy"""
    df = pd.DataFrame([d.model_dump() for d in request.data])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    current_price = df["close"].iloc[-1]
    signal = "hold"
    confidence = 0
    reasons = []
    
    if request.strategy == "volume_breakout":
        # Volume spike
        vol_sma = df["volume"].rolling(20).mean()
        vol_spike = df["volume"].iloc[-1] > (vol_sma.iloc[-1] * 1.5)
        
        # Price breaking above recent high
        high_20 = df["high"].rolling(20).max().shift(1).iloc[-1]
        breakout = current_price > high_20
        
        # RSI
        rsi = ta.momentum.rsi(df["close"], window=14).iloc[-1]
        
        if vol_spike and breakout and rsi < 70:
            signal = "buy"
            confidence = 80
            reasons = ["Volume spike detected", "Breaking above 20-period high", f"RSI at {rsi:.1f} (not overbought)"]
        elif rsi > 75:
            signal = "sell"
            confidence = 70
            reasons = [f"RSI overbought at {rsi:.1f}"]
        else:
            reasons = [f"Volume: {'spike' if vol_spike else 'normal'}", f"Price vs high: {'breakout' if breakout else 'below'}", f"RSI: {rsi:.1f}"]
    
    elif request.strategy == "support_bounce":
        low_20 = df["low"].rolling(20).min().iloc[-1]
        near_support = current_price < (low_20 * 1.02)
        rsi = ta.momentum.rsi(df["close"], window=14).iloc[-1]
        bullish = df["close"].iloc[-1] > df["open"].iloc[-1]
        
        if near_support and rsi < 35 and bullish:
            signal = "buy"
            confidence = 75
            reasons = ["Near 20-period support", f"RSI oversold at {rsi:.1f}", "Bullish candle forming"]
        elif rsi > 65:
            signal = "sell"
            confidence = 65
            reasons = [f"RSI at {rsi:.1f} - take profit zone"]
        else:
            reasons = [f"Support: ${low_20:.2f}", f"RSI: {rsi:.1f}", f"Candle: {'bullish' if bullish else 'bearish'}"]
    
    elif request.strategy == "mean_reversion":
        sma_20 = ta.trend.sma_indicator(df["close"], window=20).iloc[-1]
        std_20 = df["close"].rolling(20).std().iloc[-1]
        z_score = (current_price - sma_20) / std_20
        
        if z_score < -2:
            signal = "buy"
            confidence = 70
            reasons = [f"Price {abs(z_score):.1f} std devs below mean", "Mean reversion expected"]
        elif z_score > 0.5:
            signal = "sell"
            confidence = 60
            reasons = ["Price returned to mean", "Take profit"]
        else:
            reasons = [f"Z-score: {z_score:.2f}", f"Mean: ${sma_20:.2f}"]
    
    return {
        "symbol": request.symbol,
        "strategy": request.strategy,
        "signal": signal,
        "confidence": confidence,
        "current_price": current_price,
        "reasons": reasons,
        "timestamp": str(df["timestamp"].iloc[-1])
    }

@router.post("/scan_all")
async def scan_all_signals(symbols_data: List[dict]):
    """Scan multiple symbols for signals"""
    strategies = ["volume_breakout", "support_bounce", "mean_reversion"]
    signals = []
    
    for sym_data in symbols_data:
        symbol = sym_data["symbol"]
        df = pd.DataFrame(sym_data["data"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        for strategy in strategies:
            request = SignalRequest(symbol=symbol, data=[OHLCVData(**d) for d in sym_data["data"]], strategy=strategy)
            # Inline signal check
            result = await check_signals(request)
            
            if result["signal"] != "hold" and result["confidence"] >= 65:
                signals.append(result)
    
    # Sort by confidence
    signals.sort(key=lambda x: x["confidence"], reverse=True)
    
    return {"signals": signals}
