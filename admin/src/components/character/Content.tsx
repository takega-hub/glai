import React, { useState, useEffect } from 'react';
import useAuthStore from '../../store/useAuthStore';
import { UploadCloud } from 'lucide-react';

interface ContentItem {
  id: string;
  prompt: string;
  description?: string;
  is_erotic?: boolean;
  media_url: string | null;
}

interface ContentLayer {
  id: string;
  layer_name: string;
  layer_order: number;
  content_plan: {
    photo_prompts: ContentItem[];
    video_prompts: ContentItem[];
    audio_texts: ContentItem[];
  };
}

interface ContentProps {
  data: {
    character: { id: string };
    layers: ContentLayer[];
  };
  refetchData: () => void;
  updateLayerData: (layerId: string, newContentPlan: any) => void;
}

const Content: React.FC<ContentProps> = ({ data, refetchData, updateLayerData }) => {
  const { token } = useAuthStore();
  const [uploading, setUploading] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [generating, setGenerating] = useState<string | null>(null);
  const [generationModel, setGenerationModel] = useState('google/gemini-3.1-flash-image-preview');
  const [sexualityLevel, setSexualityLevel] = useState(1);
  const [teaserContent, setTeaserContent] = useState<ContentItem[]>([]);
  const [isGeneratingAll, setIsGeneratingAll] = useState(false);
  const [generationProgress, setGenerationProgress] = useState({ current: 0, total: 0 });

  useEffect(() => {
    const fetchTeaserContent = async () => {
      try {
        const response = await fetch(`/api/admin/characters/${data.character.id}/teaser-content`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!response.ok) {
          throw new Error('Failed to fetch teaser content');
        }
        const teaserData = await response.json();
        setTeaserContent(teaserData.teaser_content || []);
      } catch (err: any) {
        setError(`Failed to load teasers: ${err.message}`);
      }
    };

    fetchTeaserContent();
  }, [data.character.id, token]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>, contentItemId: string) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(contentItemId, file);
    }
  };

  const handleFileUpload = async (contentItemId: string, file: File) => {
    setUploading(contentItemId);
    const formData = new FormData();
    formData.append('file', file);

    console.log(`Uploading file for content item: ${contentItemId}`);
    console.log("File details:", file);

    try {
      const response = await fetch(`/api/admin/content/${contentItemId}/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      console.log("Upload response status:", response.status);
      const responseData = await response.json();
      console.log("Upload response data:", responseData);

      if (!response.ok) {
        throw new Error(responseData.detail || 'Failed to upload file');
      }

      const newMediaUrl = responseData.media_url;

      // Update teaser content state
      const updatedTeaserContent = teaserContent.map(item => 
        item.id === contentItemId ? { ...item, media_url: newMediaUrl } : item
      );
      setTeaserContent(updatedTeaserContent);

      // Update layer content state
      data.layers.forEach(layer => {
        let itemFound = false;
        const newContentPlan = JSON.parse(JSON.stringify(layer.content_plan));

        for (const key of ['photo_prompts', 'video_prompts', 'audio_texts']) {
            if (newContentPlan[key]) {
                const itemIndex = newContentPlan[key].findIndex((item: ContentItem) => item.id === contentItemId);
                if (itemIndex !== -1) {
                    newContentPlan[key][itemIndex].media_url = newMediaUrl;
                    itemFound = true;
                    break;
                }
            }
        }

        if (itemFound) {
            updateLayerData(layer.id, newContentPlan);
        }
      });

    } catch (err: any) {
      setError(`Upload error: ${err.message}`);
    } finally {
      setUploading(null);
    }
  };

  const handleGenerate = async (contentItemId: string, prompt: string) => {
    setGenerating(contentItemId);
    setError('');
    const payload = {
      character_id: data.character.id,
      content_item_id: contentItemId,
      prompt: prompt,
      model: generationModel, // Pass the selected model
      sexuality_level: sexualityLevel,
    };

    console.log("Sending payload to /generate-photo:", payload);

    try {
      const response = await fetch(`/api/content/generate-photo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload), // Send the full payload
      });

      if (!response.ok) {
        const errorData = await response.json();
        // More detailed error handling
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err: any) => `(${err.loc.join(' > ')}: ${err.msg})`).join(', ');
          throw new Error(errorMessages);
        } else if (errorData.detail) {
          throw new Error(errorData.detail);
        } else {
          throw new Error('Failed to generate photo');
        }
      }

      const responseData = await response.json();
      const newMediaUrl = responseData.media_url;

      if (newMediaUrl) {
        let itemFoundInTeasers = false;
        // Update teaser content state if the item is a teaser
        const updatedTeaserContent = teaserContent.map(item => {
          if (item.id === contentItemId) {
            itemFoundInTeasers = true;
            return { ...item, media_url: newMediaUrl };
          }
          return item;
        });

        if (itemFoundInTeasers) {
          setTeaserContent(updatedTeaserContent);
        } else {
          // If not in teasers, find and update the item in the layers
          data.layers.forEach(layer => {
            let itemFoundInLayer = false;
            const newContentPlan = JSON.parse(JSON.stringify(layer.content_plan));
            
            // Search in photo_prompts
            const photoIndex = newContentPlan.photo_prompts?.findIndex((item: ContentItem) => item.id === contentItemId);
            if (photoIndex !== -1) {
              newContentPlan.photo_prompts[photoIndex].media_url = newMediaUrl;
              itemFoundInLayer = true;
            }
            
            // If found, update the layer and stop searching
            if (itemFoundInLayer) {
              updateLayerData(layer.id, newContentPlan);
            }
          });
        }
      }

    } catch (err: any) {
      setError(`Generation error: ${err.message}`);
    } finally {
      setGenerating(null);
    }
  };

  const handleSetAvatar = async (mediaUrl: string) => {
    setError('');
    try {
      const response = await fetch(`/api/admin/characters/${data.character.id}/set-avatar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ media_url: mediaUrl }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to set avatar');
      }

      // Optionally, show a success message to the user
      alert('Avatar updated successfully!');
      // The character card on the dashboard will now show the new avatar, 
      // but we might need a way to update the avatar in the parent component if it's displayed there.

    } catch (err: any) {
      setError(`Set avatar error: ${err.message}`);
    }
  };

  const handleDeletePhoto = async (photo_id: string, target_type: 'teaser' | 'layer', target_id?: string) => {
    if (!confirm('Are you sure you want to delete this photo?')) {
      return;
    }

    const uniqueId = `delete-photo-${target_type}-${target_id || 'teaser'}`;
    setGenerating(uniqueId);
    setError('');
    try {
      // Construct URL with query parameters
      const params = new URLSearchParams({
        photo_id,
        target_type,
      });
      if (target_id) {
        params.append('target_id', target_id);
      }
      
      const url = `/api/admin/characters/${data.character.id}/delete-photo?${params.toString()}`;
      console.log('Sending delete request to:', url);

      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete photo');
      }

      // Refresh data after successful deletion
      refetchData();

    } catch (err: any) {
      setError(`Delete photo error: ${err.message}`);
    } finally {
      setGenerating(null);
    }
  };

  const handleAddPhoto = async (target_type: 'teaser' | 'layer', target_id?: string) => {
    const uniqueId = `add-photo-${target_type}-${target_id || 'teaser'}`;
    setGenerating(uniqueId);
    setError('');
    try {
      const payload = { target_type, target_id, sexuality_level: sexualityLevel };
      console.log('Sending payload to add-photo-prompt:', payload);

      const response = await fetch(`/api/admin/characters/${data.character.id}/add-photo-prompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err: any) => `(${err.loc.join(' > ')}: ${err.msg})`).join(', ');
          throw new Error(errorMessages);
        } else if (errorData.detail) {
          throw new Error(errorData.detail);
        } else {
          throw new Error('Failed to add photo prompt');
        }
      }

      const responseData = await response.json();
      const newPhotoItem = responseData.new_photo_prompt;

      if (target_type === 'teaser') {
        setTeaserContent(prev => [...prev, newPhotoItem]);
      } else if (target_id) {
        const layer = data.layers.find(l => String(l.id) === target_id);
        if (layer) {
            const newContentPlan = JSON.parse(JSON.stringify(layer.content_plan));
            if (!newContentPlan.photo_prompts) {
                newContentPlan.photo_prompts = [];
            }
            newContentPlan.photo_prompts.push(newPhotoItem);
            updateLayerData(target_id, newContentPlan);
        }
      }

    } catch (err: any) {
      setError(`Add photo error: ${err.message}`);
    } finally {
      setGenerating(null);
    }
  };

  const handleFullRegenerate = async () => {
    setGenerating('full-regenerate');
    try {
      const response = await fetch(`/api/admin/characters/${data.character.id}/regenerate-full-content-plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ 
          sexuality_level: sexualityLevel,
          layers: data.layers
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err: any) => `(${err.loc.join(' > ')}: ${err.msg})`).join(', ');
          throw new Error(errorMessages);
        } else if (errorData.detail) {
          throw new Error(errorData.detail);
        } else {
          throw new Error('Failed to regenerate content plan');
        }
      }

      refetchData();

    } catch (err: any) {
      setError(`Regeneration error: ${err.message}`);
    } finally {
      setGenerating(null);
    }
  };

  const handleGenerateAll = async () => {
    setIsGeneratingAll(true);
    setError('');

    const itemsToGenerate: { id: string; prompt: string }[] = [];

    // Collect from teasers
    teaserContent.forEach(item => {
      if (!item.media_url && item.prompt) {
        itemsToGenerate.push({ id: item.id, prompt: item.prompt });
      }
    });

    // Collect from layers
    data.layers.forEach(layer => {
      layer.content_plan.photo_prompts?.forEach(item => {
        if (!item.media_url && item.prompt) {
          itemsToGenerate.push({ id: item.id, prompt: item.prompt });
        }
      });
    });

    setGenerationProgress({ current: 0, total: itemsToGenerate.length });

    if (itemsToGenerate.length === 0) {
      alert("All content has already been generated!");
      setIsGeneratingAll(false);
      return;
    }

    let generatedCount = 0;
    for (const item of itemsToGenerate) {
      console.log(`Generating content for item: ${item.id} (${generatedCount + 1} of ${itemsToGenerate.length})`);
      try {
        await handleGenerate(item.id, item.prompt);
        generatedCount++;
        setGenerationProgress({ current: generatedCount, total: itemsToGenerate.length });
      } catch (e: any) {
        setError(`Generation failed for item ${item.id}: ${e.message}. Aborting.`);
        break; // Stop on first error
      }
    }

    console.log("Finished generating all content.");
    setIsGeneratingAll(false);
  };

  const handleGenerateTeasers = async () => {
    setGenerating('generate-teasers');
    try {
      const response = await fetch(`/api/admin/characters/${data.character.id}/generate-teasers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ sexuality_level: sexualityLevel }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate teaser prompts');
      }

      const newTeasers = await response.json();
      setTeaserContent(newTeasers.teaser_content || []);

    } catch (err: any) {
      setError(`Teaser generation error: ${err.message}`);
    } finally {
      setGenerating(null);
    }
  };

  const renderContentItem = (item: ContentItem, type: string, layerId: string) => (
    <div key={item.id} className="border rounded-lg shadow-sm overflow-hidden">
      <div className="p-4 bg-gray-50">
        <p className="text-xs text-gray-500 font-mono p-2 bg-gray-100 rounded">
          {item.prompt}
        </p>
      </div>
      <div className="aspect-square bg-gray-200 flex items-center justify-center">
        {item.media_url ? (
          <img src={item.media_url} alt="content" className="w-full h-full object-cover" />
        ) : (
          <label htmlFor={`upload-${item.id}`} className="cursor-pointer text-center p-4">
            <UploadCloud className="w-12 h-12 mx-auto text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">Upload {type}</p>
            <input
              id={`upload-${item.id}`}
              type="file"
              className="hidden"
              accept={type === 'photo' ? 'image/*' : type === 'video' ? 'video/*' : 'audio/*'}
              onChange={(e) => handleFileSelect(e, item.id)}
              disabled={uploading === item.id}
            />
          </label>
        )}
      </div>
      {uploading === item.id && <div className="p-2 text-center bg-indigo-100 text-indigo-700">Uploading...</div>}
      <div className="p-2 bg-gray-50 border-t flex justify-between items-center">
        <label htmlFor={`upload-${item.id}`} className="cursor-pointer text-sm text-indigo-600 hover:underline">
          {item.media_url ? 'Replace' : 'Upload'}
          <input
            id={`upload-${item.id}`}
            type="file"
            className="hidden"
            accept={type === 'photo' ? 'image/*' : type === 'video' ? 'video/*' : 'audio/*'}
            onChange={(e) => handleFileSelect(e, item.id)}
            disabled={uploading === item.id}
          />
        </label>
        <button 
          onClick={() => handleGenerate(item.id, item.prompt)}
          disabled={generating === item.id}
          className="px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 transition-colors disabled:bg-gray-400"
        >
          {generating === item.id ? 'Generating...' : 'Generate'}
        </button>
      </div>
      <div className="p-2 bg-gray-100 border-t flex gap-2">
        {item.media_url && (
          <button 
            onClick={() => handleSetAvatar(item.media_url!)}
            className="flex-1 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors"
          >
            Set as avatar
          </button>
        )}
        <button 
          onClick={() => handleDeletePhoto(item.id, layerId === 'teaser' ? 'teaser' : 'layer', layerId !== 'teaser' ? layerId : undefined)}
          className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition-colors"
        >
          Delete
        </button>
      </div>
    </div>
  );

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Character Content</h2>
        <div className="flex items-center space-x-4">
          <div>
            <label htmlFor="model-select" className="block text-sm font-medium text-gray-700">Generation Model</label>
            <select
              id="model-select"
              value={generationModel}
              onChange={(e) => setGenerationModel(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="COMFY">ComfyUI FaceSwap</option>
              <option value="google/gemini-3.1-flash-image-preview">Gemini 3.1 Flash</option>
              <option value="sourceful/riverflow-v2-fast">RiverFlow v2</option>
              <option value="black-forest-labs/flux.2-klein-4b">Flux Klein</option>
              <option value="sourceful/riverflow-v2-pro">RiverFlow v2 Pro</option>
              <option value="bytedance-seed/seedream-4.5">Seedream 4.5</option>
            </select>
          </div>
          <div>
            <label htmlFor="sexuality-level-select" className="block text-sm font-medium text-gray-700">🔥 Sexuality Level</label>
            <select
              id="sexuality-level-select"
              value={sexualityLevel}
              onChange={(e) => setSexualityLevel(Number(e.target.value))}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value={1}>1 (Subtle)</option>
              <option value={2}>2 (Suggestive)</option>
              <option value={3}>3 (Explicit)</option>
            </select>
          </div>
          <div className="pt-6">
            <button 
              onClick={handleFullRegenerate}
              disabled={generating === 'full-regenerate'}
              className="px-4 py-2 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition-colors disabled:bg-gray-400"
            >
              {generating === 'full-regenerate' ? 'Generating...' : 'Regenerate entire plan'}
            </button>
          </div>
          <div className="pt-6">
            <button 
              onClick={handleGenerateAll}
              disabled={isGeneratingAll || generating === 'full-regenerate'}
              className="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors disabled:bg-gray-400 w-48 text-center"
            >
              {isGeneratingAll ? `Generating... (${generationProgress.current}/${generationProgress.total})` : 'Generate All Photos'}
            </button>
          </div>
        </div>
      </div>



      {error && <div className="text-red-500 mb-4">Error: {error}</div>}

      {/* Teaser Content Section */}
      <div className="mb-8 p-4 border-2 border-dashed border-red-300 rounded-xl bg-red-50/50">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold text-red-800">🔥 Teaser Photos</h3>
          <button 
            onClick={() => handleAddPhoto('teaser')}
            disabled={generating?.startsWith('add-photo-teaser')}
            className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors disabled:bg-gray-400"
          >
            {generating === 'add-photo-teaser' ? '...' : '+ Photo'}
          </button>
        </div>
        {teaserContent.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {teaserContent.map(item => renderContentItem(item, 'photo', 'teaser'))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">Prompts for teaser photos have not been generated yet.</p>
            <button 
              onClick={handleGenerateTeasers}
              disabled={generating === 'generate-teasers'}
              className="px-4 py-2 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition-colors disabled:bg-gray-400"
            >
              {generating === 'generate-teasers' ? 'Generating...' : 'Generate prompts for teasers'}
            </button>
          </div>
        )}
      </div>

      {data.layers?.map((layer) => (
        <div key={layer.id} className="mb-8 p-4 border-2 border-gray-200 rounded-xl">
          <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold text-gray-800">Слой {layer.layer_order}: {layer.layer_name}</h3>
          <button 
            onClick={() => handleAddPhoto('layer', String(layer.id))}
            disabled={generating === `add-photo-layer-${layer.id}`}
            className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors disabled:bg-gray-400"
          >
            {generating === `add-photo-layer-${layer.id}` ? '...' : '+ Фото'}
          </button>
        </div>
          {(!layer.content_plan || (layer.content_plan.photo_prompts?.length === 0 && layer.content_plan.video_prompts?.length === 0 && layer.content_plan.audio_texts?.length === 0)) ? (
             <div className="text-center py-8">
                <p className="text-gray-500">Контент-план для этого слоя пуст.</p>
              </div>
          ) : (
            <>
              {layer.content_plan.photo_prompts?.length > 0 && (
                <div className="mb-6">
                  <h4 className="font-bold mb-3 text-lg text-gray-700">Фото</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {layer.content_plan.photo_prompts.map(item => renderContentItem(item, 'фото', layer.id))}
                  </div>
                </div>
              )}
              {layer.content_plan.video_prompts?.length > 0 && (
                <div className="mb-6">
                  <h4 className="font-bold mb-3 text-lg text-gray-700">Видео</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {layer.content_plan.video_prompts.map(item => renderContentItem(item, 'видео', layer.id))}
                  </div>
                </div>
              )}
              {layer.content_plan.audio_texts?.length > 0 && (
                <div className="mb-6">
                  <h4 className="font-bold mb-3 text-lg text-gray-700">Аудио</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {layer.content_plan.audio_texts.map(item => renderContentItem(item, 'аудио', layer.id))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      ))}
    </div>
  );
};

export default Content;
