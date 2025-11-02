# 🚀 Configuración Local para Mac

## 📋 Requisitos Previos

### 1. Python 3.9+
```bash
# Verificar versión de Python
python3 --version

# Si no tienes Python 3.9+, instálalo con Homebrew:
brew install python@3.11
```

### 2. Node.js 18+ (para el frontend React)
```bash
# Verificar versión de Node.js
node --version

# Si no tienes Node.js, instálalo:
brew install node
```

## 🛠️ Instalación Paso a Paso

### Paso 1: Crear Entorno Virtual (RECOMENDADO)
```bash
# Navegar al directorio del proyecto
cd /Users/luisgarcia/Documents/agentai

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Verificar que estás en el entorno virtual
which python
# Debería mostrar: /Users/luisgarcia/Documents/agentai/venv/bin/python
```

### Paso 2: Instalar Dependencias de Python
```bash
# Asegúrate de que el entorno virtual esté activado
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias principales
pip install fastapi uvicorn pydantic-settings python-dotenv
pip install ccxt python-binance yfinance pandas numpy scikit-learn
pip install streamlit plotly websockets aiofiles
pip install python-multipart jinja2

# O instalar todo desde requirements.txt si existe
pip install -r requirements.txt
```

### Paso 3: Instalar Dependencias del Frontend
```bash
# Navegar al directorio del frontend
cd frontend

# Instalar dependencias de Node.js
npm install

# Volver al directorio raíz
cd ..
```

### Paso 4: Configurar Variables de Entorno
```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar configuración (opcional para empezar)
nano .env
# O usar cualquier editor: code .env, vim .env, etc.
```

### Paso 5: Probar el Sistema
```bash
# Asegúrate de estar en el directorio raíz y con el entorno virtual activado
source venv/bin/activate

# Probar importaciones
python3 -c "
from utils.config.settings import settings
print('✅ Configuración cargada correctamente')
print(f'Modo: {settings.TRADING_MODE}')
"

# Si todo funciona, iniciar el sistema
python3 main.py
```

## 🎯 Comandos Rápidos

### Iniciar Sistema Completo
```bash
source venv/bin/activate
python3 main.py
```

### Iniciar Solo API
```bash
source venv/bin/activate
python3 start_api.py
```

### Iniciar Solo Frontend
```bash
source venv/bin/activate
python3 start_frontend.py
```

### Iniciar Solo Dashboard Streamlit
```bash
source venv/bin/activate
streamlit run dashboard/streamlit_app/app.py
```

## 🔧 Solución de Problemas Comunes

### Error: "ModuleNotFoundError: No module named 'pydantic_settings'"
```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar pydantic-settings
pip install pydantic-settings
```

### Error: "zsh: command not found: python"
```bash
# Usar python3 en lugar de python
python3 main.py

# O crear un alias (opcional)
echo 'alias python=python3' >> ~/.zshrc
source ~/.zshrc
```

### Error: "Permission denied" o problemas de puertos
```bash
# Cambiar puertos en .env si están ocupados
API_PORT=8001
DASHBOARD_PORT=8502
FRONTEND_PORT=3001
```

### Error: "Node.js not found"
```bash
# Instalar Node.js
brew install node

# Verificar instalación
node --version
npm --version
```

## 📱 Acceder a las Interfaces

Una vez que el sistema esté corriendo:

- **Dashboard React**: http://localhost:3000
- **API FastAPI**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **Dashboard Streamlit**: http://localhost:8501

## ⚠️ Notas Importantes

1. **Entorno Virtual**: Siempre activa el entorno virtual antes de ejecutar comandos Python
2. **Credenciales**: El sistema funciona sin credenciales reales (modo demo)
3. **Puertos**: Asegúrate de que los puertos 3000, 8000 y 8501 estén libres
4. **Binance Testnet**: Para trading real, necesitarás credenciales de Binance testnet

## 🆘 Si Necesitas Ayuda

1. **Verificar entorno virtual**: `which python` debería mostrar la ruta del venv
2. **Verificar dependencias**: `pip list | grep fastapi`
3. **Logs del sistema**: Los errores aparecerán en la terminal
4. **Reiniciar**: Si algo falla, Ctrl+C y volver a ejecutar

## 🎉 ¡Listo!

Una vez completados estos pasos, tendrás el sistema de trading con IA funcionando completamente en tu Mac local.