from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Initialize Kraken with API keys from environment
def get_exchange():
    api_key = os.getenv("KRAKEN_API_KEY")
    api_secret = os.getenv("KRAKEN_API_SECRET")
    
    if not api_key or not api_secret:
        raise HTTPException(500, "API keys not configured. Set KRAKEN_API_KEY and KRAKEN_API_SECRET in .env")
    
    return ccxt.kraken({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
    })


class OrderRequest(BaseModel):
    symbol: str  # e.g., "BTC/USD"
    side: Literal["buy", "sell"]
    amount: float  # Amount in crypto (e.g., 0.001 BTC)
    order_type: Literal["market", "limit"] = "market"
    price: Optional[float] = None  # Required for limit orders


@router.get("/balance")
async def get_balance():
    """Get account balances"""
    try:
        exchange = get_exchange()
        balance = exchange.fetch_balance()
        
        # Filter to non-zero balances
        non_zero = {k: v for k, v in balance["total"].items() if v > 0}
        
        return {
            "balances": non_zero,
            "usd_available": balance["free"].get("USD", 0),
            "usd_total": balance["total"].get("USD", 0),
        }
    except ccxt.AuthenticationError:
        raise HTTPException(401, "Invalid API keys")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/open_orders")
async def get_open_orders(symbol: Optional[str] = None):
    """Get open orders"""
    try:
        exchange = get_exchange()
        orders = exchange.fetch_open_orders(symbol)
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/order")
async def place_order(order: OrderRequest):
    """Place a live order - USE WITH CAUTION"""
    try:
        exchange = get_exchange()
        
        if order.order_type == "market":
            result = exchange.create_market_order(
                symbol=order.symbol,
                side=order.side,
                amount=order.amount
            )
        else:
            if not order.price:
                raise HTTPException(400, "Price required for limit orders")
            result = exchange.create_limit_order(
                symbol=order.symbol,
                side=order.side,
                amount=order.amount,
                price=order.price
            )
        
        return {
            "success": True,
            "order_id": result["id"],
            "symbol": result["symbol"],
            "side": result["side"],
            "amount": result["amount"],
            "price": result.get("price"),
            "status": result["status"],
            "raw": result
        }
    except ccxt.InsufficientFunds:
        raise HTTPException(400, "Insufficient funds")
    except ccxt.InvalidOrder as e:
        raise HTTPException(400, f"Invalid order: {str(e)}")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/order/{order_id}")
async def cancel_order(order_id: str, symbol: str):
    """Cancel an open order"""
    try:
        exchange = get_exchange()
        result = exchange.cancel_order(order_id, symbol)
        return {"success": True, "cancelled": result}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/trades")
async def get_recent_trades(symbol: str = "BTC/USD", limit: int = 20):
    """Get recent trades for account"""
    try:
        exchange = get_exchange()
        trades = exchange.fetch_my_trades(symbol, limit=limit)
        return {"trades": trades}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str):
    """Get current ticker for a symbol"""
    try:
        exchange = get_exchange()
        symbol = symbol.replace("-", "/")
        ticker = exchange.fetch_ticker(symbol)
        return {
            "symbol": symbol,
            "bid": ticker["bid"],
            "ask": ticker["ask"],
            "last": ticker["last"],
            "spread_pct": ((ticker["ask"] - ticker["bid"]) / ticker["bid"]) * 100 if ticker["bid"] else 0
        }
    except Exception as e:
        raise HTTPException(500, str(e))
