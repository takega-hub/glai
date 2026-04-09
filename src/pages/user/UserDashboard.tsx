import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { User as UserIcon, Heart, Flame, Star } from 'lucide-react';
import { getCharacters } from '../../api/userApiClient';
import ErrorBoundary from '../../components/user/ErrorBoundary';
import { useFavoritesStore } from '../../store/favoritesStore';

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
  is_hot: boolean;
  subscribers: number;
}

const UserDashboard = () => {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isFavorite, toggleFavorite } = useFavoritesStore();

  useEffect(() => {
    const fetchCharacters = async () => {
      try {
        const response = await getCharacters();
        const data = response.data;
        if (Array.isArray(data)) {
          setCharacters(data);
        } else if (data && Array.isArray(data.characters)) {
          setCharacters(data.characters);
        } else {
          console.error("Unexpected API response format:", data);
          setCharacters([]);
        }
      } catch (error: any) {
        console.error("Error fetching characters:", error);
        if (error.response?.status === 401) {
          return;
        }
        setError("Failed to load characters. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchCharacters();
  }, []);

  if (loading) {
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            <div className="px-4 sm:px-6 lg:px-8 py-8">
                <div className="mb-8">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 sm:gap-6">
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                            <div key={i}
                                 className="bg-white/5 backdrop-blur-sm rounded-2xl overflow-hidden border border-white/10">
                                <div className="h-48 sm:h-64 bg-white/10 animate-pulse"></div>
                                <div className="p-4 sm:p-6">
                                    <div
                                        className="h-5 sm:h-6 bg-white/10 rounded-lg w-3/4 mb-2 animate-pulse"></div>
                                    <div
                                        className="h-3 sm:h-4 bg-white/10 rounded-lg w-1/2 mb-3 sm:mb-4 animate-pulse"></div>
                                    <div
                                        className="h-2 sm:h-3 bg-white/10 rounded-full w-full mb-4 sm:mb-6 animate-pulse"></div>
                                    <div className="flex space-x-2 sm:space-x-3">
                                        <div
                                            className="h-8 sm:h-10 bg-white/10 rounded-xl flex-1 animate-pulse"></div>
                                        <div
                                            className="h-8 sm:h-10 bg-white/10 rounded-xl w-16 sm:w-20 animate-pulse"></div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
  }

    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
                <div className="px-4 sm:px-6 lg:px-8 py-8">
                    <div
                        className="bg-red-500/10 backdrop-blur-sm rounded-2xl p-6 border border-red-500/20 text-center">
                        <div
                            className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor"
                                 viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                            </svg>
                        </div>
                        <h3 className="text-xl font-semibold text-white mb-2">Loading Error</h3>
                        <p className="text-purple-300 mb-4">{error}</p>
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
          <div className="px-4 sm:px-6 lg:px-8 py-8">
              {/* Characters Grid */}
              <div className="mb-8">
                  <div className="flex items-center justify-between mb-6">
                      <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                          <Star className="w-6 h-6 text-yellow-400"/>
                          Available Characters
                      </h2>
                  </div>

                  {characters.length === 0 ? (
                      <div
                          className="bg-white/5 backdrop-blur-sm rounded-2xl p-12 text-center border border-white/10">
                          <UserIcon className="w-16 h-16 text-purple-400 mx-auto mb-4 opacity-50"/>
                          <h3 className="text-xl font-semibold text-white mb-2">Characters not found</h3>
                          <p className="text-purple-300">Try refreshing the page later</p>
                      </div>
                  ) : (
                      <div
                          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
                          {characters.map((character) => (
                              <div key={character.id} className="group relative">
                                  <Link to={`/user/character/${character.id}`}>
                                      <div
                                          className="bg-white/5 backdrop-blur-sm rounded-2xl overflow-hidden hover:bg-white/10 transition-all duration-300 border border-white/10 hover:border-purple-400/30 hover:shadow-xl hover:shadow-purple-500/10">
                                          {/* Character Image */}
                                          <div className="relative h-64 overflow-hidden">
                                              {character.avatar_url ? (
                                                  <img
                                                      src={character.avatar_url}
                                                      alt={character.display_name}
                                                      className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-500"
                                                  />
                                              ) : (
                                                  <div
                                                      className="w-full h-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
                                                      <UserIcon className="w-20 h-20 text-white opacity-60"/>
                                                  </div>
                                              )}

                                              {/* Favorite Button */}
                                              <button
                                                  onClick={(e) => {
                                                      e.preventDefault();
                                                      e.stopPropagation();
                                                      toggleFavorite(character.id);
                                                  }}
                                                  className="absolute top-3 right-3 z-20 p-2 rounded-full bg-black/30 backdrop-blur-sm hover:bg-black/50 transition-all duration-300"
                                              >
                                                  <Heart
                                                      className={`w-5 h-5 transition-all duration-300 ${
                                                          isFavorite(character.id)
                                                              ? 'text-red-500 fill-red-500'
                                                              : 'text-white hover:text-red-400'
                                                      }`}
                                                  />
                                              </button>

                                              {/* Hot Badge */}
                                              {character.is_hot && (
                                                  <div
                                                      className="absolute top-3 left-3 z-20 px-2 py-1 rounded-lg bg-red-500/80 backdrop-blur-sm">
                                                      <Flame className="w-4 h-4 text-white"/>
                                                  </div>
                                              )}

                                              {/* Gradient Overlay */}
                                              <div
                                                  className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"></div>

                                              {/* Character Info Overlay */}
                                              <div className="absolute bottom-0 left-0 right-0 p-4">
                                                  <h3 className="text-2xl font-bold text-white mb-2 group-hover:text-purple-200 transition-all">
                                                      {character.display_name}
                                                  </h3>
                                                  <div className="flex flex-wrap items-center gap-2 text-sm">
                                                      <span className="text-purple-200">
                                                          {character.personality_type || character.archetype || 'Character'}
                                                      </span>
                                                      {character.age && (
                                                          <>
                                                              <span className="text-purple-300">•</span>
                                                              <span className="text-purple-200">
                                                                  {character.age} years
                                                              </span>
                                                          </>
                                                      )}
                                                  </div>
                                              </div>
                                          </div>

                                          {/* Content Section */}
                                          <div className="p-4">
                                              {/* Status Badges */}
                                              <div className="flex flex-wrap gap-2 mb-3">
                                                  {character.status === 'active' && (
                                                      <span
                                                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-300 border border-green-400/30">
                                                          <span
                                                              className="w-1.5 h-1.5 bg-green-400 rounded-full mr-1 animate-pulse"></span>
                                                          Online
                                                      </span>
                                                  )}
                                                  <span
                                                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-300 border border-purple-400/30">
                                                      <Heart className="w-3 h-3 mr-1"/>
                                                      {Math.round(character.trust_score / 10)}% trust
                                                  </span>
                                                  <span
                                                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-500/20 text-blue-300 border border-blue-400/30">
                                                      <UserIcon className="w-3 h-3 mr-1"/>
                                                      {character.subscribers} 
                                                  </span>
                                              </div>


                                          </div>
                                      </div>
                                  </Link>
                              </div>
                          ))}
                      </div>
                  )}
              </div>
          </div>
      </div>
  );
};

const UserDashboardWithErrorBoundary = () => (
    <ErrorBoundary>
        <UserDashboard/>
    </ErrorBoundary>
);

export default UserDashboardWithErrorBoundary;