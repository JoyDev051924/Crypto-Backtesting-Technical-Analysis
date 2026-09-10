from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import market_data, backtest, analysis, paper_trading, signals, live_trading, bot_status

app = FastAPI(title="Algo Trading Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market_data.router, prefix="/api/market", tags=["market"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(paper_trading.router, prefix="/api/paper", tags=["paper"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(live_trading.router, prefix="/api/live", tags=["live"])
app.include_router(bot_status.router, prefix="/api/bot", tags=["bot"])

@app.get("/")
def root():
    return {"status": "running", "message": "Algo Trading Platform API"}
