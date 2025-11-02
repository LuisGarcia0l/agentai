#!/bin/bash

# =============================================================================
# AutoDev Trading Studio - Script de Inicio Solo Frontend
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${CYAN}$1${NC}"
}

echo ""
print_header "🎨 AutoDev Trading Studio - Frontend Only"
echo ""

# Verificar que existe el frontend
if [ ! -d "frontend" ] || [ ! -f "frontend/package.json" ]; then
    print_error "Frontend no encontrado. Asegúrate de que existe el directorio frontend/"
    exit 1
fi

# Crear directorios
mkdir -p logs

# Verificar dependencias
if [ ! -d "frontend/node_modules" ]; then
    print_status "Instalando dependencias del frontend..."
    cd frontend
    npm install
    cd ..
    print_success "Dependencias instaladas"
fi

print_status "🚀 Iniciando frontend..."

# Función de cleanup
cleanup() {
    echo ""
    print_status "🛑 Cerrando frontend..."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Iniciar frontend
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000