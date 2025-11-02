# 🚀 AI Trading System v2.0

Sistema de trading automatizado optimizado para **Mac M2 (Apple Silicon)** con arquitectura separada backend/frontend.

## ✨ Características

- 🐍 **Backend**: Python + FastAPI (Puerto 8000)
- ⚛️ **Frontend**: React + Vite (Puerto 3000)
- 🍎 **Optimizado para Mac M2** (ARM64)
- 🧪 **Binance Testnet** integrado
- 🚫 **Sin dependencias de Telegram**
- ⚡ **Rápido y minimalista**
- 🔧 **Setup automático con un solo script**

## 🎯 Instalación Rápida

```bash
# Clona el repositorio
git clone https://github.com/LuisGarcia0l/agentai.git
cd agentai

# Ejecuta el setup automático (Mac M2)
./setup_m2.sh
```

## 🚀 Uso

```bash
# Iniciar todo el sistema
./start.sh

# O por separado:
./start.sh backend    # Solo backend
./start.sh frontend   # Solo frontend
./start.sh test       # Probar sistema
./start.sh stop       # Parar servicios
```

## 🔗 URLs

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Health Check**: http://localhost:8000/api/health

## ⚙️ Configuración

Edita el archivo `.env`:

```bash
# Binance Testnet
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_SECRET_KEY=your_testnet_secret_key_here
BINANCE_TESTNET=True
```

## 🧪 Testing

```bash
# Probar conectividad Binance Testnet
python3 binance_testnet.py

# Probar sistema completo
python3 test_system.py
```

## 📁 Estructura

```
agentai/
├── simple_backend.py      # Backend principal
├── binance_testnet.py     # Integración Binance
├── setup_m2.sh           # Setup automático
├── start.sh              # Script de inicio
├── test_system.py        # Tests del sistema
├── .env                  # Configuración
└── frontend/             # React frontend
    ├── package.json      # Optimizado para M2
    └── src/              # Código React
```

## 🔧 Requisitos

- **macOS** (preferiblemente Apple Silicon)
- **Python 3.8+**
- **Node.js 18+**
- **npm 9+**

## 🎯 Características del Sistema

### Backend (Python + FastAPI)
- ✅ API REST completa
- ✅ Documentación automática (Swagger)
- ✅ CORS configurado para React
- ✅ Endpoints de trading simulado
- ✅ Integración Binance Testnet
- ✅ Sin dependencias complejas

### Frontend (React + Vite)
- ✅ Interfaz moderna y responsiva
- ✅ Optimizado para ARM64
- ✅ Hot reload para desarrollo
- ✅ TypeScript support
- ✅ Tailwind CSS

## 🚫 Lo que NO incluye

- ❌ Bot de Telegram
- ❌ Dependencias pesadas
- ❌ Configuración compleja
- ❌ Trading real (solo testnet)

## 🔒 Seguridad

- Solo usa **Binance Testnet**
- No incluye claves reales
- Entorno de desarrollo seguro
- Sin acceso a fondos reales

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu rama: `git checkout -b feature/nueva-caracteristica`
3. Commit: `git commit -m 'Añadir nueva característica'`
4. Push: `git push origin feature/nueva-caracteristica`
5. Abre un Pull Request

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE)

## ⚠️ Disclaimer

**Solo para fines educativos y de desarrollo.** Este sistema usa Binance Testnet y no maneja fondos reales. El trading de criptomonedas conlleva riesgos. Úsalo bajo tu propia responsabilidad.

---

**🍎 Optimizado para Mac M2 | 🚀 v2.0 | ⚡ Rápido y Simple**