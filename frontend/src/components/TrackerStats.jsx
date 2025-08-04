import React from 'react';
import { Server, Users, Download, Database } from 'lucide-react';

export const TrackerStats = ({ stats, detailed = false }) => {
  const statCards = [
    {
      title: 'Total Torrents',
      value: stats.total_torrents || 0,
      icon: Database,
      color: 'blue'
    },
    {
      title: 'Active Peers',
      value: stats.active_peers || 0,
      icon: Users,
      color: 'green'
    },
    {
      title: 'Total Peers',
      value: stats.total_peers || 0,
      icon: Server,
      color: 'purple'
    },
    {
      title: 'Total Users',
      value: stats.total_users || 0,
      icon: Download,
      color: 'orange'
    }
  ];

  const colorClasses = {
    blue: {
      bg: 'bg-blue-50',
      text: 'text-blue-600',
      icon: 'text-blue-500'
    },
    green: {
      bg: 'bg-green-50',
      text: 'text-green-600',
      icon: 'text-green-500'
    },
    purple: {
      bg: 'bg-purple-50',
      text: 'text-purple-600',
      icon: 'text-purple-500'
    },
    orange: {
      bg: 'bg-orange-50',
      text: 'text-orange-600',
      icon: 'text-orange-500'
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map(stat => {
        const Icon = stat.icon;
        const colors = colorClasses[stat.color];
        
        return (
          <div key={stat.title} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`${colors.bg} rounded-md p-3`}>
                <Icon className={`w-6 h-6 ${colors.icon}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">
                  {stat.title}
                </p>
                <p className={`text-2xl font-semibold ${colors.text}`}>
                  {stat.value.toLocaleString()}
                </p>
              </div>
            </div>
            
            {detailed && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center text-sm text-gray-500">
                  <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                  Real-time data
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
