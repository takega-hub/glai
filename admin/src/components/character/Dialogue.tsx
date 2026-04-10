import { useState, useEffect } from 'react';
import useAuthStore from '../../store/useAuthStore';

interface GiftProposal {
  required_gift: string;
  user_prompt: string;
}

interface Message {
  id: number;
  message: string;
  response: string;
  created_at: string;
  gift_proposal?: GiftProposal;
}

interface DialogueProps {
  data: {
    character: { id: string };
  };
}

const Dialogue: React.FC<DialogueProps> = ({ data }) => {
  const { token } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const fetchHistory = async () => {
    const characterId = data.character.id;
    const response = await fetch(`/api/dialogue/history/${characterId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (response.ok) {
      const data = await response.json();
      setMessages(data.messages);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [data.character.id, token]);

  const [lastGiftProposal, setLastGiftProposal] = useState<GiftProposal | null>(null);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    setIsLoading(true);
    setLastGiftProposal(null); // Reset proposal on new message

    const response = await fetch('/api/dialogue/send-message', {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        character_id: data.character.id,
        message: newMessage
      }),
    });

    if (response.ok) {
      const responseData = await response.json();
      if (responseData.gift_proposal) {
        setLastGiftProposal(responseData.gift_proposal);
        // Add the character's proposal message to the chat history
        setMessages(prev => [...prev, {
          id: responseData.id || Date.now(),
          message: newMessage, // Show the user's trigger message
          response: responseData.response, // Show the proposal text
          created_at: new Date().toISOString(),
          gift_proposal: responseData.gift_proposal
        }]);
      } else {
        fetchHistory(); // Standard message, just refetch everything
      }
      setNewMessage('');
    }
    setIsLoading(false);
  };

  const handleSendGift = async () => {
    if (!lastGiftProposal) return;

    setIsLoading(true);
    setLastGiftProposal(null); // Clear proposal UI immediately

    // Helper to add messages with a delay for typing animation
    const sleep = (ms: number) => new Promise(res => setTimeout(res, ms));

    const response = await fetch('/api/dialogue/send-gift/', { // CORRECT ENDPOINT
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        character_id: data.character.id,
        gift_type: lastGiftProposal.required_gift, // Use the gift type from the proposal
        intimacy_analysis: { user_intent: lastGiftProposal.user_prompt } // Pass analysis
      }),
    });

    if (response.ok) {
      const giftResponse = await response.json();
      
      // 1. Add the character's first response part
      setMessages(prev => [...prev, {
        id: Date.now(),
        message: `(You sent a ${giftResponse.message.split(' ')[3]} gift!)`,
        response: giftResponse.character_response,
        created_at: new Date().toISOString(),
      }]);
      
      await sleep(500); // Wait for first message to appear

      // 2. Add the photo if it exists
      if (giftResponse.unlocked_photo_url) {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          message: "", // No user message for the photo part
          response: giftResponse.unlocked_photo_url, // We'll render this as an image
          created_at: new Date().toISOString(),
        }]);
      }

      // 3. Add the rest of the message parts with a typing delay
      for (const part of giftResponse.character_response_parts) {
        await sleep(1000); // Simulate typing
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          message: "",
          response: part,
          created_at: new Date().toISOString(),
        }]);
      }

    } else {
      const error = await response.json();
      alert(`Ошибка: ${error.detail}`);
    }
    setIsLoading(false);
  };

  // Sort messages chronologically (oldest first)
  const sortedMessages = [...messages].sort((a, b) => 
    new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  return (
    <div className="p-6 flex flex-col h-[calc(100vh-200px)]">
      <div className="flex-grow overflow-y-auto mb-4 p-4 border border-gray-200 rounded-lg bg-gray-50 flex flex-col">
        {sortedMessages.map((msg) => (
          <div key={msg.id} className="flex flex-col space-y-2 mb-4">
            {/* User Message - aligned to the right */}
            <div className="flex justify-end">
              <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-blue-500 text-white">
                <p className="text-sm">{msg.message}</p>
                <p className="text-xs text-blue-100 mt-1 text-right">
                  {new Date(msg.created_at).toLocaleTimeString()}
                </p>
              </div>
            </div>
            
            {/* Character Response - aligned to the left */}
            <div className="flex justify-start">
              <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-gray-200 text-gray-800">
                {msg.response.startsWith('/uploads/') ? (
                  <img src={`/api${msg.response}`} alt="Unlocked content" className="rounded-lg" />
                ) : (
                  <p className="text-sm">{msg.response}</p>
                )}
                <p className="text-xs text-gray-500 mt-1 text-left">
                  {new Date(msg.created_at).toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
      <form onSubmit={handleSendMessage} className="flex items-center">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type your message..."
          className="flex-grow p-2 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          disabled={isLoading}
        />
        <button 
          type="submit"
          className="px-4 py-2 bg-indigo-600 text-white rounded-r-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-400"
          disabled={isLoading}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>

      {lastGiftProposal && (
        <div className="mt-4 p-4 bg-yellow-100 border border-yellow-300 rounded-lg text-center">
          <p className="mb-2">Персонаж предлагает особенное фото в обмен на подарок.</p>
          <button 
            onClick={handleSendGift}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400"
            disabled={isLoading}
          >
            {isLoading ? 'Отправка...' : `Отправить большой подарок`}
          </button>
        </div>
      )}
    </div>
  );
};

export default Dialogue;
