"""
Servicio de backtesting para validar estrategias
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json

from backend.services.binance_service import BinanceService
from backend.core.config import settings

class BacktestingService:
    """
    Servicio para realizar backtesting de estrategias de trading
    
    Funcionalidades:
    - Simulación histórica de estrategias
    - Cálculo de métricas de performance
    - Análisis de drawdown y riesgo
    - Comparación de estrategias
    """
    
    def __init__(self):
        self.logger = logging.getLogger("services.backtesting")
        self.binance_service: Optional[BinanceService] = None
        self.strategies = self._load_strategies()
        self.is_initialized = False
        
    async def initialize(self):
        """Inicializar el servicio de backtesting"""
        try:
            self.binance_service = BinanceService()
            await self.binance_service.initialize()
            
            self.is_initialized = True
            self.logger.info("✅ Backtesting Service inicializado")
            
        except Exception as e:
            self.logger.error(f"Error inicializando Backtesting Service: {e}")
            raise
    
    def _load_strategies(self) -> Dict[str, Any]:
        """Cargar estrategias disponibles"""
        return {
            "rsi_strategy": {
                "name": "RSI Strategy",
                "description": "Estrategia basada en RSI con niveles de sobrecompra/sobreventa",
                "parameters": {
                    "rsi_period": {"default": 14, "min": 5, "max": 50},
                    "oversold_level": {"default": 30, "min": 20, "max": 40},
                    "overbought_level": {"default": 70, "min": 60, "max": 80},
                    "stop_loss": {"default": 0.02, "min": 0.01, "max": 0.05},
                    "take_profit": {"default": 0.04, "min": 0.02, "max": 0.10}
                }
            },
            "macd_strategy": {
                "name": "MACD Strategy",
                "description": "Estrategia basada en cruces de MACD",
                "parameters": {
                    "fast_period": {"default": 12, "min": 8, "max": 20},
                    "slow_period": {"default": 26, "min": 20, "max": 35},
                    "signal_period": {"default": 9, "min": 5, "max": 15},
                    "stop_loss": {"default": 0.025, "min": 0.01, "max": 0.05},
                    "take_profit": {"default": 0.05, "min": 0.02, "max": 0.10}
                }
            },
            "ma_crossover": {
                "name": "Moving Average Crossover",
                "description": "Estrategia de cruce de medias móviles",
                "parameters": {
                    "fast_ma": {"default": 20, "min": 10, "max": 50},
                    "slow_ma": {"default": 50, "min": 30, "max": 100},
                    "stop_loss": {"default": 0.03, "min": 0.01, "max": 0.05},
                    "take_profit": {"default": 0.06, "min": 0.03, "max": 0.12}
                }
            },
            "bollinger_bands": {
                "name": "Bollinger Bands Strategy",
                "description": "Estrategia basada en Bollinger Bands",
                "parameters": {
                    "period": {"default": 20, "min": 10, "max": 30},
                    "std_dev": {"default": 2.0, "min": 1.5, "max": 2.5},
                    "stop_loss": {"default": 0.02, "min": 0.01, "max": 0.04},
                    "take_profit": {"default": 0.04, "min": 0.02, "max": 0.08}
                }
            }
        }
    
    async def run_backtest(self, backtest_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutar backtesting de una estrategia
        
        Args:
            backtest_params: Parámetros del backtest
            
        Returns:
            Resultados del backtesting
        """
        try:
            strategy_name = backtest_params.get("strategy_name")
            symbol = backtest_params.get("symbol", settings.DEFAULT_TRADING_PAIR)
            start_date = backtest_params.get("start_date", "2023-01-01")
            end_date = backtest_params.get("end_date", "2024-01-01")
            initial_capital = backtest_params.get("initial_capital", 1000.0)
            parameters = backtest_params.get("parameters", {})
            
            self.logger.info(f"🔄 Ejecutando backtest: {strategy_name} en {symbol}")
            
            # Validar estrategia
            if strategy_name not in self.strategies:
                raise ValueError(f"Estrategia no encontrada: {strategy_name}")
            
            # Obtener datos históricos
            df = await self._get_historical_data(symbol, start_date, end_date)
            if df.empty:
                raise ValueError(f"No se pudieron obtener datos históricos para {symbol}")
            
            # Ejecutar estrategia
            trades, equity_curve = await self._execute_strategy(
                strategy_name, df, parameters, initial_capital
            )
            
            # Calcular métricas
            metrics = self._calculate_metrics(trades, equity_curve, initial_capital)
            
            # Preparar resultados
            result = {
                "success": True,
                "strategy_name": strategy_name,
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "final_capital": equity_curve[-1] if equity_curve else initial_capital,
                "parameters": parameters,
                "metrics": metrics,
                "trades": trades,
                "equity_curve": equity_curve,
                "data_points": len(df),
                "execution_time": datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"✅ Backtest completado: {len(trades)} trades, Return: {metrics.get('total_return', 0):.2f}%")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error ejecutando backtest: {e}")
            return {
                "success": False,
                "error": str(e),
                "strategy_name": backtest_params.get("strategy_name"),
                "symbol": backtest_params.get("symbol")
            }
    
    async def _get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Obtener datos históricos para backtesting"""
        try:
            # Calcular número de períodos necesarios
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            days_diff = (end_dt - start_dt).days
            
            # Usar intervalos de 1 hora para backtesting detallado
            periods = min(days_diff * 24, 1000)  # Máximo 1000 períodos
            
            df = await self.binance_service.get_historical_data(symbol, "1h", periods)
            
            # Filtrar por fechas si es necesario
            if not df.empty:
                df = df.loc[start_dt:end_dt]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos históricos: {e}")
            return pd.DataFrame()
    
    async def _execute_strategy(self, strategy_name: str, df: pd.DataFrame, 
                              parameters: Dict[str, Any], initial_capital: float) -> Tuple[List[Dict], List[float]]:
        """Ejecutar estrategia en datos históricos"""
        try:
            # Obtener parámetros con valores por defecto
            strategy_config = self.strategies[strategy_name]
            params = {}
            for param_name, param_config in strategy_config["parameters"].items():
                params[param_name] = parameters.get(param_name, param_config["default"])
            
            # Ejecutar estrategia específica
            if strategy_name == "rsi_strategy":
                return await self._execute_rsi_strategy(df, params, initial_capital)
            elif strategy_name == "macd_strategy":
                return await self._execute_macd_strategy(df, params, initial_capital)
            elif strategy_name == "ma_crossover":
                return await self._execute_ma_crossover_strategy(df, params, initial_capital)
            elif strategy_name == "bollinger_bands":
                return await self._execute_bollinger_strategy(df, params, initial_capital)
            else:
                raise ValueError(f"Estrategia no implementada: {strategy_name}")
                
        except Exception as e:
            self.logger.error(f"Error ejecutando estrategia {strategy_name}: {e}")
            return [], [initial_capital]
    
    async def _execute_rsi_strategy(self, df: pd.DataFrame, params: Dict[str, Any], 
                                  initial_capital: float) -> Tuple[List[Dict], List[float]]:
        """Ejecutar estrategia RSI"""
        import ta
        
        # Calcular RSI
        rsi = ta.momentum.RSIIndicator(df['close'], window=params['rsi_period']).rsi()
        
        trades = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        position = None
        
        for i in range(1, len(df)):
            current_price = df['close'].iloc[i]
            current_rsi = rsi.iloc[i]
            timestamp = df.index[i]
            
            # Señal de compra (RSI oversold)
            if position is None and current_rsi < params['oversold_level']:
                # Abrir posición larga
                quantity = current_capital * 0.95 / current_price  # 95% del capital
                position = {
                    'type': 'LONG',
                    'entry_price': current_price,
                    'entry_time': timestamp,
                    'quantity': quantity,
                    'stop_loss': current_price * (1 - params['stop_loss']),
                    'take_profit': current_price * (1 + params['take_profit'])
                }
            
            # Verificar salida de posición
            elif position is not None:
                exit_signal = False
                exit_reason = ""
                
                # Señal de venta (RSI overbought)
                if current_rsi > params['overbought_level']:
                    exit_signal = True
                    exit_reason = "RSI_OVERBOUGHT"
                
                # Stop loss
                elif current_price <= position['stop_loss']:
                    exit_signal = True
                    exit_reason = "STOP_LOSS"
                
                # Take profit
                elif current_price >= position['take_profit']:
                    exit_signal = True
                    exit_reason = "TAKE_PROFIT"
                
                if exit_signal:
                    # Cerrar posición
                    pnl = (current_price - position['entry_price']) * position['quantity']
                    current_capital += pnl
                    
                    trade = {
                        'entry_time': position['entry_time'].isoformat(),
                        'exit_time': timestamp.isoformat(),
                        'entry_price': position['entry_price'],
                        'exit_price': current_price,
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'pnl_pct': (pnl / (position['entry_price'] * position['quantity'])) * 100,
                        'exit_reason': exit_reason,
                        'duration_hours': (timestamp - position['entry_time']).total_seconds() / 3600
                    }
                    
                    trades.append(trade)
                    position = None
            
            equity_curve.append(current_capital)
        
        return trades, equity_curve
    
    async def _execute_macd_strategy(self, df: pd.DataFrame, params: Dict[str, Any], 
                                   initial_capital: float) -> Tuple[List[Dict], List[float]]:
        """Ejecutar estrategia MACD"""
        import ta
        
        # Calcular MACD
        macd = ta.trend.MACD(
            df['close'], 
            window_fast=params['fast_period'],
            window_slow=params['slow_period'],
            window_sign=params['signal_period']
        )
        
        macd_line = macd.macd()
        macd_signal = macd.macd_signal()
        
        trades = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        position = None
        
        for i in range(1, len(df)):
            current_price = df['close'].iloc[i]
            current_macd = macd_line.iloc[i]
            current_signal = macd_signal.iloc[i]
            prev_macd = macd_line.iloc[i-1]
            prev_signal = macd_signal.iloc[i-1]
            timestamp = df.index[i]
            
            # Señal de compra (MACD cruza por encima de la señal)
            if (position is None and 
                prev_macd <= prev_signal and 
                current_macd > current_signal):
                
                quantity = current_capital * 0.95 / current_price
                position = {
                    'type': 'LONG',
                    'entry_price': current_price,
                    'entry_time': timestamp,
                    'quantity': quantity,
                    'stop_loss': current_price * (1 - params['stop_loss']),
                    'take_profit': current_price * (1 + params['take_profit'])
                }
            
            # Señal de venta (MACD cruza por debajo de la señal)
            elif (position is not None and 
                  prev_macd >= prev_signal and 
                  current_macd < current_signal):
                
                pnl = (current_price - position['entry_price']) * position['quantity']
                current_capital += pnl
                
                trade = {
                    'entry_time': position['entry_time'].isoformat(),
                    'exit_time': timestamp.isoformat(),
                    'entry_price': position['entry_price'],
                    'exit_price': current_price,
                    'quantity': position['quantity'],
                    'pnl': pnl,
                    'pnl_pct': (pnl / (position['entry_price'] * position['quantity'])) * 100,
                    'exit_reason': "MACD_SIGNAL",
                    'duration_hours': (timestamp - position['entry_time']).total_seconds() / 3600
                }
                
                trades.append(trade)
                position = None
            
            # Verificar stop loss y take profit
            elif position is not None:
                if current_price <= position['stop_loss']:
                    pnl = (current_price - position['entry_price']) * position['quantity']
                    current_capital += pnl
                    
                    trade = {
                        'entry_time': position['entry_time'].isoformat(),
                        'exit_time': timestamp.isoformat(),
                        'entry_price': position['entry_price'],
                        'exit_price': current_price,
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'pnl_pct': (pnl / (position['entry_price'] * position['quantity'])) * 100,
                        'exit_reason': "STOP_LOSS",
                        'duration_hours': (timestamp - position['entry_time']).total_seconds() / 3600
                    }
                    
                    trades.append(trade)
                    position = None
                
                elif current_price >= position['take_profit']:
                    pnl = (current_price - position['entry_price']) * position['quantity']
                    current_capital += pnl
                    
                    trade = {
                        'entry_time': position['entry_time'].isoformat(),
                        'exit_time': timestamp.isoformat(),
                        'entry_price': position['entry_price'],
                        'exit_price': current_price,
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'pnl_pct': (pnl / (position['entry_price'] * position['quantity'])) * 100,
                        'exit_reason': "TAKE_PROFIT",
                        'duration_hours': (timestamp - position['entry_time']).total_seconds() / 3600
                    }
                    
                    trades.append(trade)
                    position = None
            
            equity_curve.append(current_capital)
        
        return trades, equity_curve
    
    async def _execute_ma_crossover_strategy(self, df: pd.DataFrame, params: Dict[str, Any], 
                                           initial_capital: float) -> Tuple[List[Dict], List[float]]:
        """Ejecutar estrategia de cruce de medias móviles"""
        # Calcular medias móviles
        fast_ma = df['close'].rolling(window=params['fast_ma']).mean()
        slow_ma = df['close'].rolling(window=params['slow_ma']).mean()
        
        trades = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        position = None
        
        for i in range(1, len(df)):
            current_price = df['close'].iloc[i]
            current_fast_ma = fast_ma.iloc[i]
            current_slow_ma = slow_ma.iloc[i]
            prev_fast_ma = fast_ma.iloc[i-1]
            prev_slow_ma = slow_ma.iloc[i-1]
            timestamp = df.index[i]
            
            # Señal de compra (MA rápida cruza por encima de MA lenta)
            if (position is None and 
                prev_fast_ma <= prev_slow_ma and 
                current_fast_ma > current_slow_ma):
                
                quantity = current_capital * 0.95 / current_price
                position = {
                    'type': 'LONG',
                    'entry_price': current_price,
                    'entry_time': timestamp,
                    'quantity': quantity,
                    'stop_loss': current_price * (1 - params['stop_loss']),
                    'take_profit': current_price * (1 + params['take_profit'])
                }
            
            # Señal de venta (MA rápida cruza por debajo de MA lenta)
            elif (position is not None and 
                  prev_fast_ma >= prev_slow_ma and 
                  current_fast_ma < current_slow_ma):
                
                pnl = (current_price - position['entry_price']) * position['quantity']
                current_capital += pnl
                
                trade = {
                    'entry_time': position['entry_time'].isoformat(),
                    'exit_time': timestamp.isoformat(),
                    'entry_price': position['entry_price'],
                    'exit_price': current_price,
                    'quantity': position['quantity'],
                    'pnl': pnl,
                    'pnl_pct': (pnl / (position['entry_price'] * position['quantity'])) * 100,
                    'exit_reason': "MA_CROSSOVER",
                    'duration_hours': (timestamp - position['entry_time']).total_seconds() / 3600
                }
                
                trades.append(trade)
                position = None
            
            equity_curve.append(current_capital)
        
        return trades, equity_curve
    
    async def _execute_bollinger_strategy(self, df: pd.DataFrame, params: Dict[str, Any], 
                                        initial_capital: float) -> Tuple[List[Dict], List[float]]:
        """Ejecutar estrategia Bollinger Bands"""
        import ta
        
        # Calcular Bollinger Bands
        bb = ta.volatility.BollingerBands(
            df['close'], 
            window=params['period'],
            window_dev=params['std_dev']
        )
        
        bb_upper = bb.bollinger_hband()
        bb_lower = bb.bollinger_lband()
        bb_middle = bb.bollinger_mavg()
        
        trades = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        position = None
        
        for i in range(1, len(df)):
            current_price = df['close'].iloc[i]
            current_upper = bb_upper.iloc[i]
            current_lower = bb_lower.iloc[i]
            current_middle = bb_middle.iloc[i]
            timestamp = df.index[i]
            
            # Señal de compra (precio toca banda inferior)
            if position is None and current_price <= current_lower:
                quantity = current_capital * 0.95 / current_price
                position = {
                    'type': 'LONG',
                    'entry_price': current_price,
                    'entry_time': timestamp,
                    'quantity': quantity,
                    'stop_loss': current_price * (1 - params['stop_loss']),
                    'take_profit': current_price * (1 + params['take_profit'])
                }
            
            # Señal de venta (precio toca banda superior o media)
            elif position is not None and current_price >= current_middle:
                pnl = (current_price - position['entry_price']) * position['quantity']
                current_capital += pnl
                
                trade = {
                    'entry_time': position['entry_time'].isoformat(),
                    'exit_time': timestamp.isoformat(),
                    'entry_price': position['entry_price'],
                    'exit_price': current_price,
                    'quantity': position['quantity'],
                    'pnl': pnl,
                    'pnl_pct': (pnl / (position['entry_price'] * position['quantity'])) * 100,
                    'exit_reason': "BB_MIDDLE",
                    'duration_hours': (timestamp - position['entry_time']).total_seconds() / 3600
                }
                
                trades.append(trade)
                position = None
            
            equity_curve.append(current_capital)
        
        return trades, equity_curve
    
    def _calculate_metrics(self, trades: List[Dict], equity_curve: List[float], 
                          initial_capital: float) -> Dict[str, Any]:
        """Calcular métricas de performance"""
        try:
            if not trades:
                return {
                    "total_trades": 0,
                    "total_return": 0.0,
                    "total_return_pct": 0.0,
                    "win_rate": 0.0,
                    "profit_factor": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "average_trade": 0.0,
                    "largest_win": 0.0,
                    "largest_loss": 0.0
                }
            
            # Métricas básicas
            total_trades = len(trades)
            winning_trades = [t for t in trades if t['pnl'] > 0]
            losing_trades = [t for t in trades if t['pnl'] < 0]
            
            total_pnl = sum(t['pnl'] for t in trades)
            final_capital = equity_curve[-1] if equity_curve else initial_capital
            total_return_pct = ((final_capital - initial_capital) / initial_capital) * 100
            
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            
            # Profit factor
            gross_profit = sum(t['pnl'] for t in winning_trades)
            gross_loss = abs(sum(t['pnl'] for t in losing_trades))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Sharpe ratio (simplificado)
            if len(equity_curve) > 1:
                returns = np.diff(equity_curve) / equity_curve[:-1]
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Max drawdown
            peak = equity_curve[0]
            max_drawdown = 0
            for value in equity_curve:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            # Otras métricas
            average_trade = total_pnl / total_trades if total_trades > 0 else 0
            largest_win = max([t['pnl'] for t in trades]) if trades else 0
            largest_loss = min([t['pnl'] for t in trades]) if trades else 0
            
            return {
                "total_trades": total_trades,
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "total_return": total_pnl,
                "total_return_pct": total_return_pct,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "average_trade": average_trade,
                "average_win": np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0,
                "average_loss": np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0,
                "largest_win": largest_win,
                "largest_loss": largest_loss,
                "final_capital": final_capital,
                "total_duration_hours": sum(t.get('duration_hours', 0) for t in trades),
                "average_duration_hours": np.mean([t.get('duration_hours', 0) for t in trades]) if trades else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculando métricas: {e}")
            return {"error": str(e)}
    
    def get_available_strategies(self) -> Dict[str, Any]:
        """Obtener estrategias disponibles"""
        return self.strategies
    
    async def compare_strategies(self, comparison_params: Dict[str, Any]) -> Dict[str, Any]:
        """Comparar múltiples estrategias"""
        try:
            strategies = comparison_params.get("strategies", [])
            symbol = comparison_params.get("symbol", settings.DEFAULT_TRADING_PAIR)
            start_date = comparison_params.get("start_date", "2023-01-01")
            end_date = comparison_params.get("end_date", "2024-01-01")
            
            results = []
            
            for strategy_config in strategies:
                backtest_result = await self.run_backtest({
                    "strategy_name": strategy_config["name"],
                    "symbol": symbol,
                    "start_date": start_date,
                    "end_date": end_date,
                    "parameters": strategy_config.get("parameters", {})
                })
                
                if backtest_result.get("success"):
                    results.append({
                        "strategy_name": strategy_config["name"],
                        "metrics": backtest_result["metrics"],
                        "parameters": strategy_config.get("parameters", {})
                    })
            
            # Ranking por diferentes métricas
            rankings = {}
            metrics_to_rank = ["total_return_pct", "sharpe_ratio", "win_rate", "max_drawdown"]
            
            for metric in metrics_to_rank:
                if metric == "max_drawdown":
                    # Para drawdown, menor es mejor
                    sorted_results = sorted(results, key=lambda x: x["metrics"].get(metric, 1))
                else:
                    # Para otras métricas, mayor es mejor
                    sorted_results = sorted(results, key=lambda x: x["metrics"].get(metric, 0), reverse=True)
                
                rankings[metric] = [r["strategy_name"] for r in sorted_results]
            
            return {
                "success": True,
                "comparison_results": results,
                "rankings": rankings,
                "best_overall": results[0]["strategy_name"] if results else None,
                "symbol": symbol,
                "period": f"{start_date} to {end_date}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error comparando estrategias: {e}")
            return {
                "success": False,
                "error": str(e)
            }