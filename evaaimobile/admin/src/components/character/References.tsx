import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import useAuthStore from '../../store/useAuthStore';
import { UploadCloud } from 'lucide-react';

interface ReferencePhoto {
  id: number;
  description: string;
  prompt: string;
  media_url: string | null;
}

interface ReferencesProps {
  data: {
    character: { id: string };
    reference_photos: ReferencePhoto[];
  };
  refetchData: () => void;
}

const References: React.FC<ReferencesProps> = ({ data, refetchData }) => {
  const { id: characterId } = data.character;
  const { token } = useAuthStore();
  const [photos, setPhotos] = useState<ReferencePhoto[]>(data.reference_photos || []);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState<number | null>(null);



  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>, photoId: number) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(photoId, file);
    }
  };

  const handleFileUpload = async (photoId: number, file: File) => {
    setUploading(photoId);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`/api/admin/characters/reference_photos/${characterId}/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload photo');
      }
      
      // Refresh data to show the new image
      refetchData();

    } catch (err: any) {
      setError(`Upload error for photo ${photoId}: ${err.message}`);
    } finally {
      setUploading(null);
    }
  };

  const handleRegenerate = async (photoId: number) => {
    if (!window.confirm('Вы уверены, что хотите перегенерировать это эталонное фото? Существующее изображение будет заменено.')) {
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`/api/admin/characters/reference_photos/${photoId}/regenerate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to regenerate photo');
      }

      // Refresh data to show the new image
      refetchData();

    } catch (err: any) {
      setError(`Regeneration error for photo ${photoId}: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) return <div className="p-6">Загрузка эталонных фото...</div>;
  if (error) return <div className="text-red-500 p-6">Ошибка: {error}</div>;

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6">Эталонные фото для консистентности</h2>
      <p className="text-sm text-gray-600 mb-6">Эти изображения используются AI для сохранения внешности персонажа в разных сценах. Загрузите сюда ключевые ракурсы, сгенерированные по предложенным промптам.</p>
      
      {photos.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p className="font-bold">Эталонные промпты не найдены</p>
          <p className="text-sm">Сначала сгенерируйте персонажа с помощью AI-сценариста, чтобы появились промпты для эталонных фото.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {photos.map((photo) => (
            <div key={photo.id} className="border rounded-lg shadow-sm overflow-hidden">
              <div className="p-4 bg-gray-50">
                <p className="font-semibold text-gray-800">{photo.description}</p>
                <p className="text-xs text-gray-500 font-mono mt-2 p-2 bg-gray-100 rounded">
                  {photo.prompt}
                </p>
              </div>
              <div className="aspect-square bg-gray-200 flex items-center justify-center">
                {photo.media_url ? (
                  <img src={photo.media_url} alt={photo.description} className="w-full h-full object-cover" />
                ) : (
                  <label htmlFor={`upload-ref-${photo.id}`} className="cursor-pointer text-center p-4">
                    <UploadCloud className="w-12 h-12 mx-auto text-gray-400" />
                    <p className="mt-2 text-sm text-gray-600">Загрузить фото</p>
                    <input
                      id={`upload-ref-${photo.id}`}
                      type="file"
                      className="hidden"
                      accept="image/png, image/jpeg"
                      onChange={(e) => handleFileSelect(e, photo.id)}
                      disabled={uploading === photo.id}
                    />
                  </label>
                )}
              </div>
              {uploading === photo.id && <div className="p-2 text-center bg-indigo-100 text-indigo-700">Загрузка...</div>}
              {photo.media_url && (
                 <div className="p-2 bg-gray-50 border-t flex justify-between items-center">
                    <label htmlFor={`upload-ref-${photo.id}`} className="cursor-pointer text-sm text-indigo-600 hover:underline">
                      Заменить фото
                       <input
                        id={`upload-ref-${photo.id}`}
                        type="file"
                        className="hidden"
                        accept="image/png, image/jpeg"
                        onChange={(e) => handleFileSelect(e, photo.id)}
                        disabled={uploading === photo.id}
                      />
                    </label>
                    <button 
                        onClick={() => handleRegenerate(photo.id)}
                        className="text-sm text-green-600 hover:underline">
                        Генерация
                    </button>
                 </div>
               )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default References;
