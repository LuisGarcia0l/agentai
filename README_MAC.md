# 🍎 AI Trading System - Guía para Mac

## 🚀 Instalación Rápida (Recomendada)

```bash
# 1. Navegar al directorio del proyecto
cd /Users/luisgarcia/Documents/agentai

# 2. Ejecutar script de instalación automática
./install_mac.sh

# 3. Activar entorno virtual
source venv/bin/activate

# 4. Iniciar el sistema
python3 main.py
```

## 📋 Instalación Manual

### Paso 1: Verificar Requisitos
```bash
# Verificar Python 3.9+
python3 --version

# Si no tienes Python, instálalo:
brew install python@3.11

# Verificar Node.js (opcional, para frontend React)
node --version

# Si no tienes Node.js:
brew install node
```

### Paso 2: Crear Entorno Virtual
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Verificar que estás en el entorno virtual
which python
# Debería mostrar: .../agentai/venv/bin/python
```

### Paso 3: Instalar Dependencias
```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias básicas
pip install python-dotenv pydantic pydantic-settings
pip install fastapi uvicorn streamlit

# Instalar dependencias de trading
pip install ccxt python-binance yfinance
pip install pandas numpy scikit-learn

# O instalar todo desde requirements.txt
pip install -r requirements.txt
```

### Paso 4: Configurar Variables de Entorno
```bash
# Copiar configuración de ejemplo
cp .env.example .env

# Editar si necesitas (opcional para empezar)
nano .env
```

### Paso 5: Probar Instalación
```bash
# Probar que todo funciona
python3 -c "
from utils.config.settings import settings
print('✅ Sistema listo!')
print(f'Modo: {settings.TRADING_MODE}')
"
```

## 🎯 Comandos de Uso

### Activar Entorno Virtual (SIEMPRE PRIMERO)
```bash
source venv/bin/activate
```

### Iniciar Sistema Completo
```bash
python3 main.py
```

### Iniciar Componentes Individuales
```bash
# Solo API FastAPI
python3 start_api.py

# Solo Frontend React
python3 start_frontend.py

# Solo Dashboard Streamlit
streamlit run dashboard/streamlit_app/app.py
```

## 🌐 Acceder a las Interfaces

Una vez iniciado el sistema:

- **🎛️ Dashboard React**: http://localhost:3000
- **🚀 API FastAPI**: http://localhost:8000  
- **📚 Documentación API**: http://localhost:8000/docs
- **📊 Dashboard Streamlit**: http://localhost:8501

## 🔧 Solución de Problemas

### ❌ "ModuleNotFoundError: No module named 'pydantic_settings'"
```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencia faltante
pip install pydantic-settings
```

### ❌ "zsh: command not found: python"
```bash
# Usar python3 en lugar de python
python3 main.py

# O crear alias permanente
echo 'alias python=python3' >> ~/.zshrc
source ~/.zshrc
```

### ❌ "Permission denied" en puertos
```bash
# Cambiar puertos en .env
nano .env

# Cambiar estas líneas:
API_PORT=8001
DASHBOARD_PORT=8502
FRONTEND_PORT=3001
```

### ❌ Error de conexión con Binance
```bash
# Normal en modo demo - el sistema funciona sin credenciales reales
# Para usar credenciales reales, edita .env:
BINANCE_API_KEY=tu_api_key_aqui
BINANCE_SECRET_KEY=tu_secret_key_aqui
```

### ❌ Frontend no funciona
```bash
# Instalar Node.js si no lo tienes
brew install node

# Instalar dependencias del frontend
cd frontend
npm install
cd ..
```

## 📱 Uso del Sistema

### 1. Modo Demo (Sin Credenciales)
El sistema funciona perfectamente sin credenciales reales:
- Usa datos simulados
- Todas las funciones disponibles
- Perfecto para aprender y experimentar

### 2. Modo Paper Trading (Recomendado)
```bash
# En .env:
TRADING_MODE=paper
BINANCE_TESTNET=true
```

### 3. Modo Live Trading (¡CUIDADO!)
```bash
# Solo para usuarios experimentados
# En .env:
TRADING_MODE=live
BINANCE_TESTNET=false
```

## 🎓 Primeros Pasos

1. **Iniciar el sistema**: `python3 main.py`
2. **Abrir dashboard**: http://localhost:3000
3. **Explorar la API**: http://localhost:8000/docs
4. **Ver logs**: En la terminal donde ejecutaste el sistema
5. **Experimentar**: El sistema está en modo seguro por defecto

## 🆘 Obtener Ayuda

### Verificar Estado del Sistema
```bash
# Verificar entorno virtual
which python

# Verificar dependencias
pip list | grep fastapi

# Verificar configuración
python3 -c "from utils.config.settings import settings; print(settings.TRADING_MODE)"
```

### Logs y Debugging
```bash
# Ver logs detallados
python3 main.py --debug

# Verificar puertos ocupados
lsof -i :8000
lsof -i :3000
lsof -i :8501
```

## 🎉 ¡Listo para Usar!

Una vez completada la instalación, tendrás un sistema de trading con IA completamente funcional en tu Mac. 

**¡Disfruta explorando el mundo del trading algorítmico con inteligencia artificial!** 🤖📈