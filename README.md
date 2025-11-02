# 🤖 AutoDev Trading Studio

**Sistema de trading autónomo con agentes IA especializados**

Un sistema completo de trading automatizado que utiliza múltiples agentes de inteligencia artificial especializados para analizar mercados, gestionar riesgos, optimizar estrategias y ejecutar operaciones de forma autónoma.

## 🌟 Características Principales

### 🧠 Sistema Multi-Agente
- **ResearchAgent**: Análisis técnico y fundamental en tiempo real
- **TradingAgent**: Ejecución inteligente de operaciones
- **RiskAgent**: Gestión avanzada de riesgos y capital
- **OptimizerAgent**: Optimización automática de estrategias

### 📊 Capacidades Avanzadas
- **Backtesting Completo**: Validación histórica de estrategias
- **Optimización Bayesiana**: Búsqueda inteligente de parámetros óptimos
- **Análisis de Riesgo**: Monitoreo continuo y alertas automáticas
- **WebSocket Real-time**: Actualizaciones en tiempo real
- **Dashboard Moderno**: Interfaz React con Tailwind CSS

### 🔗 Integraciones
- **Binance Testnet**: Trading seguro con dinero virtual
- **OpenAI/Claude**: Análisis IA avanzado (opcional)
- **Múltiples Estrategias**: RSI, MACD, Bollinger Bands, MA Crossover

### ✨ Características Técnicas
- 🐍 **Backend**: Python + FastAPI (Puerto 8000)
- ⚛️ **Frontend**: React + Vite + Tailwind (Puerto 3000)
- 🍎 **Optimizado para Mac M2** (ARM64)
- 🧪 **Binance Testnet** integrado
- ⚡ **Rápido y escalable**
- 🔧 **Setup automático con un solo script**

## 🚀 Instalación Rápida (Mac M2)

### Prerrequisitos
- macOS con chip M2
- Homebrew instalado
- Credenciales de Binance Testnet (gratuitas)

### Instalación Automática
```bash
# Clona el repositorio
git clone https://github.com/LuisGarcia0l/agentai.git
cd agentai

# Ejecuta el setup automático (Mac M2)
chmod +x install_mac_m2.sh
./install_mac_m2.sh
```

### Configuración
1. **Obtener credenciales de Binance Testnet** (GRATIS):
   - Visita: https://testnet.binance.vision/
   - Crea una cuenta y genera API keys
   - ⚠️ **IMPORTANTE**: Usa solo Testnet (dinero virtual)

2. **Configurar variables de entorno**:
   ```bash
   # Editar archivo .env
   nano .env
   
   # Agregar tus credenciales:
   BINANCE_TESTNET_API_KEY=tu_api_key_aqui
   BINANCE_TESTNET_SECRET_KEY=tu_secret_key_aqui
   ```

3. **Iniciar el sistema**:
   ```bash
   ./start_system.sh
   ```

## 🌐 Acceso a la Aplicación

Una vez iniciado el sistema:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🚀 Uso del Sistema

### Iniciar/Parar Sistema
```bash
# Iniciar todo el sistema
./start_system.sh

# O por separado:
./start_backend.sh    # Solo backend
./start_frontend.sh   # Solo frontend

# Parar sistema (Ctrl+C en la terminal donde corre)
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