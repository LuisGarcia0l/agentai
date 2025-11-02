# 🚀 Quick Start Guide - AI Trading System v2.0

## ⚠️ Important: You're in the wrong directory!

Based on your terminal output, you're in `agentai_` but the refactored code is in `agentai`. 

**First, navigate to the correct directory:**
```bash
cd ../agentai  # or wherever the refactored code is located
```

## 🔧 Fix Frontend Issues (macOS ARM64)

The Rollup/Vite issue you encountered is common on Apple Silicon Macs. Here are 3 solutions:

### Option 1: Use the Fix Script (Recommended)
```bash
./fix_frontend.sh
```
Choose option 1 to fix Vite, or option 2 for Create React App.

### Option 2: Manual Fix
```bash
cd frontend
rm -rf package-lock.json node_modules
npm cache clean --force
npm install --legacy-peer-deps
npm install @rollup/rollup-darwin-arm64 --save-dev --legacy-peer-deps
```

### Option 3: Switch to Create React App (Most Stable)
```bash
cd frontend
cp package_cra.json package.json
rm -rf package-lock.json node_modules
npm install --legacy-peer-deps
npm start  # Instead of npm run dev
```

## 🐍 Start the Backend

### Option 1: Using System Starter
```bash
python3 start_system.py backend
```

### Option 2: Direct Backend Start
```bash
python3 backend_main.py
```

### Option 3: Test Backend (Simple)
```bash
python3 -c "
import uvicorn
from api.main import app
uvicorn.run(app, host='0.0.0.0', port=8000)
"
```

## ⚛️ Start the Frontend

After fixing the dependencies:

### If using Vite:
```bash
cd frontend
npm run dev
```

### If using Create React App:
```bash
cd frontend
npm start
```

## 🚀 Start Both (Full System)
```bash
python3 start_system.py both
```

## 🔗 URLs

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Health Check**: http://localhost:8000/api/health

## 📋 System Status
```bash
python3 start_system.py status
```

## 🆘 Troubleshooting

### 1. "Can't find start_system.py"
- Make sure you're in the `agentai` directory (not `agentai_`)
- The file should be in the root of the project

### 2. "structlog not found"
```bash
pip install -r requirements_backend.txt
```

### 3. Frontend won't start
- Use the `fix_frontend.sh` script
- Try switching to Create React App (more stable on ARM64)

### 4. Port already in use
```bash
# Kill processes on ports
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

## 📁 Project Structure

```
agentai/
├── backend_main.py          # Pure backend entry point
├── frontend_main.py         # Frontend starter
├── start_system.py          # System orchestrator
├── fix_frontend.sh          # Frontend fix script
├── requirements_backend.txt # Backend dependencies
├── frontend/
│   ├── package.json        # Vite setup
│   └── package_cra.json    # Create React App setup
└── api/
    └── main.py             # FastAPI endpoints
```

## 🎯 Next Steps

1. **Fix your directory**: `cd ../agentai`
2. **Fix frontend**: `./fix_frontend.sh`
3. **Start backend**: `python3 start_system.py backend`
4. **Start frontend**: `cd frontend && npm run dev`
5. **Access the app**: http://localhost:3000

The system is now properly separated with Python backend and React frontend! 🎉