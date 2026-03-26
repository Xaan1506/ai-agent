# 🚀 Deployment Guide - OpenClaw Research Agent

This application is designed to be deployed as a single unit. The FastAPI server handles both the **Autonomous Research Agent API** and serves the **React Production Build**.

## 1. Prerequisites
- Python 3.9+
- Node.js & npm
- Hugging Face API Key (`HF_API_KEY`)

## 2. Environment Setup
Create a `.env` file in the root directory:
```env
HF_API_KEY=your_huggingface_token_here
```

## 3. One-Step Deployment (Linux/macOS)
Run the following script to build and start the server:
```bash
bash deploy.sh
```

## 4. Manual Deployment

### Step A: Build the Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### Step B: Start the Backend
```bash
# In the root directory
source venv/bin/activate
pip install -r requirements.txt
python3 server.py
```

Now your application is live at **http://localhost:8000**!

## 5. Deployment Checklist
- [ ] Set `HF_API_KEY` in environment.
- [ ] Ensure `frontend/dist` exists (run `npm run build`).
- [ ] Port `8000` is open.
