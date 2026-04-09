import React, { useState, useEffect } from 'react';
import useAuthStore from '../../store/useAuthStore';
import { Plus, ArrowRight, Lock, Image, Video, Mic } from 'lucide-react';

interface Layer {
  id: number;
  name: string;
  min_trust_score: number;
  max_trust_score: number;
  content_plan: { 
    photo_prompts: any[]; 
    video_prompts: any[]; 
    audio_texts: any[]; 
  };
  requirements: { night_conversation: boolean; gift_required: boolean; min_days: number };
  initiator_prompt: string;
  system_prompt_override: string;
  layer_order: number;
}

interface LayersProps {
  data: {
    character: { id: string };
    layers: Layer[];
  };
  refetchData: () => void;
}

const Layers: React.FC<LayersProps> = ({ data, refetchData }) => {
  const { token } = useAuthStore(); // Added to get auth token
  const [layers, setLayers] = useState<Layer[]>(data.layers);
  const [selectedLayer, setSelectedLayer] = useState<Layer | null>(data.layers?.[0] || null);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isSexFocused, setIsSexFocused] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setLayers(data.layers);
    if (!selectedLayer && data.layers?.length > 0) {
      setSelectedLayer(data.layers[0]);
    }
  }, [data.layers]);

  const handleSelectLayer = (layer: Layer) => {
    setSelectedLayer(layer);
  };

  const handleAddLayer = async () => {
    const characterId = data.character.id;
    const response = await fetch('/api/admin/layers', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ character_id: characterId }),
    });

    if (response.ok) {
      const newLayer = await response.json();
      setLayers([...layers, newLayer]);
      setSelectedLayer(newLayer);
    }
  };

  const handleRegenerateLayers = async () => {
    if (!data.character.id) return;
    if (!window.confirm("Вы уверены, что хотите полностью перегенерировать все слои? Это действие необратимо.")) return;

    setIsRegenerating(true);
    setError('');
    try {
      const response = await fetch(`/api/admin/characters/${data.character.id}/regenerate-layers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ is_sex_focused: isSexFocused }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to regenerate layers');
      }
      
      // Refetch all character data to update the UI
      refetchData();

    } catch (err: any) {
      setError(`Error: ${err.message}`);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleInputChange = (field: keyof Layer, value: any) => {
    if (!selectedLayer) return;
    setSelectedLayer({ ...selectedLayer, [field]: value });
  };

  const handleRequirementChange = (field: keyof Layer['requirements'], value: any) => {
    if (!selectedLayer) return;
    setSelectedLayer({ 
      ...selectedLayer, 
      requirements: { ...selectedLayer.requirements, [field]: value }
    });
  };

  const renderContentItem = (item: any, type: string) => (
    <div key={item.id} className="mb-2 p-2 border rounded-lg bg-gray-50">
      <p className="text-xs text-gray-500 font-mono p-1 bg-gray-100 rounded">{item.prompt}</p>
      {item.media_url && (
        <div className="mt-2 aspect-square bg-gray-200 rounded-md flex items-center justify-center">
          <img src={item.media_url} alt="content" className="w-full h-full object-cover rounded-md" />
        </div>
      )}
    </div>
  );

  if (!layers || layers.length === 0) {
    return <div className="p-6">Для этого персонажа еще не создано слоев.</div>;
  }

  return (
    <div className="space-y-8">
      {/* Visual Layer Constructor */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Слои доверия</h2>
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="sex-focused-checkbox"
                checked={isSexFocused}
                onChange={(e) => setIsSexFocused(e.target.checked)}
                className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
              />
              <label htmlFor="sex-focused-checkbox" className="ml-2 text-sm font-medium text-gray-700">Максимально секс-фокус</label>
            </div>
            <button onClick={handleRegenerateLayers} disabled={isRegenerating} className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm disabled:bg-gray-400">
              {isRegenerating ? 'Генерация...' : 'Перегенерировать слои'}
            </button>
            <button onClick={handleAddLayer} className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm">
              <Plus className="w-4 h-4 mr-2" />
              Новый слой
            </button>
          </div>
        </div>
        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
        <div className="relative overflow-x-auto pb-4">
          <div className="flex items-center space-x-4">
            {layers.map((layer, index) => (
              <React.Fragment key={layer.id}>
                <div 
                  onClick={() => handleSelectLayer(layer)}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all w-48 flex-shrink-0 ${
                    selectedLayer?.id === layer.id ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 bg-white hover:border-indigo-400'
                  }`}>
                  <p className="font-bold text-gray-800">Слой {layer.layer_order}</p>
                  <p className="text-sm text-gray-600 truncate">{layer.name}</p>
                  <p className="text-xs font-mono text-gray-500 mt-2">{layer.min_trust_score} - {layer.max_trust_score}</p>
                  <div className="flex items-center space-x-2 mt-2 text-gray-500">
                    <div className="flex items-center text-xs"><Image className="w-3 h-3 mr-1"/>{layer.content_plan?.photo_prompts?.length || 0}</div>
                    <div className="flex items-center text-xs"><Video className="w-3 h-3 mr-1"/>{layer.content_plan?.video_prompts?.length || 0}</div>
                    <div className="flex items-center text-xs"><Mic className="w-3 h-3 mr-1"/>{layer.content_plan?.audio_texts?.length || 0}</div>
                  </div>
                  <Lock className="w-4 h-4 text-gray-400 mt-2" />
                </div>
                {index < layers.length - 1 && (
                  <ArrowRight className="w-6 h-6 text-gray-400 flex-shrink-0" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Layer Editor */}
      {selectedLayer && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-bold mb-6">Редактирование слоя {selectedLayer.layer_order}: <span className="text-indigo-600">{selectedLayer.name}</span></h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Left Column: Settings */}
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Название слоя</label>
                <input
                  type="text"
                  value={selectedLayer.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Пороги доверия</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={selectedLayer.min_trust_score}
                    onChange={(e) => handleInputChange('min_trust_score', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Дополнительные требования</label>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <input id="night_dialogue" type="checkbox" checked={selectedLayer.requirements.night_conversation} onChange={(e) => handleRequirementChange('night_conversation', e.target.checked)} className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500" />
                    <label htmlFor="night_dialogue" className="ml-2 block text-sm text-gray-900">Ночной диалог (после 21:00)</label>
                  </div>
                  <div className="flex items-center">
                    <input id="gift_required" type="checkbox" checked={selectedLayer.requirements.gift_required} onChange={(e) => handleRequirementChange('gift_required', e.target.checked)} className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500" />
                    <label htmlFor="gift_required" className="ml-2 block text-sm text-gray-900">Требуется подарок</label>
                  </div>
                  <div className="flex items-center">
                     <input id="min_days" type="number" value={selectedLayer.requirements.min_days} onChange={(e) => handleRequirementChange('min_days', parseInt(e.target.value))} className="w-20 px-2 py-1 border border-gray-300 rounded-md text-sm" />
                    <label htmlFor="min_days" className="ml-2 block text-sm text-gray-900">Мин. дней с начала общения</label>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Prompts & Content */}
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Промпт инициации</label>
                <textarea rows={3} value={selectedLayer.initiator_prompt} onChange={(e) => handleInputChange('initiator_prompt', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Override системного промпта (опционально)</label>
                <textarea rows={5} value={selectedLayer.system_prompt_override} onChange={(e) => handleInputChange('system_prompt_override', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-yellow-50" placeholder="Если пусто, используется системный промпт..."/>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Контент слоя</label>
                <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg">
                  {selectedLayer.content_plan && (selectedLayer.content_plan.photo_prompts?.length > 0 || selectedLayer.content_plan.video_prompts?.length > 0 || selectedLayer.content_plan.audio_texts?.length > 0) ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div>
                        <h4 className="font-semibold mb-2 text-center text-gray-600">Фото</h4>
                        {selectedLayer.content_plan.photo_prompts?.map(item => renderContentItem(item, 'фото'))}
                      </div>
                      <div>
                        <h4 className="font-semibold mb-2 text-center text-gray-600">Видео</h4>
                        {selectedLayer.content_plan.video_prompts?.map(item => renderContentItem(item, 'видео'))}
                      </div>
                      <div>
                        <h4 className="font-semibold mb-2 text-center text-gray-600">Аудио</h4>
                        {selectedLayer.content_plan.audio_texts?.map(item => renderContentItem(item, 'аудио'))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-center text-gray-500">Контент-план для этого слоя пуст. Перейдите во вкладку "Контент", чтобы сгенерировать его.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Layers;