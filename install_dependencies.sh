#!/bin/bash

# ============================================================================
# 🚀 Instalación Rápida de Dependencias - AI Trading System
# ============================================================================

echo "🔧 Instalando dependencias faltantes..."

# Instalar dependencias básicas una por una para evitar conflictos
pip install structlog
pip install python-dotenv
pip install pydantic-settings
pip install fastapi
pip install uvicorn
pip install streamlit
pip install plotly
pip install ccxt
pip install python-binance
pip install yfinance
pip install pandas
pip install numpy
pip install scikit-learn
pip install websockets
pip install aiofiles
pip install python-multipart
pip install jinja2
pip install requests
pip install aiohttp

echo "✅ Dependencias instaladas!"
echo ""
echo "🧪 Probando el sistema..."

python3 -c "
try:
    from utils.config.settings import settings
    print('✅ Configuración OK')
    from utils.logging.logger import setup_logging
    print('✅ Logging OK')
    from api.main import app
    print('✅ FastAPI OK')
    print('')
    print('🎉 ¡Sistema listo para usar!')
    print('Ejecuta: python3 main.py')
except Exception as e:
    print(f'❌ Error: {e}')
"