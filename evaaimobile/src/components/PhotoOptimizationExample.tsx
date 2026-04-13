import React, { useState } from 'react';
import { OptimizedImageUpload } from './OptimizedImageUpload';
import { Settings, Download, Zap, Upload } from 'lucide-react';

export const PhotoOptimizationExample: React.FC = () => {
  const [uploadedUrls, setUploadedUrls] = useState<{
    original: string;
    web: string;
    thumbnail: string;
  } | null>(null);

  const handleUploadComplete = (urls: {
    original: string;
    web: string;
    thumbnail: string;
  }) => {
    setUploadedUrls(urls);
    console.log('Upload completed with URLs:', urls);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold text-gray-900">
          📸 Photo Optimization Demo
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Upload images and they'll be automatically optimized for web use with 
          multiple sizes generated for different use cases.
        </p>
      </div>

      {/* Upload Component */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Upload Image
        </h2>
        <OptimizedImageUpload
          onUploadComplete={handleUploadComplete}
          maxFileSize={5 * 1024 * 1024} // 5MB limit
          createWebVersion={true}
          createThumbnail={true}
        />
      </div>

      {/* Results */}
      {uploadedUrls && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Optimization Results
          </h2>
          
          <div className="grid md:grid-cols-3 gap-6">
            {/* Original */}
            <div className="space-y-3">
              <h3 className="font-medium text-gray-700">Original</h3>
              <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                <img
                  src={uploadedUrls.original}
                  alt="Original"
                  className="w-full h-full object-cover"
                />
              </div>
              <p className="text-sm text-gray-500">Full resolution</p>
            </div>

            {/* Web Optimized */}
            <div className="space-y-3">
              <h3 className="font-medium text-gray-700 flex items-center gap-1">
                <Zap className="w-4 h-4 text-yellow-500" />
                Web Optimized
              </h3>
              <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                <img
                  src={uploadedUrls.web}
                  alt="Web optimized"
                  className="w-full h-full object-cover"
                />
              </div>
              <p className="text-sm text-gray-500">75% quality, max 1200px</p>
            </div>

            {/* Thumbnail */}
            <div className="space-y-3">
              <h3 className="font-medium text-gray-700 flex items-center gap-1">
                <Download className="w-4 h-4 text-blue-500" />
                Thumbnail
              </h3>
              <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                <img
                  src={uploadedUrls.thumbnail}
                  alt="Thumbnail"
                  className="w-full h-full object-cover"
                />
              </div>
              <p className="text-sm text-gray-500">70% quality, 300px</p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-medium text-blue-900 mb-2">Benefits:</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Faster page loading times</li>
              <li>• Reduced bandwidth usage</li>
              <li>• Better mobile experience</li>
              <li>• Multiple sizes for different use cases</li>
              <li>• WebP format for better compression</li>
            </ul>
          </div>
        </div>
      )}

      {/* Features */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-500" />
            Web Optimization
          </h3>
          <ul className="text-gray-600 space-y-2">
            <li>• Quality: 75% (perfect balance)</li>
            <li>• Max dimensions: 1200x800px</li>
            <li>• Format: WebP (30% smaller than JPEG)</li>
            <li>• Progressive loading enabled</li>
          </ul>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Download className="w-5 h-5 text-blue-500" />
            Thumbnail Generation
          </h3>
          <ul className="text-gray-600 space-y-2">
            <li>• Quality: 70% (good for small sizes)</li>
            <li>• Dimensions: 300x300px</li>
            <li>• Perfect for lists and previews</li>
            <li>• Fast loading on all devices</li>
          </ul>
        </div>
      </div>
    </div>
  );
};