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
    const response = await fetch('/api/monetization/send-gift', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        recipient_id: data.character.id,
        gift_id: 1, // Assuming gift_id 1 is 'large gift'. This should be dynamic.
        user_prompt: lastGiftProposal.user_prompt
      }),
    });

    if (response.ok) {
      alert('Подарок отправлен! Персонаж готовит для вас фото...');
      setLastGiftProposal(null); // Clear the proposal
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
                <p className="text-sm">{msg.response}</p>
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
