import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Save, AlertTriangle, Shield, Zap } from 'lucide-react';
import { useDashboardStore } from '../store';

const Settings: React.FC = () => {
  const { isLiveMode, setLiveMode } = useDashboardStore();
  const [settings, setSettings] = useState({
    tradingMode: isLiveMode ? 'live' : 'paper',
    maxPositionSize: 0.02,
    stopLossPercent: 0.02,
    takeProfitPercent: 0.04,
    agentUpdateInterval: 300,
    riskLevel: 'medium',
    notifications: {
      email: true,
      telegram: false,
      discord: false
    }
  });

  const handleSave = () => {
    setLiveMode(settings.tradingMode === 'live');
    // Aquí se guardarían los settings en el backend
    console.log('Guardando configuración:', settings);
  };

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
              Configuración del Sistema
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Ajusta los parámetros del sistema de trading
            </p>
          </div>
          <SettingsIcon className="w-8 h-8 text-blue-500" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Configuración de Trading */}
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <Zap className="w-5 h-5 mr-2 text-blue-500" />
                Trading
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Modo de Trading
                  </label>
                  <select
                    value={settings.tradingMode}
                    onChange={(e) => setSettings({...settings, tradingMode: e.target.value})}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="paper">Paper Trading (Simulación)</option>
                    <option value="live">Live Trading (Real)</option>
                  </select>
                  {settings.tradingMode === 'live' && (
                    <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="w-4 h-4 text-red-600" />
                        <span className="text-sm text-red-700 dark:text-red-300 font-medium">
                          ¡ATENCIÓN! Modo live activado - Se ejecutarán trades reales
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tamaño Máximo de Posición (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max="1"
                    value={settings.maxPositionSize}
                    onChange={(e) => setSettings({...settings, maxPositionSize: parseFloat(e.target.value)})}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Porcentaje máximo del capital por posición
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Stop Loss (%)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      max="0.1"
                      value={settings.stopLossPercent}
                      onChange={(e) => setSettings({...settings, stopLossPercent: parseFloat(e.target.value)})}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Take Profit (%)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      max="0.2"
                      value={settings.takeProfitPercent}
                      onChange={(e) => setSettings({...settings, takeProfitPercent: parseFloat(e.target.value)})}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Configuración de Riesgo */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <Shield className="w-5 h-5 mr-2 text-green-500" />
                Gestión de Riesgo
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Nivel de Riesgo
                  </label>
                  <select
                    value={settings.riskLevel}
                    onChange={(e) => setSettings({...settings, riskLevel: e.target.value})}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="low">Bajo - Conservador</option>
                    <option value="medium">Medio - Balanceado</option>
                    <option value="high">Alto - Agresivo</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Intervalo de Actualización de Agentes (segundos)
                  </label>
                  <input
                    type="number"
                    min="60"
                    max="3600"
                    step="60"
                    value={settings.agentUpdateInterval}
                    onChange={(e) => setSettings({...settings, agentUpdateInterval: parseInt(e.target.value)})}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Notificaciones */}
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Notificaciones
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">Email</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Recibir alertas por correo electrónico
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.notifications.email}
                      onChange={(e) => setSettings({
                        ...settings,
                        notifications: {...settings.notifications, email: e.target.checked}
                      })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">Telegram</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Notificaciones vía Telegram Bot
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.notifications.telegram}
                      onChange={(e) => setSettings({
                        ...settings,
                        notifications: {...settings.notifications, telegram: e.target.checked}
                      })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">Discord</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Alertas en canal de Discord
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.notifications.discord}
                      onChange={(e) => setSettings({
                        ...settings,
                        notifications: {...settings.notifications, discord: e.target.checked}
                      })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </div>

            {/* Estado del Sistema */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Estado del Sistema
              </h3>
              
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium text-green-700 dark:text-green-300">
                    Sistema Operativo
                  </span>
                </div>
                <p className="text-sm text-green-600 dark:text-green-400">
                  Todos los componentes funcionando correctamente
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Botón de guardar */}
        <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleSave}
            className="flex items-center space-x-2 py-3 px-6 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            <Save className="w-5 h-5" />
            <span>Guardar Configuración</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default Settings;