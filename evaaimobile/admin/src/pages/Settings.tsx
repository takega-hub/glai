import React, { useState, useEffect } from 'react';
import { Save, RefreshCw, Settings as SettingsIcon, AlertCircle } from 'lucide-react';
import useAuthStore from '../store/useAuthStore';
import { toast } from 'sonner';

interface SystemSettings {
  openrouter_api_key: string;
  jwt_secret: string;
  database_url: string;
  redis_url: string;
  max_trust_score: number;
  min_trust_score: number;
  content_generation_enabled: boolean;
  auto_reengagement_enabled: boolean;
  reengagement_interval_hours: number;
  max_daily_messages: number;
  gift_price_multiplier: number;
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const { token } = useAuthStore();

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    if (!token) return;

    try {
      setIsLoading(true);
      setError(null);

      // TODO: Implement settings API endpoint
      // For now, we'll use mock data
      setTimeout(() => {
        const mockSettings: SystemSettings = {
          openrouter_api_key: 'sk-or-v1-...',
          jwt_secret: 'your-jwt-secret-key',
          database_url: 'postgresql://user:pass@localhost/evadb',
          redis_url: 'redis://localhost:6379',
          max_trust_score: 150,
          min_trust_score: 0,
          content_generation_enabled: true,
          auto_reengagement_enabled: true,
          reengagement_interval_hours: 24,
          max_daily_messages: 100,
          gift_price_multiplier: 1.2,
        };
        setSettings(mockSettings);
        setIsLoading(false);
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch settings');
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!token || !settings) return;

    try {
      setIsSaving(true);
      setError(null);
      setSuccess(null);

      // TODO: Implement settings update API endpoint
      setTimeout(() => {
        setSuccess('Settings saved successfully!');
        setIsSaving(false);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
      setIsSaving(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      toast.error('Новые пароли не совпадают');
      return;
    }

    if (newPassword.length < 6) {
      toast.error('Новый пароль должен содержать минимум 6 символов');
      return;
    }

    setIsChangingPassword(true);

    try {
      const response = await fetch('/api/admin/settings/password', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Ошибка при смене пароля');
      }

      toast.success('Пароль успешно изменен');

      // Очистить форму
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');

    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Произошла ошибка при смене пароля');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleInputChange = (field: keyof SystemSettings, value: any) => {
    if (!settings) return;
    setSettings({ ...settings, [field]: value });
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">System Settings</h1>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
            <div className="space-y-4">
              {[...Array(8)].map((_, index) => (
                <div key={index}>
                  <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
                  <div className="h-10 bg-gray-200 rounded"></div>
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
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">System Settings</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading settings</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  onClick={fetchSettings}
                  className="text-sm font-medium text-red-600 hover:text-red-500"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!settings) {
    return null;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">System Settings</h1>
        <button
          onClick={fetchSettings}
          className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Success</h3>
              <div className="mt-2 text-sm text-green-700">
                <p>{success}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Password Change Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Смена пароля администратора</h3>
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Текущий пароль
              </label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
                disabled={isChangingPassword}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Новый пароль
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
                minLength={6}
                disabled={isChangingPassword}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Подтверждение нового пароля
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
                minLength={6}
                disabled={isChangingPassword}
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={isChangingPassword}
            className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isChangingPassword ? 'Изменение...' : 'Изменить пароль'}
          </button>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="space-y-6">
          {/* API Configuration */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <SettingsIcon className="w-5 h-5 mr-2" />
              API Configuration
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  OpenRouter API Key
                </label>
                <input
                  type="password"
                  value={settings.openrouter_api_key}
                  onChange={(e) => handleInputChange('openrouter_api_key', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="sk-or-v1-..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  JWT Secret
                </label>
                <input
                  type="password"
                  value={settings.jwt_secret}
                  onChange={(e) => handleInputChange('jwt_secret', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Database Configuration */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Database Configuration</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Database URL
                </label>
                <input
                  type="text"
                  value={settings.database_url}
                  onChange={(e) => handleInputChange('database_url', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Redis URL
                </label>
                <input
                  type="text"
                  value={settings.redis_url}
                  onChange={(e) => handleInputChange('redis_url', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Trust Score Configuration */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Trust Score Configuration</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Maximum Trust Score
                </label>
                <input
                  type="number"
                  value={settings.max_trust_score}
                  onChange={(e) => handleInputChange('max_trust_score', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  min="0"
                  max="200"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Minimum Trust Score
                </label>
                <input
                  type="number"
                  value={settings.min_trust_score}
                  onChange={(e) => handleInputChange('min_trust_score', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  min="0"
                  max="200"
                />
              </div>
            </div>
          </div>

          {/* Content Generation */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Content Generation</h3>
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="content_generation_enabled"
                  checked={settings.content_generation_enabled}
                  onChange={(e) => handleInputChange('content_generation_enabled', e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="content_generation_enabled" className="ml-2 block text-sm text-gray-900">
                  Enable AI Content Generation
                </label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Maximum Daily Messages per User
                </label>
                <input
                  type="number"
                  value={settings.max_daily_messages}
                  onChange={(e) => handleInputChange('max_daily_messages', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  min="1"
                  max="1000"
                />
              </div>
            </div>
          </div>

          {/* Auto Re-engagement */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Auto Re-engagement</h3>
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="auto_reengagement_enabled"
                  checked={settings.auto_reengagement_enabled}
                  onChange={(e) => handleInputChange('auto_reengagement_enabled', e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="auto_reengagement_enabled" className="ml-2 block text-sm text-gray-900">
                  Enable Auto Re-engagement
                </label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Re-engagement Interval (hours)
                </label>
                <input
                  type="number"
                  value={settings.reengagement_interval_hours}
                  onChange={(e) => handleInputChange('reengagement_interval_hours', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  min="1"
                  max="168"
                />
              </div>
            </div>
          </div>

          {/* Monetization */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Monetization</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Gift Price Multiplier
              </label>
              <input
                type="number"
                step="0.1"
                value={settings.gift_price_multiplier}
                onChange={(e) => handleInputChange('gift_price_multiplier', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                min="0.1"
                max="10"
              />
            </div>
          </div>
        </div>

        <div className="mt-8 flex justify-end">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;