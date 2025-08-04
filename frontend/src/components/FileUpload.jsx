import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, CheckCircle, AlertCircle } from 'lucide-react';
import api from '../services/api';

export const FileUpload = ({ onFileUploaded }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setUploadStatus(null);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/api/tracker/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(progress);
        },
      });

      setUploadStatus({
        type: 'success',
        message: `Successfully created torrent for "${response.data.name}"`,
        data: response.data
      });
      
      if (onFileUploaded) {
        onFileUploaded();
      }
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Upload failed'
      });
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  }, [onFileUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    disabled: uploading
  });

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Upload File & Create Torrent
      </h2>
      
      <div
        {...getRootProps()}
        className={`upload-area p-8 text-center cursor-pointer ${
          isDragActive ? 'drag-active' : ''
        } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center">
          <Upload className={`w-12 h-12 mb-4 ${
            isDragActive ? 'text-primary-500' : 'text-gray-400'
          }`} />
          
          {uploading ? (
            <div className="w-full max-w-xs">
              <p className="text-sm text-gray-600 mb-2">Uploading...</p>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary-500 h-2 rounded-full progress-bar"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 mt-1">{uploadProgress}%</p>
            </div>
          ) : (
            <>
              <p className="text-lg font-medium text-gray-900 mb-2">
                {isDragActive ? 'Drop the file here' : 'Drag & drop a file here'}
              </p>
              <p className="text-sm text-gray-500">
                or click to select a file
              </p>
            </>
          )}
        </div>
      </div>

      {uploadStatus && (
        <div className={`mt-4 p-4 rounded-md ${
          uploadStatus.type === 'success' 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
        }`}>
          <div className="flex">
            {uploadStatus.type === 'success' ? (
              <CheckCircle className="w-5 h-5 text-green-400 mr-2 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-400 mr-2 mt-0.5" />
            )}
            <div>
              <p className={`text-sm font-medium ${
                uploadStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
              }`}>
                {uploadStatus.message}
              </p>
              
              {uploadStatus.data && (
                <div className="mt-2 text-xs text-green-700">
                  <p>Info Hash: {uploadStatus.data.info_hash}</p>
                  <p>File Size: {(uploadStatus.data.file_size / 1024).toFixed(1)} KB</p>
                  <p>Pieces: {uploadStatus.data.num_pieces}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
