#!/bin/bash
#gola
# ============================================================================
# 🚀 Script de Instalación para Mac - AI Trading System
# ============================================================================

echo "🤖 AI Trading System - Instalación para Mac"
echo "=============================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✅]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠️]${NC} $1"
}

print_error() {
    echo -e "${RED}[❌]${NC} $1"
}

# Verificar si estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    print_error "No se encontró main.py. Asegúrate de estar en el directorio del proyecto."
    exit 1
fi

print_status "Verificando requisitos del sistema..."

# Verificar Python 3
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 no está instalado. Instálalo con: brew install python@3.11"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
print_success "Python $PYTHON_VERSION encontrado"

# Verificar Node.js
if ! command -v node &> /dev/null; then
    print_warning "Node.js no está instalado. Instálalo con: brew install node"
    print_status "Continuando sin frontend React..."
    INSTALL_FRONTEND=false
else
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION encontrado"
    INSTALL_FRONTEND=true
fi

# Crear entorno virtual
print_status "Creando entorno virtual..."
if [ -d "venv" ]; then
    print_warning "El entorno virtual ya existe. Eliminando..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

print_success "Entorno virtual creado y activado"

# Actualizar pip
print_status "Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias básicas primero
print_status "Instalando dependencias básicas..."
pip install python-dotenv pydantic pydantic-settings fastapi uvicorn

# Instalar dependencias principales
print_status "Instalando dependencias principales..."
pip install ccxt python-binance yfinance pandas numpy scikit-learn
pip install streamlit plotly websockets aiofiles
pip install python-multipart jinja2 requests aiohttp

print_success "Dependencias de Python instaladas"

# Instalar dependencias del frontend si Node.js está disponible
if [ "$INSTALL_FRONTEND" = true ]; then
    print_status "Instalando dependencias del frontend..."
    cd frontend
    
    if [ ! -f "package.json" ]; then
        print_warning "package.json no encontrado. Creando configuración básica..."
        cat > package.json << EOF
{
  "name": "ai-trading-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
EOF
    fi
    
    npm install
    cd ..
    print_success "Dependencias del frontend instaladas"
fi

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    print_status "Creando archivo de configuración..."
    cp .env.example .env
    print_success "Archivo .env creado desde .env.example"
else
    print_warning "El archivo .env ya existe"
fi

# Probar la instalación
print_status "Probando la instalación..."
python3 -c "
try:
    from utils.config.settings import settings
    print('✅ Configuración cargada correctamente')
    print(f'   Modo: {settings.TRADING_MODE}')
    print(f'   Exchange: {settings.DEFAULT_EXCHANGE}')
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    print_success "¡Instalación completada exitosamente!"
    echo ""
    echo "🎉 ¡Todo listo! Ahora puedes usar el sistema:"
    echo ""
    echo "📋 Comandos disponibles:"
    echo "   source venv/bin/activate    # Activar entorno virtual"
    echo "   python3 main.py             # Iniciar sistema completo"
    echo "   python3 start_api.py        # Solo API"
    echo "   python3 start_frontend.py   # Solo frontend"
    echo ""
    echo "🌐 Interfaces disponibles:"
    echo "   Dashboard React:  http://localhost:3000"
    echo "   API FastAPI:      http://localhost:8000"
    echo "   Docs API:         http://localhost:8000/docs"
    echo "   Streamlit:        http://localhost:8501"
    echo ""
    echo "⚠️  Recuerda activar el entorno virtual antes de ejecutar comandos:"
    echo "   source venv/bin/activate"
    echo ""
else
    print_error "La instalación falló. Revisa los errores arriba."
    exit 1
fi