import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { User, Heart, Star, ChevronRight } from 'lucide-react';
import { getCharacters } from '../../api/userApiClient';
import { useFavoritesStore } from '../../store/favoritesStore';
import ErrorBoundary from '../../components/user/ErrorBoundary';

interface Character {
  id: string;
  name: string;
  display_name: string;
  avatar_url?: string;
  personality_type?: string;
  archetype?: string;
  biography?: string;
  status: string;
  last_interaction?: string;
  trust_score: number;
  current_layer: number;
  age?: number;
}

const FavoritesPage = () => {
  const [favoriteCharacters, setFavoriteCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { favoriteCharacterIds, toggleFavorite } = useFavoritesStore();

  useEffect(() => {
    const fetchFavoriteCharacters = async () => {
      if (favoriteCharacterIds.length === 0) {
        setLoading(false);
        return;
      }

      try {
        const response = await getCharacters();
        const data = response.data;
        let allCharacters: Character[] = [];
        
        if (Array.isArray(data)) {
          allCharacters = data;
        } else if (data && Array.isArray(data.characters)) {
          allCharacters = data.characters;
        }

        const favorites = allCharacters.filter(character => 
          favoriteCharacterIds.includes(character.id)
        );
        
        setFavoriteCharacters(favorites);
      } catch (error: any) {
        console.error("Error fetching favorite characters:", error);
        if (error.response?.status === 401) {
          return;
        }
        setError("Failed to load favorite characters. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchFavoriteCharacters();
  }, [favoriteCharacterIds]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-white/10 rounded-xl animate-pulse"></div>
              <div className="h-8 bg-white/10 rounded-lg w-48 animate-pulse"></div>
            </div>
            <div className="h-4 bg-white/10 rounded-lg w-64 animate-pulse"></div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-white/5 backdrop-blur-sm rounded-2xl overflow-hidden border border-white/10 animate-pulse">
                <div className="h-64 bg-white/10"></div>
                <div className="p-6">
                  <div className="h-6 bg-white/10 rounded-lg w-3/4 mb-2"></div>
                  <div className="h-4 bg-white/10 rounded-lg w-1/2 mb-4"></div>
                  <div className="h-3 bg-white/10 rounded-full w-full"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <Heart className="w-8 h-8 text-purple-400" />
              <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-purple-300 bg-clip-text text-transparent">
                Favorites
              </h1>
            </div>
            <p className="text-purple-300">Your favorite characters</p>
          </div>
          <div className="bg-red-500/10 backdrop-blur-sm rounded-2xl p-8 border border-red-500/20 text-center">
            <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Loading Error</h3>
            <p className="text-purple-300 mb-6">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-2 rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all duration-300"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl">
              <Heart className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-purple-300 bg-clip-text text-transparent">
              Favorites
            </h1>
          </div>
          <p className="text-purple-300 ml-2">
            {favoriteCharacters.length === 0 
              ? 'You don\'t have any favorite characters yet. Add them by clicking on the heart!' 
              : `You have ${favoriteCharacters.length} ${favoriteCharacters.length === 1 ? 'character' : 'characters'} in your favorites`
            }
          </p>
        </div>

        {favoriteCharacters.length === 0 ? (
          <div className="text-center py-16 sm:py-24">
            <div className="w-32 h-32 bg-purple-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border-2 border-purple-400/30">
              <Heart className="w-16 h-16 text-purple-400 opacity-50" />
            </div>
            <h3 className="text-2xl font-semibold text-white mb-3">No favorite characters</h3>
            <p className="text-purple-300 mb-8 max-w-md mx-auto">
              Go to the main page and add characters to your favorites by clicking on the heart on their card.
            </p>
            <Link
              to="/user"
              className="inline-flex items-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 px-8 rounded-xl text-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition-all duration-300 shadow-lg shadow-purple-500/20"
            >
              Go to characters
              <ChevronRight className="w-5 h-5" />
            </Link>
          </div>
        ) : (
          <>
            {/* Stats Bar */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 mb-6 border border-white/10">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Star className="w-5 h-5 text-yellow-400" />
                  <span className="text-purple-200">
                    Total in favorites: <span className="text-white font-bold">{favoriteCharacters.length}</span>
                  </span>
                </div>
                <Link 
                  to="/user"
                  className="text-purple-300 hover:text-purple-200 text-sm transition-colors flex items-center gap-1"
                >
                  Add more
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </div>

            {/* Characters Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
              {favoriteCharacters.map((character) => (
                <Link 
                  to={`/user/character/${character.id}`}
                  key={character.id} 
                  className="group relative bg-white/5 backdrop-blur-sm rounded-2xl overflow-hidden hover:bg-white/10 transition-all duration-300 border border-white/10 hover:border-purple-400/30 hover:shadow-xl hover:shadow-purple-500/10 block"
                >
                  {/* Character Image */}
                  <div className="relative h-64 overflow-hidden">
                    {character.avatar_url ? (
                      <img
                        src={character.avatar_url}
                        alt={character.display_name}
                        className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full bg-gradient-to-br from-purple-600 via-purple-500 to-pink-600 flex items-center justify-center">
                        <User className="w-20 h-20 text-white opacity-60" />
                      </div>
                    )}
                    
                    {/* Favorite Button */}
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        toggleFavorite(character.id);
                      }}
                      className="absolute top-3 right-3 z-20 p-2 rounded-full bg-black/40 backdrop-blur-sm hover:bg-black/60 transition-all duration-300 group/heart"
                    >
                      <Heart 
                        className="w-5 h-5 transition-all duration-300 text-red-500 fill-red-500 hover:scale-110"
                      />
                    </button>
                    
                    {/* Trust Score Badge */}
                    <div className="absolute top-3 left-3 z-20 px-2 py-1 rounded-lg bg-black/40 backdrop-blur-sm">
                      <div className="flex items-center gap-1">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                        <span className="text-xs text-white font-medium">
                          {Math.round(character.trust_score / 10)}% trust
                        </span>
                      </div>
                    </div>
                    
                    {/* Gradient Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"></div>
                    
                    {/* Character Info Overlay */}
                    <div className="absolute bottom-0 left-0 right-0 p-4">
                      <h3 className="text-2xl font-bold text-white mb-1 group-hover:text-purple-200 transition-all line-clamp-1">
                        {character.display_name}
                      </h3>
                      <div className="flex flex-wrap items-center gap-2 text-sm">
                        <span className="text-purple-200 group-hover:text-purple-100 transition-all">
                          {character.personality_type || character.archetype || 'Character'}
                        </span>
                        {character.age && (
                          <>
                            <span className="text-purple-300">•</span>
                            <span className="text-purple-200 group-hover:text-purple-100 transition-all">
                              {character.age} years
                            </span>
                          </>
                        )}
                        {character.status === 'active' && (
                          <>
                            <span className="text-purple-300">•</span>
                            <span className="inline-flex items-center gap-1 text-green-300">
                              <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                              Online
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Biography Preview */}
                  {character.biography && (
                    <div className="p-4 border-t border-white/10">
                      <p className="text-purple-200 text-sm line-clamp-2">
                        {character.biography}
                      </p>
                    </div>
                  )}
                </Link>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

const FavoritesPageWithErrorBoundary = () => (
  <ErrorBoundary>
    <FavoritesPage />
  </ErrorBoundary>
);

export default FavoritesPageWithErrorBoundary;