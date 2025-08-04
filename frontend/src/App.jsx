import React, { useState, useEffect } from 'react';
import { FileUpload } from './components/FileUpload';
import { TorrentList } from './components/TorrentList';
import { TrackerStats } from './components/TrackerStats';
import { Header } from './components/Header';
import { Tabs } from './components/Tabs';
import { PeerList } from './components/PeerList';
import api from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [torrents, setTorrents] = useState([]);
  const [stats, setStats] = useState({});
  const [selectedTorrent, setSelectedTorrent] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchTorrents = async () => {
    try {
      const response = await api.get('/api/tracker/torrents');
      setTorrents(response.data);
    } catch (error) {
      console.error('Failed to fetch torrents:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get('/api/tracker/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  useEffect(() => {
    fetchTorrents();
    fetchStats();
    
    // Refresh data every 10 seconds
    const interval = setInterval(() => {
      fetchTorrents();
      fetchStats();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const handleFileUploaded = () => {
    fetchTorrents();
    fetchStats();
  };

  const tabs = [
    { id: 'upload', label: 'Upload File', icon: '📤' },
    { id: 'torrents', label: 'Torrents', icon: '📁' },
    { id: 'peers', label: 'Peers', icon: '👥' },
    { id: 'stats', label: 'Statistics', icon: '📊' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs 
          tabs={tabs} 
          activeTab={activeTab} 
          onTabChange={setActiveTab} 
        />

        <div className="mt-8">
          {activeTab === 'upload' && (
            <div className="space-y-6">
              <FileUpload onFileUploaded={handleFileUploaded} />
              <TrackerStats stats={stats} />
            </div>
          )}

          {activeTab === 'torrents' && (
            <TorrentList 
              torrents={torrents}
              onTorrentSelect={setSelectedTorrent}
              selectedTorrent={selectedTorrent}
            />
          )}

          {activeTab === 'peers' && (
            <PeerList selectedTorrent={selectedTorrent} />
          )}

          {activeTab === 'stats' && (
            <div className="space-y-6">
              <TrackerStats stats={stats} detailed />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Recent Activity
                  </h3>
                  <div className="space-y-3">
                    {torrents.slice(0, 5).map(torrent => (
                      <div key={torrent.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                        <div>
                          <p className="font-medium text-gray-900">{torrent.name}</p>
                          <p className="text-sm text-gray-500">
                            {new Date(torrent.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-green-600">
                            {torrent.seeders} seeders
                          </p>
                          <p className="text-sm text-gray-500">
                            {torrent.leechers} leechers
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    System Info
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Server Status</span>
                      <span className="text-green-600 font-medium">Online</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">API Version</span>
                      <span className="text-gray-900">v1.0.0</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Uptime</span>
                      <span className="text-gray-900">Active</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
