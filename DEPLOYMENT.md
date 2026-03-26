# OpenClaw Deployment (Best Option)

The best fit for this project is **Render (single web service)** because:
- Backend is Python/FastAPI with SSE streaming.
- Frontend is static Vite build already served by `server.py`.
- You need one URL for both API + UI, which avoids CORS and API URL issues.

## 1) Push code to GitHub

Render deploys from a Git repository. Push this project first.

## 2) Create Render Web Service

- In Render, choose **New +** -> **Blueprint** (recommended) or **Web Service**.
- Select your GitHub repository.
- If using Blueprint, `render.yaml` will auto-configure build/start commands.

## 3) Set required environment variable

Add this in Render service environment:
- `HF_API_KEY` = your Hugging Face API key

## 4) Deploy

Render will:
- Install Python dependencies
- Build frontend (`frontend/dist`)
- Install Playwright Chromium
- Run `uvicorn server:app --host 0.0.0.0 --port $PORT`

After deploy, open your Render URL. The chat app and API are served from the same domain.

## Notes

- If Render build fails on Playwright browser install, keep the same setup: app now includes HTTP fallback when Chromium is unavailable.
- For separate frontend hosting (e.g. Vercel), set `VITE_API_BASE_URL` to your backend URL.
