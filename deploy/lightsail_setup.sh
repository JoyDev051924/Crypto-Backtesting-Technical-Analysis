#!/bin/bash
# AWS Lightsail Setup Script for Trading Bot

echo "=========================================="
echo "Setting up Trading Bot on AWS Lightsail"
echo "=========================================="

# Update system
echo "Updating system..."
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
echo "Installing Python and dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv supervisor git

# Create bot directory
echo "Creating bot directory..."
sudo mkdir -p /opt/trading-bot/bot
cd /opt/trading-bot

# Create virtual environment
echo "Setting up Python environment..."
sudo python3 -m venv venv
sudo chown -R ubuntu:ubuntu /opt/trading-bot
source venv/bin/activate

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install requests python-dotenv alpaca-trade-api

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Upload bot files to /opt/trading-bot/"
echo "   From your local machine:"
echo "   scp -r backend/bot/ ubuntu@YOUR_IP:/opt/trading-bot/"
echo "   scp backend/.env ubuntu@YOUR_IP:/opt/trading-bot/"
echo ""
echo "2. Configure supervisor:"
echo "   sudo nano /etc/supervisor/conf.d/trading-bots.conf"
echo ""
echo "3. Start the bot:"
echo "   sudo supervisorctl reread"
echo "   sudo supervisorctl update"
echo "   sudo supervisorctl start all"
echo ""
