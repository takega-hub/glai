import React from 'react';
import { X, Gift, Star, Zap } from 'lucide-react';

const gifts = [
  { name: 'Small Gift', type: 'small', cost: 10, points: 10, icon: Gift },
  { name: 'Medium Gift', type: 'medium', cost: 25, points: 30, icon: Star },
  { name: 'Large Gift', type: 'large', cost: 50, points: 75, icon: Zap },
];

interface GiftModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSendGift: (giftType: string) => void;
  currentTokenBalance: number;
}

const GiftModal: React.FC<GiftModalProps> = ({ isOpen, onClose, onSendGift, currentTokenBalance }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white/10 border border-white/20 rounded-2xl p-6 w-full max-w-md relative shadow-xl shadow-purple-500/20">
        <button onClick={onClose} className="absolute top-3 right-3 text-purple-300 hover:text-white transition-colors">
          <X className="w-6 h-6" />
        </button>
        <h2 className="text-2xl font-bold text-white text-center mb-1">Send a Gift</h2>
        <p className="text-purple-300 text-center mb-6">Increase your trust level by sending a gift!</p>
        
        <div className="space-y-4">
          {gifts.map((gift) => {
            const canAfford = currentTokenBalance >= gift.cost;
            return (
              <div 
                key={gift.type} 
                className={`bg-white/5 rounded-xl p-4 border border-transparent transition-all ${canAfford ? 'hover:border-purple-400/50 hover:bg-white/10 cursor-pointer' : 'opacity-50'}`}
                onClick={() => canAfford && onSendGift(gift.type)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="bg-gradient-to-br from-purple-500/30 to-pink-500/30 p-3 rounded-lg">
                      <gift.icon className="w-6 h-6 text-purple-200" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white text-lg">{gift.name}</h3>
                      <p className="text-sm text-green-400">+{gift.points} to trust</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg text-white">{gift.cost}</p>
                    <p className="text-xs text-purple-300">токенов</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="text-center mt-6">
            <p className="text-purple-200">Ваш баланс: <span className="font-bold text-white">{currentTokenBalance}</span> токенов</p>
        </div>
      </div>
    </div>
  );
};

export default GiftModal;
