import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL = "https://eva.midoma.ru/api/dialogue";

const getAuthHeaders = async () => {
  const token = await AsyncStorage.getItem("@user_token");
  return { Authorization: `Bearer ${token}` };
};

const getChatHistory = async (characterId) => {
  try {
    const headers = await getAuthHeaders();
    const response = await axios.get(`${API_URL}/history/${characterId}`, { headers });
    return response.data.messages;
  } catch (error) {
    console.error(`Failed to get chat history for ${characterId}:`, error.response?.data || error.message);
    throw error;
  }
};

const sendMessage = async (characterId, message) => {
  try {
    const headers = await getAuthHeaders();
    const formData = new FormData();
    formData.append("character_id", characterId);
    formData.append("message", message);

    const response = await axios.post(`${API_URL}/send-message`, formData, {
      headers: {
        ...headers,
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Failed to send message:", error.response?.data || error.message);
    throw error;
  }
};

export default {
  getChatHistory,
  sendMessage,
};
