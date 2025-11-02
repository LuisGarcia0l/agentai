"""
📈 Indicadores Técnicos Avanzados

Implementación de indicadores técnicos populares para análisis de mercado.
Incluye RSI, MACD, Bollinger Bands, medias móviles y más.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    """Tipos de señales de trading."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class TradingSignal:
    """Señal de trading."""
    signal: SignalType
    strength: float  # 0.0 a 1.0
    price: float
    timestamp: pd.Timestamp
    reason: str
    indicators: Dict[str, float]


class TechnicalIndicators:
    """Calculadora de indicadores técnicos."""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """
        Simple Moving Average (Media Móvil Simple).
        
        Args:
            data: Serie de precios
            period: Período de la media
        
        Returns:
            Serie con la media móvil
        """
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """
        Exponential Moving Average (Media Móvil Exponencial).
        
        Args:
            data: Serie de precios
            period: Período de la media
        
        Returns:
            Serie con la media móvil exponencial
        """
        return data.ewm(span=period).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index (Índice de Fuerza Relativa).
        
        Args:
            data: Serie de precios de cierre
            period: Período del RSI (default: 14)
        
        Returns:
            Serie con valores RSI (0-100)
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def macd(
        data: pd.Series, 
        fast_period: int = 12, 
        slow_period: int = 26, 
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence).
        
        Args:
            data: Serie de precios de cierre
            fast_period: Período EMA rápida
            slow_period: Período EMA lenta
            signal_period: Período línea de señal
        
        Returns:
            Tupla (MACD, Signal, Histogram)
        """
        ema_fast = TechnicalIndicators.ema(data, fast_period)
        ema_slow = TechnicalIndicators.ema(data, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(
        data: pd.Series, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands (Bandas de Bollinger).
        
        Args:
            data: Serie de precios de cierre
            period: Período de la media móvil
            std_dev: Desviaciones estándar
        
        Returns:
            Tupla (Upper Band, Middle Band, Lower Band)
        """
        middle_band = TechnicalIndicators.sma(data, period)
        std = data.rolling(window=period).std()
        
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def stochastic(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        k_period: int = 14,
        d_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator (Oscilador Estocástico).
        
        Args:
            high: Serie de precios máximos
            low: Serie de precios mínimos
            close: Serie de precios de cierre
            k_period: Período %K
            d_period: Período %D
        
        Returns:
            Tupla (%K, %D)
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return k_percent, d_percent
    
    @staticmethod
    def atr(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        period: int = 14
    ) -> pd.Series:
        """
        Average True Range (Rango Verdadero Promedio).
        
        Args:
            high: Serie de precios máximos
            low: Serie de precios mínimos
            close: Serie de precios de cierre
            period: Período del ATR
        
        Returns:
            Serie con valores ATR
        """
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def williams_r(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        period: int = 14
    ) -> pd.Series:
        """
        Williams %R.
        
        Args:
            high: Serie de precios máximos
            low: Serie de precios mínimos
            close: Serie de precios de cierre
            period: Período del indicador
        
        Returns:
            Serie con valores Williams %R
        """
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
        
        return williams_r


class TradingStrategy:
    """Estrategia de trading basada en indicadores técnicos."""
    
    def __init__(self, name: str):
        self.name = name
        self.indicators = TechnicalIndicators()
    
    def analyze(self, df: pd.DataFrame) -> Optional[TradingSignal]:
        """
        Analizar datos y generar señal de trading.
        
        Args:
            df: DataFrame con datos OHLCV
        
        Returns:
            Señal de trading o None
        """
        raise NotImplementedError("Subclases deben implementar analyze()")


class RSIStrategy(TradingStrategy):
    """Estrategia basada en RSI."""
    
    def __init__(
        self, 
        rsi_period: int = 14,
        oversold_threshold: float = 30,
        overbought_threshold: float = 70
    ):
        super().__init__("RSI Strategy")
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
    
    def analyze(self, df: pd.DataFrame) -> Optional[TradingSignal]:
        """Analizar usando RSI."""
        if len(df) < self.rsi_period + 1:
            return None
        
        # Calcular RSI
        rsi = self.indicators.rsi(df['close'], self.rsi_period)
        current_rsi = rsi.iloc[-1]
        current_price = df['close'].iloc[-1]
        current_time = df.index[-1]
        
        # Generar señales
        if current_rsi < self.oversold_threshold:
            return TradingSignal(
                signal=SignalType.BUY,
                strength=min((self.oversold_threshold - current_rsi) / 10, 1.0),
                price=current_price,
                timestamp=current_time,
                reason=f"RSI oversold: {current_rsi:.2f}",
                indicators={"rsi": current_rsi}
            )
        
        elif current_rsi > self.overbought_threshold:
            return TradingSignal(
                signal=SignalType.SELL,
                strength=min((current_rsi - self.overbought_threshold) / 10, 1.0),
                price=current_price,
                timestamp=current_time,
                reason=f"RSI overbought: {current_rsi:.2f}",
                indicators={"rsi": current_rsi}
            )
        
        return TradingSignal(
            signal=SignalType.HOLD,
            strength=0.0,
            price=current_price,
            timestamp=current_time,
            reason=f"RSI neutral: {current_rsi:.2f}",
            indicators={"rsi": current_rsi}
        )


class MACDStrategy(TradingStrategy):
    """Estrategia basada en MACD."""
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ):
        super().__init__("MACD Strategy")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def analyze(self, df: pd.DataFrame) -> Optional[TradingSignal]:
        """Analizar usando MACD."""
        min_periods = max(self.slow_period, self.signal_period) + 2
        if len(df) < min_periods:
            return None
        
        # Calcular MACD
        macd, signal, histogram = self.indicators.macd(
            df['close'], self.fast_period, self.slow_period, self.signal_period
        )
        
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_histogram = histogram.iloc[-1]
        prev_histogram = histogram.iloc[-2]
        
        current_price = df['close'].iloc[-1]
        current_time = df.index[-1]
        
        # Detectar cruces
        if prev_histogram < 0 and current_histogram > 0:
            # Cruce alcista
            return TradingSignal(
                signal=SignalType.BUY,
                strength=min(abs(current_histogram) / abs(current_macd), 1.0),
                price=current_price,
                timestamp=current_time,
                reason="MACD bullish crossover",
                indicators={
                    "macd": current_macd,
                    "signal": current_signal,
                    "histogram": current_histogram
                }
            )
        
        elif prev_histogram > 0 and current_histogram < 0:
            # Cruce bajista
            return TradingSignal(
                signal=SignalType.SELL,
                strength=min(abs(current_histogram) / abs(current_macd), 1.0),
                price=current_price,
                timestamp=current_time,
                reason="MACD bearish crossover",
                indicators={
                    "macd": current_macd,
                    "signal": current_signal,
                    "histogram": current_histogram
                }
            )
        
        return TradingSignal(
            signal=SignalType.HOLD,
            strength=0.0,
            price=current_price,
            timestamp=current_time,
            reason="MACD no signal",
            indicators={
                "macd": current_macd,
                "signal": current_signal,
                "histogram": current_histogram
            }
        )


class BollingerBandsStrategy(TradingStrategy):
    """Estrategia basada en Bollinger Bands."""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__("Bollinger Bands Strategy")
        self.period = period
        self.std_dev = std_dev
    
    def analyze(self, df: pd.DataFrame) -> Optional[TradingSignal]:
        """Analizar usando Bollinger Bands."""
        if len(df) < self.period + 1:
            return None
        
        # Calcular Bollinger Bands
        upper, middle, lower = self.indicators.bollinger_bands(
            df['close'], self.period, self.std_dev
        )
        
        current_price = df['close'].iloc[-1]
        current_upper = upper.iloc[-1]
        current_middle = middle.iloc[-1]
        current_lower = lower.iloc[-1]
        current_time = df.index[-1]
        
        # Calcular posición relativa
        bb_position = (current_price - current_lower) / (current_upper - current_lower)
        
        # Generar señales
        if current_price <= current_lower:
            # Precio toca banda inferior - señal de compra
            return TradingSignal(
                signal=SignalType.BUY,
                strength=min((current_lower - current_price) / current_lower, 1.0),
                price=current_price,
                timestamp=current_time,
                reason="Price at lower Bollinger Band",
                indicators={
                    "bb_upper": current_upper,
                    "bb_middle": current_middle,
                    "bb_lower": current_lower,
                    "bb_position": bb_position
                }
            )
        
        elif current_price >= current_upper:
            # Precio toca banda superior - señal de venta
            return TradingSignal(
                signal=SignalType.SELL,
                strength=min((current_price - current_upper) / current_upper, 1.0),
                price=current_price,
                timestamp=current_time,
                reason="Price at upper Bollinger Band",
                indicators={
                    "bb_upper": current_upper,
                    "bb_middle": current_middle,
                    "bb_lower": current_lower,
                    "bb_position": bb_position
                }
            )
        
        return TradingSignal(
            signal=SignalType.HOLD,
            strength=0.0,
            price=current_price,
            timestamp=current_time,
            reason="Price within Bollinger Bands",
            indicators={
                "bb_upper": current_upper,
                "bb_middle": current_middle,
                "bb_lower": current_lower,
                "bb_position": bb_position
            }
        )


class MultiIndicatorStrategy(TradingStrategy):
    """Estrategia que combina múltiples indicadores."""
    
    def __init__(self):
        super().__init__("Multi-Indicator Strategy")
        self.rsi_strategy = RSIStrategy()
        self.macd_strategy = MACDStrategy()
        self.bb_strategy = BollingerBandsStrategy()
    
    def analyze(self, df: pd.DataFrame) -> Optional[TradingSignal]:
        """Analizar combinando múltiples indicadores."""
        # Obtener señales individuales
        rsi_signal = self.rsi_strategy.analyze(df)
        macd_signal = self.macd_strategy.analyze(df)
        bb_signal = self.bb_strategy.analyze(df)
        
        if not all([rsi_signal, macd_signal, bb_signal]):
            return None
        
        current_price = df['close'].iloc[-1]
        current_time = df.index[-1]
        
        # Combinar indicadores
        buy_votes = 0
        sell_votes = 0
        total_strength = 0
        
        signals = [rsi_signal, macd_signal, bb_signal]
        weights = [0.4, 0.4, 0.2]  # Pesos para cada indicador
        
        for signal, weight in zip(signals, weights):
            if signal.signal == SignalType.BUY:
                buy_votes += weight
                total_strength += signal.strength * weight
            elif signal.signal == SignalType.SELL:
                sell_votes += weight
                total_strength += signal.strength * weight
        
        # Combinar todos los indicadores
        all_indicators = {}
        for signal in signals:
            all_indicators.update(signal.indicators)
        
        # Decidir señal final
        if buy_votes > sell_votes and buy_votes > 0.5:
            return TradingSignal(
                signal=SignalType.BUY,
                strength=min(total_strength, 1.0),
                price=current_price,
                timestamp=current_time,
                reason=f"Multi-indicator BUY (votes: {buy_votes:.1f})",
                indicators=all_indicators
            )
        
        elif sell_votes > buy_votes and sell_votes > 0.5:
            return TradingSignal(
                signal=SignalType.SELL,
                strength=min(total_strength, 1.0),
                price=current_price,
                timestamp=current_time,
                reason=f"Multi-indicator SELL (votes: {sell_votes:.1f})",
                indicators=all_indicators
            )
        
        return TradingSignal(
            signal=SignalType.HOLD,
            strength=0.0,
            price=current_price,
            timestamp=current_time,
            reason=f"Multi-indicator HOLD (buy: {buy_votes:.1f}, sell: {sell_votes:.1f})",
            indicators=all_indicators
        )