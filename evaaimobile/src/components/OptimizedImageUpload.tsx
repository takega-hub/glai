import React, { useState, useCallback } from 'react';
import { Upload, Image as ImageIcon, AlertCircle, CheckCircle } from 'lucide-react';

interface UploadProgress {
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
}

interface OptimizedImageUploadProps {
  onUploadComplete?: (urls: {
    original: string;
    web: string;
    thumbnail: string;
  }) => void;
  maxFileSize?: number;
  acceptedFormats?: string[];
  className?: string;
  createWebVersion?: boolean;
  createThumbnail?: boolean;
}

export const OptimizedImageUpload: React.FC<OptimizedImageUploadProps> = ({
  onUploadComplete,
  maxFileSize = 10 * 1024 * 1024, // 10MB
  acceptedFormats = ['image/jpeg', 'image/png', 'image/webp'],
  className = '',
  createWebVersion = true,
  createThumbnail = true
}) => {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    status: 'idle',
    progress: 0,
    message: ''
  });
  const [preview, setPreview] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    if (!acceptedFormats.includes(file.type)) {
      return `Invalid format. Allowed: ${acceptedFormats.map(t => t.split('/')[1]).join(', ')}`;
    }
    if (file.size > maxFileSize) {
      return `File too large. Maximum size: ${(maxFileSize / 1024 / 1024).toFixed(0)}MB`;
    }
    return null;
  };

  const handleFileSelect = useCallback(async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setUploadProgress({
        status: 'error',
        progress: 0,
        message: validationError
      });
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    setUploadProgress({
      status: 'uploading',
      progress: 0,
      message: 'Uploading image...'
    });

    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();

      setUploadProgress({
        status: 'completed',
        progress: 100,
        message: 'Upload completed successfully!'
      });

      if (onUploadComplete && result.urls) {
        onUploadComplete(result.urls);
      }

      // Clear preview after 2 seconds
      setTimeout(() => {
        setPreview(null);
        setUploadProgress({ status: 'idle', progress: 0, message: '' });
      }, 2000);

    } catch (error) {
      setUploadProgress({
        status: 'error',
        progress: 0,
        message: error instanceof Error ? error.message : 'Upload failed'
      });
    }
  }, [onUploadComplete, maxFileSize, acceptedFormats]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const getStatusIcon = () => {
    switch (uploadProgress.status) {
      case 'uploading':
      case 'processing':
        return <Upload className="w-8 h-8 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-8 h-8 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-8 h-8 text-red-500" />;
      default:
        return <ImageIcon className="w-8 h-8 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (uploadProgress.status) {
      case 'uploading':
      case 'processing':
        return 'border-blue-300 bg-blue-50';
      case 'completed':
        return 'border-green-300 bg-green-50';
      case 'error':
        return 'border-red-300 bg-red-50';
      default:
        return 'border-gray-300 hover:border-gray-400';
    }
  };

  return (
    <div className={`w-full max-w-md mx-auto ${className}`}>
      <div
        className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 cursor-pointer ${
          getStatusColor()
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept={acceptedFormats.join(',')}
          onChange={handleFileInput}
          className="hidden"
          disabled={uploadProgress.status === 'uploading' || uploadProgress.status === 'processing'}
        />

        {preview ? (
          <div className="space-y-4">
            <img
              src={preview}
              alt="Preview"
              className="max-w-full max-h-48 mx-auto rounded-lg shadow-md"
            />
            <div className="text-sm text-gray-600">
              {uploadProgress.message}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="mx-auto w-12 h-12 flex items-center justify-center">
              {getStatusIcon()}
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                {uploadProgress.status === 'idle' && 'Upload Image'}
                {uploadProgress.status === 'uploading' && 'Uploading...'}
                {uploadProgress.status === 'processing' && 'Processing...'}
                {uploadProgress.status === 'completed' && 'Upload Complete!'}
                {uploadProgress.status === 'error' && 'Upload Failed'}
              </h3>
              
              <p className="text-sm text-gray-500 mt-1">
                {uploadProgress.status === 'idle' && 'Click to browse or drag and drop'}
                {uploadProgress.status === 'uploading' && uploadProgress.message}
                {uploadProgress.status === 'processing' && uploadProgress.message}
                {uploadProgress.status === 'completed' && uploadProgress.message}
                {uploadProgress.status === 'error' && uploadProgress.message}
              </p>
            </div>

            {uploadProgress.status === 'idle' && (
              <div className="text-xs text-gray-400">
                Max size: {(maxFileSize / 1024 / 1024).toFixed(0)}MB
                <br />
                Formats: {acceptedFormats.map(t => t.split('/')[1]).join(', ')}
                {createWebVersion && (
                  <>
                    <br />
                    ✓ Web optimization enabled
                  </>
                )}
                {createThumbnail && (
                  <>
                    <br />
                    ✓ Thumbnail generation enabled
                  </>
                )}
              </div>
            )}

            {uploadProgress.status === 'uploading' && (
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress.progress}%` }}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};