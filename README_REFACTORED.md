# 🤖 AI Trading System v2.0 - Arquitectura Refactorizada

## 📋 Descripción

Sistema de trading avanzado con agentes IA completamente refactorizado para separar el backend (Python) del frontend (React). Esta nueva arquitectura proporciona mejor escalabilidad, mantenimiento y desarrollo independiente de cada componente.

## 🏗️ Arquitectura

### Backend (Python)
- **API REST** con FastAPI
- **WebSocket** para datos en tiempo real
- **Agentes IA** autónomos
- **Motor de backtesting** avanzado
- **Análisis técnico** automatizado
- **Gestión de riesgo** inteligente

### Frontend (React)
- **Interfaz moderna** con React + TypeScript
- **Dashboard interactivo** con gráficos en tiempo real
- **Gestión de estado** con Zustand
- **Comunicación API** con Axios y React Query
- **Diseño responsive** con Tailwind CSS

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.9+
- Node.js 18+
- npm 9+

### 1. Configurar Backend

```bash
# Instalar dependencias del backend
pip install -r requirements_backend.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Ejecutar solo el backend
python backend_main.py
```

El backend estará disponible en:
- API: http://localhost:8000
- Documentación: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

### 2. Configurar Frontend

```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm run dev
```

O usar el script helper:
```bash
# Desde el directorio raíz
python frontend_main.py
```

El frontend estará disponible en: http://localhost:3000

## 📁 Estructura del Proyecto

```
agentai/
├── 🐍 BACKEND (Python)
│   ├── api/                    # API FastAPI
│   │   └── main.py            # Endpoints principales
│   ├── agents/                # Agentes IA
│   │   ├── trading_agent/     # Agente de trading
│   │   ├── research_agent/    # Agente de investigación
│   │   └── optimizer_agent/   # Agente optimizador
│   ├── data/                  # Gestión de datos
│   │   ├── feeds/            # Feeds de mercado
│   │   └── processors/       # Procesadores de datos
│   ├── strategies/           # Estrategias de trading
│   ├── backtesting/         # Motor de backtesting
│   ├── risk_management/     # Gestión de riesgo
│   ├── execution/           # Ejecución de órdenes
│   └── utils/               # Utilidades
│
├── ⚛️ FRONTEND (React)
│   ├── src/
│   │   ├── components/      # Componentes React
│   │   ├── pages/          # Páginas principales
│   │   ├── services/       # Servicios API
│   │   ├── store/          # Estado global
│   │   └── types/          # Tipos TypeScript
│   ├── package.json        # Dependencias Node.js
│   └── vite.config.ts      # Configuración Vite
│
├── 🚀 SCRIPTS DE INICIO
│   ├── backend_main.py     # Iniciar solo backend
│   ├── frontend_main.py    # Iniciar solo frontend
│   └── main.py            # Sistema completo (legacy)
│
└── 📋 CONFIGURACIÓN
    ├── requirements_backend.txt  # Dependencias backend
    ├── docker-compose.yml       # Docker setup
    └── .env.example            # Variables de entorno
```

## 🔧 Comandos Principales

### Backend
```bash
# Desarrollo
python backend_main.py

# Producción con Gunicorn
gunicorn api.main:app --host 0.0.0.0 --port 8000

# Tests
pytest tests/

# Linting
black . && flake8 .
```

### Frontend
```bash
# Desarrollo
npm run dev

# Build para producción
npm run build

# Preview build
npm run preview

# Linting
npm run lint

# Type checking
npm run type-check
```

## 🌐 API Endpoints

### Market Data
- `GET /api/market/ticker/{symbol}` - Obtener ticker
- `GET /api/market/ohlcv/{symbol}` - Datos OHLCV
- `GET /api/market/symbols` - Símbolos disponibles

### Agentes IA
- `GET /api/agents/status` - Estado de agentes
- `POST /api/agents/trading/start` - Iniciar trading agent
- `POST /api/agents/trading/stop` - Detener trading agent
- `GET /api/agents/trading/decisions` - Decisiones de trading

### Estrategias
- `GET /api/strategies/available` - Estrategias disponibles
- `POST /api/strategies/signal` - Obtener señal de trading

### Sistema
- `GET /api/health` - Estado del sistema
- `GET /api/stats` - Estadísticas del sistema

### WebSocket
- `ws://localhost:8000/ws/market-data` - Datos en tiempo real
- `ws://localhost:8000/ws/trading-signals` - Señales de trading

## 🐳 Docker

### Backend
```bash
# Build imagen backend
docker build -t ai-trading-backend .

# Ejecutar backend
docker run -p 8000:8000 ai-trading-backend
```

### Docker Compose (Sistema completo)
```bash
# Iniciar todo el sistema
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener sistema
docker-compose down
```

## 🔒 Configuración de Seguridad

### Variables de Entorno (.env)
```env
# Trading Configuration
TRADING_MODE=paper  # paper | live
DEFAULT_EXCHANGE=binance
DEFAULT_SYMBOL=BTCUSDT

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Database
DATABASE_URL=postgresql://user:pass@localhost/trading

# External APIs
BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret
OPENAI_API_KEY=your_openai_key

# Logging
LOG_LEVEL=INFO
```

## 📊 Monitoreo y Logging

### Logs
- Backend: `logs/trading.log`
- Structured logging con `structlog`
- Métricas de rendimiento
- Alertas de riesgo

### Métricas
- Prometheus metrics en `/metrics`
- Health checks en `/api/health`
- Sistema de alertas integrado

## 🧪 Testing

### Backend
```bash
# Tests unitarios
pytest tests/unit/

# Tests de integración
pytest tests/integration/

# Coverage
pytest --cov=. tests/
```

### Frontend
```bash
# Tests con Vitest
npm run test

# Tests E2E con Playwright
npm run test:e2e
```

## 🚀 Despliegue

### Desarrollo
1. Ejecutar backend: `python backend_main.py`
2. Ejecutar frontend: `python frontend_main.py`

### Producción
1. Build frontend: `npm run build`
2. Servir con nginx/apache
3. Backend con gunicorn + nginx
4. Base de datos PostgreSQL
5. Redis para cache

## 🔄 Migración desde v1.0

### Cambios Principales
- ❌ Eliminado Streamlit del backend
- ✅ API REST pura con FastAPI
- ✅ Frontend React independiente
- ✅ Separación clara de responsabilidades
- ✅ Mejor escalabilidad

### Pasos de Migración
1. Usar `requirements_backend.txt` para backend
2. Configurar frontend con `package.json`
3. Actualizar scripts de inicio
4. Migrar configuraciones a `.env`

## 🤝 Contribución

1. Fork el proyecto
2. Crear branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## 📝 Licencia

MIT License - ver `LICENSE` para detalles.

## 🆘 Soporte

- 📧 Email: support@ai-trading-system.com
- 💬 Discord: [AI Trading Community](https://discord.gg/ai-trading)
- 📖 Docs: [docs.ai-trading-system.com](https://docs.ai-trading-system.com)

---

**⚠️ ADVERTENCIA**: Este sistema es para fines educativos y de investigación. Siempre usa paper trading antes de operar con dinero real. El trading conlleva riesgos significativos.