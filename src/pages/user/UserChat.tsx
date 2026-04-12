import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Send, Heart, X, ChevronLeft, Gift } from 'lucide-react';
import { getCharacterById, getChatHistory, sendMessage as sendApiMessage, getBalance, sendGift } from '../../api/userApiClient';
import { useAuthStore } from '../../store/authStore';
import { Character, Message } from '../../types/user';

import TypingIndicator from '../../components/user/TypingIndicator';
import GiftModal from '../../components/user/GiftModal';

// Helper function to calculate typing time based on text length
// Assumes 200 characters per minute typing speed (average human typing speed)
const calculateTypingTime = (text: string): number => {
  const charsPerMinute = 200;
  const words = text.trim().split(/\s+/).length;
  const chars = text.length;
  
  // Calculate base time based on characters (primary factor)
  const charTime = (chars / charsPerMinute) * 60 * 1000; // in milliseconds
  
  // Add complexity factor for longer words
  const avgWordLength = chars / words;
  const complexityMultiplier = avgWordLength > 6 ? 1.2 : avgWordLength > 4 ? 1.1 : 1.0;
  
  // Calculate final time with bounds
  const typingTime = charTime * complexityMultiplier;
  
  // Ensure minimum 300ms for very short messages, maximum 4000ms for very long ones
  return Math.min(Math.max(typingTime, 300), 4000);
};

const UserChat = () => {
  const { user } = useAuthStore();
  const { characterId } = useParams<{ characterId: string }>();
  const navigate = useNavigate();
  const [character, setCharacter] = useState<Character | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [isGiftModalOpen, setIsGiftModalOpen] = useState(false);
  const [photoProposal, setPhotoProposal] = useState<any | null>(null);
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [guestMessageCount, setGuestMessageCount] = useState(() => {
    const storedCount = localStorage.getItem('guestMessageCount');
    return storedCount ? parseInt(storedCount, 10) : 0;
  });



  useEffect(() => {
    const fetchData = async () => {
      if (!characterId) return;
      setLoading(true);
      try {
        const historyResponse = await getChatHistory(characterId);
        const historyData = historyResponse.data;

        if (historyData && typeof historyData === 'object') {
          const { messages: apiMessages, character_info, trust_score, current_layer } = historyData;

          if (character_info) {
            console.log('Character info received:', character_info);
            console.log('Available image fields:', {
              avatar_url: character_info.avatar_url,
              avatar: character_info.avatar,
              image: character_info.image,
              profile_image: character_info.profile_image,
              photo: character_info.photo
            });
            const imageUrl = character_info.avatar_url || character_info.avatar || character_info.image || character_info.profile_image || character_info.photo;
            console.log('Selected image URL:', imageUrl);
            setCharacter({ ...character_info, trust_score, current_layer });
          } else {
            console.warn('No character_info in history response');
          }

          if (Array.isArray(apiMessages)) {
            const formattedMessages: Message[] = apiMessages.map((msg: any) => ({
              id: msg.id || `${msg.role}-${msg.created_at}`,
              text: msg.content,
              sender: msg.role,
              timestamp: new Date(msg.created_at),
              imageUrl: msg.image_url,
              giftProposal: msg.gift_proposal, // Assuming this might exist
            }));
            setMessages(formattedMessages);
          }
        } else {
          console.error("Unexpected API response format for history:", historyData);
        }
      } catch (error: any) {
        console.error("Error fetching chat data:", error);
        if (error.response?.status === 401) return;
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Fetch balance separately as it's a different concern
    const fetchBalance = async () => {
      try {
        const balanceResponse = await getBalance();
        const newBalance = balanceResponse.data.balance;
        const { user, token } = useAuthStore.getState();
        if (user && token && user.tokens !== newBalance) {
          const updatedUser = { ...user, tokens: newBalance };
          useAuthStore.getState().setAuth(token, updatedUser);
        }
      } catch (error) {
        console.error("Failed to fetch user balance:", error);
      }
    };

    fetchBalance();

    // --- WebSocket Connection ---
    if (user?.id) {
      const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8002/ws';
      const wsUrl = `${wsBaseUrl}/${user.id}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("WebSocket connection established");
      };

      ws.onmessage = (event) => {
        const messageData = JSON.parse(event.data);
        const newMessage: Message = {
          id: `ws-${Date.now()}`,
          text: messageData.response,
          sender: 'assistant',
          timestamp: new Date(),
          imageUrl: messageData.image_url,
        };
        setMessages(prev => [...prev, newMessage]);
      };

      ws.onclose = () => {
        console.log("WebSocket connection closed");
      };

      // Cleanup on component unmount
      return () => {
        ws.close();
      };
    }

  }, [characterId, user?.id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (character) {
      console.log('Character state updated:', character);
      console.log('Character image URL for rendering:', character.avatar_url || character.avatar);
    }
  }, [character]);





  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async () => {
    if (user?.is_guest && guestMessageCount >= 5) {
      alert('You have reached the message limit for guest users. Please register to continue chatting.');
      navigate('/user/auth');
      return;
    }

    if (inputMessage.trim() && characterId) {
      if (user?.is_guest) {
        const newCount = guestMessageCount + 1;
        setGuestMessageCount(newCount);
        localStorage.setItem('guestMessageCount', newCount.toString());
      }

      const userMessage: Message = {
        id: `user-${Date.now()}`,
        text: inputMessage,
        sender: 'user',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);
      const messageToSend = inputMessage;
      setInputMessage('');

      try {
        const response = await sendApiMessage(characterId, messageToSend);
        const characterResponse = response.data;

        // Update trust score and layer if provided
        if (characterResponse.new_trust_score !== undefined && character) {
          setCharacter({ 
            ...character, 
            trust_score: characterResponse.new_trust_score,
            current_layer: characterResponse.new_layer || character.current_layer
          });
        }

        const allParts = [characterResponse.response, ...(characterResponse.response_parts || [])];
        const responseBaseId = `ai-response-${Date.now()}`;

        for (let i = 0; i < allParts.length; i++) {
            const part = allParts[i];
            if (!part || !part.trim()) {
                continue;
            }

            const typingTime = calculateTypingTime(part);
            setIsTyping(true);
            await new Promise(resolve => setTimeout(resolve, typingTime));
            setIsTyping(false);

            const newAiMessage: Message = {
                id: `${responseBaseId}-${i}`,
                text: part,
                sender: 'assistant',
                timestamp: new Date(),
                imageUrl: i === 0 ? characterResponse.image_url : undefined,
                action: i === 0 ? characterResponse.action : undefined,
                photo_proposal_details: i === 0 ? characterResponse.photo_proposal_details : undefined,
            };
            if (newAiMessage.action === 'awaiting_gift_for_generation') {
              setPhotoProposal(newAiMessage.photo_proposal_details);
            }
            setMessages(prev => [...prev, newAiMessage]);
        }

      } catch (error: any) {
        console.error("Error sending message:", error);
        setIsTyping(false);
        if (error.response?.status === 402) {
          alert("You don't have enough tokens to send a message.");
        }
      }
    }
  };

  const handleSendGift = async (giftType: string) => {
    if (!characterId) return;

    try {
      const response = await sendGift(characterId, giftType, photoProposal);
      const { new_trust_score, new_token_balance, new_layer, character_response, character_response_parts, unlocked_photo_url } = response.data;

      // --- Update State (Character & User) ---
      if (character) {
        setCharacter({ ...character, trust_score: new_trust_score, current_layer: new_layer || character.current_layer });
      }
      const { user, token } = useAuthStore.getState();
      if (user && token) {
        useAuthStore.getState().setAuth(token, { ...user, tokens: new_token_balance });
      }

      // --- Reset proposal state after sending gift ---
      setPhotoProposal(null);

      // --- Prepare the Queue of New Messages ---
      const messageQueue: Omit<Message, 'id' | 'timestamp'>[] = [];

      // 1. System message for the gift itself
      messageQueue.push({ text: `You sent a ${giftType} gift!`, sender: 'system' });

      // 2. First part of the character's text response
      if (character_response && character_response.trim()) {
        messageQueue.push({ text: character_response, sender: 'assistant' });
      }

      // 3. The photo message (if it exists)
      if (unlocked_photo_url) {
        messageQueue.push({ text: '', sender: 'assistant', imageUrl: unlocked_photo_url });
      }

      // 4. The rest of the character's text responses
      if (character_response_parts && character_response_parts.length > 0) {
        character_response_parts.forEach((part: string) => {
          if (part && part.trim()) {
            messageQueue.push({ text: part, sender: 'assistant' });
          }
        });
      }

      // --- Display Messages from the Queue Sequentially ---
      setIsGiftModalOpen(false);
      for (const msgData of messageQueue) {
        // Use a longer delay for photos, shorter for system messages
        const typingTime = msgData.imageUrl ? 1200 : (msgData.sender === 'system' ? 50 : calculateTypingTime(msgData.text));
        
        if(msgData.sender === 'assistant') {
          setIsTyping(true);
          await new Promise(resolve => setTimeout(resolve, typingTime));
          setIsTyping(false);
        }

        const newMessage: Message = {
          ...msgData,
          id: `msg-${Date.now()}-${Math.random()}`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, newMessage]);
      }

    } catch (error: any) {
      console.error('Error sending gift:', error);
      alert(error.response?.data?.detail || "Failed to send gift. Please try again.");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (loading || !character) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-b from-gray-900 to-purple-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gradient-to-b from-gray-900 to-purple-900">
      {/* Header */}
      <div className="bg-black bg-opacity-50 backdrop-blur-md border-b border-white border-opacity-20">
        <div className="px-3 sm:px-4 py-3 sm:py-4">
          <div className="flex items-center space-x-2 sm:space-x-4">
            <button
              onClick={() => navigate(-1)}
              className="text-white hover:text-purple-300 transition-colors p-1 sm:p-0"
            >
              <ChevronLeft className="w-5 h-5 sm:w-6 sm:h-6" />
            </button>
            
            <Link to={`/user/character/${characterId}`} className="flex-shrink-0">
              {character.avatar_url || character.avatar ? (
                <img
                  src={character.avatar_url || character.avatar}
                  alt={character.display_name}
                  className="w-10 h-10 sm:w-12 sm:h-12 rounded-full object-cover"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    console.log('Image failed to load, using fallback');
                    target.style.display = 'none';
                    const fallback = target.nextElementSibling as HTMLElement;
                    if (fallback) fallback.style.display = 'flex';
                  }}
                />
              ) : null}
              <div 
                className={`w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 items-center justify-center ${(character.avatar_url || character.avatar) ? 'hidden' : 'flex'}`}
              >
                <span className="text-white font-bold text-lg">
                  {character.display_name.charAt(0).toUpperCase()}
                </span>
              </div>
            </Link>
            
            <div className="flex-1 min-w-0">
              <Link to={`/user/character/${characterId}`}>
                <h2 className="text-base sm:text-xl font-semibold text-white hover:underline truncate">
                  {character.display_name}
                </h2>
              </Link>
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1">
                  <Heart className="w-3 h-3 sm:w-4 sm:h-4 text-pink-400 flex-shrink-0" />
                  <span className="text-xs sm:text-sm text-purple-200">
                    Trust: {character.trust_score} (Layer {character.current_layer})
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-2 sm:px-4 py-3 sm:py-4">
        <div className="flex flex-col space-y-3 sm:space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`px-3 sm:px-4 py-2 rounded-2xl shadow-lg ${
                  message.sender === 'user'
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-br-sm'
                    : 'bg-gray-800 bg-opacity-90 backdrop-blur-sm text-gray-100 rounded-bl-sm'
                } max-w-[85%] sm:max-w-[75%] lg:max-w-[65%]`}
              >
                {message.imageUrl && (
                  <div 
                    className="cursor-pointer mt-2 bg-black/20 rounded-lg p-1"
                    onClick={() => setLightboxImage(message.imageUrl!)}
                  >
                    <img
                      src={message.imageUrl}
                      alt="Content"
                      className="w-full rounded-md max-h-48 sm:max-h-64 object-contain hover:opacity-80 transition-opacity"
                    />
                  </div>
                )}
                  <p className="text-sm sm:text-base font-medium break-words whitespace-pre-wrap leading-relaxed">
                    {message.text}
                  </p>
                <p className="text-xs opacity-60 mt-1.5 text-right">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <div className="px-3 sm:px-4 py-2 rounded-2xl bg-gray-800 bg-opacity-90 backdrop-blur-sm text-gray-100 shadow-lg rounded-bl-sm">
                <TypingIndicator />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
    </div>
      </div>

      {/* Input */}
      <div className="bg-black bg-opacity-50 backdrop-blur-md border-t border-white border-opacity-20">
        <div className="p-2 sm:p-4">
          
          <div className="flex items-end gap-2 sm:gap-3">
            <button
              onClick={() => setIsGiftModalOpen(true)}
              className="text-white hover:text-purple-300 transition-colors mb-1 p-2 hover:bg-white/10 rounded-lg"
            >
              <Gift className="w-5 h-5 sm:w-5 sm:h-5" />
            </button>
            
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Write a message..."
                className="w-full bg-gray-800 bg-opacity-90 backdrop-blur-sm text-gray-100 placeholder-gray-400 rounded-2xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none text-sm sm:text-base"
                rows={1}
                style={{ minHeight: '44px', maxHeight: '120px' }}
              />
            </div>
            
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim()}
              className="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-2.5 rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <GiftModal
        isOpen={isGiftModalOpen}
        onClose={() => setIsGiftModalOpen(false)}
        onSendGift={handleSendGift}
        currentTokenBalance={user?.tokens || 0}
      />

      {/* Lightbox for Images */}
      {lightboxImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setLightboxImage(null)}
        >
          <img 
            src={lightboxImage} 
            alt="Lightbox" 
            className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
          />
          <button 
            className="absolute top-4 right-4 text-white bg-black/50 rounded-full p-2 hover:bg-black/70 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      )}
    </div>
  );
};

export default UserChat;