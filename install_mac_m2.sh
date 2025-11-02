#!/bin/bash

# =============================================================================
# AutoDev Trading Studio - Instalación para Mac M2
# =============================================================================

set -e  # Salir si hay errores

echo "🚀 Instalando AutoDev Trading Studio para Mac M2..."
echo "=================================================="

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
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en Mac
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "Este script está diseñado para macOS"
    exit 1
fi

# Verificar arquitectura M2
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    print_warning "Este script está optimizado para Mac M2 (arm64), detectado: $ARCH"
    read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. Verificar/Instalar Homebrew
print_status "Verificando Homebrew..."
if ! command -v brew &> /dev/null; then
    print_status "Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Agregar Homebrew al PATH para M2
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    print_success "Homebrew ya está instalado"
fi

# 2. Actualizar Homebrew
print_status "Actualizando Homebrew..."
brew update

# 3. Instalar Python 3.11 (optimizado para M2)
print_status "Instalando Python 3.11..."
brew install python@3.11

# Crear enlace simbólico
if ! command -v python3.11 &> /dev/null; then
    print_warning "Python 3.11 no encontrado en PATH"
    # Intentar agregar al PATH
    echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zprofile
    export PATH="/opt/homebrew/bin:$PATH"
fi

# 4. Instalar Node.js (para el frontend)
print_status "Instalando Node.js..."
brew install node

# 5. Instalar dependencias del sistema
print_status "Instalando dependencias del sistema..."
brew install postgresql redis git

# 6. Instalar TA-Lib (requerido para análisis técnico)
print_status "Instalando TA-Lib..."
brew install ta-lib

# 7. Crear entorno virtual de Python
print_status "Creando entorno virtual de Python..."
python3.11 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# 8. Actualizar pip
print_status "Actualizando pip..."
pip install --upgrade pip setuptools wheel

# 9. Instalar dependencias de Python
print_status "Instalando dependencias de Python..."

# Instalar dependencias básicas primero
pip install numpy==1.25.2
pip install pandas==2.1.4

# Instalar TA-Lib Python wrapper
pip install TA-Lib

# Instalar el resto de dependencias
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_warning "requirements.txt no encontrado, instalando dependencias básicas..."
    
    # Dependencias core
    pip install fastapi==0.108.0
    pip install uvicorn==0.25.0
    pip install python-dotenv==1.0.0
    pip install pydantic==2.5.0
    pip install pydantic-settings==2.1.0
    
    # Trading y datos financieros
    pip install python-binance==1.0.19
    pip install ccxt==4.1.92
    pip install yfinance==0.2.28
    
    # Análisis técnico
    pip install pandas-ta==0.3.14b0
    
    # Machine Learning
    pip install scikit-learn==1.3.2
    pip install optuna==3.5.0
    
    # AI/LLM
    pip install openai==1.6.1
    pip install anthropic==0.8.1
    
    # Base de datos
    pip install sqlalchemy==2.0.25
    pip install aiosqlite==0.19.0
    
    # Utilidades
    pip install aiohttp==3.9.1
    pip install requests==2.31.0
    pip install websockets==12.0
    
    # Visualización
    pip install plotly==5.17.0
    pip install streamlit==1.29.0
fi

# 10. Configurar frontend
print_status "Configurando frontend React..."
cd frontend

# Verificar si package.json existe
if [ ! -f "package.json" ]; then
    print_status "Inicializando proyecto React con Vite..."
    npm create vite@latest . -- --template react-ts
fi

# Instalar dependencias del frontend
print_status "Instalando dependencias del frontend..."
npm install

# Instalar Tailwind CSS
print_status "Configurando Tailwind CSS..."
npm install -D tailwindcss postcss autoprefixer
npm install @headlessui/react @heroicons/react
npm install recharts axios
npm install @tanstack/react-query

# Volver al directorio raíz
cd ..

# 11. Crear directorios necesarios
print_status "Creando directorios necesarios..."
mkdir -p logs
mkdir -p data
mkdir -p backtest_results

# 12. Configurar archivo de entorno
print_status "Configurando archivo de entorno..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_success "Archivo .env creado desde .env.example"
    print_warning "¡IMPORTANTE! Edita el archivo .env con tus credenciales de API"
else
    print_success "Archivo .env ya existe"
fi

# 13. Inicializar base de datos
print_status "Inicializando base de datos..."
python -c "
import asyncio
import sys
sys.path.append('.')
from backend.core.database import init_db

async def main():
    try:
        await init_db()
        print('✅ Base de datos inicializada correctamente')
    except Exception as e:
        print(f'❌ Error inicializando base de datos: {e}')

asyncio.run(main())
"

# 14. Crear scripts de inicio
print_status "Creando scripts de inicio..."

# Script para iniciar el backend
cat > start_backend.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
EOF

# Script para iniciar el frontend
cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000
EOF

# Script para iniciar todo el sistema
cat > start_system.sh << 'EOF'
#!/bin/bash
echo "🚀 Iniciando AutoDev Trading Studio..."

# Función para limpiar procesos al salir
cleanup() {
    echo "🛑 Cerrando sistema..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Iniciar backend en background
echo "📡 Iniciando backend..."
source venv/bin/activate
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Esperar un poco para que el backend inicie
sleep 3

# Iniciar frontend en background
echo "🎨 Iniciando frontend..."
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!
cd ..

echo "✅ Sistema iniciado:"
echo "   - Backend: http://localhost:8000"
echo "   - Frontend: http://localhost:3000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "Presiona Ctrl+C para detener el sistema"

# Esperar a que terminen los procesos
wait $BACKEND_PID $FRONTEND_PID
EOF

# Hacer ejecutables los scripts
chmod +x start_backend.sh
chmod +x start_frontend.sh
chmod +x start_system.sh

# 15. Verificar instalación
print_status "Verificando instalación..."

# Verificar Python
if python --version | grep -q "3.11"; then
    print_success "Python 3.11 instalado correctamente"
else
    print_warning "Python 3.11 no detectado correctamente"
fi

# Verificar Node.js
if node --version | grep -q "v"; then
    print_success "Node.js instalado correctamente"
else
    print_warning "Node.js no detectado correctamente"
fi

# Verificar dependencias críticas
python -c "
try:
    import fastapi, uvicorn, pandas, numpy, ta
    print('✅ Dependencias críticas de Python instaladas')
except ImportError as e:
    print(f'❌ Error con dependencias de Python: {e}')
"

# 16. Mostrar información final
echo ""
echo "=================================================="
print_success "¡Instalación completada!"
echo "=================================================="
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. 🔑 Configura tus credenciales en el archivo .env:"
echo "   - BINANCE_TESTNET_API_KEY"
echo "   - BINANCE_TESTNET_SECRET_KEY"
echo "   - OPENAI_API_KEY (opcional)"
echo ""
echo "2. 🚀 Inicia el sistema:"
echo "   ./start_system.sh"
echo ""
echo "3. 🌐 Accede a la aplicación:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - Documentación API: http://localhost:8000/docs"
echo ""
echo "📚 Documentación adicional:"
echo "   - README.md para más información"
echo "   - Logs en: logs/trading_studio.log"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   - Este sistema usa Binance Testnet por defecto (dinero virtual)"
echo "   - Nunca uses credenciales de producción sin entender completamente el sistema"
echo "   - Revisa la configuración de riesgo en .env antes de usar"
echo ""
print_success "¡Disfruta tu sistema de trading autónomo!"