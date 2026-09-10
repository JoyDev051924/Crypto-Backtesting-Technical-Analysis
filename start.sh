#!/bin/bash

# Set default port if not provided
export PORT=${PORT:-8080}

# Set Python path so imports work
export PYTHONPATH=/app/backend:$PYTHONPATH

# Start trading bot in background with logging
cd /app/backend
echo "Starting trading bot..."
echo "Python path: $PYTHONPATH"
echo "Current directory: $(pwd)"
echo "Checking environment variables..."
echo "ALPACA_API_KEY: ${ALPACA_API_KEY:0:10}..."
echo "ALPACA_BASE_URL: $ALPACA_BASE_URL"

# Run bot with unbuffered output
python -u bot/stock_bot.py 2>&1 | while IFS= read -r line; do echo "[BOT] $line"; done &
BOT_PID=$!
echo "Trading bot started with PID: $BOT_PID"

# Give bot a moment to start
sleep 3

# Check if bot is still running
if ps -p $BOT_PID > /dev/null; then
   echo "✅ Bot is running"
else
   echo "❌ Bot crashed on startup!"
fi

# Start dashboard API (this keeps the process alive)
echo "Starting dashboard API..."
gunicorn bot.dashboard_api:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --chdir /app/backend
