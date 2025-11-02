#!/usr/bin/env python3
"""
📊 Ejemplo Básico de Backtesting

Script de ejemplo que demuestra cómo usar el sistema de trading
para hacer backtesting de estrategias.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.feeds.market_data import MarketDataManager
from strategies.technical.indicators import RSIStrategy, MACDStrategy, MultiIndicatorStrategy
from backtesting.engine.backtest_engine import BacktestEngine
from utils.config.settings import settings
from utils.logging.logger import setup_logging


def generate_sample_data(days: int = 365) -> pd.DataFrame:
    """
    Generar datos de ejemplo para backtesting.
    
    Args:
        days: Número de días de datos
    
    Returns:
        DataFrame con datos OHLCV
    """
    print(f"📊 Generando {days} días de datos de ejemplo...")
    
    # Configurar semilla para reproducibilidad
    np.random.seed(42)
    
    # Generar fechas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='1H')
    
    # Simular precio de Bitcoin
    initial_price = 45000
    returns = np.random.normal(0.0001, 0.02, len(dates))  # Drift positivo pequeño
    
    prices = [initial_price]
    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(max(new_price, 1000))  # Precio mínimo
    
    # Crear datos OHLCV
    data = []
    for i, (date, close_price) in enumerate(zip(dates, prices)):
        # Simular OHLC basado en el precio de cierre
        volatility = abs(np.random.normal(0, 0.01))
        
        high = close_price * (1 + volatility)
        low = close_price * (1 - volatility)
        open_price = prices[i-1] if i > 0 else close_price
        
        # Asegurar que OHLC sea consistente
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        volume = np.random.uniform(100, 1000)
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    print(f"✅ Datos generados: {len(df)} velas")
    print(f"📈 Precio inicial: ${df['close'].iloc[0]:,.2f}")
    print(f"📈 Precio final: ${df['close'].iloc[-1]:,.2f}")
    print(f"📊 Rendimiento total: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")
    
    return df


async def run_strategy_comparison():
    """Ejecutar comparación de múltiples estrategias."""
    print("\n🔬 Iniciando comparación de estrategias...")
    
    # Generar datos de prueba
    data = generate_sample_data(days=180)  # 6 meses de datos
    
    # Configurar motor de backtesting
    initial_capital = 10000
    backtest_engine = BacktestEngine(
        initial_capital=initial_capital,
        commission_rate=0.001,  # 0.1%
        slippage=0.0001,       # 0.01%
        max_position_size=0.95  # 95% del capital
    )
    
    # Estrategias a probar
    strategies = {
        'RSI': RSIStrategy(rsi_period=14, oversold_threshold=30, overbought_threshold=70),
        'MACD': MACDStrategy(fast_period=12, slow_period=26, signal_period=9),
        'Multi-Indicator': MultiIndicatorStrategy()
    }
    
    results = {}
    
    print(f"\n📊 Probando {len(strategies)} estrategias con ${initial_capital:,} inicial...")
    print("=" * 60)
    
    # Ejecutar backtesting para cada estrategia
    for name, strategy in strategies.items():
        print(f"\n🧠 Probando estrategia: {name}")
        print("-" * 40)
        
        try:
            result = backtest_engine.run_backtest(
                strategy=strategy,
                data=data,
                symbol="BTCUSDT"
            )
            
            results[name] = result
            
            # Mostrar resultados
            print(f"📈 Rendimiento Total: {result['total_return']:.2f}%")
            print(f"🎯 Trades Totales: {result['total_trades']}")
            print(f"✅ Trades Ganadores: {result['winning_trades']} ({result['win_rate']:.1f}%)")
            print(f"❌ Trades Perdedores: {result['losing_trades']}")
            print(f"💰 Ganancia Promedio: {result['avg_win']:.2f}%")
            print(f"💸 Pérdida Promedio: {result['avg_loss']:.2f}%")
            print(f"⚖️ Factor de Beneficio: {result['profit_factor']:.2f}")
            print(f"📉 Máximo Drawdown: {result['max_drawdown']:.2f}%")
            print(f"📊 Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            print(f"💵 Capital Final: ${result['final_capital']:,.2f}")
            
        except Exception as e:
            print(f"❌ Error probando {name}: {e}")
            results[name] = None
    
    # Comparación final
    print("\n" + "=" * 60)
    print("🏆 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    # Crear tabla de comparación
    comparison_data = []
    for name, result in results.items():
        if result:
            comparison_data.append({
                'Estrategia': name,
                'Rendimiento (%)': f"{result['total_return']:.2f}",
                'Trades': result['total_trades'],
                'Win Rate (%)': f"{result['win_rate']:.1f}",
                'Sharpe Ratio': f"{result['sharpe_ratio']:.2f}",
                'Max DD (%)': f"{result['max_drawdown']:.2f}",
                'Capital Final': f"${result['final_capital']:,.0f}"
            })
    
    if comparison_data:
        df_comparison = pd.DataFrame(comparison_data)
        print(df_comparison.to_string(index=False))
        
        # Encontrar mejor estrategia
        best_strategy = max(
            [(name, result) for name, result in results.items() if result],
            key=lambda x: x[1]['total_return']
        )
        
        print(f"\n🥇 Mejor Estrategia: {best_strategy[0]}")
        print(f"📈 Rendimiento: {best_strategy[1]['total_return']:.2f}%")
        print(f"📊 Sharpe Ratio: {best_strategy[1]['sharpe_ratio']:.2f}")
    
    return results


def main():
    """Función principal."""
    print("🤖 AI Trading System - Ejemplo de Backtesting")
    print("=" * 60)
    
    # Configurar logging
    logger = setup_logging(level="INFO")
    
    try:
        # Ejecutar comparación de estrategias
        loop = asyncio.get_event_loop()
        
        print("\n🔬 FASE 1: Comparación de Estrategias")
        comparison_results = loop.run_until_complete(run_strategy_comparison())
        
        print("\n✅ Backtesting completado exitosamente!")
        print("\n💡 RECOMENDACIONES:")
        print("1. Siempre usa paper trading antes de trading real")
        print("2. Prueba las estrategias en diferentes condiciones de mercado")
        print("3. Considera la gestión de riesgo en todas las operaciones")
        print("4. Monitorea las métricas de drawdown regularmente")
        print("5. Ajusta los parámetros según el rendimiento histórico")
        
    except Exception as e:
        print(f"❌ Error en backtesting: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())