import React, { useState, useEffect } from 'react';
import { Users, Clock, Download, Upload, Globe } from 'lucide-react';
import api from '../services/api';

export const PeerList = ({ selectedTorrent }) => {
  const [peers, setPeers] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedTorrent) {
      fetchPeers();
    }
  }, [selectedTorrent]);

  const fetchPeers = async () => {
    if (!selectedTorrent) return;
    
    setLoading(true);
    try {
      const response = await api.get(`/api/tracker/peers/${selectedTorrent.info_hash}`);
      setPeers(response.data);
    } catch (error) {
      console.error('Failed to fetch peers:', error);
      setPeers([]);
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (dateString) => {
    const now = new Date();
    const lastSeen = new Date(dateString);
    const diffMs = now - lastSeen;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  if (!selectedTorrent) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Select a torrent</h3>
        <p className="text-gray-500">Choose a torrent from the list to view its peers</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
        <p className="mt-4 text-gray-500">Loading peers...</p>
      </div>
    );
  }

  if (peers.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No peers found</h3>
        <p className="text-gray-500">
          No active peers for "{selectedTorrent.name}"
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">
          Peers for "{selectedTorrent.name}" ({peers.length})
        </h2>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Peer
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Transfer
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Seen
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {peers.map(peer => (
              <tr key={peer.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <Globe className="w-5 h-5 text-gray-400 mr-3" />
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {peer.ip_address}:{peer.port}
                      </div>
                      <div className="text-sm text-gray-500 font-mono">
                        {peer.peer_id}
                      </div>
                    </div>
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    peer.is_seeder 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {peer.is_seeder ? 'Seeder' : 'Leecher'}
                  </span>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    <div className="flex items-center mb-1">
                      <Upload className="w-4 h-4 text-green-500 mr-1" />
                      {formatBytes(peer.uploaded)}
                    </div>
                    <div className="flex items-center">
                      <Download className="w-4 h-4 text-blue-500 mr-1" />
                      {formatBytes(peer.downloaded)}
                    </div>
                  </div>
                  {!peer.is_seeder && peer.left > 0 && (
                    <div className="text-xs text-gray-500 mt-1">
                      {formatBytes(peer.left)} remaining
                    </div>
                  )}
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-500">
                    <Clock className="w-4 h-4 mr-1" />
                    {formatTime(peer.last_announce)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
