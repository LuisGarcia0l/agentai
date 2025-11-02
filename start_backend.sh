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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header() {
    echo -e "${CYAN}$1${NC}"
}

check_mongodb() {
    print_status "Verificando estado de MongoDB..."
    
    # Verificar si el puerto está en uso
    if lsof -i :27017 > /dev/null 2>&1; then
        print_success "MongoDB está ejecutándose (puerto 27017 en uso)"
        return 0
    fi
    
    # Verificar si el proceso está ejecutándose
    if ps aux | grep -q "[m]ongod"; then
        print_success "MongoDB está ejecutándose"
        return 0
    fi
    
    print_warning "MongoDB no está ejecutándose"
    
    # Intentar solucionar problemas comunes
    print_status "Intentando solucionar problemas de MongoDB..."
    
    # Eliminar archivos de lock que puedan causar problemas
    sudo rm -f /tmp/mongodb-27017.sock 2>/dev/null || true
    sudo rm -f /usr/local/var/mongodb/mongod.lock 2>/dev/null || true
    
    # Intentar iniciar con Homebrew
    if command -v brew > /dev/null 2>&1; then
        print_status "Intentando iniciar MongoDB con Homebrew..."
        brew services stop mongodb/brew/mongodb-community 2>/dev/null || true
        sleep 2
        if brew services start mongodb/brew/mongodb-community 2>/dev/null; then
            sleep 3
            if lsof -i :27017 > /dev/null 2>&1; then
                print_success "MongoDB iniciado correctamente con Homebrew"
                return 0
            fi
        fi
    fi
    
    # Último intento: iniciar manualmente
    print_status "Intentando iniciar MongoDB manualmente..."
    if [ -f "/usr/local/etc/mongod.conf" ]; then
        mkdir -p /usr/local/var/mongodb 2>/dev/null || true
        mkdir -p /usr/local/var/log/mongodb 2>/dev/null || true
        mongod --config /usr/local/etc/mongod.conf --fork --logpath /tmp/mongod.log 2>/dev/null
        sleep 3
        if lsof -i :27017 > /dev/null 2>&1; then
            print_success "MongoDB iniciado manualmente"
            return 0
        fi
    fi
    
    print_error "No se pudo iniciar MongoDB automáticamente"
    print_warning "Algunas funciones pueden no estar disponibles"
    echo ""
    echo "Para solucionar manualmente:"
    echo "  1. Revisar logs: tail -f /usr/local/var/log/mongodb/mongo.log"
    echo "  2. Forzar inicio: brew services restart mongodb/brew/mongodb-community"
    echo "  3. O iniciar manualmente: mongod --config /usr/local/etc/mongod.conf --fork"
    return 1
}

echo ""
print_header "🤖 AutoDev Trading Studio - Backend Only"
echo ""

# Verificar MongoDB
check_mongodb

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