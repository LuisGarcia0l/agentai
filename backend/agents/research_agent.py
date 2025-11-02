"""
Research Agent - Agente especializado en investigación y análisis de mercado
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import yfinance as yf
import ta

from backend.agents.base_agent import BaseAgent, AgentTask
from backend.services.binance_service import BinanceService
from backend.services.llm_service import LLMService
from backend.core.config import settings

class ResearchAgent(BaseAgent):
    """
    Agente especializado en investigación de mercado y análisis técnico/fundamental
    
    Responsabilidades:
    - Análisis técnico de instrumentos financieros
    - Investigación de tendencias de mercado
    - Identificación de oportunidades de trading
    - Análisis de correlaciones entre activos
    - Generación de reportes de investigación
    """
    
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            description="Agente especializado en investigación y análisis de mercado"
        )
        self.binance_service: Optional[BinanceService] = None
        self.llm_service: Optional[LLMService] = None
        self.analysis_cache = {}
        self.supported_timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        
    async def _initialize_agent(self):
        """Inicializar servicios del agente de investigación"""
        # Inicializar servicio de Binance
        self.binance_service = BinanceService()
        await self.binance_service.initialize()
        
        # Inicializar servicio de LLM
        self.llm_service = LLMService()
        await self.llm_service.initialize()
        
        self.logger.info("ResearchAgent inicializado con servicios de Binance y LLM")
    
    async def _process_task(self, task: AgentTask) -> Any:
        """Procesar tareas de investigación"""
        task_type = task.task_type
        parameters = task.parameters
        
        if task_type == "technical_analysis":
            return await self._perform_technical_analysis(parameters)
        elif task_type == "market_research":
            return await self._perform_market_research(parameters)
        elif task_type == "opportunity_scan":
            return await self._scan_opportunities(parameters)
        elif task_type == "correlation_analysis":
            return await self._analyze_correlations(parameters)
        elif task_type == "sentiment_analysis":
            return await self._analyze_sentiment(parameters)
        else:
            raise ValueError(f"Tipo de tarea no soportado: {task_type}")
    
    async def _perform_technical_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realizar análisis técnico de un símbolo
        
        Args:
            parameters: Debe contener 'symbol', 'timeframe', 'periods'
            
        Returns:
            Diccionario con resultados del análisis técnico
        """
        symbol = parameters.get("symbol", settings.DEFAULT_TRADING_PAIR)
        timeframe = parameters.get("timeframe", "1h")
        periods = parameters.get("periods", 100)
        
        self.logger.info(f"Realizando análisis técnico de {symbol} en {timeframe}")
        
        try:
            # Obtener datos históricos
            df = await self.binance_service.get_historical_data(symbol, timeframe, periods)
            
            if df.empty:
                raise ValueError(f"No se pudieron obtener datos para {symbol}")
            
            # Calcular indicadores técnicos
            indicators = self._calculate_technical_indicators(df)
            
            # Generar señales
            signals = self._generate_trading_signals(df, indicators)
            
            # Análisis con LLM
            llm_analysis = await self._get_llm_analysis(symbol, df, indicators, signals)
            
            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat(),
                "current_price": float(df['close'].iloc[-1]),
                "price_change_24h": float((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100) if len(df) >= 24 else 0,
                "indicators": indicators,
                "signals": signals,
                "llm_analysis": llm_analysis,
                "data_points": len(df)
            }
            
            # Guardar en caché
            cache_key = f"{symbol}_{timeframe}_{datetime.utcnow().strftime('%Y%m%d_%H')}"
            self.analysis_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error en análisis técnico: {e}")
            raise
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcular indicadores técnicos"""
        indicators = {}
        
        try:
            # RSI
            indicators["rsi"] = {
                "value": float(ta.momentum.RSIIndicator(df['close']).rsi().iloc[-1]),
                "signal": self._interpret_rsi(ta.momentum.RSIIndicator(df['close']).rsi().iloc[-1])
            }
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            macd_line = macd.macd().iloc[-1]
            macd_signal = macd.macd_signal().iloc[-1]
            indicators["macd"] = {
                "macd": float(macd_line),
                "signal": float(macd_signal),
                "histogram": float(macd_line - macd_signal),
                "signal_interpretation": "bullish" if macd_line > macd_signal else "bearish"
            }
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['close'])
            current_price = df['close'].iloc[-1]
            bb_upper = bb.bollinger_hband().iloc[-1]
            bb_lower = bb.bollinger_lband().iloc[-1]
            bb_middle = bb.bollinger_mavg().iloc[-1]
            
            indicators["bollinger_bands"] = {
                "upper": float(bb_upper),
                "middle": float(bb_middle),
                "lower": float(bb_lower),
                "position": self._interpret_bb_position(current_price, bb_upper, bb_lower, bb_middle)
            }
            
            # Moving Averages
            sma_20 = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator().iloc[-1]
            sma_50 = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator().iloc[-1]
            ema_12 = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator().iloc[-1]
            ema_26 = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator().iloc[-1]
            
            indicators["moving_averages"] = {
                "sma_20": float(sma_20),
                "sma_50": float(sma_50),
                "ema_12": float(ema_12),
                "ema_26": float(ema_26),
                "trend": "bullish" if current_price > sma_20 > sma_50 else "bearish"
            }
            
            # Volume indicators
            indicators["volume"] = {
                "current": float(df['volume'].iloc[-1]),
                "average_20": float(df['volume'].rolling(20).mean().iloc[-1]),
                "volume_trend": "increasing" if df['volume'].iloc[-1] > df['volume'].rolling(20).mean().iloc[-1] else "decreasing"
            }
            
            # Support and Resistance levels
            indicators["support_resistance"] = self._calculate_support_resistance(df)
            
        except Exception as e:
            self.logger.error(f"Error calculando indicadores: {e}")
            indicators["error"] = str(e)
        
        return indicators
    
    def _interpret_rsi(self, rsi_value: float) -> str:
        """Interpretar valor RSI"""
        if rsi_value >= 70:
            return "overbought"
        elif rsi_value <= 30:
            return "oversold"
        else:
            return "neutral"
    
    def _interpret_bb_position(self, price: float, upper: float, lower: float, middle: float) -> str:
        """Interpretar posición en Bollinger Bands"""
        if price >= upper:
            return "above_upper_band"
        elif price <= lower:
            return "below_lower_band"
        elif price > middle:
            return "above_middle"
        else:
            return "below_middle"
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, List[float]]:
        """Calcular niveles de soporte y resistencia"""
        try:
            # Método simple: usar máximos y mínimos locales
            highs = df['high'].rolling(window=10, center=True).max()
            lows = df['low'].rolling(window=10, center=True).min()
            
            resistance_levels = []
            support_levels = []
            
            for i in range(10, len(df) - 10):
                if df['high'].iloc[i] == highs.iloc[i]:
                    resistance_levels.append(float(df['high'].iloc[i]))
                if df['low'].iloc[i] == lows.iloc[i]:
                    support_levels.append(float(df['low'].iloc[i]))
            
            # Tomar los niveles más relevantes (últimos 5)
            resistance_levels = sorted(set(resistance_levels), reverse=True)[:5]
            support_levels = sorted(set(support_levels), reverse=True)[:5]
            
            return {
                "resistance": resistance_levels,
                "support": support_levels
            }
        except Exception as e:
            self.logger.error(f"Error calculando soporte/resistencia: {e}")
            return {"resistance": [], "support": []}
    
    def _generate_trading_signals(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generar señales de trading basadas en indicadores"""
        signals = {
            "overall_signal": "neutral",
            "strength": 0,
            "individual_signals": {}
        }
        
        try:
            signal_score = 0
            
            # Señal RSI
            rsi_signal = indicators.get("rsi", {}).get("signal", "neutral")
            if rsi_signal == "oversold":
                signals["individual_signals"]["rsi"] = "buy"
                signal_score += 1
            elif rsi_signal == "overbought":
                signals["individual_signals"]["rsi"] = "sell"
                signal_score -= 1
            else:
                signals["individual_signals"]["rsi"] = "neutral"
            
            # Señal MACD
            macd_signal = indicators.get("macd", {}).get("signal_interpretation", "neutral")
            if macd_signal == "bullish":
                signals["individual_signals"]["macd"] = "buy"
                signal_score += 1
            elif macd_signal == "bearish":
                signals["individual_signals"]["macd"] = "sell"
                signal_score -= 1
            else:
                signals["individual_signals"]["macd"] = "neutral"
            
            # Señal de tendencia (medias móviles)
            ma_trend = indicators.get("moving_averages", {}).get("trend", "neutral")
            if ma_trend == "bullish":
                signals["individual_signals"]["trend"] = "buy"
                signal_score += 1
            elif ma_trend == "bearish":
                signals["individual_signals"]["trend"] = "sell"
                signal_score -= 1
            else:
                signals["individual_signals"]["trend"] = "neutral"
            
            # Señal general
            if signal_score >= 2:
                signals["overall_signal"] = "buy"
            elif signal_score <= -2:
                signals["overall_signal"] = "sell"
            else:
                signals["overall_signal"] = "neutral"
            
            signals["strength"] = abs(signal_score)
            
        except Exception as e:
            self.logger.error(f"Error generando señales: {e}")
            signals["error"] = str(e)
        
        return signals
    
    async def _get_llm_analysis(self, symbol: str, df: pd.DataFrame, 
                              indicators: Dict[str, Any], signals: Dict[str, Any]) -> str:
        """Obtener análisis del LLM"""
        try:
            if not self.llm_service:
                return "Análisis LLM no disponible"
            
            # Preparar contexto para el LLM
            context = f"""
            Análisis técnico para {symbol}:
            
            Precio actual: ${df['close'].iloc[-1]:.2f}
            Cambio 24h: {((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100):.2f}% (si hay datos suficientes)
            
            Indicadores técnicos:
            - RSI: {indicators.get('rsi', {}).get('value', 'N/A')} ({indicators.get('rsi', {}).get('signal', 'N/A')})
            - MACD: {indicators.get('macd', {}).get('signal_interpretation', 'N/A')}
            - Tendencia MA: {indicators.get('moving_averages', {}).get('trend', 'N/A')}
            - Volumen: {indicators.get('volume', {}).get('volume_trend', 'N/A')}
            
            Señales:
            - Señal general: {signals.get('overall_signal', 'N/A')}
            - Fuerza: {signals.get('strength', 0)}/3
            
            Por favor, proporciona un análisis conciso y profesional de esta información técnica.
            """
            
            analysis = await self.llm_service.analyze_market_data(context)
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error en análisis LLM: {e}")
            return f"Error en análisis LLM: {str(e)}"
    
    async def _perform_market_research(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Realizar investigación general de mercado"""
        symbols = parameters.get("symbols", [settings.DEFAULT_TRADING_PAIR])
        timeframe = parameters.get("timeframe", "1d")
        
        self.logger.info(f"Realizando investigación de mercado para {len(symbols)} símbolos")
        
        research_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "market_overview": {},
            "symbol_analysis": {},
            "correlations": {},
            "recommendations": []
        }
        
        try:
            # Analizar cada símbolo
            for symbol in symbols:
                analysis = await self._perform_technical_analysis({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "periods": 200
                })
                research_results["symbol_analysis"][symbol] = analysis
            
            # Análisis de correlaciones si hay múltiples símbolos
            if len(symbols) > 1:
                research_results["correlations"] = await self._analyze_correlations({
                    "symbols": symbols,
                    "timeframe": timeframe
                })
            
            # Generar recomendaciones generales
            research_results["recommendations"] = self._generate_market_recommendations(
                research_results["symbol_analysis"]
            )
            
            return research_results
            
        except Exception as e:
            self.logger.error(f"Error en investigación de mercado: {e}")
            raise
    
    async def _scan_opportunities(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Escanear oportunidades de trading"""
        # Lista de símbolos populares para escanear
        symbols_to_scan = parameters.get("symbols", [
            "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
            "BNBUSDT", "SOLUSDT", "MATICUSDT", "AVAXUSDT", "ATOMUSDT"
        ])
        
        self.logger.info(f"Escaneando oportunidades en {len(symbols_to_scan)} símbolos")
        
        opportunities = {
            "timestamp": datetime.utcnow().isoformat(),
            "scanned_symbols": len(symbols_to_scan),
            "opportunities": [],
            "summary": {}
        }
        
        buy_opportunities = []
        sell_opportunities = []
        
        for symbol in symbols_to_scan:
            try:
                analysis = await self._perform_technical_analysis({
                    "symbol": symbol,
                    "timeframe": "1h",
                    "periods": 100
                })
                
                signal = analysis.get("signals", {}).get("overall_signal", "neutral")
                strength = analysis.get("signals", {}).get("strength", 0)
                
                if signal == "buy" and strength >= 2:
                    buy_opportunities.append({
                        "symbol": symbol,
                        "signal": signal,
                        "strength": strength,
                        "price": analysis.get("current_price"),
                        "analysis": analysis
                    })
                elif signal == "sell" and strength >= 2:
                    sell_opportunities.append({
                        "symbol": symbol,
                        "signal": signal,
                        "strength": strength,
                        "price": analysis.get("current_price"),
                        "analysis": analysis
                    })
                
            except Exception as e:
                self.logger.warning(f"Error analizando {symbol}: {e}")
                continue
        
        # Ordenar por fuerza de señal
        buy_opportunities.sort(key=lambda x: x["strength"], reverse=True)
        sell_opportunities.sort(key=lambda x: x["strength"], reverse=True)
        
        opportunities["opportunities"] = {
            "buy": buy_opportunities[:5],  # Top 5 oportunidades de compra
            "sell": sell_opportunities[:5]  # Top 5 oportunidades de venta
        }
        
        opportunities["summary"] = {
            "total_buy_opportunities": len(buy_opportunities),
            "total_sell_opportunities": len(sell_opportunities),
            "market_sentiment": self._calculate_market_sentiment(buy_opportunities, sell_opportunities)
        }
        
        return opportunities
    
    def _calculate_market_sentiment(self, buy_ops: List, sell_ops: List) -> str:
        """Calcular sentimiento general del mercado"""
        total_buy_strength = sum(op["strength"] for op in buy_ops)
        total_sell_strength = sum(op["strength"] for op in sell_ops)
        
        if total_buy_strength > total_sell_strength * 1.5:
            return "bullish"
        elif total_sell_strength > total_buy_strength * 1.5:
            return "bearish"
        else:
            return "neutral"
    
    def _generate_market_recommendations(self, symbol_analysis: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones basadas en análisis"""
        recommendations = []
        
        buy_signals = 0
        sell_signals = 0
        
        for symbol, analysis in symbol_analysis.items():
            signal = analysis.get("signals", {}).get("overall_signal", "neutral")
            if signal == "buy":
                buy_signals += 1
            elif signal == "sell":
                sell_signals += 1
        
        if buy_signals > sell_signals:
            recommendations.append("El mercado muestra señales alcistas predominantes")
        elif sell_signals > buy_signals:
            recommendations.append("El mercado muestra señales bajistas predominantes")
        else:
            recommendations.append("El mercado se encuentra en una fase neutral")
        
        recommendations.append(f"Se identificaron {buy_signals} señales de compra y {sell_signals} señales de venta")
        
        return recommendations
    
    async def _analyze_correlations(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar correlaciones entre activos"""
        symbols = parameters.get("symbols", [])
        timeframe = parameters.get("timeframe", "1d")
        periods = parameters.get("periods", 100)
        
        if len(symbols) < 2:
            return {"error": "Se necesitan al menos 2 símbolos para análisis de correlación"}
        
        self.logger.info(f"Analizando correlaciones entre {len(symbols)} símbolos")
        
        try:
            # Obtener datos para todos los símbolos
            price_data = {}
            for symbol in symbols:
                df = await self.binance_service.get_historical_data(symbol, timeframe, periods)
                if not df.empty:
                    price_data[symbol] = df['close']
            
            if len(price_data) < 2:
                return {"error": "No se pudieron obtener datos suficientes"}
            
            # Crear DataFrame con todos los precios
            combined_df = pd.DataFrame(price_data)
            
            # Calcular matriz de correlación
            correlation_matrix = combined_df.corr()
            
            # Convertir a formato serializable
            correlations = {}
            for i, symbol1 in enumerate(symbols):
                correlations[symbol1] = {}
                for j, symbol2 in enumerate(symbols):
                    if symbol1 in correlation_matrix.index and symbol2 in correlation_matrix.columns:
                        correlations[symbol1][symbol2] = float(correlation_matrix.loc[symbol1, symbol2])
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "symbols": symbols,
                "timeframe": timeframe,
                "periods": periods,
                "correlations": correlations,
                "strongest_positive": self._find_strongest_correlation(correlations, positive=True),
                "strongest_negative": self._find_strongest_correlation(correlations, positive=False)
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis de correlaciones: {e}")
            return {"error": str(e)}
    
    def _find_strongest_correlation(self, correlations: Dict, positive: bool = True) -> Dict[str, Any]:
        """Encontrar la correlación más fuerte"""
        strongest = {"pair": None, "correlation": 0 if positive else 0}
        
        for symbol1, corr_dict in correlations.items():
            for symbol2, corr_value in corr_dict.items():
                if symbol1 != symbol2:  # Evitar autocorrelación
                    if positive and corr_value > strongest["correlation"]:
                        strongest = {"pair": f"{symbol1}-{symbol2}", "correlation": corr_value}
                    elif not positive and corr_value < strongest["correlation"]:
                        strongest = {"pair": f"{symbol1}-{symbol2}", "correlation": corr_value}
        
        return strongest
    
    async def _analyze_sentiment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar sentimiento del mercado usando LLM"""
        try:
            if not self.llm_service:
                return {"error": "Servicio LLM no disponible"}
            
            # Obtener datos recientes del mercado
            symbol = parameters.get("symbol", settings.DEFAULT_TRADING_PAIR)
            analysis = await self._perform_technical_analysis({
                "symbol": symbol,
                "timeframe": "1h",
                "periods": 50
            })
            
            # Preparar contexto para análisis de sentimiento
            context = f"""
            Analiza el sentimiento del mercado para {symbol} basado en los siguientes datos técnicos:
            
            Precio actual: ${analysis.get('current_price', 0):.2f}
            Señal técnica: {analysis.get('signals', {}).get('overall_signal', 'neutral')}
            RSI: {analysis.get('indicators', {}).get('rsi', {}).get('value', 'N/A')}
            Tendencia: {analysis.get('indicators', {}).get('moving_averages', {}).get('trend', 'N/A')}
            
            Proporciona un análisis de sentimiento (bullish/bearish/neutral) con justificación.
            """
            
            sentiment_analysis = await self.llm_service.analyze_sentiment(context)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "sentiment_analysis": sentiment_analysis,
                "technical_context": analysis
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis de sentimiento: {e}")
            return {"error": str(e)}
    
    async def _periodic_tasks(self):
        """Tareas periódicas del agente de investigación"""
        # Limpiar caché antiguo cada hora
        current_time = datetime.utcnow()
        keys_to_remove = []
        
        for key in self.analysis_cache:
            # Extraer timestamp del key
            try:
                timestamp_str = key.split('_')[-2] + '_' + key.split('_')[-1]
                cache_time = datetime.strptime(timestamp_str, '%Y%m%d_%H')
                if (current_time - cache_time).total_seconds() > 3600:  # 1 hora
                    keys_to_remove.append(key)
            except:
                keys_to_remove.append(key)  # Remover keys malformados
        
        for key in keys_to_remove:
            del self.analysis_cache[key]
        
        if keys_to_remove:
            self.logger.debug(f"Limpiados {len(keys_to_remove)} elementos del caché")
        
        await asyncio.sleep(0.1)