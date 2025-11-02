import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, DollarSign, PieChart } from 'lucide-react';

const PortfolioSummary: React.FC = () => {
  // Datos simulados del portafolio
  const portfolioData = {
    totalValue: 52450.75,
    totalPnL: 2450.75,
    totalPnLPercent: 4.89,
    cashBalance: 10000.00,
    exposurePercent: 78.5,
    positions: [
      {
        symbol: 'BTCUSDT',
        quantity: 0.5,
        entryPrice: 42000,
        currentPrice: 45200,
        pnl: 1600,
        pnlPercent: 7.62,
        value: 22600
      },
      {
        symbol: 'ETHUSDT',
        quantity: 8.2,
        entryPrice: 2800,
        currentPrice: 3150,
        pnl: 2870,
        pnlPercent: 12.5,
        value: 25830
      },
      {
        symbol: 'ADAUSDT',
        quantity: 15000,
        entryPrice: 0.45,
        currentPrice: 0.52,
        pnl: 1050,
        pnlPercent: 15.56,
        value: 7800
      }
    ]
  };

  const isPositive = portfolioData.totalPnL > 0;

  return (
    <div className="space-y-6">
      {/* Resumen general */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <DollarSign className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Valor Total
            </span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            ${portfolioData.totalValue.toLocaleString()}
          </p>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            {isPositive ? (
              <TrendingUp className="w-4 h-4 text-green-500" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500" />
            )}
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              PnL Total
            </span>
          </div>
          <p className={`text-xl font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            ${portfolioData.totalPnL.toLocaleString()}
          </p>
          <p className={`text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {portfolioData.totalPnLPercent > 0 ? '+' : ''}{portfolioData.totalPnLPercent}%
          </p>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <DollarSign className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Efectivo
            </span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            ${portfolioData.cashBalance.toLocaleString()}
          </p>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <PieChart className="w-4 h-4 text-purple-500" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Exposición
            </span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            {portfolioData.exposurePercent}%
          </p>
        </div>
      </div>

      {/* Posiciones activas */}
      <div>
        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Posiciones Activas
        </h4>
        
        <div className="space-y-3">
          {portfolioData.positions.map((position, index) => (
            <motion.div
              key={position.symbol}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">
                    {position.symbol.slice(0, 3)}
                  </span>
                </div>
                <div>
                  <h5 className="font-medium text-gray-900 dark:text-white">
                    {position.symbol}
                  </h5>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {position.quantity} @ ${position.entryPrice.toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="text-right">
                <p className="font-medium text-gray-900 dark:text-white">
                  ${position.value.toLocaleString()}
                </p>
                <div className="flex items-center space-x-2">
                  <span className={`text-sm font-medium ${
                    position.pnl > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {position.pnl > 0 ? '+' : ''}${position.pnl.toLocaleString()}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    position.pnl > 0 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300'
                  }`}>
                    {position.pnlPercent > 0 ? '+' : ''}{position.pnlPercent}%
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Barra de exposición */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Exposición del Portafolio
          </span>
          <span className="text-sm font-bold text-gray-900 dark:text-white">
            {portfolioData.exposurePercent}%
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              portfolioData.exposurePercent > 80 
                ? 'bg-red-500' 
                : portfolioData.exposurePercent > 60 
                ? 'bg-yellow-500' 
                : 'bg-green-500'
            }`}
            style={{ width: `${portfolioData.exposurePercent}%` }}
          ></div>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {portfolioData.exposurePercent > 80 
            ? 'Exposición alta - Considerar reducir posiciones'
            : portfolioData.exposurePercent > 60 
            ? 'Exposición moderada - Monitorear de cerca'
            : 'Exposición conservadora - Espacio para más posiciones'
          }
        </p>
      </div>
    </div>
  );
};

export default PortfolioSummary;