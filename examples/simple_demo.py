#!/usr/bin/env python3
"""
🚀 Demo Simplificado del Sistema de Trading con IA

Demostración básica de las funcionalidades principales sin dependencias externas.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.technical.indicators import RSIStrategy, MACDStrategy, MultiIndicatorStrategy
from backtesting.engine.backtest_engine import BacktestEngine
from utils.logging.logger import setup_logging


def generate_sample_data(days: int = 180) -> pd.DataFrame:
    """Generar datos de ejemplo para demostración."""
    print(f"📊 Generando {days} días de datos de ejemplo...")
    
    # Configurar semilla para reproducibilidad
    np.random.seed(42)
    
    # Generar fechas (cada hora)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='1H')
    
    # Simular precio de Bitcoin con tendencia alcista
    initial_price = 40000
    trend = 0.00005  # Tendencia alcista pequeña
    volatility = 0.015  # Volatilidad del 1.5%
    
    prices = [initial_price]
    for i in range(1, len(dates)):
        # Precio con tendencia + ruido aleatorio
        change = trend + np.random.normal(0, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1000))  # Precio mínimo
    
    # Crear datos OHLCV realistas
    data = []
    for i, (date, close_price) in enumerate(zip(dates, prices)):
        # Simular OHLC basado en el precio de cierre
        intraday_volatility = abs(np.random.normal(0, 0.008))
        
        high = close_price * (1 + intraday_volatility)
        low = close_price * (1 - intraday_volatility)
        open_price = prices[i-1] if i > 0 else close_price
        
        # Asegurar consistencia OHLC
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        # Volumen correlacionado con volatilidad
        volume = np.random.uniform(50, 200) * (1 + intraday_volatility * 10)
        
        data.append({
            'timestamp': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close_price, 2),
            'volume': round(volume, 2)
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    print(f"✅ Datos generados: {len(df)} velas")
    print(f"📈 Precio inicial: ${df['close'].iloc[0]:,.2f}")
    print(f"📈 Precio final: ${df['close'].iloc[-1]:,.2f}")
    
    total_return = ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
    print(f"📊 Rendimiento del activo: {total_return:.2f}%")
    
    return df


def demo_technical_indicators():
    """Demostrar el funcionamiento de los indicadores técnicos."""
    print("\n🧠 DEMO: Indicadores Técnicos")
    print("=" * 50)
    
    # Generar datos de prueba
    data = generate_sample_data(days=90)
    
    # Probar estrategia RSI
    print("\n📊 Probando Estrategia RSI...")
    rsi_strategy = RSIStrategy(rsi_period=14, oversold_threshold=30, overbought_threshold=70)
    
    # Analizar últimas 50 velas
    recent_data = data.tail(50)
    signal = rsi_strategy.analyze(recent_data)
    
    if signal:
        print(f"🎯 Señal RSI: {signal.signal.value.upper()}")
        print(f"💪 Fuerza: {signal.strength:.2f}")
        print(f"💰 Precio: ${signal.price:.2f}")
        print(f"📝 Razón: {signal.reason}")
        print(f"📊 RSI: {signal.indicators.get('rsi', 'N/A'):.2f}")
    else:
        print("❌ No se pudo generar señal RSI")
    
    # Probar estrategia MACD
    print("\n📈 Probando Estrategia MACD...")
    macd_strategy = MACDStrategy()
    signal = macd_strategy.analyze(recent_data)
    
    if signal:
        print(f"🎯 Señal MACD: {signal.signal.value.upper()}")
        print(f"💪 Fuerza: {signal.strength:.2f}")
        print(f"💰 Precio: ${signal.price:.2f}")
        print(f"📝 Razón: {signal.reason}")
        indicators = signal.indicators
        print(f"📊 MACD: {indicators.get('macd', 0):.4f}")
        print(f"📊 Signal: {indicators.get('signal', 0):.4f}")
        print(f"📊 Histogram: {indicators.get('histogram', 0):.4f}")
    else:
        print("❌ No se pudo generar señal MACD")
    
    # Probar estrategia multi-indicador
    print("\n🔄 Probando Estrategia Multi-Indicador...")
    multi_strategy = MultiIndicatorStrategy()
    signal = multi_strategy.analyze(recent_data)
    
    if signal:
        print(f"🎯 Señal Multi: {signal.signal.value.upper()}")
        print(f"💪 Fuerza: {signal.strength:.2f}")
        print(f"💰 Precio: ${signal.price:.2f}")
        print(f"📝 Razón: {signal.reason}")
        print(f"📊 Indicadores combinados: {len(signal.indicators)} métricas")
    else:
        print("❌ No se pudo generar señal multi-indicador")


def demo_backtesting():
    """Demostrar el sistema de backtesting."""
    print("\n🔬 DEMO: Sistema de Backtesting")
    print("=" * 50)
    
    # Generar datos más largos para backtesting
    data = generate_sample_data(days=120)  # 4 meses
    
    # Configurar motor de backtesting
    initial_capital = 10000
    backtest_engine = BacktestEngine(
        initial_capital=initial_capital,
        commission_rate=0.001,  # 0.1%
        slippage=0.0001,       # 0.01%
        max_position_size=0.8   # 80% del capital máximo
    )
    
    print(f"\n💰 Capital inicial: ${initial_capital:,}")
    print(f"💸 Comisión: {backtest_engine.commission_rate * 100:.2f}%")
    print(f"📊 Slippage: {backtest_engine.slippage * 100:.3f}%")
    
    # Probar estrategia RSI
    print(f"\n🧠 Backtesting Estrategia RSI...")
    print("-" * 30)
    
    rsi_strategy = RSIStrategy(rsi_period=14, oversold_threshold=35, overbought_threshold=65)
    
    try:
        result = backtest_engine.run_backtest(
            strategy=rsi_strategy,
            data=data,
            symbol="BTCUSDT"
        )
        
        print(f"📈 Rendimiento Total: {result['total_return']:.2f}%")
        print(f"🎯 Trades Totales: {result['total_trades']}")
        
        if result['total_trades'] > 0:
            print(f"✅ Trades Ganadores: {result['winning_trades']} ({result['win_rate']:.1f}%)")
            print(f"❌ Trades Perdedores: {result['losing_trades']}")
            print(f"⚖️ Factor de Beneficio: {result['profit_factor']:.2f}")
            print(f"📉 Máximo Drawdown: {result['max_drawdown']:.2f}%")
            print(f"📊 Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            print(f"💵 Capital Final: ${result['final_capital']:,.2f}")
            
            # Mostrar algunos trades
            if result['trades']:
                print(f"\n📋 Últimos 3 trades:")
                for i, trade in enumerate(result['trades'][-3:]):
                    profit_emoji = "💚" if trade.is_winner else "💔"
                    print(f"  {profit_emoji} Trade {i+1}: {trade.side} @ ${trade.entry_price:.2f} → ${trade.exit_price:.2f} = {trade.pnl_percent:.2f}%")
        else:
            print("⚠️ No se ejecutaron trades")
            
    except Exception as e:
        print(f"❌ Error en backtesting: {e}")


def demo_risk_analysis():
    """Demostrar análisis de riesgo básico."""
    print("\n🛡️ DEMO: Análisis de Riesgo")
    print("=" * 50)
    
    # Simular datos de portafolio
    portfolio_value = 50000
    positions = {
        'BTCUSDT': {'size': 0.5, 'price': 45000, 'entry_price': 42000},
        'ETHUSDT': {'size': 2.0, 'price': 3200, 'entry_price': 3000}
    }
    
    print(f"💼 Valor del Portafolio: ${portfolio_value:,}")
    print(f"📊 Posiciones Activas: {len(positions)}")
    
    total_exposure = 0
    for symbol, pos in positions.items():
        position_value = abs(pos['size'] * pos['price'])
        weight = (position_value / portfolio_value) * 100
        pnl = (pos['price'] - pos['entry_price']) / pos['entry_price'] * 100
        
        total_exposure += position_value
        
        print(f"\n🪙 {symbol}:")
        print(f"  📏 Tamaño: {pos['size']}")
        print(f"  💰 Valor: ${position_value:,.2f} ({weight:.1f}%)")
        print(f"  📈 PnL: {pnl:+.2f}%")
    
    exposure_percent = (total_exposure / portfolio_value) * 100
    print(f"\n📊 Exposición Total: {exposure_percent:.1f}%")
    
    # Análisis de riesgo básico
    if exposure_percent > 90:
        print("🚨 RIESGO ALTO: Exposición muy alta")
    elif exposure_percent > 70:
        print("⚠️ RIESGO MEDIO: Exposición considerable")
    else:
        print("✅ RIESGO BAJO: Exposición controlada")
    
    # Recomendaciones
    print(f"\n💡 Recomendaciones:")
    if exposure_percent > 80:
        print("  • Considerar reducir posiciones")
        print("  • Implementar stop-loss más estrictos")
    
    print("  • Diversificar en más activos")
    print("  • Monitorear correlaciones entre posiciones")
    print("  • Revisar límites de riesgo regularmente")


def main():
    """Función principal del demo."""
    print("🤖 AI Trading System - Demo Simplificado")
    print("=" * 60)
    print("Sistema de trading avanzado con agentes IA")
    print("Versión de demostración sin dependencias externas")
    print("=" * 60)
    
    # Configurar logging básico
    logger = setup_logging(level="INFO")
    
    try:
        # Demo 1: Indicadores Técnicos
        demo_technical_indicators()
        
        # Demo 2: Backtesting
        demo_backtesting()
        
        # Demo 3: Análisis de Riesgo
        demo_risk_analysis()
        
        # Resumen final
        print("\n" + "=" * 60)
        print("✅ DEMO COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        
        print("\n🎯 Funcionalidades Demostradas:")
        print("  ✅ Indicadores técnicos (RSI, MACD, Multi-Indicador)")
        print("  ✅ Sistema de backtesting completo")
        print("  ✅ Análisis de riesgo básico")
        print("  ✅ Generación de señales de trading")
        print("  ✅ Cálculo de métricas de rendimiento")
        
        print("\n🚀 Próximos Pasos:")
        print("  1. Configurar APIs de exchanges reales")
        print("  2. Implementar agentes IA avanzados")
        print("  3. Conectar dashboard en tiempo real")
        print("  4. Añadir más estrategias de trading")
        print("  5. Implementar machine learning")
        
        print("\n⚠️ IMPORTANTE:")
        print("  • Este es un sistema de demostración")
        print("  • Siempre usar paper trading primero")
        print("  • Nunca invertir más de lo que puedes permitirte perder")
        print("  • El trading conlleva riesgos significativos")
        
        print("\n🎉 ¡Gracias por probar el AI Trading System!")
        
    except Exception as e:
        print(f"\n❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())