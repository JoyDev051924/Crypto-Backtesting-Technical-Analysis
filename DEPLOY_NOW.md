# 🚀 Deploy in 5 Minutes

## Quick Railway Deployment

### 1. Install Railway CLI (Optional - or use web)

```bash
npm install -g @railway/cli
```

### 2. Push to GitHub

```bash
# If you haven't already
git init
git add .
git commit -m "Ready for deployment"

# Create repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/trading-bot.git
git push -u origin main
```

### 3. Deploy via Railway Website (EASIEST)

1. Go to **https://railway.app**
2. Click **"Start a New Project"**
3. Click **"Deploy from GitHub repo"**
4. Select your repo
5. Add environment variables:
   ```
   ALPACA_API_KEY=AK73UB2FO5SKVSRV4X5AREZIU2
   ALPACA_API_SECRET=6y37KUH1h6eFMFK76q4pYdRsrwLjVMURd4jNTcepMM6f
   ALPACA_BASE_URL=https://api.alpaca.markets
   ```
6. Click **"Deploy"**

### 4. Get Your URL

Railway will give you a URL like:
```
https://your-bot.up.railway.app
```

Open it - your dashboard is live!

## OR Deploy via CLI (Advanced)

```bash
# Login
railway login

# Link to project
railway init

# Add environment variables
railway variables set ALPACA_API_KEY=AK73UB2FO5SKVSRV4X5AREZIU2
railway variables set ALPACA_API_SECRET=6y37KUH1h6eFMFK76q4pYdRsrwLjVMURd4jNTcepMM6f
railway variables set ALPACA_BASE_URL=https://api.alpaca.markets

# Deploy
railway up
```

## What Happens

✅ Bot starts trading automatically  
✅ Dashboard goes live at your Railway URL  
✅ Runs 24/7 even when Mac is off  
✅ Auto-restarts if it crashes  
✅ Costs $5/month  

## Access Dashboard

From anywhere:
- **Computer**: Open Railway URL in browser
- **Phone**: Open Railway URL in mobile browser
- **Tablet**: Same URL works everywhere

## Monitor Bot

In Railway dashboard:
- View real-time logs
- See resource usage
- Restart if needed
- Update environment variables

## Update Bot Later

```bash
git add .
git commit -m "Updated bot"
git push
```

Railway auto-deploys! No manual work.

## Cost

- **First $5**: FREE (Railway gives you $5 credit)
- **After that**: $5/month
- **Worth it?**: YES - for $3k live trading, $5/month is nothing

## Ready?

Follow the steps above. You'll be live in 5 minutes!

Questions? Check the full guide in `RAILWAY_DEPLOY.md`
