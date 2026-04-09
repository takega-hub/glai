import React, { useState } from 'react';
import { Upload, Trash2, Sparkles } from 'lucide-react';

interface CharacterProfile {
  id: string;
  name: string;
  display_name: string;
  age: number;
  archetype: string;
  biography: string;
  secret: string;
  avatar_url: string;
  status: string;
  is_hot: boolean;
  llm_model: string; // Add the new field
}

interface ProfileProps {
  data: {
    character: CharacterProfile;
    visual_description?: any;
  };
  setData: (character: CharacterProfile) => void;
  deleteCharacter: () => void;
}

const Profile: React.FC<ProfileProps> = ({ data, setData, deleteCharacter }) => {
  const profile = data.character;

  const [isAiEditing, setIsAiEditing] = useState(false);

  // List of available LLM models
  const llmModels = [
    { id: 'google/gemini-3-flash-preview', name: 'Google Gemini 3 Flash (Default)' },
    { id: 'google/gemini-2.5-pro', name: 'Google Gemini 2.5 Pro' },
    { id: 'anthropic/claude-3-haiku', name: 'Anthropic Claude 3 Haiku' },
    { id: 'anthropic/claude-3.7-sonnet', name: 'Anthropic Claude 3.7 Sonnet' },
    { id: 'openai/gpt-4o', name: 'OpenAI GPT-4o' },
    { id: 'x-ai/grok-4.20', name: 'xAI Grok 4.20' },
    { id: 'deepseek/deepseek-chat-v3-0324', name: 'DeepSeek Chat v3' },
    // Add other models here in the future
  ];

  const handleInputChange = (field: keyof CharacterProfile, value: any) => {
    const updatedProfile = { ...profile, [field]: value };
    setData(updatedProfile);
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !profile.name) return;

    const formData = new FormData();
    formData.append('avatar', file);

    const reader = new FileReader();
    reader.onloadend = () => {
      // Optimistically update UI
      handleInputChange('avatar_url', reader.result as string);
    };
    reader.readAsDataURL(file);

    try {
      const response = await fetch(`/api/admin/characters/${profile.id}/upload_avatar`, {
        method: 'POST',
        body: formData, // No token needed if using cookies or other auth methods managed by browser
      });

      if (!response.ok) throw new Error('Server error');

      const result = await response.json();
      // Final update with the persistent URL from server
      handleInputChange('avatar_url', result.filePath);
    } catch (error) {
      console.error("Ошибка загрузки аватара:", error);
      alert("Не удалось загрузить изображение. Попробуйте еще раз.");
    }
  };

  const handleAiEdit = async () => {
    setIsAiEditing(true);
    try {
      // Ensure visual_description is a valid object
      const visualDescription = data.visual_description || {};
      if (typeof visualDescription !== 'object' || Array.isArray(visualDescription)) {
        console.error('Invalid visual_description type:', typeof visualDescription, visualDescription);
        throw new Error('Неверный формат описания внешности. Пожалуйста, проверьте данные персонажа.');
      }
      
      const response = await fetch('/api/admin/characters/ai-edit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add Authorization header if needed
        },
        body: JSON.stringify({
          display_name: profile.display_name,
          age: profile.age,
          archetype: profile.archetype,
          biography: profile.biography,
          secret: profile.secret,
          visual_description: visualDescription,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("AI Editor API Error Body:", errorData); // Log the full error from the server
        
        // Handle different error formats
        let errorMessage = 'AI processing failed';
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Pydantic validation errors
            errorMessage = errorData.detail.map((err: any) => err.msg).join(', ');
          } else if (typeof errorData.detail === 'string') {
            // Simple error message
            errorMessage = errorData.detail;
          }
        }
        throw new Error(errorMessage);
      }

      const aiData = await response.json();

      // Check if AI returned empty object (all fields already filled)
      if (Object.keys(aiData).length === 0) {
        alert('Все поля профиля уже заполнены. Нет необходимости в дополнении.');
        return;
      }

      // Merge only the new AI data into the current profile
      const updatedProfile = {
        ...profile,
        archetype: aiData.archetype || profile.archetype || '',
        biography: aiData.biography || profile.biography || '',
        secret: aiData.secret || profile.secret || '',
      };
      
      // Show success message with what was generated
      const generatedFields = Object.keys(aiData).join(', ');
      alert(`AI успешно дополнил профиль: ${generatedFields}`);
      setData(updatedProfile);

    } catch (error: any) {
      alert(`AI Editor Error: ${error.message}`);
    } finally {
      setIsAiEditing(false);
    }
  };

  return (
    <div className="bg-white p-8 rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">Редактирование профиля</h2>
        <button 
          onClick={handleAiEdit}
          disabled={isAiEditing}
          className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:bg-purple-300">
          <Sparkles className="w-4 h-4 mr-2" />
          {isAiEditing ? 'Думаю...' : 'Дополнить с помощью AI'}
        </button>
      </div>
<>
        {/* Avatar Section */}
        <div className="relative mb-6 md:mb-0 md:mr-8 text-center">
          <img
            src={profile.avatar_url || '/placeholder.png'} // Fallback for missing avatar
            alt="Avatar"
            className="w-32 h-32 rounded-full object-cover border-4 border-gray-200 shadow-lg mx-auto"
          />
          <label htmlFor="avatar-upload" className="absolute bottom-0 right-0 cursor-pointer bg-indigo-600 text-white p-2 rounded-full hover:bg-indigo-700 transition-transform duration-300 transform hover:scale-110">
            <Upload className="w-4 h-4" />
            <input id="avatar-upload" type="file" className="hidden" accept="image/*" onChange={handleAvatarUpload} />
          </label>
        </div>

        {/* Basic Info Section */}
        <div className="flex-1 w-full">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Имя (внутреннее, нередактируемое)</label>
              <input
                type="text"
                value={profile.name}
                readOnly
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-100 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Отображаемое имя</label>
              <input
                type="text"
                value={profile.display_name || ''}
                onChange={(e) => handleInputChange('display_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Возраст</label>
              <input
                type="number"
                value={profile.age || 0}
                onChange={(e) => handleInputChange('age', parseInt(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Типаж</label>
              <input
                type="text"
                value={profile.archetype || ''}
                onChange={(e) => handleInputChange('archetype', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">AI Model</label>
              <select
                value={profile.llm_model || 'google/gemini-3-flash-preview'}
                onChange={(e) => handleInputChange('llm_model', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                {llmModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </>

      {/* Biography and Secret Section */}
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Биография</label>
          <textarea
            rows={4}
            value={profile.biography || ''}
            onChange={(e) => handleInputChange('biography', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Тайна</label>
          <textarea
            rows={4}
            value={profile.secret || ''}
            onChange={(e) => handleInputChange('secret', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Status and Actions */}
      <div className="mt-8 pt-6 border-t border-gray-200 flex justify-between items-end">
        <div className="flex items-center gap-6">
          <div>
            <label htmlFor="status-select" className="block text-sm font-medium text-gray-700">
              Статус персонажа
            </label>
            <select
              id="status-select"
              value={profile.status}
              onChange={(e) => handleInputChange('status', e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="draft">draft</option>
              <option value="active">active</option>
              <option value="archived">archived</option>
            </select>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is-hot-checkbox"
              checked={profile.is_hot || false}
              onChange={(e) => handleInputChange('is_hot', e.target.checked)}
              className="h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
            />
            <label htmlFor="is-hot-checkbox" className="ml-2 text-sm font-medium text-gray-700">
              🔥 Hot (сексуализированный персонаж)
            </label>
          </div>
        </div>
        <div className="flex items-center gap-4">
            <button 
                onClick={deleteCharacter}
                className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm">
                <Trash2 className="w-4 h-4 mr-2" />
                Удалить
            </button>
        </div>
      </div>
    </div>
  );
};

export default Profile;
