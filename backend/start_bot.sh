#!/bin/bash

# Navigate to the backend directory
cd /Users/codyrutscher/Desktop/outlier-projects/trading-platform/backend

# Activate virtual environment
source venv/bin/activate

# Start the trading bot
python bot/stock_bot.py >> bot/bot_startup.log 2>&1
