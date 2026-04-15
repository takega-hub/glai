import axios from "axios";
import { useAuthStore, forceLogout } from "../store/authStore";
import AsyncStorage from "@react-native-async-storage/async-storage";

const apiClient = axios.create({
  baseURL: "https://eva.midoma.ru/api",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

apiClient.interceptors.request.use(
  async (config) => {
    const state = useAuthStore.getState();
    const token = state ? state.token : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest.skipAuthError) {
      console.log("CRITICAL: 401 Unauthorized. Using forceLogout...");

      forceLogout();

      try {
        await AsyncStorage.removeItem('auth-storage');
      } catch (e) {
        console.log("AsyncStorage clear error:", e);
      }

      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
