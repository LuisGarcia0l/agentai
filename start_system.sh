#!/bin/bash

# =============================================================================
# AutoDev Trading Studio - Script de Inicio del Sistema Completo
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

print_header() {
    echo -e "${CYAN}$1${NC}"
}

# Banner del sistema
echo ""
print_header "🤖 =============================================="
print_header "   AutoDev Trading Studio"
print_header "   Sistema de Trading Autónomo con Agentes IA"
print_header "============================================== 🚀"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "backend/main.py" ]; then
    print_error "No se encontró backend/main.py. Asegúrate de estar en el directorio raíz del proyecto."
    exit 1
fi

# Verificar entorno virtual
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "No se detectó entorno virtual activo."
    if [ -d "venv" ]; then
        print_status "Activando entorno virtual..."
        source venv/bin/activate
        print_success "Entorno virtual activado"
    else
        print_error "No se encontró entorno virtual. Ejecuta primero: ./install_mac_m2.sh"
        exit 1
    fi
else
    print_success "Entorno virtual activo: $VIRTUAL_ENV"
fi

# Verificar archivo .env
if [ ! -f ".env" ]; then
    print_warning "No se encontró archivo .env"
    if [ -f ".env.example" ]; then
        print_status "Copiando .env.example a .env..."
        cp .env.example .env
        print_warning "¡IMPORTANTE! Edita el archivo .env con tus credenciales de Binance Testnet"
        print_warning "Visita: https://testnet.binance.vision/ para obtener credenciales gratuitas"
    else
        print_error "No se encontró .env.example"
        exit 1
    fi
fi

# Crear directorios necesarios
print_status "Creando directorios necesarios..."
mkdir -p logs
mkdir -p data
mkdir -p backtest_results

# Verificar dependencias críticas
print_status "Verificando dependencias críticas..."
python -c "
import sys
try:
    import fastapi, uvicorn, pandas, numpy
    print('✅ Dependencias básicas OK')
except ImportError as e:
    print(f'❌ Error con dependencias: {e}')
    sys.exit(1)
" || {
    print_error "Faltan dependencias críticas. Ejecuta: pip install -r requirements.txt"
    exit 1
}

# Función para limpiar procesos al salir
cleanup() {
    echo ""
    print_status "🛑 Cerrando AutoDev Trading Studio..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        print_status "Cerrando backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        print_status "Cerrando frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Esperar un poco para que los procesos terminen
    sleep 2
    
    print_success "✅ Sistema cerrado correctamente"
    echo ""
    print_header "¡Gracias por usar AutoDev Trading Studio! 🤖"
    exit 0
}

# Configurar trap para cleanup
trap cleanup SIGINT SIGTERM

# Verificar si los puertos están disponibles
check_port() {
    local port=$1
    local service=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Puerto $port ya está en uso (posible $service ejecutándose)"
        print_status "¿Quieres continuar de todos modos? (y/N)"
        read -r response
        if [[ ! $response =~ ^[Yy]$ ]]; then
            print_status "Cancelando inicio..."
            exit 1
        fi
    fi
}

print_status "Verificando puertos disponibles..."
check_port 8000 "backend"
check_port 3000 "frontend"

# Inicializar base de datos si es necesario
if [ ! -f "trading_studio.db" ]; then
    print_status "Inicializando base de datos..."
    python -c "
import asyncio
import sys
sys.path.append('.')
from backend.core.database import init_db

async def main():
    try:
        await init_db()
        print('✅ Base de datos inicializada')
    except Exception as e:
        print(f'❌ Error inicializando base de datos: {e}')
        sys.exit(1)

asyncio.run(main())
    " || {
        print_error "Error inicializando base de datos"
        exit 1
    }
fi

echo ""
print_header "🚀 Iniciando servicios..."
echo ""

# Iniciar backend
print_status "📡 Iniciando backend (FastAPI + Agentes IA)..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

print_success "Backend iniciado (PID: $BACKEND_PID)"
print_status "Logs del backend: tail -f logs/backend.log"

# Esperar a que el backend inicie
print_status "Esperando a que el backend inicie..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "✅ Backend respondiendo correctamente"
        break
    fi
    
    if [ $i -eq 30 ]; then
        print_error "❌ Backend no responde después de 30 segundos"
        print_status "Revisa los logs: tail -f logs/backend.log"
        cleanup
        exit 1
    fi
    
    echo -n "."
    sleep 1
done

echo ""

# Verificar si existe el frontend
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    print_status "🎨 Iniciando frontend (React + Vite)..."
    
    # Verificar si node_modules existe
    if [ ! -d "frontend/node_modules" ]; then
        print_status "Instalando dependencias del frontend..."
        cd frontend
        npm install > ../logs/frontend_install.log 2>&1
        cd ..
        print_success "Dependencias del frontend instaladas"
    fi
    
    cd frontend
    npm run dev -- --host 0.0.0.0 --port 3000 > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    print_success "Frontend iniciado (PID: $FRONTEND_PID)"
    print_status "Logs del frontend: tail -f logs/frontend.log"
    
    # Esperar a que el frontend inicie
    print_status "Esperando a que el frontend inicie..."
    sleep 5
    
    FRONTEND_AVAILABLE=true
else
    print_warning "⚠️ Frontend no encontrado o no configurado"
    print_status "Solo se ejecutará el backend"
    FRONTEND_AVAILABLE=false
fi

echo ""
print_header "✅ ¡AutoDev Trading Studio iniciado correctamente!"
echo ""

# Mostrar información del sistema
print_status "📊 Estado del sistema:"
echo ""
echo "   🔗 URLs disponibles:"
echo "   ├── Backend API:      http://localhost:8000"
echo "   ├── Documentación:    http://localhost:8000/docs"
echo "   ├── Health Check:     http://localhost:8000/health"
echo "   ├── System Status:    http://localhost:8000/system/status"

if [ "$FRONTEND_AVAILABLE" = true ]; then
    echo "   └── Frontend:         http://localhost:3000"
else
    echo "   └── Frontend:         No disponible"
fi

echo ""
echo "   📁 Archivos importantes:"
echo "   ├── Logs backend:     logs/backend.log"
if [ "$FRONTEND_AVAILABLE" = true ]; then
    echo "   ├── Logs frontend:    logs/frontend.log"
fi
echo "   ├── Base de datos:    trading_studio.db"
echo "   └── Configuración:    .env"

echo ""
echo "   🤖 Agentes IA activos:"
echo "   ├── ResearchAgent:    Análisis de mercado"
echo "   ├── TradingAgent:     Ejecución de trades"
echo "   ├── RiskAgent:        Gestión de riesgo"
echo "   └── OptimizerAgent:   Optimización de estrategias"

echo ""
print_header "🔧 Comandos útiles:"
echo ""
echo "   # Ver logs en tiempo real:"
echo "   tail -f logs/backend.log"
if [ "$FRONTEND_AVAILABLE" = true ]; then
    echo "   tail -f logs/frontend.log"
fi
echo ""
echo "   # Probar el sistema:"
echo "   curl http://localhost:8000/health"
echo ""
echo "   # Ver estado de agentes:"
echo "   curl http://localhost:8000/system/status"
echo ""

print_warning "⚠️  IMPORTANTE:"
echo "   • Este sistema usa Binance Testnet (dinero virtual)"
echo "   • Configura tus credenciales en el archivo .env"
echo "   • Nunca uses credenciales de producción"
echo ""

print_success "🎯 ¡El sistema está listo para usar!"
print_header "Presiona Ctrl+C para detener el sistema"
echo ""

# Mostrar logs en tiempo real (opcional)
print_status "¿Quieres ver los logs en tiempo real? (y/N)"
read -t 10 -r response || response="n"
if [[ $response =~ ^[Yy]$ ]]; then
    print_status "Mostrando logs del backend (Ctrl+C para salir)..."
    tail -f logs/backend.log
else
    # Mantener el script corriendo
    print_status "Sistema ejecutándose en background..."
    print_status "Usa 'tail -f logs/backend.log' para ver logs"
    
    # Esperar a que terminen los procesos
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
fi