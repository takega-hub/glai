import axios from "axios";
import { useAuthStore } from "../store/authStore";

const API_URL = "https://eva.midoma.ru/api";

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Добавляем токен к каждому запросу
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Обработка 401 ошибки (Unauthorized)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const url = error.config.url;
      console.log(`401 Unauthorized at ${url}. Clearing auth.`);
      // Вызываем logout из стора
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

export default apiClient;
