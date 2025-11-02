import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, BarChart3, Settings, TrendingUp } from 'lucide-react';

const Backtesting: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Sistema de Backtesting
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Prueba tus estrategias con datos históricos
            </p>
          </div>
          <BarChart3 className="w-8 h-8 text-blue-500" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Configuración */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Configuración
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Estrategia
                </label>
                <select className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                  <option>RSI Strategy</option>
                  <option>MACD Strategy</option>
                  <option>Multi-Indicator Strategy</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Fecha Inicio
                  </label>
                  <input
                    type="date"
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    defaultValue="2024-01-01"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Fecha Fin
                  </label>
                  <input
                    type="date"
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    defaultValue="2024-12-31"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Capital Inicial
                </label>
                <input
                  type="number"
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  defaultValue="10000"
                  placeholder="10000"
                />
              </div>

              <button
                onClick={() => setIsRunning(!isRunning)}
                disabled={isRunning}
                className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium transition-colors ${
                  isRunning
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                <Play className="w-5 h-5" />
                <span>{isRunning ? 'Ejecutando...' : 'Ejecutar Backtest'}</span>
              </button>
            </div>
          </div>

          {/* Resultados */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Resultados
            </h3>
            
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <div className="text-center py-8">
                <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  Ejecuta un backtest para ver los resultados
                </p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Backtesting;