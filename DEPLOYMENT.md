# Deployment Guide

This app has two deployable parts:

- `frontend`: Vite static site.
- `backend`: Express API that starts a Python bridge for the ML model.

## Backend Environment Variables

Set these on the backend host:

```text
PORT=5050
PYTHON_PATH=/app/.venv/bin/python
MODEL_DIR=/app/artifacts/bert_fake_news_large
DATA_PATH=/app/data/synthetic_fake_news_large.csv
MONGODB_URI=
CLIENT_ORIGIN=https://your-frontend-domain
```

`MONGODB_URI` is optional. Leave it empty if you do not need saved history.

## Backend Deployment

Use a Docker-capable host such as Render, Railway, Fly.io, or a VPS.

For Render:

```text
New Web Service
Environment: Docker
Root Directory: repo root
Dockerfile Path: ./Dockerfile
```

After deployment, open:

```text
https://your-backend-domain/api/health
```

## Frontend Deployment

Use Vercel or Netlify.

For Vercel:

```text
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
```

Set this frontend environment variable:

```text
VITE_API_BASE_URL=https://your-backend-domain
```

Then redeploy the frontend.

## Git LFS

The model file is large, so Git LFS must be enabled before pushing artifacts:

```powershell
git lfs install
git lfs track "artifacts/**/*.safetensors"
git add .gitattributes artifacts
git commit -m "Add model artifacts"
```
