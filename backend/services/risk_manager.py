"""
Servicio de gestión de riesgo
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from backend.core.config import settings

class RiskManager:
    """
    Servicio centralizado de gestión de riesgo
    
    Funcionalidades:
    - Validación de trades antes de ejecución
    - Monitoreo continuo de exposición
    - Cálculo de métricas de riesgo
    - Alertas automáticas
    - Gestión de límites dinámicos
    """
    
    def __init__(self):
        self.logger = logging.getLogger("services.risk_manager")
        self.risk_limits = self._load_risk_limits()
        self.position_tracker = {}
        self.daily_pnl = 0.0
        self.max_drawdown_today = 0.0
        self.alerts_sent = []
        self.is_initialized = False
        
    async def initialize(self):
        """Inicializar el gestor de riesgo"""
        try:
            self.logger.info("🛡️ Inicializando Risk Manager...")
            
            # Cargar configuración de riesgo
            self.risk_limits = self._load_risk_limits()
            
            # Inicializar tracking
            self.position_tracker = {}
            self.daily_pnl = 0.0
            self.max_drawdown_today = 0.0
            self.alerts_sent = []
            
            self.is_initialized = True
            self.logger.info("✅ Risk Manager inicializado")
            
        except Exception as e:
            self.logger.error(f"Error inicializando Risk Manager: {e}")
            raise
    
    def _load_risk_limits(self) -> Dict[str, Any]:
        """Cargar límites de riesgo desde configuración"""
        return {
            # Límites de posición
            "max_position_size": settings.MAX_POSITION_SIZE,  # 10% del capital
            "max_total_exposure": 0.8,  # 80% del capital máximo en posiciones
            "max_single_asset_exposure": 0.3,  # 30% en un solo activo
            "max_correlated_exposure": 0.5,  # 50% en activos correlacionados
            
            # Límites de pérdida
            "max_daily_loss": settings.MAX_DAILY_LOSS,  # 5% pérdida diaria máxima
            "max_weekly_loss": 0.15,  # 15% pérdida semanal máxima
            "max_drawdown": settings.MAX_DRAWDOWN,  # 15% drawdown máximo
            
            # Límites de trading
            "max_trades_per_hour": 10,
            "max_trades_per_day": 50,
            "min_time_between_trades": 60,  # segundos
            
            # Límites de volatilidad
            "max_portfolio_volatility": 0.4,  # 40% volatilidad anual
            "max_asset_volatility": 0.8,  # 80% volatilidad individual
            
            # Gestión de capital
            "min_cash_reserve": 0.1,  # 10% mínimo en efectivo
            "max_leverage": 1.0,  # Sin apalancamiento
            
            # Límites de concentración
            "max_positions": 10,  # Máximo 10 posiciones simultáneas
            "min_diversification_score": 0.6,  # Score mínimo de diversificación
        }
    
    async def check_trade_risk(self, trade_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verificar riesgo de un trade antes de ejecución
        
        Args:
            trade_params: Parámetros del trade a verificar
            
        Returns:
            Resultado de la verificación de riesgo
        """
        try:
            symbol = trade_params.get("symbol")
            side = trade_params.get("side")
            quantity = trade_params.get("quantity", 0)
            current_balance = trade_params.get("current_balance", 1000.0)
            active_positions = trade_params.get("active_positions", {})
            
            risk_check = {
                "approved": True,
                "risk_score": 0,
                "warnings": [],
                "violations": [],
                "reason": ""
            }
            
            # 1. Verificar tamaño de posición
            position_check = await self._check_position_size(
                symbol, quantity, current_balance, active_positions
            )
            risk_check["risk_score"] += position_check["risk_score"]
            risk_check["warnings"].extend(position_check["warnings"])
            
            if not position_check["approved"]:
                risk_check["approved"] = False
                risk_check["violations"].append("position_size")
                risk_check["reason"] = position_check["reason"]
            
            # 2. Verificar exposición total
            exposure_check = await self._check_total_exposure(
                symbol, side, quantity, current_balance, active_positions
            )
            risk_check["risk_score"] += exposure_check["risk_score"]
            risk_check["warnings"].extend(exposure_check["warnings"])
            
            if not exposure_check["approved"]:
                risk_check["approved"] = False
                risk_check["violations"].append("total_exposure")
                if not risk_check["reason"]:
                    risk_check["reason"] = exposure_check["reason"]
            
            # 3. Verificar límites de pérdida diaria
            daily_loss_check = await self._check_daily_loss_limits(current_balance)
            risk_check["risk_score"] += daily_loss_check["risk_score"]
            risk_check["warnings"].extend(daily_loss_check["warnings"])
            
            if not daily_loss_check["approved"]:
                risk_check["approved"] = False
                risk_check["violations"].append("daily_loss")
                if not risk_check["reason"]:
                    risk_check["reason"] = daily_loss_check["reason"]
            
            # 4. Verificar frecuencia de trading
            frequency_check = await self._check_trading_frequency()
            risk_check["risk_score"] += frequency_check["risk_score"]
            risk_check["warnings"].extend(frequency_check["warnings"])
            
            if not frequency_check["approved"]:
                risk_check["approved"] = False
                risk_check["violations"].append("trading_frequency")
                if not risk_check["reason"]:
                    risk_check["reason"] = frequency_check["reason"]
            
            # 5. Verificar diversificación
            diversification_check = await self._check_diversification(
                symbol, active_positions, current_balance
            )
            risk_check["risk_score"] += diversification_check["risk_score"]
            risk_check["warnings"].extend(diversification_check["warnings"])
            
            # 6. Verificar correlaciones
            correlation_check = await self._check_correlation_risk(
                symbol, active_positions
            )
            risk_check["risk_score"] += correlation_check["risk_score"]
            risk_check["warnings"].extend(correlation_check["warnings"])
            
            # Calcular score final
            risk_check["risk_level"] = self._calculate_risk_level(risk_check["risk_score"])
            
            # Log del resultado
            if risk_check["approved"]:
                self.logger.info(f"✅ Trade aprobado: {symbol} {side} {quantity} (Risk Score: {risk_check['risk_score']})")
            else:
                self.logger.warning(f"❌ Trade rechazado: {symbol} {side} {quantity} - {risk_check['reason']}")
            
            return risk_check
            
        except Exception as e:
            self.logger.error(f"Error verificando riesgo de trade: {e}")
            return {
                "approved": False,
                "risk_score": 100,
                "reason": f"Error en verificación de riesgo: {str(e)}",
                "warnings": [],
                "violations": ["system_error"]
            }
    
    async def _check_position_size(self, symbol: str, quantity: float, 
                                 current_balance: float, active_positions: Dict) -> Dict[str, Any]:
        """Verificar tamaño de posición"""
        try:
            # Estimar valor de la posición (necesitaríamos precio actual)
            estimated_price = 100.0  # Placeholder - en producción obtener precio real
            position_value = quantity * estimated_price
            position_ratio = position_value / current_balance
            
            result = {
                "approved": True,
                "risk_score": 0,
                "warnings": [],
                "reason": ""
            }
            
            # Verificar límite de tamaño de posición
            if position_ratio > self.risk_limits["max_position_size"]:
                result["approved"] = False
                result["reason"] = f"Tamaño de posición excede límite: {position_ratio:.2%} > {self.risk_limits['max_position_size']:.2%}"
                result["risk_score"] = 50
            elif position_ratio > self.risk_limits["max_position_size"] * 0.8:
                result["warnings"].append(f"Posición grande: {position_ratio:.2%} del capital")
                result["risk_score"] = 20
            
            # Verificar concentración en un activo
            if symbol in active_positions:
                current_position_value = active_positions[symbol].get("current_price", 0) * active_positions[symbol].get("quantity", 0)
                total_position_value = current_position_value + position_value
                total_concentration = total_position_value / current_balance
                
                if total_concentration > self.risk_limits["max_single_asset_exposure"]:
                    result["approved"] = False
                    result["reason"] = f"Concentración en {symbol} excede límite: {total_concentration:.2%}"
                    result["risk_score"] = max(result["risk_score"], 40)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error verificando tamaño de posición: {e}")
            return {
                "approved": False,
                "risk_score": 50,
                "reason": f"Error verificando posición: {str(e)}",
                "warnings": []
            }
    
    async def _check_total_exposure(self, symbol: str, side: str, quantity: float,
                                  current_balance: float, active_positions: Dict) -> Dict[str, Any]:
        """Verificar exposición total del portafolio"""
        try:
            result = {
                "approved": True,
                "risk_score": 0,
                "warnings": [],
                "reason": ""
            }
            
            # Calcular exposición actual
            current_exposure = 0.0
            for pos_symbol, position in active_positions.items():
                if position.get("quantity", 0) > 0:
                    pos_value = position.get("current_price", 0) * position.get("quantity", 0)
                    current_exposure += pos_value
            
            # Agregar nueva posición
            estimated_price = 100.0  # Placeholder
            new_position_value = quantity * estimated_price
            
            if side == "BUY":
                total_exposure = current_exposure + new_position_value
            else:
                total_exposure = current_exposure  # SELL reduce exposición
            
            exposure_ratio = total_exposure / current_balance
            
            # Verificar límite de exposición total
            if exposure_ratio > self.risk_limits["max_total_exposure"]:
                result["approved"] = False
                result["reason"] = f"Exposición total excede límite: {exposure_ratio:.2%} > {self.risk_limits['max_total_exposure']:.2%}"
                result["risk_score"] = 40
            elif exposure_ratio > self.risk_limits["max_total_exposure"] * 0.9:
                result["warnings"].append(f"Alta exposición total: {exposure_ratio:.2%}")
                result["risk_score"] = 15
            
            # Verificar reserva de efectivo
            cash_reserve = (current_balance - total_exposure) / current_balance
            if cash_reserve < self.risk_limits["min_cash_reserve"]:
                result["warnings"].append(f"Baja reserva de efectivo: {cash_reserve:.2%}")
                result["risk_score"] += 10
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error verificando exposición total: {e}")
            return {
                "approved": True,
                "risk_score": 10,
                "reason": "",
                "warnings": [f"Error verificando exposición: {str(e)}"]
            }
    
    async def _check_daily_loss_limits(self, current_balance: float) -> Dict[str, Any]:
        """Verificar límites de pérdida diaria"""
        try:
            result = {
                "approved": True,
                "risk_score": 0,
                "warnings": [],
                "reason": ""
            }
            
            # Calcular pérdida diaria como porcentaje
            daily_loss_pct = abs(self.daily_pnl) / current_balance if self.daily_pnl < 0 else 0
            
            # Verificar límite de pérdida diaria
            if daily_loss_pct > self.risk_limits["max_daily_loss"]:
                result["approved"] = False
                result["reason"] = f"Pérdida diaria excede límite: {daily_loss_pct:.2%} > {self.risk_limits['max_daily_loss']:.2%}"
                result["risk_score"] = 60
            elif daily_loss_pct > self.risk_limits["max_daily_loss"] * 0.8:
                result["warnings"].append(f"Acercándose al límite de pérdida diaria: {daily_loss_pct:.2%}")
                result["risk_score"] = 25
            
            # Verificar drawdown
            if self.max_drawdown_today > self.risk_limits["max_drawdown"]:
                result["approved"] = False
                result["reason"] = f"Drawdown excede límite: {self.max_drawdown_today:.2%} > {self.risk_limits['max_drawdown']:.2%}"
                result["risk_score"] = max(result["risk_score"], 70)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error verificando límites de pérdida: {e}")
            return {
                "approved": True,
                "risk_score": 5,
                "reason": "",
                "warnings": []
            }
    
    async def _check_trading_frequency(self) -> Dict[str, Any]:
        """Verificar frecuencia de trading"""
        try:
            result = {
                "approved": True,
                "risk_score": 0,
                "warnings": [],
                "reason": ""
            }
            
            # En una implementación real, verificaríamos:
            # - Número de trades en la última hora
            # - Número de trades hoy
            # - Tiempo desde el último trade
            
            # Por ahora, simulamos verificación básica
            current_hour_trades = 0  # Placeholder
            daily_trades = 0  # Placeholder
            
            if current_hour_trades >= self.risk_limits["max_trades_per_hour"]:
                result["approved"] = False
                result["reason"] = f"Demasiados trades por hora: {current_hour_trades}"
                result["risk_score"] = 30
            
            if daily_trades >= self.risk_limits["max_trades_per_day"]:
                result["approved"] = False
                result["reason"] = f"Límite diario de trades alcanzado: {daily_trades}"
                result["risk_score"] = max(result["risk_score"], 40)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error verificando frecuencia de trading: {e}")
            return {
                "approved": True,
                "risk_score": 0,
                "reason": "",
                "warnings": []
            }
    
    async def _check_diversification(self, symbol: str, active_positions: Dict, 
                                   current_balance: float) -> Dict[str, Any]:
        """Verificar diversificación del portafolio"""
        try:
            result = {
                "approved": True,
                "risk_score": 0,
                "warnings": [],
                "reason": ""
            }
            
            # Contar número de posiciones
            num_positions = len([pos for pos in active_positions.values() if pos.get("quantity", 0) > 0])
            
            if num_positions >= self.risk_limits["max_positions"]:
                result["warnings"].append(f"Máximo número de posiciones alcanzado: {num_positions}")
                result["risk_score"] = 15
            
            # Calcular score de diversificación (simplificado)
            if num_positions == 0:
                diversification_score = 1.0  # Perfectamente diversificado (sin posiciones)
            else:
                # Score basado en distribución de valores
                position_values = []
                for pos in active_positions.values():
                    if pos.get("quantity", 0) > 0:
                        value = pos.get("current_price", 0) * pos.get("quantity", 0)
                        position_values.append(value)
                
                if position_values:
                    # Calcular índice de Herfindahl (inverso)
                    total_value = sum(position_values)
                    hhi = sum((value / total_value) ** 2 for value in position_values)
                    diversification_score = 1 - hhi
                else:
                    diversification_score = 1.0
            
            if diversification_score < self.risk_limits["min_diversification_score"]:
                result["warnings"].append(f"Baja diversificación: {diversification_score:.2f}")
                result["risk_score"] += 20
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error verificando diversificación: {e}")
            return {
                "approved": True,
                "risk_score": 5,
                "reason": "",
                "warnings": []
            }
    
    async def _check_correlation_risk(self, symbol: str, active_positions: Dict) -> Dict[str, Any]:
        """Verificar riesgo de correlación"""
        try:
            result = {
                "approved": True,
                "risk_score": 0,
                "warnings": [],
                "reason": ""
            }
            
            # Verificar si ya tenemos posiciones en activos correlacionados
            # En una implementación real, usaríamos datos históricos de correlación
            
            # Correlaciones conocidas (simplificado)
            correlations = {
                "BTCUSDT": ["ETHUSDT", "ADAUSDT"],
                "ETHUSDT": ["BTCUSDT", "LINKUSDT"],
                "ADAUSDT": ["BTCUSDT", "DOTUSDT"]
            }
            
            correlated_symbols = correlations.get(symbol, [])
            correlated_exposure = 0.0
            
            for corr_symbol in correlated_symbols:
                if corr_symbol in active_positions:
                    pos = active_positions[corr_symbol]
                    if pos.get("quantity", 0) > 0:
                        value = pos.get("current_price", 0) * pos.get("quantity", 0)
                        correlated_exposure += value
            
            if correlated_exposure > 0:
                result["warnings"].append(f"Exposición a activos correlacionados: ${correlated_exposure:.2f}")
                result["risk_score"] += 10
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error verificando correlaciones: {e}")
            return {
                "approved": True,
                "risk_score": 0,
                "reason": "",
                "warnings": []
            }
    
    def _calculate_risk_level(self, risk_score: int) -> str:
        """Calcular nivel de riesgo basado en score"""
        if risk_score >= 80:
            return "CRITICAL"
        elif risk_score >= 60:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        elif risk_score >= 20:
            return "LOW"
        else:
            return "MINIMAL"
    
    async def update_position_tracking(self, trade_data: Dict[str, Any]):
        """Actualizar tracking de posiciones después de un trade"""
        try:
            symbol = trade_data.get("symbol")
            side = trade_data.get("side")
            quantity = trade_data.get("executed_quantity", 0)
            price = trade_data.get("executed_price", 0)
            pnl = trade_data.get("pnl", 0)
            
            # Actualizar PnL diario
            self.daily_pnl += pnl
            
            # Actualizar drawdown
            if self.daily_pnl < 0:
                drawdown_pct = abs(self.daily_pnl) / 1000.0  # Asumiendo capital inicial de 1000
                self.max_drawdown_today = max(self.max_drawdown_today, drawdown_pct)
            
            # Actualizar tracking de posiciones
            if symbol not in self.position_tracker:
                self.position_tracker[symbol] = {
                    "quantity": 0.0,
                    "average_price": 0.0,
                    "total_pnl": 0.0,
                    "trades_count": 0
                }
            
            pos = self.position_tracker[symbol]
            
            if side == "BUY":
                # Actualizar posición larga
                total_cost = pos["quantity"] * pos["average_price"] + quantity * price
                pos["quantity"] += quantity
                pos["average_price"] = total_cost / pos["quantity"] if pos["quantity"] > 0 else 0
            else:
                # Reducir posición
                pos["quantity"] -= quantity
                if pos["quantity"] <= 0:
                    pos["quantity"] = 0
                    pos["average_price"] = 0
            
            pos["total_pnl"] += pnl
            pos["trades_count"] += 1
            
            self.logger.debug(f"Posición actualizada: {symbol} - Cantidad: {pos['quantity']}, PnL: {pos['total_pnl']}")
            
        except Exception as e:
            self.logger.error(f"Error actualizando tracking de posiciones: {e}")
    
    async def generate_risk_alert(self, alert_type: str, message: str, severity: str = "MEDIUM"):
        """Generar alerta de riesgo"""
        try:
            alert = {
                "timestamp": datetime.utcnow(),
                "type": alert_type,
                "message": message,
                "severity": severity
            }
            
            # Evitar spam de alertas
            alert_key = f"{alert_type}_{severity}"
            recent_alerts = [a for a in self.alerts_sent if (datetime.utcnow() - a["timestamp"]).total_seconds() < 3600]
            
            if not any(a["key"] == alert_key for a in recent_alerts):
                alert["key"] = alert_key
                self.alerts_sent.append(alert)
                
                # Log de la alerta
                if severity == "CRITICAL":
                    self.logger.critical(f"🚨 ALERTA CRÍTICA: {message}")
                elif severity == "HIGH":
                    self.logger.error(f"⚠️ ALERTA ALTA: {message}")
                else:
                    self.logger.warning(f"⚠️ ALERTA: {message}")
                
                # En producción, aquí enviaríamos notificaciones (email, Telegram, etc.)
                
        except Exception as e:
            self.logger.error(f"Error generando alerta: {e}")
    
    async def get_risk_metrics(self) -> Dict[str, Any]:
        """Obtener métricas actuales de riesgo"""
        try:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "daily_pnl": self.daily_pnl,
                "max_drawdown_today": self.max_drawdown_today,
                "active_positions": len([pos for pos in self.position_tracker.values() if pos["quantity"] > 0]),
                "total_trades_today": sum(pos["trades_count"] for pos in self.position_tracker.values()),
                "risk_limits": self.risk_limits,
                "recent_alerts": len([a for a in self.alerts_sent if (datetime.utcnow() - a["timestamp"]).total_seconds() < 3600]),
                "position_tracker": self.position_tracker
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo métricas de riesgo: {e}")
            return {"error": str(e)}
    
    async def reset_daily_metrics(self):
        """Resetear métricas diarias (llamar al inicio de cada día)"""
        try:
            self.daily_pnl = 0.0
            self.max_drawdown_today = 0.0
            
            # Limpiar alertas antiguas
            cutoff_time = datetime.utcnow() - timedelta(days=1)
            self.alerts_sent = [a for a in self.alerts_sent if a["timestamp"] > cutoff_time]
            
            self.logger.info("📊 Métricas diarias de riesgo reseteadas")
            
        except Exception as e:
            self.logger.error(f"Error reseteando métricas diarias: {e}")
    
    def update_risk_limits(self, new_limits: Dict[str, Any]):
        """Actualizar límites de riesgo dinámicamente"""
        try:
            for key, value in new_limits.items():
                if key in self.risk_limits:
                    old_value = self.risk_limits[key]
                    self.risk_limits[key] = value
                    self.logger.info(f"Límite de riesgo actualizado: {key} {old_value} -> {value}")
                else:
                    self.logger.warning(f"Límite de riesgo desconocido: {key}")
                    
        except Exception as e:
            self.logger.error(f"Error actualizando límites de riesgo: {e}")