import React, { useState, useEffect } from 'react';

interface PromptsData {
  system_prompt: string;
  context_instructions: any;
}

interface PromptsProps {
  data: {
    character: { id: string };
    prompts: PromptsData;
  };
  refetchData: () => void;
}

const Prompts: React.FC<PromptsProps> = ({ data, refetchData }) => {
  const [prompts, setPrompts] = useState<PromptsData | null>(data.prompts);
  const [isLoading, setIsLoading] = useState(false);
  const [sexualityLevel, setSexualityLevel] = useState(1);

  useEffect(() => {
    setPrompts(data.prompts);
  }, [data.prompts]);

  const handleRegenerate = async () => {
    setIsLoading(true);
    const characterId = data.character.id;
    const response = await fetch(`/api/admin/characters/${characterId}/generate-llm-prompts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ sexuality_level: sexualityLevel }),
    });

    if (response.ok) {
      refetchData(); // This will re-fetch all character data including the updated prompts
    }
    setIsLoading(false);
  };

  if (!prompts && !isLoading) {
    return (
      <div className="p-6 text-center">
        <p className="mb-4">Промпты для этого персонажа еще не сгенерированы.</p>
        <button onClick={handleRegenerate} className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
          Сгенерировать промпты
        </button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">LLM Prompts</h1>
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <label htmlFor="sexuality-level-select" className="mr-2 text-sm font-medium text-gray-700">Sexuality Level:</label>
            <select
              id="sexuality-level-select"
              value={sexualityLevel}
              onChange={(e) => setSexualityLevel(Number(e.target.value))}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value={1}>Friendly</option>
              <option value={2}>Moderate</option>
              <option value={3}>Maximum</option>
            </select>
          </div>
          <button 
            onClick={handleRegenerate}
            disabled={isLoading}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-400"
          >
            {isLoading ? 'Regenerating...' : 'Regenerate Prompts'}
          </button>
        </div>
      </div>

      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">System Prompt</h2>
          <textarea
            readOnly
            value={prompts?.system_prompt || ''}
            className="w-full h-64 p-2 border border-gray-300 rounded-md bg-gray-50"
          />
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-2">Context Instructions</h2>
          <textarea
            readOnly
            value={prompts?.context_instructions ? JSON.stringify(prompts.context_instructions, null, 2) : ''}
            className="w-full h-64 p-2 border border-gray-300 rounded-md bg-gray-50"
          />
        </div>
      </div>
    </div>
  );
};

export default Prompts;
