#!/bin/bash

# --- OpenClaw Deployment Script ---

echo "🚀 Starting OpenClaw Deployment..."

# 1. Build Frontend
echo "📦 Building Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
  npm install
fi
npm run build
if [ $? -ne 0 ]; then
  echo "❌ Frontend build failed!"
  exit 1
fi
cd ..

# 2. Setup Backend (Choosing Stable Python)
echo "🐍 Setting up Backend..."
if [ ! -d "venv" ]; then
  # Prefer Python 3.12 or 3.11 for stability (avoiding experimental 3.14)
  if [ -x "/opt/homebrew/bin/python3.12" ]; then
    echo "Using Python 3.12 (Stable)"
    /opt/homebrew/bin/python3.12 -m venv venv
  elif [ -x "/opt/homebrew/bin/python3.11" ]; then
    echo "Using Python 3.11 (Stable)"
    /opt/homebrew/bin/python3.11 -m venv venv
  else
    echo "Warning: No stable Homebrew Python found. Using default."
    python3 -m venv venv
  fi
fi

# Ensure virual environment is used
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
  echo "❌ Pip install failed! If you are on an experimental Python (like 3.14), manually run: /opt/homebrew/bin/python3.12 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# 3. Final Verification
if [ ! -d "frontend/dist" ]; then
  echo "❌ Error: frontend/dist not found. Build may have failed silently."
  exit 1
fi

echo "✅ Build Successful!"
echo "📡 Starting server on http://localhost:8000..."
python3 server.py
