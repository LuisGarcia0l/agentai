# 🤖 AI Trading System - Sistema de Trading con Agentes IA

Un sistema de trading avanzado que combina análisis técnico, machine learning y agentes autónomos para optimizar estrategias de trading en tiempo real.

## 🏗️ Arquitectura del Sistema

```
ai-trading-system/
├── 📊 data/                    # Capa de datos
│   ├── feeds/                  # APIs de mercado (Binance, Yahoo Finance)
│   ├── storage/               # Base de datos y cache
│   └── processors/            # Procesamiento de datos
├── 🧠 strategies/             # Estrategias de trading
│   ├── technical/             # Análisis técnico (RSI, MACD, etc.)
│   ├── ml_models/            # Modelos de Machine Learning
│   └── signals/              # Generación de señales
├── 🤖 agents/                # Agentes IA autónomos
│   ├── research_agent/       # Investigación de estrategias
│   ├── optimizer_agent/      # Optimización de parámetros
│   ├── risk_agent/          # Gestión de riesgo
│   └── trading_agent/       # Ejecución de trades
├── 💼 execution/             # Ejecución de órdenes
│   ├── brokers/             # Conexiones con exchanges
│   ├── paper_trading/       # Trading simulado
│   └── order_management/    # Gestión de órdenes
├── 📈 backtesting/          # Simulación y pruebas
│   ├── engine/              # Motor de backtesting
│   ├── metrics/             # Métricas de rendimiento
│   └── reports/             # Reportes de resultados
├── 🛡️ risk_management/      # Gestión de riesgo
│   ├── position_sizing/     # Tamaño de posiciones
│   ├── stop_loss/          # Stop-loss dinámico
│   └── portfolio/          # Gestión de portafolio
├── 📱 dashboard/            # Interface y monitoreo
│   ├── streamlit_app/      # Dashboard web
│   ├── monitoring/         # Monitoreo en tiempo real
│   └── alerts/            # Sistema de alertas
└── 🔧 utils/               # Utilidades
    ├── config/             # Configuración
    ├── logging/           # Sistema de logs
    └── helpers/           # Funciones auxiliares
```

## 🚀 Características Principales

### 🎯 Niveles de Autonomía
1. **Semi-automático**: Genera señales, tú decides
2. **Automatizado**: Ejecuta trades basado en reglas
3. **Autónomo**: Agentes IA optimizan y aprenden del mercado

### 🤖 Agentes IA Especializados
- **ResearchAgent**: Descubre y prueba nuevas estrategias
- **OptimizerAgent**: Optimiza parámetros automáticamente
- **RiskAgent**: Evalúa y ajusta el riesgo dinámicamente
- **TradingAgent**: Ejecuta operaciones validadas

### 📊 Estrategias Soportadas
- **Análisis Técnico**: RSI, MACD, Bollinger Bands, Medias Móviles
- **Machine Learning**: Random Forest, LSTM, Transformers
- **Estadísticas**: Cointegración, correlaciones, ARIMA
- **Reinforcement Learning**: Agentes que aprenden a maximizar ganancias

## 🛠️ Tecnologías Utilizadas

- **Python 3.11+**: Lenguaje principal
- **FastAPI**: API REST para servicios
- **Streamlit**: Dashboard interactivo
- **LangChain**: Orquestación de agentes IA
- **Pandas/NumPy**: Análisis de datos
- **Scikit-learn/PyTorch**: Machine Learning
- **CCXT**: Conexión con múltiples exchanges
- **Docker**: Containerización
- **PostgreSQL**: Base de datos principal

## 🚦 Instalación y Configuración

### Prerrequisitos
- Python 3.11+
- Docker y Docker Compose
- Cuenta en exchange (Binance recomendado)
- API keys del exchange

### Instalación Rápida
```bash
# Clonar el repositorio
git clone <repo-url>
cd ai-trading-system

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# Ejecutar con Docker
docker-compose up -d

# O ejecutar localmente
python main.py
```

## 📋 Plan de Desarrollo (8 Semanas)

### Semanas 1-2: Base del Sistema
- ✅ Estructura del proyecto
- ✅ APIs de datos (Binance, Yahoo Finance)
- ✅ Estrategias técnicas básicas
- ✅ Backtesting inicial

### Semanas 3-4: Automatización
- 🔄 Paper trading
- 🔄 Gestión de riesgo
- 🔄 Sistema de órdenes
- 🔄 Dashboard básico

### Semanas 5-6: Machine Learning
- 🔄 Modelos predictivos
- 🔄 Optimización de parámetros
- 🔄 Validación cruzada
- 🔄 Métricas avanzadas

### Semanas 7-8: Agentes IA
- 🔄 Agentes especializados
- 🔄 Comunicación entre agentes
- 🔄 Aprendizaje automático
- 🔄 Dashboard avanzado

## ⚠️ Advertencias Importantes

1. **Nunca operes en real sin paper trading extensivo**
2. **Siempre usa stop-loss y gestión de riesgo**
3. **Backtestea en diferentes condiciones de mercado**
4. **Mantén logs detallados de todas las decisiones**
5. **Empieza con cantidades pequeñas**

## 📊 Métricas de Rendimiento

- **Sharpe Ratio**: Rendimiento ajustado por riesgo
- **Max Drawdown**: Pérdida máxima desde el pico
- **Win Rate**: Porcentaje de trades ganadores
- **Profit Factor**: Ganancias/Pérdidas
- **Calmar Ratio**: Rendimiento anual/Max Drawdown

## 🤝 Contribución

Este es un proyecto en desarrollo activo. Las contribuciones son bienvenidas.

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles.

---

**⚡ Construido con IA para el futuro del trading automatizado**