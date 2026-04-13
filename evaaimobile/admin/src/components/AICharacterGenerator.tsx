import React, { useState } from 'react';
import useAuthStore from '../store/useAuthStore';

interface AICharacterGeneratorProps {
  onGenerationSuccess: () => void;
}

const AICharacterGenerator: React.FC<AICharacterGeneratorProps> = ({ onGenerationSuccess }) => {
  const [gender, setGender] = useState('Женский');
  const [archetype, setArchetype] = useState('');
  const [numberOfLayers, setNumberOfLayers] = useState(8);
  const [additionalInstructions, setAdditionalInstructions] = useState('');
  const [isSexFocused, setIsSexFocused] = useState(false);
  const [referencePhoto, setReferencePhoto] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const { token } = useAuthStore();

  const handleGenerate = async () => {
    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      // Create FormData for file upload support
      const formData = new FormData();
      formData.append('gender', gender);
      formData.append('number_of_layers', numberOfLayers.toString());
      formData.append('is_sex_focused', isSexFocused.toString());
      
      if (archetype) {
        formData.append('archetype', archetype);
      }
      if (additionalInstructions) {
        formData.append('additional_instructions', additionalInstructions);
      }
      if (referencePhoto) {
        formData.append('reference_photo', referencePhoto);
      }

      const response = await fetch('/api/admin/characters/generate-with-ai', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate character');
      }

      const data = await response.json();
      setResult(data);
      onGenerationSuccess(); // Сообщаем родителю об успехе
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 my-6 bg-white rounded-lg shadow-md">
      <h3 className="text-2xl font-bold mb-4 text-gray-800">🤖 AI Сценарист — Создание Персонажа</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Пол</label>
          <select
            value={gender}
            onChange={(e) => setGender(e.target.value)}
            className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          >
            <option>Женский</option>
            <option>Мужской</option>
            <option>Небинарный</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Количество слоев</label>
          <input
            type="number"
            min="4"
            max="12"
            value={numberOfLayers}
            onChange={(e) => setNumberOfLayers(parseInt(e.target.value))}
            className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>

        <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700">ИЛИ Загрузите фото типажа</label>
            <div className="mt-1 flex items-center">
                <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setReferencePhoto(e.target.files ? e.target.files[0] : null)}
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"/>
            </div>
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700">Типаж (необязательно)</label>
          <input
            type="text"
            placeholder="Например, Таинственная, Игривая, Романтичная..."
            value={archetype}
            onChange={(e) => setArchetype(e.target.value)}
            className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700">Дополнительные инструкции (необязательно)</label>
          <textarea
            placeholder="Должна быть связана с музыкой, иметь травму..."
            value={additionalInstructions}
            onChange={(e) => setAdditionalInstructions(e.target.value)}
            rows={3}
            className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <div className="md:col-span-2 flex items-center">
          <input
            type="checkbox"
            id="sex-focused-creation-checkbox"
            checked={isSexFocused}
            onChange={(e) => setIsSexFocused(e.target.checked)}
            className="h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
          />
          <label htmlFor="sex-focused-creation-checkbox" className="ml-2 text-sm font-medium text-gray-900">🔥 Максимально секс-фокус</label>
        </div>
      </div>

      <div className="flex items-center justify-end">
        <button
          onClick={handleGenerate}
          disabled={isLoading}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Генерация...
            </>
          ) : (
            '✨ Сгенерировать персонажа'
          )}
        </button>
      </div>

      {error && <div className="mt-4 p-4 bg-red-100 text-red-700 border border-red-400 rounded-md">{error}</div>}

      {result && (
        <div className="mt-6 p-4 bg-green-100 border border-green-400 rounded-md">
          <h4 className="text-lg font-bold text-green-800 mb-2">✅ {result.message}</h4>
          <p className="text-sm text-green-700">ID Персонажа: {result.character_id}</p>
          <details className="mt-2 text-xs text-gray-600">
            <summary>Показать/скрыть JSON предпросмотр</summary>
            <pre className="mt-2 p-2 bg-gray-800 text-white rounded-md overflow-x-auto">{JSON.stringify(result.preview, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
};

export default AICharacterGenerator;
