"""
🛡️ Risk Manager - Gestor de Riesgo Avanzado

Sistema inteligente de gestión de riesgo que monitorea exposición,
calcula stop-loss dinámicos y protege el capital.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from utils.logging.logger import trading_logger
from utils.config.settings import Settings


class RiskLevel(Enum):
    """Niveles de riesgo."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetrics:
    """Métricas de riesgo."""
    portfolio_risk: float
    position_risk: float
    volatility_risk: float
    correlation_risk: float
    drawdown_risk: float
    overall_risk: RiskLevel
    risk_score: float  # 0.0 a 1.0
    recommendations: List[str]


@dataclass
class PositionRisk:
    """Riesgo de una posición específica."""
    symbol: str
    position_size: float
    market_value: float
    portfolio_weight: float
    var_1d: float  # Value at Risk 1 día
    var_5d: float  # Value at Risk 5 días
    stop_loss_price: float
    take_profit_price: float
    risk_reward_ratio: float
    max_loss_amount: float
    max_loss_percent: float


class RiskManager:
    """Gestor principal de riesgo."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.risk_limits = {
            'max_position_size': settings.MAX_POSITION_SIZE,
            'max_daily_loss': settings.MAX_DAILY_LOSS,
            'stop_loss_percent': settings.STOP_LOSS_PERCENT,
            'take_profit_percent': settings.TAKE_PROFIT_PERCENT,
            'max_correlation': 0.7,  # Correlación máxima entre posiciones
            'max_portfolio_var': 0.05,  # VaR máximo del portafolio (5%)
            'max_drawdown': 0.15  # Drawdown máximo (15%)
        }
        
        self.position_history: Dict[str, List[Dict]] = {}
        self.portfolio_history: List[Dict] = []
        
    def assess_portfolio_risk(
        self,
        positions: Dict[str, Dict],
        market_data: Dict[str, pd.DataFrame],
        portfolio_value: float
    ) -> RiskMetrics:
        """
        Evaluar riesgo del portafolio completo.
        
        Args:
            positions: Diccionario de posiciones {symbol: position_data}
            market_data: Datos de mercado por símbolo
            portfolio_value: Valor total del portafolio
        
        Returns:
            Métricas de riesgo del portafolio
        """
        try:
            # Calcular riesgos individuales
            portfolio_risk = self._calculate_portfolio_risk(positions, portfolio_value)
            position_risk = self._calculate_position_risk(positions, portfolio_value)
            volatility_risk = self._calculate_volatility_risk(market_data)
            correlation_risk = self._calculate_correlation_risk(positions, market_data)
            drawdown_risk = self._calculate_drawdown_risk()
            
            # Calcular riesgo general
            risk_components = [
                portfolio_risk, position_risk, volatility_risk,
                correlation_risk, drawdown_risk
            ]
            
            risk_score = np.mean(risk_components)
            overall_risk = self._determine_risk_level(risk_score)
            
            # Generar recomendaciones
            recommendations = self._generate_risk_recommendations(
                risk_score, portfolio_risk, position_risk, 
                volatility_risk, correlation_risk, drawdown_risk
            )
            
            metrics = RiskMetrics(
                portfolio_risk=portfolio_risk,
                position_risk=position_risk,
                volatility_risk=volatility_risk,
                correlation_risk=correlation_risk,
                drawdown_risk=drawdown_risk,
                overall_risk=overall_risk,
                risk_score=risk_score,
                recommendations=recommendations
            )
            
            # Log de evaluación de riesgo
            if overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                trading_logger.risk_alert(
                    message=f"Riesgo {overall_risk.value}: {risk_score:.2f}",
                    severity=overall_risk.value,
                    portfolio_risk=portfolio_risk,
                    position_risk=position_risk,
                    volatility_risk=volatility_risk
                )
            
            return metrics
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error evaluando riesgo del portafolio: {e}")
            return self._default_risk_metrics()
    
    def calculate_position_risk(
        self,
        symbol: str,
        position_size: float,
        entry_price: float,
        current_price: float,
        market_data: pd.DataFrame,
        portfolio_value: float
    ) -> PositionRisk:
        """
        Calcular riesgo de una posición específica.
        
        Args:
            symbol: Símbolo del activo
            position_size: Tamaño de la posición
            entry_price: Precio de entrada
            current_price: Precio actual
            market_data: Datos históricos del activo
            portfolio_value: Valor total del portafolio
        
        Returns:
            Métricas de riesgo de la posición
        """
        try:
            # Valor de mercado de la posición
            market_value = abs(position_size * current_price)
            portfolio_weight = market_value / portfolio_value
            
            # Calcular volatilidad
            returns = market_data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Volatilidad anualizada
            
            # Value at Risk (VaR)
            confidence_level = 0.05  # 95% de confianza
            var_1d = market_value * abs(np.percentile(returns, confidence_level * 100))
            var_5d = var_1d * np.sqrt(5)  # VaR para 5 días
            
            # Stop loss y take profit
            if position_size > 0:  # Posición larga
                stop_loss_price = entry_price * (1 - self.risk_limits['stop_loss_percent'])
                take_profit_price = entry_price * (1 + self.risk_limits['take_profit_percent'])
            else:  # Posición corta
                stop_loss_price = entry_price * (1 + self.risk_limits['stop_loss_percent'])
                take_profit_price = entry_price * (1 - self.risk_limits['take_profit_percent'])
            
            # Ratio riesgo/beneficio
            potential_loss = abs(entry_price - stop_loss_price) * abs(position_size)
            potential_profit = abs(take_profit_price - entry_price) * abs(position_size)
            risk_reward_ratio = potential_profit / potential_loss if potential_loss > 0 else 0
            
            # Pérdida máxima
            max_loss_amount = potential_loss
            max_loss_percent = (max_loss_amount / portfolio_value) * 100
            
            return PositionRisk(
                symbol=symbol,
                position_size=position_size,
                market_value=market_value,
                portfolio_weight=portfolio_weight,
                var_1d=var_1d,
                var_5d=var_5d,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                risk_reward_ratio=risk_reward_ratio,
                max_loss_amount=max_loss_amount,
                max_loss_percent=max_loss_percent
            )
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error calculando riesgo de posición {symbol}: {e}")
            return self._default_position_risk(symbol)
    
    def should_open_position(
        self,
        symbol: str,
        position_size: float,
        entry_price: float,
        portfolio_value: float,
        current_positions: Dict[str, Dict]
    ) -> Tuple[bool, str]:
        """
        Determinar si se debe abrir una nueva posición.
        
        Args:
            symbol: Símbolo del activo
            position_size: Tamaño propuesto de la posición
            entry_price: Precio de entrada propuesto
            portfolio_value: Valor actual del portafolio
            current_positions: Posiciones actuales
        
        Returns:
            Tupla (permitir, razón)
        """
        try:
            # Verificar tamaño de posición
            position_value = abs(position_size * entry_price)
            position_weight = position_value / portfolio_value
            
            if position_weight > self.risk_limits['max_position_size']:
                return False, f"Posición muy grande: {position_weight:.2%} > {self.risk_limits['max_position_size']:.2%}"
            
            # Verificar exposición total
            total_exposure = sum(
                abs(pos.get('size', 0) * pos.get('price', 0)) 
                for pos in current_positions.values()
            )
            total_exposure += position_value
            
            if total_exposure / portfolio_value > 0.95:  # 95% máximo
                return False, f"Exposición total muy alta: {total_exposure/portfolio_value:.2%}"
            
            # Verificar límites de pérdida diaria
            daily_loss = self._calculate_daily_loss(current_positions)
            if daily_loss > self.risk_limits['max_daily_loss']:
                return False, f"Límite de pérdida diaria alcanzado: {daily_loss:.2%}"
            
            return True, "Posición aprobada por gestión de riesgo"
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error evaluando nueva posición: {e}")
            return False, "Error en evaluación de riesgo"
    
    def should_close_position(
        self,
        symbol: str,
        current_price: float,
        position_data: Dict
    ) -> Tuple[bool, str]:
        """
        Determinar si se debe cerrar una posición.
        
        Args:
            symbol: Símbolo del activo
            current_price: Precio actual
            position_data: Datos de la posición
        
        Returns:
            Tupla (cerrar, razón)
        """
        try:
            entry_price = position_data.get('entry_price', 0)
            position_size = position_data.get('size', 0)
            
            if entry_price == 0 or position_size == 0:
                return False, "Datos de posición inválidos"
            
            # Calcular PnL actual
            if position_size > 0:  # Posición larga
                pnl_percent = (current_price - entry_price) / entry_price
            else:  # Posición corta
                pnl_percent = (entry_price - current_price) / entry_price
            
            # Verificar stop loss
            if pnl_percent <= -self.risk_limits['stop_loss_percent']:
                return True, f"Stop loss activado: {pnl_percent:.2%}"
            
            # Verificar take profit
            if pnl_percent >= self.risk_limits['take_profit_percent']:
                return True, f"Take profit activado: {pnl_percent:.2%}"
            
            # Verificar tiempo en posición (opcional)
            entry_time = position_data.get('entry_time')
            if entry_time:
                time_in_position = datetime.now() - entry_time
                if time_in_position > timedelta(days=7):  # Más de 7 días
                    return True, "Posición muy antigua, cerrar por gestión de tiempo"
            
            return False, "Posición dentro de parámetros normales"
            
        except Exception as e:
            trading_logger.logger.error(f"❌ Error evaluando cierre de posición {symbol}: {e}")
            return False, "Error en evaluación de cierre"
    
    def _calculate_portfolio_risk(
        self, 
        positions: Dict[str, Dict], 
        portfolio_value: float
    ) -> float:
        """Calcular riesgo del portafolio."""
        if not positions:
            return 0.0
        
        # Concentración de posiciones
        position_weights = []
        for pos in positions.values():
            weight = abs(pos.get('size', 0) * pos.get('price', 0)) / portfolio_value
            position_weights.append(weight)
        
        # Índice de Herfindahl (concentración)
        hhi = sum(w**2 for w in position_weights)
        concentration_risk = min(hhi * 2, 1.0)  # Normalizar
        
        return concentration_risk
    
    def _calculate_position_risk(
        self, 
        positions: Dict[str, Dict], 
        portfolio_value: float
    ) -> float:
        """Calcular riesgo de posiciones individuales."""
        if not positions:
            return 0.0
        
        max_position_risk = 0.0
        
        for symbol, pos in positions.items():
            position_value = abs(pos.get('size', 0) * pos.get('price', 0))
            position_weight = position_value / portfolio_value
            
            # Riesgo basado en tamaño de posición
            size_risk = position_weight / self.risk_limits['max_position_size']
            max_position_risk = max(max_position_risk, size_risk)
        
        return min(max_position_risk, 1.0)
    
    def _calculate_volatility_risk(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """Calcular riesgo de volatilidad."""
        if not market_data:
            return 0.0
        
        volatilities = []
        
        for symbol, df in market_data.items():
            if len(df) > 20:
                returns = df['close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)  # Anualizada
                volatilities.append(volatility)
        
        if not volatilities:
            return 0.0
        
        avg_volatility = np.mean(volatilities)
        # Normalizar: volatilidad > 50% = riesgo alto
        return min(avg_volatility / 0.5, 1.0)
    
    def _calculate_correlation_risk(
        self, 
        positions: Dict[str, Dict], 
        market_data: Dict[str, pd.DataFrame]
    ) -> float:
        """Calcular riesgo de correlación."""
        if len(positions) < 2:
            return 0.0
        
        symbols = list(positions.keys())
        correlations = []
        
        for i, symbol1 in enumerate(symbols):
            for symbol2 in symbols[i+1:]:
                if symbol1 in market_data and symbol2 in market_data:
                    df1 = market_data[symbol1]
                    df2 = market_data[symbol2]
                    
                    if len(df1) > 20 and len(df2) > 20:
                        returns1 = df1['close'].pct_change().dropna()
                        returns2 = df2['close'].pct_change().dropna()
                        
                        # Alinear fechas
                        common_dates = returns1.index.intersection(returns2.index)
                        if len(common_dates) > 10:
                            corr = returns1[common_dates].corr(returns2[common_dates])
                            if not np.isnan(corr):
                                correlations.append(abs(corr))
        
        if not correlations:
            return 0.0
        
        max_correlation = max(correlations)
        return max_correlation  # Ya está entre 0 y 1
    
    def _calculate_drawdown_risk(self) -> float:
        """Calcular riesgo de drawdown."""
        if len(self.portfolio_history) < 10:
            return 0.0
        
        # Calcular drawdown actual
        values = [entry['value'] for entry in self.portfolio_history[-100:]]  # Últimos 100 valores
        peak = max(values)
        current = values[-1]
        
        current_drawdown = (peak - current) / peak if peak > 0 else 0
        
        # Normalizar con límite máximo
        return min(current_drawdown / self.risk_limits['max_drawdown'], 1.0)
    
    def _calculate_daily_loss(self, positions: Dict[str, Dict]) -> float:
        """Calcular pérdida diaria actual."""
        # Simplificado - en implementación real, usar datos históricos
        total_loss = 0.0
        
        for pos in positions.values():
            entry_price = pos.get('entry_price', 0)
            current_price = pos.get('current_price', entry_price)
            size = pos.get('size', 0)
            
            if size > 0:  # Posición larga
                loss = max(0, (entry_price - current_price) * size)
            else:  # Posición corta
                loss = max(0, (current_price - entry_price) * abs(size))
            
            total_loss += loss
        
        # Retornar como porcentaje del capital inicial
        return total_loss / self.settings.BACKTEST_INITIAL_CAPITAL
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determinar nivel de riesgo basado en score."""
        if risk_score < 0.3:
            return RiskLevel.LOW
        elif risk_score < 0.6:
            return RiskLevel.MEDIUM
        elif risk_score < 0.8:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _generate_risk_recommendations(
        self,
        risk_score: float,
        portfolio_risk: float,
        position_risk: float,
        volatility_risk: float,
        correlation_risk: float,
        drawdown_risk: float
    ) -> List[str]:
        """Generar recomendaciones basadas en riesgo."""
        recommendations = []
        
        if risk_score > 0.7:
            recommendations.append("🚨 Riesgo general alto - Considerar reducir exposición")
        
        if portfolio_risk > 0.6:
            recommendations.append("📊 Alta concentración - Diversificar posiciones")
        
        if position_risk > 0.8:
            recommendations.append("⚖️ Posiciones muy grandes - Reducir tamaños")
        
        if volatility_risk > 0.7:
            recommendations.append("📈 Alta volatilidad - Ajustar stop-loss más estrictos")
        
        if correlation_risk > 0.7:
            recommendations.append("🔗 Alta correlación - Buscar activos no correlacionados")
        
        if drawdown_risk > 0.6:
            recommendations.append("📉 Drawdown elevado - Considerar pausa en trading")
        
        if not recommendations:
            recommendations.append("✅ Riesgo bajo - Continuar con estrategia actual")
        
        return recommendations
    
    def _default_risk_metrics(self) -> RiskMetrics:
        """Métricas de riesgo por defecto en caso de error."""
        return RiskMetrics(
            portfolio_risk=0.5,
            position_risk=0.5,
            volatility_risk=0.5,
            correlation_risk=0.5,
            drawdown_risk=0.5,
            overall_risk=RiskLevel.MEDIUM,
            risk_score=0.5,
            recommendations=["⚠️ Error en cálculo de riesgo - Revisar sistema"]
        )
    
    def _default_position_risk(self, symbol: str) -> PositionRisk:
        """Riesgo de posición por defecto en caso de error."""
        return PositionRisk(
            symbol=symbol,
            position_size=0.0,
            market_value=0.0,
            portfolio_weight=0.0,
            var_1d=0.0,
            var_5d=0.0,
            stop_loss_price=0.0,
            take_profit_price=0.0,
            risk_reward_ratio=0.0,
            max_loss_amount=0.0,
            max_loss_percent=0.0
        )
    
    def update_portfolio_history(self, portfolio_value: float):
        """Actualizar historial del portafolio."""
        self.portfolio_history.append({
            'timestamp': datetime.now(),
            'value': portfolio_value
        })
        
        # Mantener solo últimos 1000 registros
        if len(self.portfolio_history) > 1000:
            self.portfolio_history = self.portfolio_history[-1000:]