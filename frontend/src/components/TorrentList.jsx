import React from 'react';
import { File, Download, Users, Calendar, HardDrive } from 'lucide-react';

export const TorrentList = ({ torrents, onTorrentSelect, selectedTorrent }) => {
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const downloadTorrentFile = async (torrent, event) => {
    event.stopPropagation(); // Prevent torrent selection when clicking download
    try {
      const response = await fetch(`http://localhost:8000/api/tracker/torrents/${torrent.info_hash}/download`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${torrent.name.split('.')[0]}.torrent`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        alert('Failed to download torrent file');
      }
    } catch (error) {
      console.error('Error downloading torrent file:', error);
      alert('Error downloading torrent file');
    }
  };

  if (torrents.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <File className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No torrents yet</h3>
        <p className="text-gray-500">Upload a file to create your first torrent</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">
          Available Torrents ({torrents.length})
        </h2>
      </div>
      
      <div className="divide-y divide-gray-200">
        {torrents.map(torrent => (
          <div
            key={torrent.id}
            onClick={() => onTorrentSelect(torrent)}
            className={`torrent-card p-6 cursor-pointer ${
              selectedTorrent?.id === torrent.id ? 'bg-blue-50 border-l-4 border-primary-500' : 'hover:bg-gray-50'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center">
                  <File className="w-5 h-5 text-gray-400 mr-3" />
                  <h3 className="text-lg font-medium text-gray-900">
                    {torrent.name}
                  </h3>
                </div>
                
                <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-500">
                  <div className="flex items-center">
                    <HardDrive className="w-4 h-4 mr-1" />
                    {formatFileSize(torrent.file_size)}
                  </div>
                  
                  <div className="flex items-center">
                    <Users className="w-4 h-4 mr-1" />
                    {torrent.seeders} seeders, {torrent.leechers} leechers
                  </div>
                  
                  <div className="flex items-center">
                    <Download className="w-4 h-4 mr-1" />
                    {torrent.completed} downloads
                  </div>
                  
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-1" />
                    {formatDate(torrent.created_at)}
                  </div>
                </div>
                
                <div className="mt-3">
                  <p className="text-xs text-gray-400 font-mono">
                    Info Hash: {torrent.info_hash}
                  </p>
                </div>
              </div>
              
              <div className="ml-4 flex flex-col items-end">
                <div className="flex space-x-2 mb-2">
                  <button
                    onClick={(e) => downloadTorrentFile(torrent, e)}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                    title="Download .torrent file"
                  >
                    <Download className="w-3 h-3 mr-1" />
                    Download .torrent
                  </button>
                </div>
                
                <div className="flex space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    torrent.seeders > 0 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {torrent.seeders > 0 ? 'Active' : 'Waiting'}
                  </span>
                </div>
                
                <div className="mt-2 text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {torrent.num_pieces} pieces
                  </p>
                  <p className="text-xs text-gray-500">
                    {(torrent.piece_length / 1024).toFixed(0)}KB each
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
