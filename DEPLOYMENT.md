# 🚀 Deployment Guide - Transcript AI

## Overview

This project is a **monorepo** with:
- **Frontend**: Vue 3 + Vite (deployed on Cloudflare Pages)
- **Backend**: FastAPI + Python (separate hosting)

---

## Quick Start - Cloudflare Pages (Frontend Only)

### Step 1: Prepare GitHub Repository

```bash
# Ensure all files are committed
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### Step 2: Connect to Cloudflare Pages

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click **Pages** → **Create a project** → **Connect to Git**
3. Authorize GitHub
4. Select your repository
5. Configure build settings:

| Setting | Value |
|---------|-------|
| **Framework preset** | Vue (Vite) |
| **Build command** | `npm run build` |
| **Build output directory** | `frontend/dist` |
| **Root directory** | Leave empty or `/` |
| **Environment variables** | (see below) |

### Step 3: Add Environment Variables

In Cloudflare Pages settings, add:

```
VITE_API_URL=https://your-backend-api.com
```

### Step 4: Deploy

Click **Save and Deploy** → Cloudflare will build and deploy automatically!

For future deployments, just push to `main` branch - it's automatic.

---

## Backend Deployment Options

### Option A: Railway.app (Recommended for Beginners)

1. Sign up at [Railway.app](https://railway.app/)
2. Create new project → Deploy from GitHub
3. Select your repository
4. Configure variables in Railway dashboard:
   - `CLOUDFLARE_ACCOUNT_ID`
   - `CLOUDFLARE_API_TOKEN`
   - Any other `.env` variables

5. Railway gives you a public URL automatically
6. Use that URL in frontend's `VITE_API_URL`

### Option B: Render.com

1. Sign up at [Render.com](https://render.com)
2. Create new Web Service → Connect GitHub repo
3. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - **Root Directory**: `backend`

4. Add environment variables in Render dashboard

### Option C: Docker + Self-Hosted

```bash
# Build Docker image
docker build -t myapp:latest ./backend

# Deploy to your server
# (depends on your infrastructure)
```

### Option D: PythonAnywhere

1. Sign up at [PythonAnywhere.com](https://www.pythonanywhere.com)
2. Upload your code
3. Configure FastAPI app
4. Get public URL

---

## GitHub Actions CI/CD (Optional)

We've included a GitHub Actions workflow (`.github/workflows/deploy.yml`) for automatic deployment.

### Setup GitHub Actions

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Add these secrets:

```
CLOUDFLARE_ACCOUNT_ID     = your account id
CLOUDFLARE_API_TOKEN      = your api token
CLOUDFLARE_ZONE_ID        = your zone id (optional)
```

4. On every push to `main`, GitHub Actions will:
   - Install dependencies
   - Build frontend
   - Deploy to Cloudflare Pages

---

## Environment Variables Reference

### `.env` file for local development

```env
# Cloudflare Configuration
CLOUDFLARE_ACCOUNT_ID=xxxxxxxxxxxxxxxxxxxx
CLOUDFLARE_API_TOKEN=xxxxxxxxxxxxxxxxxxxx
CLOUDFLARE_ZONE_ID=xxxxxxxxxxxxxxxxxxxx (optional)

# Backend Configuration  
BACKEND_URL=http://localhost:8000
BACKEND_PORT=8000

# Frontend Configuration
VITE_API_URL=http://localhost:8000
```

### Cloudflare Pages Environment Variables

Set in Pages → Settings → Environment variables:

```
VITE_API_URL = https://your-backend-api.com
```

---

## Troubleshooting

### "npm error ENOENT: no such file or directory"
- ✅ **Fixed!** We added root `package.json` with proper build command
- This redirects to `frontend/npm run build`

### "API Not Found" in browser
- Check your `VITE_API_URL` environment variable
- Ensure backend is running and accessible
- Check CORS settings in backend

### "Cloudflare API Error"
- Verify `CLOUDFLARE_API_TOKEN` is correct
- Token must have "Workers AI" permission
- Check token hasn't expired

### Build takes too long
- Frontend build usually takes 1-2 minutes
- This is normal with Vite

---

## Project Structure

```
TranscriptNis/
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       └── App.vue
├── backend/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── app/
│       ├── main.py
│       └── services/
├── package.json          ← ROOT (new)
├── wrangler.toml         ← Cloudflare config (new)
├── .github/
│   └── workflows/
│       └── deploy.yml    ← GitHub Actions (new)
└── .env.example
```

---

## Verification

After deployment, test your live site:

```bash
# Frontend should load
curl https://your-site.pages.dev

# Backend API should respond (if deployed)
curl https://your-backend-api.com/health
```

---

## Support

- 📖 Cloudflare Pages Docs: https://developers.cloudflare.com/pages/
- 🔧 Railway.app Docs: https://docs.railway.app/
- 🐳 Docker Docs: https://docs.docker.com/
- ⚡ Vite Docs: https://vitejs.dev/
- 🚀 FastAPI Docs: https://fastapi.tiangolo.com/

---

**Happy deploying! 🎉**
