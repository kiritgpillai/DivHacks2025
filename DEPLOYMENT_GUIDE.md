# 🚀 Market Mayhem - Complete Deployment Guide

This guide walks you through deploying the entire Market Mayhem application to production.

## 📋 Prerequisites

- Node.js 18+ (for frontend)
- Python 3.10+ (for backend)
- Supabase account (for database) - optional for MVP
- Render/Railway account (for backend hosting)
- Vercel account (for frontend hosting)
- API Keys:
  - Google (Gemini Pro)
  - Tavily (news fetching)
  - Opik (observability) - optional
  - LangSmith (observability) - optional

## 🎯 Quick Deploy (MVP)

### 1. Backend Deployment (Render)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Complete Market Mayhem implementation"
   git push origin main
   ```

2. **Create Render Web Service**
   - Go to [render.com](https://render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repo
   - Configure:
     - Name: `market-mayhem-backend`
     - Region: Choose closest to you
     - Branch: `main`
     - Root Directory: `backend`
     - Runtime: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - Instance Type: `Starter` (free tier)

3. **Add Environment Variables**
   In Render dashboard, go to Environment:
   ```
   GOOGLE_API_KEY=your_gemini_key
   TAVILY_API_KEY=your_tavily_key
   TICKER_UNIVERSE=AAPL,MSFT,GOOGL,AMZN,TSLA,META,NVDA,JPM,V,WMT
   ALLOWED_ORIGINS=https://your-frontend.vercel.app
   
   # Optional
   OPIK_API_KEY=your_opik_key
   LANGSMITH_API_KEY=your_langsmith_key
   DATABASE_URL=your_supabase_url
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for deployment
   - Copy the backend URL (e.g., `https://market-mayhem-backend.onrender.com`)

### 2. Frontend Deployment (Vercel)

1. **Update Environment**
   Create `frontend/.env.production`:
   ```
   NEXT_PUBLIC_API_URL=https://market-mayhem-backend.onrender.com
   NEXT_PUBLIC_WS_URL=wss://market-mayhem-backend.onrender.com
   ```

2. **Deploy to Vercel**
   ```bash
   cd frontend
   npm install -g vercel
   vercel --prod
   ```

   Or use Vercel dashboard:
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repo
   - Configure:
     - Framework: `Next.js`
     - Root Directory: `frontend`
     - Build Command: `npm run build`
     - Output Directory: `.next`

3. **Add Environment Variables**
   In Vercel dashboard, go to Settings → Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://market-mayhem-backend.onrender.com
   NEXT_PUBLIC_WS_URL=wss://market-mayhem-backend.onrender.com
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Your app is live! 🎉

### 3. Test Deployment

Visit your Vercel URL and test:
1. ✅ Home page loads
2. ✅ Portfolio builder works
3. ✅ Can create portfolio
4. ✅ Game starts and WebSocket connects
5. ✅ Can make decisions
6. ✅ Final report generates

## 🗄️ Database Setup (Optional but Recommended)

### Supabase Setup

1. **Create Project**
   - Go to [supabase.com](https://supabase.com)
   - Click "New Project"
   - Choose organization and region
   - Set database password
   - Wait for project to initialize

2. **Run Schema Migration**
   - Go to SQL Editor
   - Copy contents of `database/schema.sql`
   - Paste and run

3. **Seed Historical Cases**
   ```bash
   # Get connection string from Supabase
   # Settings → Database → Connection String (URI)
   
   export DATABASE_URL="your_supabase_connection_string"
   python database/seed_historical_cases.py
   ```

4. **Update Environment**
   Add to both Render and local .env:
   ```
   DATABASE_URL=your_supabase_connection_string
   ```

## 📊 Observability Setup (Optional)

### Opik (Comet ML)

1. Create account at [comet.com](https://www.comet.com/)
2. Get API key from Settings
3. Add to environment:
   ```
   OPIK_API_KEY=your_opik_key
   ```
4. View traces at https://www.comet.com/opik

### LangSmith

1. Create account at [smith.langchain.com](https://smith.langchain.com/)
2. Get API key from Settings
3. Add to environment:
   ```
   LANGSMITH_API_KEY=your_langsmith_key
   LANGSMITH_PROJECT=market-mayhem
   ```
4. View graphs at https://smith.langchain.com

## 🔧 Alternative Deployment Options

### Backend Options

**Railway**
```bash
railway init
railway add
railway up
```

**Fly.io**
```bash
fly launch
fly deploy
```

**AWS Lambda** (Serverless)
- Use Mangum adapter
- Deploy with AWS SAM or Serverless Framework

### Frontend Options

**Netlify**
```bash
netlify deploy --prod
```

**Cloudflare Pages**
- Connect GitHub repo
- Auto-deploy on push

### Database Options

**Neon** (Serverless Postgres)
- Similar to Supabase
- Better for serverless

**PlanetScale** (MySQL)
- Need to adapt schema from PostgreSQL

## 🧪 Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../env.example .env
# Edit .env with your API keys
python main.py
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local
npm run dev
```

### Test
```bash
# Backend test
pip install httpx rich
python test_backend.py

# Frontend test
# Open http://localhost:3000
```

## 🐛 Troubleshooting

### Backend Issues

**"Module not found" errors**
```bash
pip install -r requirements.txt --force-reinstall
```

**"WebSocket connection failed"**
- Check CORS settings in backend
- Verify `wss://` protocol for production

**"Agent timeout"**
- Gemini API can be slow (30-60s per round)
- Increase timeout in Render/Railway settings
- Consider caching common responses

### Frontend Issues

**"Failed to fetch"**
- Check API_URL is correct
- Verify CORS allows your frontend domain
- Check backend is running

**Build fails**
- Clear `.next` folder
- Delete `node_modules` and reinstall
- Check Node version (18+)

### Database Issues

**"Connection refused"**
- Check DATABASE_URL is correct
- Verify Supabase project is running
- Check IP allowlist (Supabase allows all by default)

**"Insufficient data for seeding"**
- yfinance may fail for some tickers
- Script will skip and continue
- Should still seed 150-200 cases

## 🎯 Production Checklist

- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] WebSocket connection working
- [ ] Environment variables set
- [ ] API keys configured
- [ ] CORS configured for frontend domain
- [ ] Database schema created (optional)
- [ ] Historical cases seeded (optional)
- [ ] Observability enabled (optional)
- [ ] SSL/HTTPS enabled
- [ ] Error monitoring setup
- [ ] Rate limiting configured (optional)
- [ ] Backup strategy in place

## 📈 Monitoring & Maintenance

### Health Checks
```bash
# Backend health
curl https://your-backend.onrender.com/health

# Test game flow
python test_backend.py
```

### Logs
- **Render**: View logs in dashboard
- **Vercel**: View logs in deployment
- **Opik**: View traces for errors
- **LangSmith**: Debug agent failures

### Updates
```bash
# Update backend
git push origin main
# Render auto-deploys

# Update frontend
git push origin main
# Vercel auto-deploys
```

## 💰 Cost Estimation

### Free Tier (MVP)
- **Render**: 750 hours/month free
- **Vercel**: Unlimited deployments
- **Supabase**: 500MB database free
- **Gemini**: Free tier available
- **Tavily**: Free tier (1000 requests/month)
- **Total**: $0/month for MVP

### Production Scale
- **Render**: $7-21/month (Starter to Standard)
- **Vercel**: $20/month (Pro)
- **Supabase**: $25/month (Pro)
- **Gemini**: ~$10-50/month (depends on usage)
- **Tavily**: $20-100/month
- **Total**: ~$82-$217/month

## 🎉 Success!

Once deployed, you'll have:
- ✅ Live backend API with WebSocket
- ✅ Beautiful React frontend
- ✅ 6 AI agents working together
- ✅ Real historical outcome replay
- ✅ Trash-talking Villain AI
- ✅ Behavioral profiling and coaching
- ✅ Full observability (optional)
- ✅ Persistent database (optional)

Share your deployed app! 🚀

**Backend**: https://your-backend.onrender.com
**Frontend**: https://your-frontend.vercel.app
**Docs**: https://your-backend.onrender.com/docs

---

## Need Help?

- Check `BACKEND_COMPLETE.md` for backend details
- Check `frontend/README.md` for frontend details
- Check `database/README.md` for database details
- Check `backend/infrastructure/observability/README.md` for observability details

**The project is 100% complete and ready to deploy!** 🎊
