import axios from "axios";
import { useAuthStore } from "../store/authStore";

const API_URL = "https://eva.midoma.ru/api";

const getAuthHeaders = () => {
  const token = useAuthStore.getState().token;
  return { Authorization: `Bearer ${token}` };
};

const getChatHistory = async (characterId) => {
  try {
    const headers = getAuthHeaders();
    const response = await axios.get(`${API_URL}/dialogue/history/${characterId}`, { headers });
    return response.data.messages;
  } catch (error) {
    console.error(`Failed to get chat history for ${characterId}:`, error.response?.data || error.message);
    throw error;
  }
};

const sendMessage = async (characterId, message, image) => {
  try {
    const headers = getAuthHeaders();
    const formData = new FormData();
    formData.append("character_id", characterId);
    if (message) {
      formData.append("message", message);
    }
    if (image) {
      formData.append("image", {
        uri: image.uri,
        type: image.type,
        name: image.fileName,
      });
    }

    const response = await axios.post(`${API_URL}/dialogue/send-message`, formData, {
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

const sendGift = async (characterId, giftType) => {
  try {
    const headers = getAuthHeaders();
    const response = await axios.post(`${API_URL}/dialogue/send-gift`, { character_id: characterId, gift_type: giftType }, { headers });
    return response.data;
  } catch (error) {
    console.error("Failed to send gift:", error.response?.data || error.message);
    throw error;
  }
};

const getBalance = async () => {
  try {
    const headers = getAuthHeaders();
    const response = await axios.get(`${API_URL}/tokens/balance`, { headers }); 
    return response.data;
  } catch (error) {
    console.error("Failed to get balance:", error.response?.data || error.message);
    throw error;
  }
};

export default {
  getChatHistory,
  sendMessage,
  sendGift,
  getBalance,
};
