"""
Risk Agent - Agente especializado en gestión de riesgo
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from backend.agents.base_agent import BaseAgent, AgentTask
from backend.services.binance_service import BinanceService
from backend.core.database import DatabaseManager
from backend.core.config import settings

class RiskAgent(BaseAgent):
    """
    Agente especializado en gestión de riesgo
    
    Responsabilidades:
    - Monitorear exposición al riesgo del portafolio
    - Calcular métricas de riesgo (VaR, drawdown, etc.)
    - Alertar sobre violaciones de límites de riesgo
    - Sugerir ajustes de posición para reducir riesgo
    - Implementar reglas de gestión de capital
    """
    
    def __init__(self):
        super().__init__(
            name="RiskAgent",
            description="Agente especializado en gestión de riesgo"
        )
        self.binance_service: Optional[BinanceService] = None
        self.risk_limits = {
            "max_position_size": settings.MAX_POSITION_SIZE,
            "max_daily_loss": settings.MAX_DAILY_LOSS,
            "max_drawdown": settings.MAX_DRAWDOWN,
            "max_correlation_exposure": 0.7,  # Máxima exposición a activos correlacionados
            "max_leverage": 1.0,  # Sin apalancamiento en testnet
            "min_cash_reserve": 0.1  # 10% mínimo en efectivo
        }
        self.risk_metrics = {}
        self.alerts = []
        
    async def _initialize_agent(self):
        """Inicializar servicios del agente de riesgo"""
        self.binance_service = BinanceService()
        await self.binance_service.initialize()
        
        self.logger.info("RiskAgent inicializado con servicios de monitoreo de riesgo")
    
    async def _process_task(self, task: AgentTask) -> Any:
        """Procesar tareas de gestión de riesgo"""
        task_type = task.task_type
        parameters = task.parameters
        
        if task_type == "assess_portfolio_risk":
            return await self._assess_portfolio_risk(parameters)
        elif task_type == "check_trade_risk":
            return await self._check_trade_risk(parameters)
        elif task_type == "calculate_var":
            return await self._calculate_var(parameters)
        elif task_type == "monitor_drawdown":
            return await self._monitor_drawdown(parameters)
        elif task_type == "check_correlation_risk":
            return await self._check_correlation_risk(parameters)
        elif task_type == "generate_risk_report":
            return await self._generate_risk_report(parameters)
        elif task_type == "suggest_position_adjustments":
            return await self._suggest_position_adjustments(parameters)
        else:
            raise ValueError(f"Tipo de tarea no soportado: {task_type}")
    
    async def _assess_portfolio_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluar riesgo general del portafolio
        
        Args:
            parameters: Debe contener información del portafolio
            
        Returns:
            Evaluación completa de riesgo
        """
        portfolio = parameters.get("portfolio", {})
        
        self.logger.info("Evaluando riesgo del portafolio")
        
        try:
            risk_assessment = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_risk_score": 0,
                "risk_level": "LOW",
                "metrics": {},
                "violations": [],
                "recommendations": []
            }
            
            # Calcular métricas de riesgo
            risk_assessment["metrics"] = await self._calculate_risk_metrics(portfolio)
            
            # Verificar violaciones de límites
            violations = await self._check_risk_violations(portfolio, risk_assessment["metrics"])
            risk_assessment["violations"] = violations
            
            # Calcular score de riesgo general
            risk_score = self._calculate_overall_risk_score(risk_assessment["metrics"], violations)
            risk_assessment["overall_risk_score"] = risk_score
            
            # Determinar nivel de riesgo
            if risk_score >= 80:
                risk_assessment["risk_level"] = "CRITICAL"
            elif risk_score >= 60:
                risk_assessment["risk_level"] = "HIGH"
            elif risk_score >= 40:
                risk_assessment["risk_level"] = "MEDIUM"
            else:
                risk_assessment["risk_level"] = "LOW"
            
            # Generar recomendaciones
            risk_assessment["recommendations"] = self._generate_risk_recommendations(
                risk_assessment["metrics"], violations
            )
            
            # Actualizar métricas internas
            self.risk_metrics = risk_assessment["metrics"]
            
            return risk_assessment
            
        except Exception as e:
            self.logger.error(f"Error evaluando riesgo del portafolio: {e}")
            raise
    
    async def _calculate_risk_metrics(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular métricas de riesgo del portafolio"""
        metrics = {}
        
        try:
            positions = portfolio.get("active_positions", {})
            current_balance = portfolio.get("current_balance", 1000.0)
            total_portfolio_value = portfolio.get("total_portfolio_value", current_balance)
            
            # Concentración de posiciones
            if positions:
                position_values = []
                for symbol, position in positions.items():
                    if position.get("quantity", 0) > 0:
                        position_value = position.get("current_price", 0) * position.get("quantity", 0)
                        position_values.append(position_value)
                
                if position_values:
                    max_position_value = max(position_values)
                    metrics["max_position_concentration"] = max_position_value / total_portfolio_value
                    metrics["position_count"] = len(position_values)
                    metrics["average_position_size"] = np.mean(position_values) / total_portfolio_value
                else:
                    metrics["max_position_concentration"] = 0
                    metrics["position_count"] = 0
                    metrics["average_position_size"] = 0
            else:
                metrics["max_position_concentration"] = 0
                metrics["position_count"] = 0
                metrics["average_position_size"] = 0
            
            # Exposición total
            total_position_value = sum(
                pos.get("current_price", 0) * pos.get("quantity", 0) 
                for pos in positions.values() 
                if pos.get("quantity", 0) > 0
            )
            metrics["total_exposure"] = total_position_value / total_portfolio_value
            metrics["cash_reserve"] = (current_balance - total_position_value) / total_portfolio_value
            
            # PnL no realizado como porcentaje
            total_unrealized_pnl = sum(
                pos.get("unrealized_pnl", 0) for pos in positions.values()
            )
            metrics["unrealized_pnl_percentage"] = (total_unrealized_pnl / 1000.0) * 100  # Asumiendo capital inicial de 1000
            
            # Volatilidad del portafolio (estimación simple)
            if positions:
                volatilities = []
                for symbol in positions.keys():
                    vol = await self._estimate_asset_volatility(symbol)
                    if vol:
                        volatilities.append(vol)
                
                if volatilities:
                    metrics["estimated_portfolio_volatility"] = np.mean(volatilities)
                else:
                    metrics["estimated_portfolio_volatility"] = 0
            else:
                metrics["estimated_portfolio_volatility"] = 0
            
            # Drawdown actual
            metrics["current_drawdown"] = max(0, -metrics["unrealized_pnl_percentage"])
            
        except Exception as e:
            self.logger.error(f"Error calculando métricas de riesgo: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    async def _estimate_asset_volatility(self, symbol: str, periods: int = 30) -> Optional[float]:
        """Estimar volatilidad de un activo"""
        try:
            df = await self.binance_service.get_historical_data(symbol, "1d", periods)
            if df.empty:
                return None
            
            # Calcular retornos diarios
            returns = df['close'].pct_change().dropna()
            
            # Volatilidad anualizada (asumiendo 365 días)
            volatility = returns.std() * np.sqrt(365)
            
            return float(volatility)
            
        except Exception as e:
            self.logger.error(f"Error estimando volatilidad de {symbol}: {e}")
            return None
    
    async def _check_risk_violations(self, portfolio: Dict[str, Any], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verificar violaciones de límites de riesgo"""
        violations = []
        
        try:
            # Verificar concentración máxima de posición
            max_concentration = metrics.get("max_position_concentration", 0)
            if max_concentration > self.risk_limits["max_position_size"]:
                violations.append({
                    "type": "position_concentration",
                    "severity": "HIGH",
                    "current_value": max_concentration,
                    "limit": self.risk_limits["max_position_size"],
                    "message": f"Concentración de posición excede el límite: {max_concentration:.2%} > {self.risk_limits['max_position_size']:.2%}"
                })
            
            # Verificar drawdown máximo
            current_drawdown = metrics.get("current_drawdown", 0)
            if current_drawdown > self.risk_limits["max_drawdown"] * 100:
                violations.append({
                    "type": "max_drawdown",
                    "severity": "CRITICAL",
                    "current_value": current_drawdown,
                    "limit": self.risk_limits["max_drawdown"] * 100,
                    "message": f"Drawdown excede el límite: {current_drawdown:.2f}% > {self.risk_limits['max_drawdown']*100:.2f}%"
                })
            
            # Verificar reserva mínima de efectivo
            cash_reserve = metrics.get("cash_reserve", 0)
            if cash_reserve < self.risk_limits["min_cash_reserve"]:
                violations.append({
                    "type": "cash_reserve",
                    "severity": "MEDIUM",
                    "current_value": cash_reserve,
                    "limit": self.risk_limits["min_cash_reserve"],
                    "message": f"Reserva de efectivo por debajo del mínimo: {cash_reserve:.2%} < {self.risk_limits['min_cash_reserve']:.2%}"
                })
            
            # Verificar pérdida diaria
            unrealized_pnl_pct = metrics.get("unrealized_pnl_percentage", 0)
            if unrealized_pnl_pct < -self.risk_limits["max_daily_loss"] * 100:
                violations.append({
                    "type": "daily_loss",
                    "severity": "HIGH",
                    "current_value": unrealized_pnl_pct,
                    "limit": -self.risk_limits["max_daily_loss"] * 100,
                    "message": f"Pérdida diaria excede el límite: {unrealized_pnl_pct:.2f}% < {-self.risk_limits['max_daily_loss']*100:.2f}%"
                })
            
        except Exception as e:
            self.logger.error(f"Error verificando violaciones de riesgo: {e}")
            violations.append({
                "type": "error",
                "severity": "HIGH",
                "message": f"Error verificando riesgo: {str(e)}"
            })
        
        return violations
    
    def _calculate_overall_risk_score(self, metrics: Dict[str, Any], violations: List[Dict[str, Any]]) -> int:
        """Calcular score general de riesgo (0-100)"""
        score = 0
        
        # Score base por métricas
        max_concentration = metrics.get("max_position_concentration", 0)
        score += min(max_concentration * 100, 30)  # Máximo 30 puntos por concentración
        
        total_exposure = metrics.get("total_exposure", 0)
        score += min(total_exposure * 20, 20)  # Máximo 20 puntos por exposición
        
        volatility = metrics.get("estimated_portfolio_volatility", 0)
        score += min(volatility * 100, 20)  # Máximo 20 puntos por volatilidad
        
        # Penalización por violaciones
        for violation in violations:
            if violation["severity"] == "CRITICAL":
                score += 25
            elif violation["severity"] == "HIGH":
                score += 15
            elif violation["severity"] == "MEDIUM":
                score += 10
        
        return min(int(score), 100)
    
    def _generate_risk_recommendations(self, metrics: Dict[str, Any], violations: List[Dict[str, Any]]) -> List[str]:
        """Generar recomendaciones para reducir riesgo"""
        recommendations = []
        
        # Recomendaciones basadas en violaciones
        for violation in violations:
            if violation["type"] == "position_concentration":
                recommendations.append("Reducir el tamaño de la posición más grande para mejorar diversificación")
            elif violation["type"] == "max_drawdown":
                recommendations.append("URGENTE: Cerrar posiciones perdedoras para limitar drawdown")
            elif violation["type"] == "cash_reserve":
                recommendations.append("Aumentar reserva de efectivo cerrando algunas posiciones")
            elif violation["type"] == "daily_loss":
                recommendations.append("Considerar cerrar posiciones para limitar pérdidas diarias")
        
        # Recomendaciones generales
        max_concentration = metrics.get("max_position_concentration", 0)
        if max_concentration > 0.3:  # 30%
            recommendations.append("Considerar diversificar más el portafolio")
        
        position_count = metrics.get("position_count", 0)
        if position_count > 10:
            recommendations.append("Considerar consolidar posiciones para mejor gestión")
        elif position_count < 3 and position_count > 0:
            recommendations.append("Considerar diversificar en más activos")
        
        volatility = metrics.get("estimated_portfolio_volatility", 0)
        if volatility > 0.5:  # 50% volatilidad anual
            recommendations.append("Portafolio con alta volatilidad - considerar activos menos volátiles")
        
        if not recommendations:
            recommendations.append("Perfil de riesgo dentro de parámetros aceptables")
        
        return recommendations
    
    async def _check_trade_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar riesgo de un trade específico antes de ejecutar"""
        symbol = parameters.get("symbol")
        side = parameters.get("side")
        quantity = parameters.get("quantity")
        current_balance = parameters.get("current_balance", 1000.0)
        active_positions = parameters.get("active_positions", {})
        
        self.logger.info(f"Verificando riesgo de trade: {side} {quantity} {symbol}")
        
        try:
            risk_check = {
                "approved": True,
                "risk_score": 0,
                "warnings": [],
                "reason": ""
            }
            
            # Obtener precio actual
            current_price = await self.binance_service.get_current_price(symbol)
            if not current_price:
                risk_check["approved"] = False
                risk_check["reason"] = "No se pudo obtener precio actual"
                return risk_check
            
            # Calcular valor del trade
            trade_value = float(quantity) * current_price
            
            # Verificar tamaño de posición
            position_size_ratio = trade_value / current_balance
            if position_size_ratio > self.risk_limits["max_position_size"]:
                risk_check["approved"] = False
                risk_check["reason"] = f"Tamaño de posición excede límite: {position_size_ratio:.2%} > {self.risk_limits['max_position_size']:.2%}"
                return risk_check
            
            # Verificar concentración después del trade
            if symbol in active_positions:
                current_position_value = active_positions[symbol].get("current_price", 0) * active_positions[symbol].get("quantity", 0)
                new_position_value = current_position_value + (trade_value if side == "BUY" else -trade_value)
                new_concentration = new_position_value / current_balance
                
                if new_concentration > self.risk_limits["max_position_size"]:
                    risk_check["approved"] = False
                    risk_check["reason"] = f"Nueva concentración excedería límite: {new_concentration:.2%}"
                    return risk_check
            
            # Verificar reserva de efectivo
            if side == "BUY":
                remaining_cash = current_balance - trade_value
                cash_ratio = remaining_cash / current_balance
                
                if cash_ratio < self.risk_limits["min_cash_reserve"]:
                    risk_check["warnings"].append(f"Reserva de efectivo quedará baja: {cash_ratio:.2%}")
                    risk_check["risk_score"] += 20
            
            # Calcular score de riesgo del trade
            risk_check["risk_score"] += min(position_size_ratio * 100, 50)
            
            # Verificar volatilidad del activo
            volatility = await self._estimate_asset_volatility(symbol)
            if volatility and volatility > 0.8:  # 80% volatilidad anual
                risk_check["warnings"].append(f"Activo con alta volatilidad: {volatility:.2%}")
                risk_check["risk_score"] += 15
            
            return risk_check
            
        except Exception as e:
            self.logger.error(f"Error verificando riesgo de trade: {e}")
            return {
                "approved": False,
                "risk_score": 100,
                "reason": f"Error en verificación de riesgo: {str(e)}"
            }
    
    async def _calculate_var(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular Value at Risk del portafolio"""
        portfolio = parameters.get("portfolio", {})
        confidence_level = parameters.get("confidence_level", 0.95)
        time_horizon = parameters.get("time_horizon", 1)  # días
        
        try:
            positions = portfolio.get("active_positions", {})
            
            if not positions:
                return {
                    "var": 0,
                    "confidence_level": confidence_level,
                    "time_horizon": time_horizon,
                    "message": "No hay posiciones activas"
                }
            
            # Método simplificado: usar volatilidad histórica
            portfolio_value = 0
            weighted_volatility = 0
            
            for symbol, position in positions.items():
                if position.get("quantity", 0) > 0:
                    position_value = position.get("current_price", 0) * position.get("quantity", 0)
                    portfolio_value += position_value
                    
                    volatility = await self._estimate_asset_volatility(symbol)
                    if volatility:
                        weight = position_value / portfolio_value if portfolio_value > 0 else 0
                        weighted_volatility += weight * volatility
            
            # Calcular VaR usando distribución normal
            # VaR = Portfolio Value * Z-score * Volatility * sqrt(time_horizon)
            if confidence_level == 0.95:
                z_score = 1.645
            elif confidence_level == 0.99:
                z_score = 2.326
            else:
                z_score = 1.645  # Default
            
            var = portfolio_value * z_score * weighted_volatility * np.sqrt(time_horizon)
            
            return {
                "var": float(var),
                "var_percentage": (var / portfolio_value * 100) if portfolio_value > 0 else 0,
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "portfolio_value": portfolio_value,
                "estimated_volatility": weighted_volatility
            }
            
        except Exception as e:
            self.logger.error(f"Error calculando VaR: {e}")
            return {"error": str(e)}
    
    async def _monitor_drawdown(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Monitorear drawdown del portafolio"""
        try:
            # Obtener historial de performance (simplificado)
            current_pnl = parameters.get("current_pnl", 0)
            initial_capital = parameters.get("initial_capital", 1000.0)
            
            # Calcular drawdown actual
            current_value = initial_capital + current_pnl
            peak_value = max(initial_capital, current_value)  # Simplificado
            
            drawdown = (peak_value - current_value) / peak_value if peak_value > 0 else 0
            drawdown_percentage = drawdown * 100
            
            # Verificar si excede límites
            exceeds_limit = drawdown > self.risk_limits["max_drawdown"]
            
            result = {
                "current_drawdown": drawdown_percentage,
                "max_allowed_drawdown": self.risk_limits["max_drawdown"] * 100,
                "exceeds_limit": exceeds_limit,
                "current_value": current_value,
                "peak_value": peak_value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if exceeds_limit:
                result["alert"] = f"ALERTA: Drawdown excede límite ({drawdown_percentage:.2f}% > {self.risk_limits['max_drawdown']*100:.2f}%)"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error monitoreando drawdown: {e}")
            return {"error": str(e)}
    
    async def _check_correlation_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar riesgo de correlación entre activos"""
        symbols = parameters.get("symbols", [])
        
        if len(symbols) < 2:
            return {"message": "Se necesitan al menos 2 símbolos"}
        
        try:
            # Obtener datos de correlación (simplificado)
            correlations = {}
            high_correlations = []
            
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols[i+1:], i+1):
                    # Calcular correlación entre pares (implementación simplificada)
                    correlation = await self._calculate_pair_correlation(symbol1, symbol2)
                    
                    if correlation is not None:
                        pair = f"{symbol1}-{symbol2}"
                        correlations[pair] = correlation
                        
                        if abs(correlation) > self.risk_limits["max_correlation_exposure"]:
                            high_correlations.append({
                                "pair": pair,
                                "correlation": correlation,
                                "risk_level": "HIGH" if abs(correlation) > 0.8 else "MEDIUM"
                            })
            
            return {
                "correlations": correlations,
                "high_correlations": high_correlations,
                "risk_assessment": "HIGH" if len(high_correlations) > 0 else "LOW",
                "recommendation": "Considerar reducir exposición a activos altamente correlacionados" if high_correlations else "Diversificación adecuada"
            }
            
        except Exception as e:
            self.logger.error(f"Error verificando correlaciones: {e}")
            return {"error": str(e)}
    
    async def _calculate_pair_correlation(self, symbol1: str, symbol2: str, periods: int = 30) -> Optional[float]:
        """Calcular correlación entre dos activos"""
        try:
            df1 = await self.binance_service.get_historical_data(symbol1, "1d", periods)
            df2 = await self.binance_service.get_historical_data(symbol2, "1d", periods)
            
            if df1.empty or df2.empty:
                return None
            
            # Calcular retornos
            returns1 = df1['close'].pct_change().dropna()
            returns2 = df2['close'].pct_change().dropna()
            
            # Alinear fechas
            min_length = min(len(returns1), len(returns2))
            returns1 = returns1.tail(min_length)
            returns2 = returns2.tail(min_length)
            
            # Calcular correlación
            correlation = returns1.corr(returns2)
            
            return float(correlation) if not np.isnan(correlation) else None
            
        except Exception as e:
            self.logger.error(f"Error calculando correlación {symbol1}-{symbol2}: {e}")
            return None
    
    async def _generate_risk_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generar reporte completo de riesgo"""
        try:
            portfolio = parameters.get("portfolio", {})
            
            # Evaluar riesgo del portafolio
            portfolio_risk = await self._assess_portfolio_risk({"portfolio": portfolio})
            
            # Calcular VaR
            var_analysis = await self._calculate_var({"portfolio": portfolio})
            
            # Monitorear drawdown
            drawdown_analysis = await self._monitor_drawdown({
                "current_pnl": portfolio.get("total_unrealized_pnl", 0),
                "initial_capital": 1000.0
            })
            
            # Verificar correlaciones
            symbols = list(portfolio.get("active_positions", {}).keys())
            correlation_analysis = await self._check_correlation_risk({"symbols": symbols})
            
            risk_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "portfolio_risk": portfolio_risk,
                "var_analysis": var_analysis,
                "drawdown_analysis": drawdown_analysis,
                "correlation_analysis": correlation_analysis,
                "summary": {
                    "overall_risk_level": portfolio_risk.get("risk_level", "UNKNOWN"),
                    "risk_score": portfolio_risk.get("overall_risk_score", 0),
                    "critical_alerts": len([v for v in portfolio_risk.get("violations", []) if v.get("severity") == "CRITICAL"]),
                    "recommendations_count": len(portfolio_risk.get("recommendations", []))
                }
            }
            
            return risk_report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte de riesgo: {e}")
            return {"error": str(e)}
    
    async def _suggest_position_adjustments(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Sugerir ajustes de posición para reducir riesgo"""
        portfolio = parameters.get("portfolio", {})
        target_risk_level = parameters.get("target_risk_level", "MEDIUM")
        
        try:
            positions = portfolio.get("active_positions", {})
            suggestions = []
            
            # Evaluar cada posición
            for symbol, position in positions.items():
                if position.get("quantity", 0) > 0:
                    position_value = position.get("current_price", 0) * position.get("quantity", 0)
                    portfolio_value = portfolio.get("total_portfolio_value", 1000.0)
                    concentration = position_value / portfolio_value
                    
                    # Sugerir reducción si concentración es alta
                    if concentration > self.risk_limits["max_position_size"]:
                        reduction_needed = concentration - self.risk_limits["max_position_size"]
                        quantity_to_reduce = (reduction_needed * portfolio_value) / position.get("current_price", 1)
                        
                        suggestions.append({
                            "symbol": symbol,
                            "action": "REDUCE",
                            "current_concentration": concentration,
                            "target_concentration": self.risk_limits["max_position_size"],
                            "quantity_to_reduce": quantity_to_reduce,
                            "reason": "Concentración excede límite de riesgo"
                        })
                    
                    # Sugerir cierre si hay pérdidas significativas
                    unrealized_pnl = position.get("unrealized_pnl", 0)
                    if unrealized_pnl < -position_value * 0.1:  # Pérdida > 10%
                        suggestions.append({
                            "symbol": symbol,
                            "action": "CLOSE",
                            "current_pnl": unrealized_pnl,
                            "pnl_percentage": (unrealized_pnl / position_value) * 100,
                            "reason": "Pérdida significativa - considerar cerrar posición"
                        })
            
            return {
                "suggestions": suggestions,
                "total_suggestions": len(suggestions),
                "priority_actions": [s for s in suggestions if s["action"] == "CLOSE"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error sugiriendo ajustes: {e}")
            return {"error": str(e)}
    
    async def _periodic_tasks(self):
        """Tareas periódicas del agente de riesgo"""
        # Limpiar alertas antiguas
        current_time = datetime.utcnow()
        self.alerts = [
            alert for alert in self.alerts 
            if (current_time - alert.get("timestamp", current_time)).total_seconds() < 3600  # 1 hora
        ]
        
        await asyncio.sleep(0.1)