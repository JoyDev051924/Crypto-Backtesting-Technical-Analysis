from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter()

BOT_DIR = Path(__file__).parent.parent.parent / "bot"
STATE_FILE = BOT_DIR / "bot_state.json"
LOG_FILE = BOT_DIR / "bot_log.json"


@router.get("/state")
async def get_bot_state():
    """Get current bot state"""
    if not STATE_FILE.exists():
        return {"status": "not_started", "message": "Bot has not been started yet"}
    
    with open(STATE_FILE) as f:
        state = json.load(f)
    
    return {
        "status": "running",
        "cash": state["cash"],
        "positions": state["positions"],
        "total_trades": len(state["trades"]),
        "total_pnl": state["total_pnl"],
        "started_at": state.get("started_at"),
        "recent_trades": state["trades"][-10:] if state["trades"] else []
    }


@router.get("/logs")
async def get_bot_logs(limit: int = 50):
    """Get recent bot logs"""
    if not LOG_FILE.exists():
        return {"logs": []}
    
    with open(LOG_FILE) as f:
        logs = json.load(f)
    
    return {"logs": logs[-limit:]}


@router.get("/performance")
async def get_performance():
    """Get bot performance summary"""
    if not STATE_FILE.exists():
        return {"error": "Bot not started"}
    
    with open(STATE_FILE) as f:
        state = json.load(f)
    
    trades = state["trades"]
    
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_win": 0,
            "avg_loss": 0
        }
    
    sells = [t for t in trades if t["type"] == "sell"]
    wins = [t for t in sells if t.get("pnl", 0) > 0]
    losses = [t for t in sells if t.get("pnl", 0) <= 0]
    
    return {
        "total_trades": len(trades),
        "completed_trades": len(sells),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": (len(wins) / len(sells) * 100) if sells else 0,
        "total_pnl": state["total_pnl"],
        "avg_win": sum(t["pnl"] for t in wins) / len(wins) if wins else 0,
        "avg_loss": sum(t["pnl"] for t in losses) / len(losses) if losses else 0,
        "best_trade": max((t.get("pnl", 0) for t in sells), default=0),
        "worst_trade": min((t.get("pnl", 0) for t in sells), default=0),
    }


@router.post("/reset")
async def reset_bot():
    """Reset bot state"""
    initial_state = {
        "cash": 10000,
        "positions": {},
        "trades": [],
        "started_at": None,
        "total_pnl": 0
    }
    
    with open(STATE_FILE, "w") as f:
        json.dump(initial_state, f, indent=2)
    
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    
    return {"message": "Bot state reset", "state": initial_state}
