from fastapi import APIRouter, HTTPException
from typing import Optional
import ccxt
import pandas as pd
from datetime import datetime, timedelta

router = APIRouter()

# Initialize exchange - using Kraken (works globally, no restrictions)
exchange = ccxt.kraken({"enableRateLimit": True})

# Common crypto pairs available on Kraken
SUPPORTED_SYMBOLS = [
    "BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD", "ADA/USD",
    "DOGE/USD", "DOT/USD", "LINK/USD", "AVAX/USD", "MATIC/USD",
    "LTC/USD", "UNI/USD", "ATOM/USD", "XLM/USD", "ALGO/USD",
    "BTC/EUR", "ETH/EUR", "ETH/BTC"
]

@router.get("/symbols")
async def get_symbols():
    """Get available trading symbols"""
    return {"symbols": SUPPORTED_SYMBOLS}

@router.get("/ohlcv/{symbol}")
async def get_ohlcv(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 500
):
    """Get OHLCV candlestick data"""
    try:
        symbol = symbol.replace("-", "/")
        
        # Kraken timeframe mapping
        tf_map = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
        kraken_tf = tf_map.get(timeframe, "1h")
        
        ohlcv = exchange.fetch_ohlcv(symbol, kraken_tf, limit=limit)
        
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": df.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/price/{symbol}")
async def get_current_price(symbol: str):
    """Get current price for a symbol"""
    try:
        symbol = symbol.replace("-", "/")
        ticker = exchange.fetch_ticker(symbol)
        return {
            "symbol": symbol,
            "price": ticker["last"],
            "change_24h": ticker.get("percentage", 0),
            "volume_24h": ticker.get("quoteVolume", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan")
async def scan_all_symbols(timeframe: str = "4h", limit: int = 500):
    """Scan all symbols and return their data for batch analysis"""
    results = []
    scan_symbols = ["BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD", "LINK/USD", "AVAX/USD", "DOT/USD", "LTC/USD"]
    
    tf_map = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
    kraken_tf = tf_map.get(timeframe, "4h")
    
    for symbol in scan_symbols:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, kraken_tf, limit=limit)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            
            results.append({
                "symbol": symbol,
                "data": df.to_dict(orient="records")
            })
        except Exception:
            continue
    
    return {"symbols": results}
