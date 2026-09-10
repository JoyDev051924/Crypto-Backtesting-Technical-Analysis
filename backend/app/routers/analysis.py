from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
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

class AnalysisRequest(BaseModel):
    data: List[OHLCVData]
    indicators: List[str] = ["sma_20", "sma_50", "rsi", "macd", "bollinger"]

@router.post("/indicators")
async def calculate_indicators(request: AnalysisRequest):
    """Calculate technical indicators for given OHLCV data"""
    try:
        df = pd.DataFrame([d.model_dump() for d in request.data])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        result = {"timestamp": df["timestamp"].astype(str).tolist()}
        
        # Simple Moving Averages
        if "sma_20" in request.indicators:
            result["sma_20"] = ta.trend.sma_indicator(df["close"], window=20).tolist()
        if "sma_50" in request.indicators:
            result["sma_50"] = ta.trend.sma_indicator(df["close"], window=50).tolist()
        
        # RSI
        if "rsi" in request.indicators:
            result["rsi"] = ta.momentum.rsi(df["close"], window=14).tolist()
        
        # MACD
        if "macd" in request.indicators:
            macd = ta.trend.MACD(df["close"])
            result["macd"] = macd.macd().tolist()
            result["macd_signal"] = macd.macd_signal().tolist()
            result["macd_histogram"] = macd.macd_diff().tolist()
        
        # Bollinger Bands
        if "bollinger" in request.indicators:
            bb = ta.volatility.BollingerBands(df["close"])
            result["bb_upper"] = bb.bollinger_hband().tolist()
            result["bb_middle"] = bb.bollinger_mavg().tolist()
            result["bb_lower"] = bb.bollinger_lband().tolist()
        
        # Support/Resistance levels (simple pivot points)
        if "support_resistance" in request.indicators:
            pivot = (df["high"] + df["low"] + df["close"]) / 3
            result["pivot"] = pivot.tolist()
            result["resistance_1"] = (2 * pivot - df["low"]).tolist()
            result["support_1"] = (2 * pivot - df["high"]).tolist()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/patterns")
async def detect_patterns(request: AnalysisRequest):
    """Detect common chart patterns"""
    try:
        df = pd.DataFrame([d.model_dump() for d in request.data])
        patterns = []
        
        # Golden Cross / Death Cross detection
        sma_20 = ta.trend.sma_indicator(df["close"], window=20)
        sma_50 = ta.trend.sma_indicator(df["close"], window=50)
        
        for i in range(1, len(df)):
            if pd.notna(sma_20.iloc[i]) and pd.notna(sma_50.iloc[i]):
                # Golden Cross
                if sma_20.iloc[i] > sma_50.iloc[i] and sma_20.iloc[i-1] <= sma_50.iloc[i-1]:
                    patterns.append({
                        "type": "golden_cross",
                        "index": i,
                        "timestamp": str(df["timestamp"].iloc[i]),
                        "signal": "bullish"
                    })
                # Death Cross
                elif sma_20.iloc[i] < sma_50.iloc[i] and sma_20.iloc[i-1] >= sma_50.iloc[i-1]:
                    patterns.append({
                        "type": "death_cross",
                        "index": i,
                        "timestamp": str(df["timestamp"].iloc[i]),
                        "signal": "bearish"
                    })
        
        # RSI Oversold/Overbought
        rsi = ta.momentum.rsi(df["close"], window=14)
        for i in range(1, len(df)):
            if pd.notna(rsi.iloc[i]):
                if rsi.iloc[i] < 30 and rsi.iloc[i-1] >= 30:
                    patterns.append({
                        "type": "rsi_oversold",
                        "index": i,
                        "timestamp": str(df["timestamp"].iloc[i]),
                        "signal": "bullish",
                        "value": rsi.iloc[i]
                    })
                elif rsi.iloc[i] > 70 and rsi.iloc[i-1] <= 70:
                    patterns.append({
                        "type": "rsi_overbought",
                        "index": i,
                        "timestamp": str(df["timestamp"].iloc[i]),
                        "signal": "bearish",
                        "value": rsi.iloc[i]
                    })
        
        return {"patterns": patterns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
