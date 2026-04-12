import axios from 'axios';

import { useAuthStore } from '../store/authStore';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the auth token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add a response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth data and redirect to login
      useAuthStore.getState().logout();
      window.location.href = '/user/auth';
    }
    return Promise.reject(error);
  }
);

// Character API calls
export const getCharacters = () => apiClient.get('/characters/');
export const getCharacterById = (id: string) => apiClient.get(`/characters/${id}`);

// Auth API calls
export const login = (credentials: any) => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.email);
  formData.append('password', credentials.password);
  return apiClient.post('/auth/token', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
};

export const sendGift = (characterId: string, giftType: string, proposalDetails: any | null) => {
  return apiClient.post('/dialogue/send-gift/', { 
    character_id: characterId,
    gift_type: giftType,
    proposal_details: proposalDetails
  });
};
export const register = (userInfo: any) => apiClient.post('/auth/register', userInfo);
export const loginAsGuest = () => apiClient.post('/auth/guest');


// Chat API calls
export const getChatHistory = (characterId: string) => apiClient.get(`/dialogue/history/${characterId}`);
export const sendMessage = (characterId: string, message: string, image?: File) => {
  return apiClient.post('/dialogue/send-message', {
    character_id: characterId,
    message: message,
  });
};

// User Profile API calls
export const getUserProfile = () => apiClient.get('/user/profile');
export const updateUserProfile = (profileData: any) => apiClient.put('/user/profile', profileData);
export const uploadAvatar = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.post("/user/profile/avatar", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

// Other Profile API calls
export const updateEmailNotifications = (enabled: boolean) => apiClient.put('/profile/notifications', { enabled });
export const changePassword = (current_password: any, new_password: any) => apiClient.put('/profile/change-password', { current_password, new_password });

// Content Gallery API calls
export const getContentGallery = (characterId: string) => apiClient.get(`/content/character/${characterId}`);
export const getPersonalGallery = (characterId: string) => apiClient.get(`/characters/${characterId}/personal-gallery`);

// Token API calls
export const getBalance = () => apiClient.get('/tokens/balance');
export const getHistory = () => apiClient.get('/tokens/history');
export const getPackages = () => apiClient.get('/tokens/packages');

// User Analytics API calls
export const getUserAnalytics = () => apiClient.get('/user-analytics/');

export default apiClient;