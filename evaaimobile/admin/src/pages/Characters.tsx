import React, { useState, useEffect, useCallback } from 'react';
import { NavLink } from 'react-router-dom';
import AICharacterGenerator from '../components/AICharacterGenerator';
import useAuthStore from '../store/useAuthStore';

interface Character {
  id: string;
  name: string;
  display_name: string;
  age: number;
  archetype: string;
  status: string;
  created_at: string;
  avatar_url: string | null;
}

const Characters: React.FC = () => {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const { token } = useAuthStore();

  const fetchCharacters = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch('/api/admin/characters/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        throw new Error('Failed to fetch characters');
      }
      const data = await response.json();
      setCharacters(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchCharacters();
  }, [fetchCharacters]);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Персонажи</h1>
      
      <AICharacterGenerator onGenerationSuccess={fetchCharacters} />

      <div className="mt-8 bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">Существующие персонажи</h2>
        {isLoading && <p>Загрузка...</p>}
        {error && <p className="text-red-500">{error}</p>}
        {!isLoading && !error && (
          characters.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {characters.map(char => (
                <NavLink 
                  key={char.id}
                  to={`/characters/${char.id}`}
                  className="relative block bg-gray-200 shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow h-80 bg-cover bg-top"
                  style={{ backgroundImage: `url(${char.avatar_url || 'https://placehold.co/600x400'})` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/50 to-transparent"></div>
                  <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
                    <h3 className="font-bold text-xl">{char.display_name}</h3>
                    <p className="text-sm">{char.archetype}</p>
                    <div className="mt-2 flex items-center">
                       <span className={`px-2 py-0.5 text-xs rounded-full ${char.status === 'draft' ? 'bg-yellow-400/80 text-yellow-900' : 'bg-green-400/80 text-green-900'}`}>
                        {char.status}
                      </span>
                    </div>
                  </div>
                </NavLink>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">Пока нет ни одного персонажа. Создайте первого с помощью AI-сценариста!</p>
          )
        )}
      </div>
    </div>
  );
};

export default Characters;

