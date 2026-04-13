import { useState, useEffect, useRef } from 'react';
import { User, Mail, Edit, Save, X, Bell, Moon, Sun, Lock, Info, CreditCard, History, MessageSquare, Heart, Smile, HelpCircle, Flame, TrendingUp } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { getUserProfile, updateUserProfile, uploadAvatar, getBalance, getHistory, getPackages, updateEmailNotifications, changePassword } from '../../api/userApiClient';
import UserAnalytics from '../../components/user/UserAnalytics';
import { useThemeStore } from '../../store/themeStore';
import ChangePasswordModal from '../../components/user/ChangePasswordModal';

interface Transaction {
  id: string;
  type: string;
  token_amount: number;
  created_at: string;
  description: string;
}

interface Package {
  id: string;
  name: string;
  token_amount: number;
  price_usd: number;
}

const TrustInfoSection: React.FC = () => {
  const trustActions = [
    { icon: MessageSquare, text: 'Regular message', points: '+3' },
    { icon: Heart, text: 'Compliment', points: '+5' },
    { icon: Smile, text: 'Showing empathy', points: '+8' },
    { icon: HelpCircle, text: 'Deep question', points: '+10' },
    { icon: Flame, text: 'Successful flirt', points: '+6' },
  ];

  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
      <div className="flex items-center gap-3 mb-6">
        <TrendingUp className="w-6 h-6 text-purple-400" />
        <h2 className="text-2xl font-bold text-white">How to increase trust?</h2>
      </div>
      <p className="text-purple-300 mb-6">
        The level of trust affects the depth of communication and opens access to exclusive content. Here's how you can increase it:
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {trustActions.map((action, index) => (
          <div key={index} className="bg-white/5 rounded-xl p-4 flex items-center justify-between hover:bg-white/10 transition-all">
            <div className="flex items-center gap-3">
              <action.icon className="w-5 h-5 text-purple-400" />
              <span className="text-white">{action.text}</span>
            </div>
            <span className="font-bold text-green-400">{action.points}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const TokensSection: React.FC = () => {
  const [balance, setBalance] = useState(0);
  const [history, setHistory] = useState<Transaction[]>([]);
  const [packages, setPackages] = useState<Package[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const balanceData = await getBalance();
        setBalance(balanceData.data.balance);

        const historyData = await getHistory();
        setHistory(historyData.data);

        const packagesData = await getPackages();
        setPackages(packagesData.data);
      } catch (error) {
        console.error("Failed to fetch token data", error);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
      <div className="flex items-center gap-3 mb-6">
        <CreditCard className="w-6 h-6 text-purple-400" />
        <h2 className="text-2xl font-bold text-white">Tokens</h2>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Balance Card */}
        <div className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-xl p-6 border border-purple-400/30">
          <h3 className="text-purple-300 text-sm font-medium mb-2">Current balance</h3>
          <p className="text-4xl font-bold text-white mb-1">{balance} <span className="text-lg text-purple-300">tokens</span></p>
          <p className="text-purple-300 text-xs">1 token = 1 message</p>
        </div>
        
        {/* Buy Tokens */}
        <div>
          <h3 className="text-white font-semibold mb-3">Top up balance</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {packages.map((pkg) => (
              <div key={pkg.id} className="bg-white/5 rounded-xl p-4 text-center hover:bg-white/10 transition-all border border-white/10 hover:border-purple-400/30">
                <p className="text-lg font-bold text-white">{pkg.name}</p>
                <p className="text-2xl font-bold text-purple-400 my-2">{pkg.token_amount}</p>
                <p className="text-sm text-purple-300 mb-3">tokens</p>
                <p className="text-xl font-bold text-white mb-3">${pkg.price_usd}</p>
                <button className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold py-2 px-4 rounded-lg transition-all">
                  Buy
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Transaction History */}
      <div className="mt-6">
        <div className="flex items-center gap-2 mb-4">
          <History className="w-5 h-5 text-purple-400" />
          <h3 className="text-white font-semibold">Transaction History</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-white/10">
              <tr className="text-purple-300 text-sm">
                <th className="p-3">Date</th>
                <th className="p-3">Type</th>
                <th className="p-3">Description</th>
                <th className="p-3 text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {history.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-6 text-center text-purple-300">
                    No transactions
                  </td>
                </tr>
              ) : (
                history.map((tx) => (
                  <tr key={tx.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="p-3 text-purple-200 text-sm">{new Date(tx.created_at).toLocaleDateString()}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        tx.type === 'purchase' || tx.type === 'admin_grant' ? 'bg-green-500/20 text-green-300' : 'bg-purple-500/20 text-purple-300'
                      }`}>
                        {tx.type === 'purchase' || tx.type === 'admin_grant' ? 'Credit' : 'Debit'}
                      </span>
                    </td>
                    <td className="p-3 text-purple-200 text-sm">{tx.description}</td>
                    <td className={`p-3 text-right font-medium ${tx.token_amount > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {tx.token_amount > 0 ? `+${tx.token_amount}` : tx.token_amount}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const UserProfile = () => {
  const { user, setAuth } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editedProfile, setEditedProfile] = useState<any>(null);
  const [isChangePasswordModalOpen, setChangePasswordModalOpen] = useState(false);
  const [emailNotifications, setEmailNotifications] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const response = await getUserProfile();
        setEditedProfile(response.data);
        if (response.data.email_notifications !== undefined) {
          setEmailNotifications(response.data.email_notifications);
        }
      } catch (error) {
        console.error("Failed to fetch user profile", error);
      }
    };

    if (user) {
      fetchUserProfile();
    }
  }, [user]);

  const handleEmailNotificationsToggle = async () => {
    const newValue = !emailNotifications;
    setEmailNotifications(newValue);
    try {
      await updateEmailNotifications(newValue);
    } catch (error) {
      console.error('Failed to update email notifications:', error);
      setEmailNotifications(!newValue);
    }
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      try {
        const response = await uploadAvatar(file);
        setEditedProfile(response.data);
        const token = useAuthStore.getState().token;
        if (token) {
          const updatedUser = { ...user, ...response.data };
          setAuth(token, updatedUser);
        }
      } catch (error) {
        console.error("Failed to upload avatar", error);
      }
    }
  };

  const handleChangePassword = async (currentPassword: string, newPassword: string) => {
    try {
      await changePassword(currentPassword, newPassword);
      alert('Password changed successfully!');
    } catch (error) {
      console.error('Failed to change password:', error);
      alert('Error changing password. Please try again.');
      throw error;
    }
  };

  const handleSave = async () => {
    try {
      const response = await updateUserProfile(editedProfile);
      const token = useAuthStore.getState().token;
      if (token) {
        const updatedUser = { ...user, ...response.data };
        setAuth(token, updatedUser);
      }
      setIsEditing(false);
    } catch (error) {
      console.error("Failed to update user profile", error);
    }
  };

  const handleCancel = () => {
    setEditedProfile(user);
    setIsEditing(false);
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-b from-gray-900 to-purple-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <>
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-purple-900 py-8">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleAvatarChange}
          className="hidden"
          accept="image/*"
        />
        <div className="px-4 sm:px-6 lg:px-8">
        {/* Profile Card */}
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 sm:p-8 border border-white/10">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
            <h1 className="text-3xl font-bold text-white">Profile</h1>
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center justify-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all"
              >
                <Edit className="w-5 h-5" />
                <span>Edit</span>
              </button>
            ) : (
              <div className="flex gap-3">
                <button
                  onClick={handleSave}
                  className="flex items-center gap-2 bg-green-500/80 text-white px-4 py-2 rounded-xl hover:bg-green-500 transition-all"
                >
                  <Save className="w-5 h-5" />
                  <span>Save</span>
                </button>
                <button
                  onClick={handleCancel}
                  className="flex items-center gap-2 bg-white/20 text-white px-4 py-2 rounded-xl hover:bg-white/30 transition-all"
                >
                  <X className="w-5 h-5" />
                  <span>Cancel</span>
                </button>
              </div>
            )}
          </div>

          {/* Avatar and Basic Info */}
          <div className="flex flex-col sm:flex-row items-center gap-6 mb-8">
            <div className="relative">
              <div className="w-28 h-28 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center shadow-lg shadow-purple-500/20">
                {editedProfile?.avatar_url ? (
                  <img src={editedProfile.avatar_url} alt={editedProfile.display_name} className="w-28 h-28 rounded-full object-cover" />
                ) : (
                  <User className="w-16 h-16 text-white" />
                )}
              </div>
              {isEditing && (
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="absolute bottom-0 right-0 bg-purple-500 text-white p-2 rounded-full hover:bg-purple-600 transition-all border-2 border-gray-900"
                >
                  <Edit className="w-4 h-4" />
                </button>
              )}
            </div>
            
            <div className="flex-1 text-center sm:text-left">
              {isEditing ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-purple-200 text-sm mb-1">Name</label>
                    <input
                      type="text"
                      value={editedProfile?.display_name || ''}
                      onChange={(e) => setEditedProfile(editedProfile ? {...editedProfile, display_name: e.target.value} : null)}
                      className="w-full bg-white/10 border border-white/20 rounded-xl py-3 px-4 text-white placeholder-purple-300/70 focus:outline-none focus:ring-2 focus:ring-purple-400 transition-all"
                      placeholder="Your name"
                    />
                  </div>
                  <div>
                    <label className="block text-purple-200 text-sm mb-1">Email</label>
                    <p className="text-purple-300 py-3 px-4 bg-white/5 rounded-xl">{user.email}</p>
                  </div>
                </div>
              ) : (
                <>
                  <h2 className="text-3xl font-bold text-white mb-2">{editedProfile?.display_name || user.email}</h2>
                  <div className="flex items-center justify-center sm:justify-start gap-2 text-purple-200">
                    <Mail className="w-5 h-5" />
                    <span>{user.email}</span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Settings Section */}
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-1 h-6 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full"></div>
              <h2 className="text-2xl font-bold text-white">Settings</h2>
            </div>
            
            <div className="space-y-4">
              {/* About Me */}
              {isEditing && (
                <div className="bg-white/5 rounded-xl p-4">
                  <label className="flex items-center gap-2 text-purple-200 text-sm mb-2">
                    <Info className="w-4 h-4" />
                    About me
                  </label>
                  <textarea
                    value={editedProfile?.about || ''}
                    onChange={(e) => setEditedProfile(editedProfile ? {...editedProfile, about: e.target.value} : null)}
                    className="w-full bg-white/10 border border-white/20 rounded-xl py-3 px-4 text-white placeholder-purple-300/70 focus:outline-none focus:ring-2 focus:ring-purple-400 transition-all resize-none"
                    rows={3}
                    placeholder="Tell us a little about yourself..."
                  />
                </div>
              )}

              {/* Change Password */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-white/5 rounded-xl p-4 hover:bg-white/10 transition-all">
                <div className="flex items-start gap-3">
                  <Lock className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-white">Change password</h3>
                    <p className="text-sm text-purple-300/80">It is recommended to update your password periodically for security</p>
                  </div>
                </div>
                <button
                  onClick={() => setChangePasswordModalOpen(true)}
                  className="text-sm bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-all"
                >
                  Change
                </button>
              </div>

              {/* Email Notifications */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-white/5 rounded-xl p-4 hover:bg-white/10 transition-all">
                <div className="flex items-start gap-3">
                  <Bell className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-white">Email notifications</h3>
                    <p className="text-sm text-purple-300/80">Receive notifications about new messages and updates</p>
                  </div>
                </div>
                <button
                  onClick={handleEmailNotificationsToggle}
                  className={`relative w-12 h-6 rounded-full flex items-center transition-colors ${
                    emailNotifications ? 'bg-purple-600' : 'bg-gray-600'
                  }`}
                >
                  <div
                    className={`w-4 h-4 bg-white rounded-full transform transition-transform ${
                      emailNotifications ? 'translate-x-7' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Theme Switcher */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-white/5 rounded-xl p-4 hover:bg-white/10 transition-all">
                <div className="flex items-start gap-3">
                  {theme === 'dark' ? (
                    <Moon className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                  ) : (
                    <Sun className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <h3 className="font-semibold text-white">Theme</h3>
                    <p className="text-sm text-purple-300/80">Switch between light and dark theme</p>
                  </div>
                </div>
                <button
                  onClick={toggleTheme}
                  className={`relative w-12 h-6 rounded-full flex items-center transition-colors ${
                    theme === 'dark' ? 'bg-purple-600' : 'bg-gray-600'
                  }`}
                >
                  <div
                    className={`w-4 h-4 bg-white rounded-full transform transition-transform ${
                      theme === 'dark' ? 'translate-x-7' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Analytics Section */}
        <div className="mt-6">
          <UserAnalytics />
        </div>

        {/* Trust Info Section */}
        <div className="mt-6">
          <TrustInfoSection />
        </div>

        {/* Tokens Section */}
        <div className="mt-6">
          <TokensSection />
        </div>
      </div>

      {/* Change Password Modal */}
      {isChangePasswordModalOpen && (
        <ChangePasswordModal 
          onClose={() => setChangePasswordModalOpen(false)} 
          onSubmit={handleChangePassword} 
        />
      )}
      </div>
    </>
  );
};

export default UserProfile;