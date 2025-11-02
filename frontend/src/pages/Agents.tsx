import React from 'react';
import { motion } from 'framer-motion';
import { Bot, Zap, Search, Settings, Play, Pause } from 'lucide-react';

const Agents: React.FC = () => {
  const agents = [
    {
      id: 'trading_agent',
      name: 'Trading Agent',
      description: 'Ejecuta operaciones de trading automáticamente',
      status: 'running',
      icon: Bot,
      color: 'blue',
      metrics: {
        'Decisiones tomadas': 156,
        'Precisión': '78.5%',
        'Última actividad': '2 min ago'
      }
    },
    {
      id: 'research_agent',
      name: 'Research Agent',
      description: 'Investiga y descubre nuevas estrategias',
      status: 'idle',
      icon: Search,
      color: 'green',
      metrics: {
        'Estrategias encontradas': 12,
        'Éxito promedio': '65.2%',
        'Última investigación': '1 hora ago'
      }
    },
    {
      id: 'optimizer_agent',
      name: 'Optimizer Agent',
      description: 'Optimiza parámetros de estrategias existentes',
      status: 'running',
      icon: Zap,
      color: 'purple',
      metrics: {
        'Optimizaciones': 8,
        'Mejora promedio': '12.3%',
        'Última optimización': '30 min ago'
      }
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-300';
      case 'idle':
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-300';
      case 'stopped':
        return 'text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-300';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-900/20 dark:text-gray-300';
    }
  };

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'blue':
        return 'from-blue-500 to-blue-600';
      case 'green':
        return 'from-green-500 to-green-600';
      case 'purple':
        return 'from-purple-500 to-purple-600';
      default:
        return 'from-gray-500 to-gray-600';
    }
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
              Agentes IA
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Gestiona y monitorea tus agentes inteligentes
            </p>
          </div>
          <Bot className="w-8 h-8 text-blue-500" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {agents.map((agent, index) => {
            const Icon = agent.icon;
            return (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-gray-50 dark:bg-gray-700 rounded-xl p-6 card-hover"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 bg-gradient-to-br ${getColorClasses(agent.color)} rounded-lg flex items-center justify-center`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                      {agent.status === 'running' ? 'Activo' : agent.status === 'idle' ? 'Inactivo' : 'Detenido'}
                    </span>
                    <button className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600">
                      {agent.status === 'running' ? (
                        <Pause className="w-4 h-4 text-red-600" />
                      ) : (
                        <Play className="w-4 h-4 text-green-600" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {agent.name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {agent.description}
                  </p>
                </div>

                <div className="space-y-2">
                  {Object.entries(agent.metrics).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">{key}:</span>
                      <span className="font-medium text-gray-900 dark:text-white">{value}</span>
                    </div>
                  ))}
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
                  <button className="w-full flex items-center justify-center space-x-2 py-2 px-4 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-500 transition-colors">
                    <Settings className="w-4 h-4" />
                    <span className="text-sm font-medium">Configurar</span>
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* Panel de control global */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Control Global
        </h3>
        
        <div className="flex flex-wrap gap-4">
          <button className="flex items-center space-x-2 py-2 px-4 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">
            <Play className="w-4 h-4" />
            <span>Iniciar Todos</span>
          </button>
          
          <button className="flex items-center space-x-2 py-2 px-4 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors">
            <Pause className="w-4 h-4" />
            <span>Detener Todos</span>
          </button>
          
          <button className="flex items-center space-x-2 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
            <Settings className="w-4 h-4" />
            <span>Configuración Global</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default Agents;