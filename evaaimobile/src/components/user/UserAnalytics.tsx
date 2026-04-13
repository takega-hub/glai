import React, { useState, useEffect } from 'react';
import { MessageCircle, User, Zap, ImageIcon } from 'lucide-react';
import { getUserAnalytics } from '../../api/userApiClient';

interface AnalyticsData {
  total_messages: number;
  total_characters_interacted: number;
  total_tokens_spent: number;
  unlocked_content: number;
}

const UserAnalytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await getUserAnalytics();
        setAnalytics(response.data);
      } catch (error) {
        console.error("Failed to fetch user analytics", error);
      }
    };

    fetchAnalytics();
  }, []);

  if (!analytics) {
    return <div>Loading analytics...</div>;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 text-white">
      <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
            <MessageCircle className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-purple-300 mb-1">Total messages</h3>
            <p className="text-2xl font-bold">{analytics.total_messages}</p>
          </div>
        </div>
      </div>
      <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center">
            <User className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-purple-300 mb-1">Unique characters</h3>
            <p className="text-2xl font-bold">{analytics.total_characters_interacted}</p>
          </div>
        </div>
      </div>
      <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-gradient-to-br from-pink-500 to-rose-500 rounded-xl flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-purple-300 mb-1">Tokens spent</h3>
            <p className="text-2xl font-bold">{analytics.total_tokens_spent}</p>
          </div>
        </div>
      </div>
      <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-teal-500 rounded-xl flex items-center justify-center">
            <ImageIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-purple-300 mb-1">Content unlocked</h3>
            <p className="text-2xl font-bold">{analytics.unlocked_content}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserAnalytics;
