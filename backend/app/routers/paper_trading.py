from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime
import json
import os

router = APIRouter()

# Simple file-based storage for paper trading state
PAPER_STATE_FILE = "paper_trading_state.json"

class PaperState(BaseModel):
    cash: float = 10000
    positions: dict = {}  # {symbol: {amount, entry_price, entry_time}}
    trades: List[dict] = []
    pnl: float = 0

class OrderRequest(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    amount_usd: Optional[float] = None  # For buy orders
    amount_crypto: Optional[float] = None  # For sell orders (sell all if None)

def load_state() -> dict:
    if os.path.exists(PAPER_STATE_FILE):
        with open(PAPER_STATE_FILE, "r") as f:
            return json.load(f)
    return {"cash": 10000, "positions": {}, "trades": [], "pnl": 0}

def save_state(state: dict):
    with open(PAPER_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)

@router.get("/state")
async def get_state():
    """Get current paper trading state"""
    return load_state()

@router.post("/reset")
async def reset_state(initial_capital: float = 10000):
    """Reset paper trading account"""
    state = {"cash": initial_capital, "positions": {}, "trades": [], "pnl": 0}
    save_state(state)
    return {"message": "Paper trading reset", "state": state}

@router.post("/order")
async def place_order(order: OrderRequest, current_price: float):
    """Place a paper trade order"""
    state = load_state()
    now = datetime.now().isoformat()
    
    if order.side == "buy":
        if order.amount_usd is None:
            raise HTTPException(400, "amount_usd required for buy orders")
        if order.amount_usd > state["cash"]:
            raise HTTPException(400, f"Insufficient cash. Have ${state['cash']:.2f}")
        
        # Calculate fees (0.1%)
        fee = order.amount_usd * 0.001
        net_amount = order.amount_usd - fee
        crypto_amount = net_amount / current_price
        
        # Update state
        state["cash"] -= order.amount_usd
        if order.symbol in state["positions"]:
            # Average into position
            existing = state["positions"][order.symbol]
            total_amount = existing["amount"] + crypto_amount
            avg_price = ((existing["amount"] * existing["entry_price"]) + (crypto_amount * current_price)) / total_amount
            state["positions"][order.symbol] = {
                "amount": total_amount,
                "entry_price": avg_price,
                "entry_time": existing["entry_time"]
            }
        else:
            state["positions"][order.symbol] = {
                "amount": crypto_amount,
                "entry_price": current_price,
                "entry_time": now
            }
        
        trade = {
            "type": "buy",
            "symbol": order.symbol,
            "price": current_price,
            "amount": crypto_amount,
            "usd_value": order.amount_usd,
            "fee": fee,
            "timestamp": now
        }
        state["trades"].append(trade)
        save_state(state)
        
        return {"message": "Buy order executed", "trade": trade, "state": state}
    
    elif order.side == "sell":
        if order.symbol not in state["positions"]:
            raise HTTPException(400, f"No position in {order.symbol}")
        
        position = state["positions"][order.symbol]
        sell_amount = order.amount_crypto or position["amount"]
        
        if sell_amount > position["amount"]:
            raise HTTPException(400, f"Insufficient {order.symbol}. Have {position['amount']}")
        
        # Calculate sale
        gross = sell_amount * current_price
        fee = gross * 0.001
        net = gross - fee
        
        # Calculate PnL
        cost_basis = sell_amount * position["entry_price"]
        trade_pnl = net - cost_basis
        
        # Update state
        state["cash"] += net
        state["pnl"] += trade_pnl
        
        if sell_amount >= position["amount"]:
            del state["positions"][order.symbol]
        else:
            state["positions"][order.symbol]["amount"] -= sell_amount
        
        trade = {
            "type": "sell",
            "symbol": order.symbol,
            "price": current_price,
            "amount": sell_amount,
            "usd_value": net,
            "fee": fee,
            "pnl": trade_pnl,
            "timestamp": now
        }
        state["trades"].append(trade)
        save_state(state)
        
        return {"message": "Sell order executed", "trade": trade, "state": state}

@router.get("/portfolio")
async def get_portfolio():
    """Get portfolio with current values (need to call with prices)"""
    state = load_state()
    return {
        "cash": state["cash"],
        "positions": state["positions"],
        "total_trades": len(state["trades"]),
        "realized_pnl": state["pnl"]
    }
