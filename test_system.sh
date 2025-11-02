#!/bin/bash

# =============================================================================
# AutoDev Trading Studio - Script de Prueba del Sistema
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

echo ""
print_header "🧪 AutoDev Trading Studio - Pruebas del Sistema"
echo ""

# Verificar entorno virtual
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        print_status "Activando entorno virtual..."
        source venv/bin/activate
    else
        print_error "No se encontró entorno virtual"
        exit 1
    fi
fi

# Contador de pruebas
TESTS_PASSED=0
TESTS_FAILED=0

# Función para ejecutar prueba
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    print_status "Ejecutando: $test_name"
    
    if eval "$test_command" > /dev/null 2>&1; then
        print_success "✅ $test_name"
        ((TESTS_PASSED++))
    else
        print_error "❌ $test_name"
        ((TESTS_FAILED++))
    fi
}

# Función para ejecutar prueba con output
run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    
    print_status "Ejecutando: $test_name"
    
    if result=$(eval "$test_command" 2>&1); then
        print_success "✅ $test_name"
        echo "   Resultado: $result"
        ((TESTS_PASSED++))
    else
        print_error "❌ $test_name"
        echo "   Error: $result"
        ((TESTS_FAILED++))
    fi
}

print_header "🔍 Pruebas de Dependencias"
echo ""

# Pruebas de dependencias Python
run_test "Python disponible" "python --version"
run_test "FastAPI instalado" "python -c 'import fastapi'"
run_test "Uvicorn instalado" "python -c 'import uvicorn'"
run_test "Pandas instalado" "python -c 'import pandas'"
run_test "NumPy instalado" "python -c 'import numpy'"
run_test "SQLAlchemy instalado" "python -c 'import sqlalchemy'"
run_test "Python-binance instalado" "python -c 'import binance'"
run_test "Requests instalado" "python -c 'import requests'"
run_test "WebSockets instalado" "python -c 'import websockets'"

echo ""
print_header "🏗️ Pruebas de Estructura del Proyecto"
echo ""

# Pruebas de estructura
run_test "Directorio backend existe" "[ -d 'backend' ]"
run_test "Archivo main.py existe" "[ -f 'backend/main.py' ]"
run_test "Directorio agents existe" "[ -d 'backend/agents' ]"
run_test "Directorio services existe" "[ -d 'backend/services' ]"
run_test "Directorio core existe" "[ -d 'backend/core' ]"
run_test "Archivo requirements.txt existe" "[ -f 'requirements.txt' ]"
run_test "Archivo .env.example existe" "[ -f '.env.example' ]"

echo ""
print_header "🤖 Pruebas de Agentes IA"
echo ""

# Pruebas de agentes
run_test "BaseAgent importable" "python -c 'from backend.agents.base_agent import BaseAgent'"
run_test "ResearchAgent importable" "python -c 'from backend.agents.research_agent import ResearchAgent'"
run_test "TradingAgent importable" "python -c 'from backend.agents.trading_agent import TradingAgent'"
run_test "RiskAgent importable" "python -c 'from backend.agents.risk_agent import RiskAgent'"
run_test "OptimizerAgent importable" "python -c 'from backend.agents.optimizer_agent import OptimizerAgent'"
run_test "AgentManager importable" "python -c 'from backend.agents.agent_manager import AgentManager'"

echo ""
print_header "🔧 Pruebas de Servicios"
echo ""

# Pruebas de servicios
run_test "BinanceService importable" "python -c 'from backend.services.binance_service import BinanceService'"
run_test "LLMService importable" "python -c 'from backend.services.llm_service import LLMService'"
run_test "RiskManager importable" "python -c 'from backend.services.risk_manager import RiskManager'"
run_test "BacktestingService importable" "python -c 'from backend.services.backtesting_service import BacktestingService'"
run_test "WebSocketManager importable" "python -c 'from backend.services.websocket_manager import WebSocketManager'"

echo ""
print_header "🗄️ Pruebas de Base de Datos"
echo ""

# Crear base de datos de prueba
run_test "Inicialización de base de datos" "python -c '
import asyncio
import sys
sys.path.append(\".\")
from backend.core.database import init_db
asyncio.run(init_db())
'"

run_test "Modelos de base de datos" "python -c '
import sys
sys.path.append(\".\")
from backend.core.database import Trade, BacktestResult, Strategy
'"

echo ""
print_header "⚙️ Pruebas de Configuración"
echo ""

# Pruebas de configuración
run_test "Configuración cargable" "python -c 'from backend.core.config import settings'"
run_test "Logging configuración" "python -c 'from backend.core.logging_config import setup_logging; setup_logging()'"

echo ""
print_header "🌐 Pruebas de Red (si hay backend corriendo)"
echo ""

# Verificar si el backend está corriendo
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend está corriendo"
    
    run_test_with_output "Health check" "curl -s http://localhost:8000/health"
    run_test_with_output "System status" "curl -s http://localhost:8000/system/status"
    run_test "API docs accesible" "curl -s http://localhost:8000/docs > /dev/null"
else
    print_warning "Backend no está corriendo - saltando pruebas de red"
    print_status "Para probar la API, ejecuta primero: ./start_backend.sh"
fi

echo ""
print_header "📊 Resumen de Pruebas"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

echo "   Total de pruebas: $TOTAL_TESTS"
echo "   ✅ Pasaron: $TESTS_PASSED"
echo "   ❌ Fallaron: $TESTS_FAILED"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    print_success "🎉 ¡Todas las pruebas pasaron! El sistema está listo."
    echo ""
    print_header "🚀 Próximos pasos:"
    echo "   1. Configura tus credenciales en .env"
    echo "   2. Ejecuta: ./start_system.sh"
    echo "   3. Visita: http://localhost:8000/docs"
    exit 0
else
    echo ""
    print_error "❌ Algunas pruebas fallaron. Revisa los errores arriba."
    echo ""
    print_header "🔧 Posibles soluciones:"
    echo "   1. Ejecuta: pip install -r requirements.txt"
    echo "   2. Verifica que estés en el entorno virtual"
    echo "   3. Ejecuta: ./install_mac_m2.sh"
    exit 1
fi