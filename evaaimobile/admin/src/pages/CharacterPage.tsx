import React, { useState, useEffect } from 'react';
import { NavLink, useParams, useNavigate, Navigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

import Profile from '../components/character/Profile';
import References from '../components/character/References';
import Layers from '../components/character/Layers';
import Content from '../components/character/Content';
import Prompts from '../components/character/Prompts';
import Dialogue from '../components/character/Dialogue';
import Voice from '../components/character/Voice';

const characterTabs = [
  { name: 'Profile', path: 'profile' },
  { name: 'References', path: 'references' },
  { name: 'Layers', path: 'layers' },
  { name: 'Content', path: 'content' },
  { name: 'Prompts', path: 'prompts' },
  { name: 'Dialogue', path: 'dialogue' },
  { name: 'Voice', path: 'voice' },
];

const CharacterPage: React.FC = () => {
  const { id, '*': activeTab = 'profile' } = useParams<{ id: string; '*': string }>();

  const renderContent = () => {
    if (!characterData) return <div>Character not found.</div>;
    if (!promptsExist && activeTab === 'prompts') {
      return (
        <div className="p-6 text-center">
          <p className="mb-4">Prompts for this character have not been generated yet.</p>
          <button onClick={generatePrompts} className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
            Generate prompts
          </button>
        </div>
      );
    }

    switch (activeTab) {
      case 'profile':
        return <Profile data={characterData} setData={handleUpdateCharacter} deleteCharacter={handleDelete} />;
      case 'references':
        return <References data={characterData} refetchData={fetchAllData} />;
      case 'layers':
        return <Layers data={characterData} refetchData={fetchAllData} />;
      case 'content':
        return <Content data={characterData} refetchData={fetchAllData} updateLayerData={updateLayerData} />;
      case 'prompts':
        return <Prompts data={{...characterData, prompts: promptsData}} refetchData={fetchAllData} />;
      case 'dialogue':
        return <Dialogue data={characterData} />;
      case 'voice':
        return <Voice data={characterData} />;
      default:
        return <Navigate to={`/characters/${id}/profile`} replace />;
    }
  };
  const navigate = useNavigate();
  const [characterData, setCharacterData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const { token } = useAuthStore();

  const [promptsData, setPromptsData] = useState<any>(null);
  const [promptsExist, setPromptsExist] = useState(false);

  const fetchAllData = async () => {
    if (!id || !token) return;
    setIsLoading(true);
    setError('');
    try {
      console.log('Fetching character...');
      const charResponse = await fetch(`/api/admin/characters/${id}`, { headers: { 'Authorization': `Bearer ${token}` } });
      console.log('Character response:', charResponse);
      if (!charResponse.ok) {
        throw new Error(`Failed to fetch character: ${charResponse.statusText}`);
      }
      const charData = await charResponse.json();

      // Parse content_plan for each layer
      if (charData.layers && charData.layers.length > 0) {
        charData.layers.forEach((layer: any) => {
          if (typeof layer.content_plan === 'string') {
            try {
              layer.content_plan = JSON.parse(layer.content_plan);
            } catch (e) {
              console.error('Failed to parse content_plan for layer:', layer.id, e);
              layer.content_plan = {}; // Reset on parse error
            }
          }
          if (typeof layer.requirements === 'string') {
            try {
              layer.requirements = JSON.parse(layer.requirements);
            } catch (e) {
              console.error('Failed to parse requirements for layer:', layer.id, e);
              layer.requirements = {}; // Reset on parse error
            }
          }
        });
      }
      console.log('Character data:', charData);

      // Fetch reference photos
      const refPhotosResponse = await fetch(`/api/admin/characters/${id}/reference_photos`, { headers: { 'Authorization': `Bearer ${token}` } });
      if (refPhotosResponse.ok) {
        const refPhotosData = await refPhotosResponse.json();
        charData.reference_photos = refPhotosData.reference_photos || [];
      }

      setCharacterData(charData);

      // Then fetch prompts
      try {
        const promptsResponse = await fetch(`/api/admin/prompts/${id}`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (promptsResponse.ok) {
          const prompts = await promptsResponse.json();
          setPromptsData(prompts);
          setPromptsExist(true);
        } else if (promptsResponse.status === 404) {
          setPromptsExist(false);
          setPromptsData(null);
        } else {
          console.warn(`Failed to fetch prompts: ${promptsResponse.statusText}`);
          setPromptsExist(false);
        }
      } catch (promptErr) {
        console.warn('Error fetching prompts:', promptErr);
        setPromptsExist(false);
      }

    } catch (err: any) {
      setError(err.message);
      setCharacterData(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    console.log('CharacterPage: useEffect triggered', { id, token });
    fetchAllData();
  }, [id, token]);



  const generatePrompts = async () => {
    if (!id) return;
    try {
      const response = await fetch('/api/admin/prompts/regenerate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ character_id: id }),
      });
      if (!response.ok) {
        throw new Error('Failed to generate prompts');
      }
      // Reload the page to refetch all data
      window.location.reload();
    } catch (err: any) {
      alert(`Error generating prompts: ${err.message}`);
    }
  };

  const handleSave = async () => {
    if (!characterData) return;
    try {
      const response = await fetch(`/api/admin/characters/${id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(characterData.character),
        }
      );
      if (!response.ok) {
        throw new Error('Failed to save character');
      }
      alert('Character saved successfully!');
    } catch (err: any) {
      setError(err.message);
      alert(`Error saving: ${err.message}`);
    }
  };

  const handleDelete = async () => {
    if (!id || !window.confirm('Are you sure you want to delete this character? This action is irreversible.')) {
      return;
    }
    try {
      const response = await fetch(`/api/admin/characters/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error('Failed to delete character');
      }
      alert('Character deleted.');
      navigate('/characters');
    } catch (err: any) {
      setError(err.message);
      alert(`Error deleting: ${err.message}`);
    }
  };

  const handleUpdateCharacter = (updatedCharacter: any) => {
    setCharacterData({ ...characterData, character: updatedCharacter });
  };

  const updateLayerData = (layerId: string, newContentPlan: any) => {
    setCharacterData((prevData: any) => {
      const newLayers = prevData.layers.map((layer: any) => {
        if (String(layer.id) === layerId) {
          return { ...layer, content_plan: newContentPlan };
        }
        return layer;
      });
      return { ...prevData, layers: newLayers };
    });
  };

  if (isLoading) return <div>Loading character...</div>;
  if (error) return <div className="text-red-500">Error: {error}</div>;

  console.log('CharacterPage: Rendering', { isLoading, characterData, error });

  return (
    <div>
      {!characterData ? (
        <div>Character not found.</div>
      ) : (
        <>
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold capitalize">{characterData.character.display_name}</h1>
            <button 
              onClick={handleSave}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
              Save all
            </button>
          </div>

          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-6" aria-label="Tabs">
              {characterTabs.map((tab) => (
                <NavLink
                  key={tab.name}
                  to={`/characters/${id}/${tab.path}`}
                  end
                  className={({ isActive }) =>
                    `whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                      isActive || (tab.path === 'profile' && activeTab === 'profile')
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`
                  }
                >
                  {tab.name}
                </NavLink>
              ))}
            </nav>
          </div>

          <div>
            {renderContent()}
          </div>
        </>
      )}
    </div>
  );
};

export default CharacterPage;