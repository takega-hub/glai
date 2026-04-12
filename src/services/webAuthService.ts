import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://eva.midoma.ru/api';
const API_URL = `${API_BASE_URL}/auth`;

const handleAuthSuccess = (token: string, user: any) => {
  useAuthStore.getState().setAuth(token, user);
};

const login = async (email: string, password: string) => {
  const response = await axios.post(`${API_URL}/token`, 
    new URLSearchParams({
      username: email,
      password: password,
    }),
    {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    }
  );
  if (response.data.access_token) {
    handleAuthSuccess(response.data.access_token, response.data.user);
  }
  return response.data;
};

const register = async (email: string, password: string, name: string) => {
  const response = await axios.post(`${API_URL}/register`, {
    email: email,
    password: password,
    username: name,
  });
  if (response.data.access_token) {
    handleAuthSuccess(response.data.access_token, response.data.user);
  }
  return response.data;
};

const loginAsGuest = async () => {
  const response = await axios.post(`${API_URL}/guest`);
  if (response.data.access_token) {
    handleAuthSuccess(response.data.access_token, response.data.user);
  }
  return response.data;
};

const loginWithGoogle = async (credential: string) => {
  const response = await axios.post(`${API_URL}/google`, {
    id_token: credential,
  });
  if (response.data.access_token) {
    handleAuthSuccess(response.data.access_token, response.data.user);
  }
  return response.data;
};

const loginWithApple = async (id_token: string, full_name: string | null, email: string | null) => {
    const response = await axios.post(`${API_URL}/apple`, {
        identity_token: id_token,
        full_name: full_name,
        email: email,
    });
    if (response.data.access_token) {
        handleAuthSuccess(response.data.access_token, response.data.user);
    }
    return response.data;
};

const logout = () => {
  useAuthStore.getState().logout();
};

export const webAuthService = {
  login,
  register,
  loginAsGuest,
  loginWithGoogle,
  loginWithApple,
  logout,
};
