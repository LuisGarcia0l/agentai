import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus, Clock } from 'lucide-react';
import { useTradingSignalsStore } from '../store';

const TradingSignals: React.FC = () => {
  const { signals, latestSignal } = useTradingSignalsStore();

  const getSignalIcon = (signal: string) => {
    switch (signal.toLowerCase()) {
      case 'buy':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'sell':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Minus className="w-4 h-4 text-gray-600" />;
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal.toLowerCase()) {
      case 'buy':
        return 'signal-buy';
      case 'sell':
        return 'signal-sell';
      default:
        return 'signal-hold';
    }
  };

  if (signals.length === 0) {
    return (
      <div className="text-center py-8">
        <Clock className="w-8 h-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-500 dark:text-gray-400">
          No hay señales disponibles
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Última señal destacada */}
      {latestSignal && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`p-3 rounded-lg border ${getSignalColor(latestSignal.signal)} pulse-glow`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {getSignalIcon(latestSignal.signal)}
              <span className="font-medium text-sm">
                {latestSignal.signal.toUpperCase()}
              </span>
            </div>
            <span className="text-xs opacity-75">
              Última
            </span>
          </div>
          <div className="mt-2">
            <p className="text-xs opacity-75">
              ${latestSignal.price.toLocaleString()} • Fuerza: {(latestSignal.strength * 100).toFixed(0)}%
            </p>
            <p className="text-xs mt-1 opacity-60">
              {latestSignal.reason}
            </p>
          </div>
        </motion.div>
      )}

      {/* Historial de señales */}
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {signals.slice(0, 5).map((signal, index) => (
          <motion.div
            key={`${signal.timestamp}-${index}`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="flex items-center justify-between p-2 rounded-lg bg-gray-50 dark:bg-gray-700"
          >
            <div className="flex items-center space-x-2">
              {getSignalIcon(signal.signal)}
              <div>
                <span className="text-sm font-medium">
                  {signal.signal.toUpperCase()}
                </span>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  ${signal.price.toLocaleString()}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {new Date(signal.timestamp).toLocaleTimeString()}
              </div>
              <div className="text-xs font-medium">
                {(signal.strength * 100).toFixed(0)}%
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {signals.length > 5 && (
        <div className="text-center pt-2">
          <button className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400">
            Ver todas las señales ({signals.length})
          </button>
        </div>
      )}
    </div>
  );
};

export default TradingSignals;