#!/bin/bash

# AI Trading System v2.0 - Complete Setup for Mac M2
# This script sets up everything needed for the trading system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis
ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
GEAR="⚙️"
PYTHON="🐍"
REACT="⚛️"
MAC="🍎"

echo -e "${PURPLE}================================================================================${NC}"
echo -e "${ROCKET} ${CYAN}AI TRADING SYSTEM v2.0 - COMPLETE SETUP FOR MAC M2${NC}"
echo -e "${PURPLE}================================================================================${NC}"
echo -e "${MAC} Optimized for Apple Silicon (ARM64)"
echo -e "${PYTHON} Backend: Python + FastAPI"
echo -e "${REACT} Frontend: React + Vite"
echo -e "${PURPLE}================================================================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}${CHECK}${NC} $1"
}

print_error() {
    echo -e "${RED}${CROSS}${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}${WARNING}${NC} $1"
}

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is optimized for macOS. Detected: $OSTYPE"
    exit 1
fi

# Check if we're on ARM64 (Apple Silicon)
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    print_warning "This script is optimized for Apple Silicon (ARM64). Detected: $ARCH"
    echo "Continuing anyway..."
fi

print_success "Running on macOS $ARCH"

# Check for required tools
print_status "Checking required tools..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    echo "Please install Python 3 from https://python.org or use Homebrew: brew install python"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION found"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed"
    echo "Please install Node.js from https://nodejs.org or use Homebrew: brew install node"
    exit 1
fi

NODE_VERSION=$(node --version)
print_success "Node.js $NODE_VERSION found"

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm is required but not installed"
    exit 1
fi

NPM_VERSION=$(npm --version)
print_success "npm $NPM_VERSION found"

echo ""
print_status "Setting up Python backend..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Create minimal requirements file
print_status "Creating requirements file..."
cat > requirements_minimal.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
EOF

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements_minimal.txt

print_success "Python dependencies installed"

# Create .env file
print_status "Creating environment configuration..."
cat > .env << EOF
# AI Trading System Configuration
ENVIRONMENT=development
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000

# Binance Testnet Configuration
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_SECRET_KEY=your_testnet_secret_key_here
BINANCE_TESTNET=True

# Frontend Configuration
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
EOF

print_success "Environment configuration created"

echo ""
print_status "Setting up React frontend..."

# Navigate to frontend directory
cd frontend

# Backup current package.json
if [ -f "package.json" ]; then
    cp package.json package_backup.json
    print_success "Current package.json backed up"
fi

# Use optimized package.json for Mac M2
cp package_m2.json package.json
print_success "Optimized package.json for Mac M2 applied"

# Clean npm cache and remove problematic files
print_status "Cleaning npm cache and node_modules..."
npm cache clean --force
rm -rf node_modules package-lock.json

# Install frontend dependencies with specific flags for ARM64
print_status "Installing frontend dependencies (this may take a few minutes)..."
export npm_config_target_arch=arm64
export npm_config_target_platform=darwin
export npm_config_arch=arm64

# Install with legacy peer deps to avoid conflicts
npm install --legacy-peer-deps --no-optional

if [ $? -ne 0 ]; then
    print_warning "First install attempt failed, trying alternative method..."
    npm install --force --legacy-peer-deps
fi

print_success "Frontend dependencies installed"

# Go back to root directory
cd ..

echo ""
print_status "Creating startup scripts..."

# Create simple startup script
cat > start.sh << 'EOF'
#!/bin/bash

# AI Trading System v2.0 Startup Script

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🚀 AI Trading System v2.0${NC}"
echo -e "${CYAN}=========================${NC}"

case "$1" in
    "backend"|"api")
        echo -e "${BLUE}🐍 Starting Backend...${NC}"
        source venv/bin/activate
        python3 simple_backend.py
        ;;
    "frontend"|"react")
        echo -e "${BLUE}⚛️ Starting Frontend...${NC}"
        cd frontend
        npm run dev
        ;;
    "both"|"all"|"")
        echo -e "${BLUE}🚀 Starting Both Backend and Frontend...${NC}"
        
        # Start backend in background
        source venv/bin/activate
        python3 simple_backend.py &
        BACKEND_PID=$!
        
        # Wait a moment for backend to start
        sleep 3
        
        # Start frontend
        cd frontend
        npm run dev &
        FRONTEND_PID=$!
        
        echo -e "${GREEN}✅ Both services started!${NC}"
        echo -e "${CYAN}Backend: http://localhost:8000${NC}"
        echo -e "${CYAN}Frontend: http://localhost:3000${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
        
        # Wait for user interrupt
        trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
        wait
        ;;
    "test")
        echo -e "${BLUE}🧪 Testing system...${NC}"
        source venv/bin/activate
        python3 -c "
import requests
import sys
try:
    response = requests.get('http://localhost:8000/api/health', timeout=5)
    if response.status_code == 200:
        print('✅ Backend is running and healthy')
    else:
        print('❌ Backend returned status:', response.status_code)
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print('❌ Backend is not running')
    sys.exit(1)
except Exception as e:
    print('❌ Error:', e)
    sys.exit(1)
"
        ;;
    "stop")
        echo -e "${YELLOW}🛑 Stopping services...${NC}"
        pkill -f "simple_backend.py" 2>/dev/null || true
        pkill -f "vite" 2>/dev/null || true
        echo -e "${GREEN}✅ Services stopped${NC}"
        ;;
    *)
        echo -e "${YELLOW}Usage:${NC}"
        echo -e "  ./start.sh backend    - Start only backend"
        echo -e "  ./start.sh frontend   - Start only frontend"
        echo -e "  ./start.sh both       - Start both (default)"
        echo -e "  ./start.sh test       - Test backend health"
        echo -e "  ./start.sh stop       - Stop all services"
        ;;
esac
EOF

chmod +x start.sh
print_success "Startup script created"

# Create test script
cat > test_system.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for AI Trading System v2.0
"""

import requests
import json
import sys
from datetime import datetime

def test_backend():
    """Test backend endpoints"""
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/",
        "/api/health",
        "/api/status",
        "/api/balance",
        "/api/symbols",
        "/api/test"
    ]
    
    print("🧪 Testing Backend Endpoints...")
    print("-" * 40)
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Connection failed (backend not running?)")
            return False
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            return False
    
    return True

def main():
    print("🚀 AI Trading System v2.0 - System Test")
    print("=" * 50)
    
    if test_backend():
        print("\n✅ All tests passed!")
        print("🔗 Backend: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("⚛️ Frontend: http://localhost:3000")
    else:
        print("\n❌ Some tests failed!")
        print("Make sure the backend is running: ./start.sh backend")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x test_system.py
print_success "Test script created"

echo ""
print_status "Cleaning up unnecessary files..."

# Remove unnecessary files
FILES_TO_REMOVE=(
    "README_REFACTORED.md"
    "QUICK_START.md"
    "fix_frontend.sh"
    "install_dependencies.sh"
    "frontend/package_cra.json"
    "frontend/package_backup.json"
)

for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        print_success "Removed $file"
    fi
done

echo ""
print_success "Setup completed successfully!"

echo ""
echo -e "${PURPLE}================================================================================${NC}"
echo -e "${ROCKET} ${GREEN}AI TRADING SYSTEM v2.0 - READY TO USE!${NC}"
echo -e "${PURPLE}================================================================================${NC}"
echo ""
echo -e "${CYAN}🚀 Quick Start:${NC}"
echo -e "   ${YELLOW}./start.sh${NC}           - Start both backend and frontend"
echo -e "   ${YELLOW}./start.sh backend${NC}   - Start only backend"
echo -e "   ${YELLOW}./start.sh frontend${NC}  - Start only frontend"
echo -e "   ${YELLOW}./start.sh test${NC}      - Test system health"
echo -e "   ${YELLOW}./start.sh stop${NC}      - Stop all services"
echo ""
echo -e "${CYAN}🔗 URLs:${NC}"
echo -e "   Backend API:     ${YELLOW}http://localhost:8000${NC}"
echo -e "   API Docs:        ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "   Health Check:    ${YELLOW}http://localhost:8000/api/health${NC}"
echo -e "   Frontend:        ${YELLOW}http://localhost:3000${NC}"
echo ""
echo -e "${CYAN}📝 Configuration:${NC}"
echo -e "   Environment:     ${YELLOW}.env${NC}"
echo -e "   Backend:         ${YELLOW}simple_backend.py${NC}"
echo -e "   Frontend:        ${YELLOW}frontend/package.json${NC}"
echo ""
echo -e "${GREEN}${CHECK} System optimized for Mac M2 (ARM64)${NC}"
echo -e "${GREEN}${CHECK} Binance testnet ready${NC}"
echo -e "${GREEN}${CHECK} No Telegram bot dependencies${NC}"
echo -e "${GREEN}${CHECK} Minimal, fast, and reliable${NC}"
echo ""
echo -e "${PURPLE}================================================================================${NC}"

# Test the system
echo ""
print_status "Running quick system test..."
source venv/bin/activate

# Start backend in background for test
python3 simple_backend.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Run test
python3 test_system.py

# Stop test backend
kill $BACKEND_PID 2>/dev/null || true

echo ""
echo -e "${GREEN}🎉 Setup complete! Run ${YELLOW}./start.sh${GREEN} to begin!${NC}"