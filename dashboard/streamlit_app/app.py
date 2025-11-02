"""
📱 Dashboard de Trading con IA

Dashboard interactivo para monitorear el sistema de trading,
visualizar métricas, señales y rendimiento en tiempo real.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Configurar página
st.set_page_config(
    page_title="🤖 AI Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    
    .status-running {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-stopped {
        color: #dc3545;
        font-weight: bold;
    }
    
    .signal-buy {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    
    .signal-sell {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
    
    .signal-hold {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)


class TradingDashboard:
    """Dashboard principal del sistema de trading."""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Inicializar estado de la sesión."""
        if 'last_update' not in st.session_state:
            st.session_state.last_update = datetime.now()
        
        if 'mock_data_initialized' not in st.session_state:
            st.session_state.mock_data_initialized = False
            self.initialize_mock_data()
    
    def initialize_mock_data(self):
        """Inicializar datos de ejemplo para demostración."""
        # Datos de ejemplo del agente
        st.session_state.agent_status = {
            'agent_id': 'trading_agent_001',
            'is_running': True,
            'last_update': datetime.now().isoformat(),
            'active_strategies': ['multi', 'rsi'],
            'performance_metrics': {
                'total_decisions': 156,
                'recent_decisions': 24,
                'buy_decisions': 12,
                'sell_decisions': 8,
                'avg_confidence': 0.73,
                'avg_risk': 0.42
            },
            'total_decisions': 156,
            'recent_decisions': 24
        }
        
        # Datos de ejemplo de trading
        st.session_state.trading_data = self.generate_mock_trading_data()
        st.session_state.signals_data = self.generate_mock_signals()
        st.session_state.performance_data = self.generate_mock_performance()
        
        st.session_state.mock_data_initialized = True
    
    def generate_mock_trading_data(self) -> pd.DataFrame:
        """Generar datos de trading de ejemplo."""
        import numpy as np
        
        # Generar datos OHLCV simulados
        dates = pd.date_range(start='2024-01-01', end='2024-11-02', freq='1H')
        np.random.seed(42)
        
        # Simular precio de Bitcoin
        price_base = 45000
        returns = np.random.normal(0, 0.02, len(dates))
        prices = [price_base]
        
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 1000))  # Precio mínimo
        
        # Crear OHLCV
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = prices[i-1] if i > 0 else price
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        return df.tail(200)  # Últimas 200 velas
    
    def generate_mock_signals(self) -> List[Dict]:
        """Generar señales de ejemplo."""
        signals = []
        base_time = datetime.now() - timedelta(hours=24)
        
        signal_types = ['buy', 'sell', 'hold']
        strategies = ['RSI', 'MACD', 'Bollinger Bands', 'Multi-Indicator']
        
        for i in range(20):
            signal_time = base_time + timedelta(minutes=i*30)
            signal_type = np.random.choice(signal_types, p=[0.3, 0.3, 0.4])
            strategy = np.random.choice(strategies)
            
            signals.append({
                'timestamp': signal_time,
                'signal': signal_type,
                'strategy': strategy,
                'confidence': np.random.uniform(0.5, 0.95),
                'price': np.random.uniform(44000, 46000),
                'reason': f"{strategy} signal: {'bullish' if signal_type == 'buy' else 'bearish' if signal_type == 'sell' else 'neutral'}"
            })
        
        return sorted(signals, key=lambda x: x['timestamp'], reverse=True)
    
    def generate_mock_performance(self) -> Dict:
        """Generar métricas de rendimiento de ejemplo."""
        return {
            'total_return': 12.5,
            'total_trades': 45,
            'winning_trades': 28,
            'losing_trades': 17,
            'win_rate': 62.2,
            'avg_win': 2.3,
            'avg_loss': -1.8,
            'profit_factor': 1.42,
            'max_drawdown': 8.7,
            'sharpe_ratio': 1.85,
            'calmar_ratio': 1.44
        }
    
    def run(self):
        """Ejecutar el dashboard."""
        # Header principal
        st.markdown('<h1 class="main-header">🤖 AI Trading System Dashboard</h1>', unsafe_allow_html=True)
        
        # Sidebar
        self.render_sidebar()
        
        # Contenido principal
        self.render_main_content()
        
        # Auto-refresh cada 30 segundos
        if st.button("🔄 Actualizar Datos"):
            st.session_state.last_update = datetime.now()
            st.experimental_rerun()
    
    def render_sidebar(self):
        """Renderizar sidebar con controles."""
        st.sidebar.markdown("## 🎛️ Control Panel")
        
        # Estado del sistema
        agent_status = st.session_state.agent_status
        status_text = "🟢 ACTIVO" if agent_status['is_running'] else "🔴 DETENIDO"
        status_class = "status-running" if agent_status['is_running'] else "status-stopped"
        
        st.sidebar.markdown(f'**Estado del Sistema:** <span class="{status_class}">{status_text}</span>', 
                           unsafe_allow_html=True)
        
        # Configuración
        st.sidebar.markdown("### ⚙️ Configuración")
        
        trading_mode = st.sidebar.selectbox(
            "Modo de Trading",
            ["Paper Trading", "Live Trading"],
            index=0
        )
        
        symbol = st.sidebar.selectbox(
            "Símbolo",
            ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT"],
            index=0
        )
        
        timeframe = st.sidebar.selectbox(
            "Marco Temporal",
            ["1m", "5m", "15m", "1h", "4h", "1d"],
            index=3
        )
        
        # Estrategias activas
        st.sidebar.markdown("### 🧠 Estrategias Activas")
        active_strategies = agent_status.get('active_strategies', [])
        for strategy in active_strategies:
            st.sidebar.markdown(f"✅ {strategy.upper()}")
        
        # Métricas rápidas
        st.sidebar.markdown("### 📊 Métricas Rápidas")
        metrics = agent_status.get('performance_metrics', {})
        
        st.sidebar.metric(
            "Decisiones Totales",
            metrics.get('total_decisions', 0)
        )
        
        st.sidebar.metric(
            "Confianza Promedio",
            f"{metrics.get('avg_confidence', 0):.2f}"
        )
        
        st.sidebar.metric(
            "Riesgo Promedio",
            f"{metrics.get('avg_risk', 0):.2f}"
        )
    
    def render_main_content(self):
        """Renderizar contenido principal."""
        # Tabs principales
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Trading", "🤖 Agentes", "📊 Rendimiento", 
            "🔍 Señales", "⚙️ Configuración"
        ])
        
        with tab1:
            self.render_trading_tab()
        
        with tab2:
            self.render_agents_tab()
        
        with tab3:
            self.render_performance_tab()
        
        with tab4:
            self.render_signals_tab()
        
        with tab5:
            self.render_config_tab()
    
    def render_trading_tab(self):
        """Renderizar tab de trading."""
        st.markdown("## 📈 Vista de Trading")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Precio Actual",
                "$45,234.56",
                delta="$234.56 (0.52%)"
            )
        
        with col2:
            st.metric(
                "Volumen 24h",
                "1,234.56 BTC",
                delta="12.3%"
            )
        
        with col3:
            st.metric(
                "Posición Actual",
                "0.0234 BTC",
                delta="$1,059.45"
            )
        
        with col4:
            st.metric(
                "PnL Diario",
                "$156.78",
                delta="1.2%"
            )
        
        # Gráfico de precios
        st.markdown("### 📊 Gráfico de Precios")
        self.render_price_chart()
        
        # Indicadores técnicos
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_indicators_chart()
        
        with col2:
            self.render_volume_chart()
    
    def render_price_chart(self):
        """Renderizar gráfico de precios."""
        df = st.session_state.trading_data
        
        fig = go.Figure()
        
        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="BTCUSDT"
        ))
        
        # Configuración
        fig.update_layout(
            title="Bitcoin/USDT - 1H",
            yaxis_title="Precio (USDT)",
            xaxis_title="Tiempo",
            height=500,
            showlegend=False
        )
        
        fig.update_xaxes(rangeslider_visible=False)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_indicators_chart(self):
        """Renderizar gráfico de indicadores."""
        st.markdown("#### 📈 Indicadores Técnicos")
        
        # Datos simulados para RSI
        dates = pd.date_range(start='2024-11-01', periods=50, freq='1H')
        rsi_values = np.random.uniform(20, 80, 50)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=rsi_values,
            mode='lines',
            name='RSI',
            line=dict(color='purple')
        ))
        
        # Líneas de referencia
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sobrecompra")
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sobreventa")
        
        fig.update_layout(
            title="RSI (14)",
            yaxis_title="RSI",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_volume_chart(self):
        """Renderizar gráfico de volumen."""
        st.markdown("#### 📊 Volumen")
        
        df = st.session_state.trading_data
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            name='Volumen',
            marker_color='lightblue'
        ))
        
        fig.update_layout(
            title="Volumen de Trading",
            yaxis_title="Volumen",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_agents_tab(self):
        """Renderizar tab de agentes."""
        st.markdown("## 🤖 Estado de los Agentes")
        
        agent_status = st.session_state.agent_status
        
        # Estado general
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_color = "🟢" if agent_status['is_running'] else "🔴"
            st.markdown(f"### {status_color} Trading Agent")
            st.markdown(f"**ID:** {agent_status['agent_id']}")
            st.markdown(f"**Estado:** {'Activo' if agent_status['is_running'] else 'Detenido'}")
            st.markdown(f"**Última actualización:** {datetime.fromisoformat(agent_status['last_update']).strftime('%H:%M:%S')}")
        
        with col2:
            st.markdown("### 📊 Métricas de Rendimiento")
            metrics = agent_status['performance_metrics']
            st.metric("Decisiones Totales", metrics['total_decisions'])
            st.metric("Decisiones Recientes", metrics['recent_decisions'])
            st.metric("Confianza Promedio", f"{metrics['avg_confidence']:.2f}")
        
        with col3:
            st.markdown("### 🎯 Distribución de Decisiones")
            
            # Gráfico de dona
            labels = ['Compra', 'Venta', 'Mantener']
            values = [
                metrics['buy_decisions'],
                metrics['sell_decisions'],
                metrics['recent_decisions'] - metrics['buy_decisions'] - metrics['sell_decisions']
            ]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=['#28a745', '#dc3545', '#ffc107']
            )])
            
            fig.update_layout(height=300, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        # Historial de decisiones
        st.markdown("### 📋 Historial de Decisiones Recientes")
        
        # Tabla de decisiones simuladas
        decisions_data = []
        for i in range(10):
            time = datetime.now() - timedelta(minutes=i*15)
            action = np.random.choice(['buy', 'sell', 'hold'], p=[0.3, 0.3, 0.4])
            confidence = np.random.uniform(0.5, 0.95)
            
            decisions_data.append({
                'Tiempo': time.strftime('%H:%M'),
                'Acción': action.upper(),
                'Confianza': f"{confidence:.2f}",
                'Precio': f"${np.random.uniform(44000, 46000):,.2f}",
                'Razón': f"Señal {action} basada en indicadores técnicos"
            })
        
        df_decisions = pd.DataFrame(decisions_data)
        st.dataframe(df_decisions, use_container_width=True)
    
    def render_performance_tab(self):
        """Renderizar tab de rendimiento."""
        st.markdown("## 📊 Análisis de Rendimiento")
        
        performance = st.session_state.performance_data
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Rendimiento Total",
                f"{performance['total_return']:.1f}%",
                delta=f"{performance['total_return']:.1f}%"
            )
        
        with col2:
            st.metric(
                "Trades Totales",
                performance['total_trades'],
                delta=f"+{performance['total_trades']}"
            )
        
        with col3:
            st.metric(
                "Tasa de Acierto",
                f"{performance['win_rate']:.1f}%",
                delta=f"{performance['win_rate']:.1f}%"
            )
        
        with col4:
            st.metric(
                "Sharpe Ratio",
                f"{performance['sharpe_ratio']:.2f}",
                delta=f"{performance['sharpe_ratio']:.2f}"
            )
        
        # Gráficos de rendimiento
        col1, col2 = st.columns(2)
        
        with col1:
            # Curva de equity
            st.markdown("### 📈 Curva de Equity")
            
            dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
            equity_values = np.cumsum(np.random.normal(0.1, 2, 100)) + 10000
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=equity_values,
                mode='lines',
                name='Equity',
                line=dict(color='blue', width=2)
            ))
            
            fig.update_layout(
                yaxis_title="Valor del Portafolio ($)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Distribución de returns
            st.markdown("### 📊 Distribución de Returns")
            
            returns = np.random.normal(0.5, 3, 100)
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=returns,
                nbinsx=20,
                name='Returns',
                marker_color='lightgreen'
            ))
            
            fig.update_layout(
                xaxis_title="Return (%)",
                yaxis_title="Frecuencia",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de métricas detalladas
        st.markdown("### 📋 Métricas Detalladas")
        
        metrics_df = pd.DataFrame([
            ["Rendimiento Total", f"{performance['total_return']:.2f}%"],
            ["Trades Ganadores", f"{performance['winning_trades']} ({performance['win_rate']:.1f}%)"],
            ["Trades Perdedores", f"{performance['losing_trades']} ({100-performance['win_rate']:.1f}%)"],
            ["Ganancia Promedio", f"{performance['avg_win']:.2f}%"],
            ["Pérdida Promedio", f"{performance['avg_loss']:.2f}%"],
            ["Factor de Beneficio", f"{performance['profit_factor']:.2f}"],
            ["Máximo Drawdown", f"{performance['max_drawdown']:.2f}%"],
            ["Ratio de Calmar", f"{performance['calmar_ratio']:.2f}"]
        ], columns=["Métrica", "Valor"])
        
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
    
    def render_signals_tab(self):
        """Renderizar tab de señales."""
        st.markdown("## 🔍 Señales de Trading")
        
        signals = st.session_state.signals_data
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            signal_filter = st.selectbox(
                "Filtrar por Señal",
                ["Todas", "Compra", "Venta", "Mantener"]
            )
        
        with col2:
            strategy_filter = st.selectbox(
                "Filtrar por Estrategia",
                ["Todas", "RSI", "MACD", "Bollinger Bands", "Multi-Indicator"]
            )
        
        with col3:
            time_filter = st.selectbox(
                "Período",
                ["Última hora", "Últimas 6 horas", "Últimas 24 horas", "Última semana"]
            )
        
        # Lista de señales
        st.markdown("### 📋 Señales Recientes")
        
        for signal in signals[:10]:  # Mostrar últimas 10 señales
            signal_type = signal['signal']
            
            # Determinar clase CSS
            if signal_type == 'buy':
                css_class = 'signal-buy'
                icon = '🟢'
            elif signal_type == 'sell':
                css_class = 'signal-sell'
                icon = '🔴'
            else:
                css_class = 'signal-hold'
                icon = '🟡'
            
            # Renderizar señal
            st.markdown(f"""
            <div class="{css_class}">
                <strong>{icon} {signal_type.upper()}</strong> - {signal['strategy']}<br>
                <small>
                    🕐 {signal['timestamp'].strftime('%H:%M:%S')} | 
                    💰 ${signal['price']:,.2f} | 
                    🎯 Confianza: {signal['confidence']:.2f}<br>
                    📝 {signal['reason']}
                </small>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
    
    def render_config_tab(self):
        """Renderizar tab de configuración."""
        st.markdown("## ⚙️ Configuración del Sistema")
        
        # Configuración de trading
        st.markdown("### 💼 Configuración de Trading")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.number_input(
                "Tamaño Máximo de Posición (%)",
                min_value=1,
                max_value=100,
                value=5,
                help="Porcentaje máximo del portafolio por posición"
            )
            
            st.number_input(
                "Stop Loss (%)",
                min_value=0.1,
                max_value=10.0,
                value=2.0,
                step=0.1,
                help="Porcentaje de stop loss automático"
            )
            
            st.number_input(
                "Take Profit (%)",
                min_value=0.1,
                max_value=20.0,
                value=4.0,
                step=0.1,
                help="Porcentaje de take profit automático"
            )
        
        with col2:
            st.number_input(
                "Pérdida Máxima Diaria (%)",
                min_value=1,
                max_value=20,
                value=5,
                help="Pérdida máxima permitida por día"
            )
            
            st.selectbox(
                "Modo de Trading",
                ["Paper Trading", "Live Trading"],
                index=0,
                help="Modo de operación del sistema"
            )
            
            st.number_input(
                "Intervalo de Actualización (segundos)",
                min_value=10,
                max_value=3600,
                value=300,
                help="Frecuencia de actualización del agente"
            )
        
        # Configuración de estrategias
        st.markdown("### 🧠 Configuración de Estrategias")
        
        st.multiselect(
            "Estrategias Activas",
            ["RSI", "MACD", "Bollinger Bands", "Multi-Indicator"],
            default=["Multi-Indicator"],
            help="Seleccionar estrategias a utilizar"
        )
        
        # Configuración de notificaciones
        st.markdown("### 📢 Notificaciones")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Notificaciones por Email", value=False)
            st.text_input("Email de Notificaciones", placeholder="tu@email.com")
        
        with col2:
            st.checkbox("Notificaciones por Telegram", value=False)
            st.text_input("Token del Bot de Telegram", placeholder="123456:ABC-DEF...")
        
        # Botones de acción
        st.markdown("### 🎛️ Acciones del Sistema")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("▶️ Iniciar Sistema", type="primary"):
                st.success("Sistema iniciado correctamente")
        
        with col2:
            if st.button("⏸️ Pausar Sistema"):
                st.warning("Sistema pausado")
        
        with col3:
            if st.button("🛑 Detener Sistema"):
                st.error("Sistema detenido")
        
        with col4:
            if st.button("🔄 Reiniciar Sistema"):
                st.info("Sistema reiniciado")


def run_dashboard():
    """Función principal para ejecutar el dashboard."""
    dashboard = TradingDashboard()
    dashboard.run()


if __name__ == "__main__":
    run_dashboard()