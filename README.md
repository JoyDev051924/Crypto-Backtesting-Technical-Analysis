# 📈 Algo Trading Platform

A full-stack cryptocurrency algorithmic trading platform for **real-time market analysis, technical indicators, strategy backtesting, and trading-pattern detection**.

The platform combines a **Python backend** with a **React frontend** and integrates live public market data from Binance.

## ✨ Features

### 📊 Real-Time Market Data

* Fetch live cryptocurrency market data from Binance.
* Browse available trading pairs.
* Retrieve OHLCV candlestick data for technical analysis.
* No API key required for public market data.

### 🧪 Backtesting Engine

Run historical simulations against multiple built-in trading strategies:

* **SMA Crossover**
* **RSI**
* **MACD**
* **Bollinger Bands Bounce**

The backtesting engine evaluates strategy performance using historical market data and generates performance metrics for comparison.

### 🔍 Pattern Detection

Automatically identify common market signals and patterns, including:

* Golden Cross
* Death Cross
* RSI-based signals

### 📐 Technical Analysis

Calculate commonly used technical indicators:

* Simple Moving Average (SMA)
* Relative Strength Index (RSI)
* Moving Average Convergence Divergence (MACD)
* Bollinger Bands

### 📈 Performance Analytics

Evaluate strategy results using metrics such as:

* Sharpe Ratio
* Maximum Drawdown
* Win Rate
* Trade performance

## 🏗️ Architecture

```text
┌─────────────────────┐
│    React Frontend   │
│                     │
│  Charts & Analysis  │
│  Strategy Controls  │
└──────────┬──────────┘
           │ REST API
           ▼
┌─────────────────────┐
│   Python Backend    │
│                     │
│ Market Data         │
│ Technical Analysis  │
│ Pattern Detection   │
│ Backtesting Engine  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│       Binance       │
│   Public Market API │
└─────────────────────┘
```

## 🛠️ Tech Stack

**Frontend**

* React
* JavaScript / TypeScript
* Charting and market-data visualization

**Backend**

* Python
* FastAPI
* Uvicorn

**Market Data**

* Binance Public API

**Trading Analysis**

* SMA
* RSI
* MACD
* Bollinger Bands
* Pattern detection
* Backtesting

## 🚀 Quick Start

### Backend

```bash
cd backend

python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
# venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

The backend will be available at:

`http://localhost:8000`

### Frontend

In a separate terminal:

```bash
cd frontend

npm install
npm run dev
```

The frontend will be available at:

`http://localhost:5173`

## 🔌 API Endpoints

| Method | Endpoint                     | Description                    |
| ------ | ---------------------------- | ------------------------------ |
| `GET`  | `/api/market/symbols`        | List available trading pairs   |
| `GET`  | `/api/market/ohlcv/{symbol}` | Retrieve OHLCV market data     |
| `POST` | `/api/backtest/run`          | Run a strategy backtest        |
| `POST` | `/api/analysis/indicators`   | Calculate technical indicators |
| `POST` | `/api/analysis/patterns`     | Detect market patterns         |

## 🔄 Typical Workflow

```text
Select Trading Pair
        ↓
Retrieve Historical Market Data
        ↓
Calculate Technical Indicators
        ↓
Detect Patterns / Signals
        ↓
Select Trading Strategy
        ↓
Run Backtest
        ↓
Evaluate Performance
        ↓
Compare Results
```

## ⚠️ Disclaimer

This project is intended for **educational and research purposes only**.

Backtested or historical performance does not guarantee future results. This software does not constitute financial or investment advice. Never trade with money you cannot afford to lose.
