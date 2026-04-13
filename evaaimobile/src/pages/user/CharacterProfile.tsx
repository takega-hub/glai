import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getCharacterById, getContentGallery, getPersonalGallery } from '../../api/userApiClient';
import { Character, ContentItem } from '../../types/user';
import { MessageCircle, Image, Video, Lock, Eye } from 'lucide-react';

const CharacterProfile = () => {
  const { characterId } = useParams<{ characterId: string }>();
  const [character, setCharacter] = useState<Character | null>(null);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [personalContent, setPersonalContent] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('public');
  const [loading, setLoading] = useState(true);
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (characterId) {
        try {
          const characterResponse = await getCharacterById(characterId);
          setCharacter(characterResponse.data);

          const contentResponse = await getContentGallery(characterId);
          const data = contentResponse.data;
          
          if (data && Array.isArray(data.content)) {
            console.log('Content gallery data:', data);
            setContent(data.content);
          }

          const personalContentResponse = await getPersonalGallery(characterId);
          if (personalContentResponse.data && Array.isArray(personalContentResponse.data)) {
            setPersonalContent(personalContentResponse.data);
          }
        } catch (error) {
          console.error("Error fetching data:", error);
        }
      }
      setLoading(false);
    };

    fetchData();
  }, [characterId]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!character) {
    return <div>Character not found</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      <div className="p-8">
        <div className="flex flex-col md:flex-row gap-8">
          <div className="md:w-1/3">
            <img src={character.avatar_url} alt={character.display_name} className="rounded-lg w-full" />
          </div>
          <div className="md:w-2/3">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-4xl font-bold">{character.display_name}</h1>
              {character.is_hot && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-500/20 text-red-300 border border-red-400/30">
                  🔥 Hot
                </span>
              )}
            </div>
            <p className="text-purple-300 text-lg mb-4">{character.archetype}</p>
            <p className="text-gray-300 mb-6">{character.biography}</p>
            
            {/* Trust Score Bar */}
            <div className="mb-6">
              <div className="mb-4">
                <div className="flex justify-between text-sm text-purple-300 mb-2">
                  <span>Trust</span>
                  <span className="font-semibold">{Math.min(Math.round(character.trust_score / 10), 100)}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-purple-400 via-pink-400 to-rose-400 h-3 rounded-full transition-all duration-500 group-hover:from-purple-500 group-hover:via-pink-500 group-hover:to-rose-500" 
                    style={{ width: `${Math.min(Math.round(character.trust_score / 10), 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
            
            <Link 
              to={`/user/chat/${character.id}`}
              className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 px-6 rounded-xl text-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition-all duration-300"
            >
              <MessageCircle />
              Chat
            </Link>
          </div>
          
        </div>
        
        {/* Content Gallery will go here */}
        <div className="mt-12">
          <div className="flex border-b border-white/10 mb-6">
            <button 
              onClick={() => setActiveTab('public')}
              className={`px-6 py-3 text-lg font-medium transition-colors ${
                activeTab === 'public' 
                  ? 'text-white border-b-2 border-purple-500' 
                  : 'text-purple-300 hover:text-white'
              }`}>
              Gallery
            </button>
            <button 
              onClick={() => setActiveTab('private')}
              className={`px-6 py-3 text-lg font-medium transition-colors ${
                activeTab === 'private' 
                  ? 'text-white border-b-2 border-purple-500' 
                  : 'text-purple-300 hover:text-white'
              }`}>
              Private Gallery
            </button>
          </div>

          {activeTab === 'public' && (
            <div>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {content.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => !item.is_locked && setSelectedContent(item)}
                    className={`relative aspect-square rounded-xl overflow-hidden group transition-all duration-300 ${
                      !item.is_locked 
                        ? 'cursor-pointer hover:scale-105 hover:shadow-2xl' 
                        : 'cursor-not-allowed'
                    }`}
                  >
                    {/* Image or Placeholder */}
                    <img
                      src={item.thumbnail_url || item.media_url}
                      alt={item.description || 'Content'}
                      className={`w-full h-full object-cover`}
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        if (target.src !== item.media_url) {
                          target.src = item.media_url;
                        } else if (target.src !== item.url) {
                          target.src = item.url;
                        }
                      }}
                    />

                    {/* Locked Overlay */}
                    {item.is_locked && (
                      <div className="absolute inset-0 bg-black/20 backdrop-blur-md flex flex-col items-center justify-center p-2">
                        <Lock className="w-8 h-8 text-white/70 mb-2" />
                        <p className="text-white/90 text-xs font-medium text-center">{item.unlock_requirement}</p>
                      </div>
                    )}

                    {/* Unlocked Hover Icon */}
                    {!item.is_locked && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                        <Eye className="w-8 h-8 text-white" />
                      </div>
                    )}

                    {/* Content Type Icon */}
                    <div className="absolute top-2 left-2 bg-black bg-opacity-50 rounded-full p-1">
                      {item.type === 'photo' ? (
                        <Image className="w-4 h-4 text-white" />
                      ) : (
                        <Video className="w-4 h-4 text-white" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
              {content.length === 0 && (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Image className="w-8 h-8 text-purple-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">Content not found</h3>
                  <p className="text-purple-300">There is no available content for this character yet</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'private' && (
            <div>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {personalContent.map((imgUrl, index) => (
                  <div
                    key={index}
                    onClick={() => setSelectedContent({ id: `private-${index}`, url: imgUrl, type: 'photo', is_locked: false, media_url: imgUrl, thumbnail_url: imgUrl, description: 'Personal Photo', unlock_requirement: '', title: 'Personal Photo', trust_level_required: 0 })}
                    className="relative aspect-square rounded-xl overflow-hidden group transition-all duration-300 cursor-pointer hover:scale-105 hover:shadow-2xl"
                  >
                    <img
                      src={imgUrl}
                      alt="Personal Content"
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <Eye className="w-8 h-8 text-white" />
                    </div>
                  </div>
                ))}
              </div>
              {personalContent.length === 0 && (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Image className="w-8 h-8 text-purple-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">No Personal Photos Yet</h3>
                  <p className="text-purple-300">Engage with the character in chat to generate unique photos!</p>
                </div>
              )}
            </div>
          )}
        </div>

        {selectedContent && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-90 backdrop-blur-sm flex items-center justify-center z-50"
            onClick={() => setSelectedContent(null)}
          >
            <div className="relative max-w-4xl max-h-screen p-4" onClick={(e) => e.stopPropagation()}>
              <button
                onClick={() => setSelectedContent(null)}
                className="absolute top-4 right-4 text-white hover:text-gray-300 z-10 bg-black bg-opacity-50 rounded-full p-2"
              >
                ✕
              </button>
              {selectedContent.type === 'photo' ? (
                <img
                                                      src={selectedContent.media_url}
                  alt={selectedContent.description || 'Content'}
                  className="w-full h-auto max-h-screen object-contain rounded-lg"
                                    onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    if (target.src !== selectedContent.url) {
                      target.src = selectedContent.url;
                    }
                  }}
                />
              ) : (
                <video
                  src={selectedContent.url}
                  controls
                  autoPlay
                  className="w-full h-auto max-h-screen object-contain rounded-lg"
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CharacterProfile;
