import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL = "https://eva.midoma.ru/api/auth";

const login = async (email, password) => {
  try {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await axios.post(`${API_URL}/token`, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    if (response.data.access_token) {
      await AsyncStorage.setItem("@user_token", response.data.access_token);
    }
    return response.data;
  } catch (error) {
    console.error("Login failed:", error.response?.data || error.message);
    throw error;
  }
};

const logout = async () => {
  await AsyncStorage.removeItem("@user_token");
};

const getCurrentUser = async () => {
  const token = await AsyncStorage.getItem("@user_token");
  return token;
};

export default {
  login,
  logout,
  getCurrentUser,
};
