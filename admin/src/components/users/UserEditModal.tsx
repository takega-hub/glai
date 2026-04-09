import React, { useState, useEffect } from 'react';
import { X, Save, User, Mail, Shield, Activity } from 'lucide-react';

interface User {
  id: string;
  email: string;
  display_name: string | null;
  role: string;
  status: string;
  created_at: string;
  last_active_at: string | null;
  tokens_balance: number;
}

interface UserEditModalProps {
  user: User | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (userData: Partial<User>) => Promise<void>;
}

const UserEditModal: React.FC<UserEditModalProps> = ({ user, isOpen, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    email: '',
    display_name: '',
    role: 'app_user',
    status: 'active'
  });
  const [addTokens, setAddTokens] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFormData({
        email: user.email,
        display_name: user.display_name || '',
        role: user.role,
        status: user.status
      });
      setAddTokens(0);
      setError(null);
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    setIsLoading(true);
    setError(null);

    try {
      await onSave({
        ...formData,
        id: user.id,
        add_tokens: addTokens,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  if (!isOpen || !user) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Edit User</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form id="userEditForm" onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              <Mail className="inline w-4 h-4 mr-1" />
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
          </div>

          <div>
            <label htmlFor="display_name" className="block text-sm font-medium text-gray-700 mb-1">
              <User className="inline w-4 h-4 mr-1" />
              Display Name
            </label>
            <input
              type="text"
              id="display_name"
              name="display_name"
              value={formData.display_name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Enter display name"
            />
          </div>

          <div>
            <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
              <Shield className="inline w-4 h-4 mr-1" />
              Role
            </label>
            <select
              id="role"
              name="role"
              value={formData.role}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="app_user">App User</option>
              <option value="admin">Admin</option>
              <option value="super_admin">Super Admin</option>
            </select>
          </div>

          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
              <Activity className="inline w-4 h-4 mr-1" />
              Status
            </label>
            <select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="active">Active</option>
              <option value="blocked">Blocked</option>
            </select>
          </div>

          <div className="bg-gray-50 rounded-md p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Current Information</h3>
            <div className="space-y-1 text-sm text-gray-600">
              <p><span className="font-medium">Tokens:</span> {user.tokens_balance.toLocaleString()}</p>
              <p><span className="font-medium">Created:</span> {new Date(user.created_at).toLocaleDateString()}</p>
              <p><span className="font-medium">Last Active:</span> {user.last_active_at ? new Date(user.last_active_at).toLocaleDateString() : 'N/A'}</p>
            </div>
          </div>

          <div>
            <label htmlFor="add_tokens" className="block text-sm font-medium text-gray-700 mb-1">
              Add Tokens
            </label>
            <input
              type="number"
              id="add_tokens"
              name="add_tokens"
              value={addTokens}
              onChange={(e) => setAddTokens(parseInt(e.target.value, 10) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="0"
            />
          </div>
        </form>

        <div className="flex justify-end space-x-3 p-6 border-t bg-gray-50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="userEditForm"
            disabled={isLoading}
            onClick={handleSubmit}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Saving...
              </span>
            ) : (
              <span className="flex items-center">
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserEditModal;