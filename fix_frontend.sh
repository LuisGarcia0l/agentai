#!/bin/bash

# Fix Frontend Dependencies for macOS ARM64
# This script fixes the Rollup/Vite issue on Apple Silicon Macs

echo "🔧 Frontend Setup for macOS ARM64"
echo "=================================="
echo ""
echo "Choose setup option:"
echo "1) Fix Vite setup (recommended for development)"
echo "2) Switch to Create React App (more stable on ARM64)"
echo "3) Just install current dependencies"
echo ""
read -p "Enter choice (1-3): " choice

# Navigate to frontend directory
cd frontend

echo "📁 Current directory: $(pwd)"

# Remove problematic files
echo "🗑️  Removing package-lock.json and node_modules..."
rm -rf package-lock.json node_modules

# Clear npm cache
echo "🧹 Clearing npm cache..."
npm cache clean --force

case $choice in
    1)
        echo "🔧 Option 1: Fixing Vite setup..."
        # Install dependencies with legacy peer deps flag
        echo "📦 Installing dependencies..."
        npm install --legacy-peer-deps
        
        # Install specific ARM64 rollup package
        echo "🍎 Installing ARM64 specific packages..."
        npm install @rollup/rollup-darwin-arm64 --save-dev --legacy-peer-deps
        
        echo "✅ Vite setup fixed!"
        echo "🚀 Run: npm run dev"
        ;;
    2)
        echo "🔄 Option 2: Switching to Create React App..."
        # Backup current package.json
        cp package.json package_vite_backup.json
        # Use CRA package.json
        cp package_cra.json package.json
        
        echo "📦 Installing Create React App dependencies..."
        npm install --legacy-peer-deps
        
        echo "✅ Create React App setup complete!"
        echo "🚀 Run: npm start"
        ;;
    3)
        echo "📦 Option 3: Installing current dependencies..."
        npm install --legacy-peer-deps
        
        # If that fails, try with force flag
        if [ $? -ne 0 ]; then
            echo "⚠️  First install failed, trying with --force flag..."
            npm install --force
        fi
        
        echo "✅ Dependencies installed!"
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "📝 You can also use the system starter:"
echo "   python3 start_system.py frontend"
echo ""
echo "🔗 Backend should be running on: http://localhost:8000"
echo "🔗 Frontend will run on: http://localhost:3000"