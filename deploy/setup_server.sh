#!/bin/bash
# DigitalOcean Server Setup Script for Stock Trading Bot

echo "=========================================="
echo "Setting up Stock Trading Bot Server"
echo "=========================================="

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Python and dependencies
echo "Installing Python..."
apt-get install -y python3 python3-pip python3-venv git

# Install supervisor (keeps bot running)
echo "Installing supervisor..."
apt-get install -y supervisor

# Create bot directory
echo "Creating bot directory..."
mkdir -p /opt/trading-bot
cd /opt/trading-bot

# Create virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install requests python-dotenv alpaca-trade-api

# Create bot directory structure
mkdir -p bot

echo ""
echo "=========================================="
echo "Server setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Upload your bot files to /opt/trading-bot/"
echo "2. Create .env file with your API keys"
echo "3. Configure supervisor to run the bot"
echo ""
