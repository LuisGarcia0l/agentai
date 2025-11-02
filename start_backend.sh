#!/bin/bash

# =============================================================================
# AutoDev Trading Studio - Script de Inicio Solo Backend
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
print_header "🤖 AutoDev Trading Studio - Backend Only"
echo ""

# Verificar entorno virtual
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        print_status "Activando entorno virtual..."
        source venv/bin/activate
    else
        print_error "No se encontró entorno virtual. Ejecuta: ./install_mac_m2.sh"
        exit 1
    fi
fi

# Crear directorios
mkdir -p logs

# Verificar archivo .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status "Archivo .env creado desde .env.example"
    fi
fi

# Inicializar base de datos si es necesario
if [ ! -f "trading_studio.db" ]; then
    print_status "Inicializando base de datos..."
    python -c "
import asyncio
import sys
sys.path.append('.')
from backend.core.database import init_db
asyncio.run(init_db())
print('✅ Base de datos inicializada')
    "
fi

print_status "🚀 Iniciando backend..."

# Función de cleanup
cleanup() {
    echo ""
    print_status "🛑 Cerrando backend..."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Iniciar backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
