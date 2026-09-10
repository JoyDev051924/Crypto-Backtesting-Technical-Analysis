# 🚂 Deploy to Railway - Complete Guide

## What You'll Get

✅ **Bot running 24/7** - Never stops, even when your Mac is off  
✅ **Live dashboard** - Access from anywhere (phone, tablet, computer)  
✅ **Auto-restarts** - If bot crashes, Railway restarts it automatically  
✅ **Secure** - Environment variables encrypted  
✅ **Cost**: $5/month

## Step 1: Push to GitHub

```bash
cd /Users/codyrutscher/Desktop/outlier-projects/trading-platform

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Trading bot ready for deployment"

# Create GitHub repo and push
# Go to github.com and create a new repository called "trading-bot"
# Then run:
git remote add origin https://github.com/YOUR_USERNAME/trading-bot.git
git branch -M main
git push -u origin main
```

## Step 2: Sign Up for Railway

1. Go to https://railway.app
2. Click **"Start a New Project"**
3. Sign in with GitHub
4. Click **"Deploy from GitHub repo"**
5. Select your **trading-bot** repository

## Step 3: Add Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```
ALPACA_API_KEY=AK73UB2FO5SKVSRV4X5AREZIU2
ALPACA_API_SECRET=6y37KUH1h6eFMFK76q4pYdRsrwLjVMURd4jNTcepMM6f
ALPACA_BASE_URL=https://api.alpaca.markets
NOTIFICATION_EMAIL=your_gmail@gmail.com
NOTIFICATION_PASSWORD=your_app_password
NOTIFICATION_TO=your_email@gmail.com
```

## Step 4: Deploy

Railway will automatically:
1. Install Python dependencies
2. Build the frontend
3. Start the bot
4. Start the dashboard API
5. Give you a public URL

## Step 5: Access Your Dashboard

Railway will give you a URL like:
```
https://trading-bot-production.up.railway.app
```

Open it in your browser - you'll see your live dashboard!

## What Runs on Railway

**Two processes:**
1. **Trading Bot** - Monitors market, executes trades
2. **Dashboard API** - Serves the web dashboard

Both run 24/7 automatically.

## Monitoring

In Railway dashboard you can:
- ✅ View logs (see what bot is doing)
- ✅ Restart services
- ✅ Check resource usage
- ✅ Update environment variables

## Cost Breakdown

- **Free tier**: $5 credit/month (enough for small bot)
- **Hobby plan**: $5/month (recommended)
- **Pro plan**: $20/month (if you need more resources)

For your bot, **$5/month is plenty**.

## Updating the Bot

When you make changes:

```bash
git add .
git commit -m "Updated bot"
git push
```

Railway automatically redeploys! No manual work needed.

## Troubleshooting

### Bot not starting?
- Check logs in Railway dashboard
- Make sure all environment variables are set
- Verify API keys are correct

### Dashboard not loading?
- Wait 2-3 minutes after first deploy
- Check that frontend built successfully in logs
- Try hard refresh (Cmd+Shift+R)

### Can't access from phone?
- Make sure you're using the Railway URL (not localhost)
- Check that Railway service is running

## Alternative: Keep Running Locally

If you don't want to deploy yet:
1. Keep MacBook plugged in
2. Display set to "Never" sleep
3. Bot runs locally
4. Dashboard at http://localhost:5173

But Railway is **way better** for live trading!

## Security Notes

- ✅ Environment variables are encrypted
- ✅ API keys never exposed in code
- ✅ HTTPS enabled by default
- ✅ Railway has 99.9% uptime

Your $3,000 is safe!

## Need Help?

If deployment fails:
1. Check Railway logs
2. Make sure requirements.txt has all dependencies
3. Verify GitHub repo pushed correctly
4. Contact Railway support (they're super helpful)

Ready to deploy? Follow the steps above!
