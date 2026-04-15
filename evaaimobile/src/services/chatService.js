import apiClient from "./apiClient";

const getChatHistory = async (characterId) => {
  try {
    console.log(`API Call: getChatHistory for ${characterId}`);
    const response = await apiClient.get(`/dialogue/history/${characterId}`);
    console.log(`API Response: getChatHistory successful, status ${response.status}`);

    // Бэкенд возвращает объект { messages: [...], trust_score: X, ... }
    if (response.data && Array.isArray(response.data.messages)) {
      return response.data.messages;
    }
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return [];
  } catch (error) {
    console.error(`Failed to get chat history for ${characterId}:`, error.response?.data || error.message);
    return [];
  }
};

const sendMessage = async (characterId, message, image = null) => {
  try {
    const data = {
      character_id: characterId,
      message: message || ""
    };

    const response = await apiClient.post("/dialogue/send-message", data);
    return response.data;
  } catch (error) {
    console.error("Failed to send message:", error.response?.data || error.message);
    throw error;
  }
};

const sendGift = async (characterId, giftType) => {
  try {
    const response = await apiClient.post("/dialogue/send-gift", {
      character_id: characterId,
      gift_type: giftType
    });
    return response.data;
  } catch (error) {
    console.error("Failed to send gift:", error.response?.data || error.message);
    throw error;
  }
};

const getBalance = async () => {
  try {
    const response = await apiClient.get("/tokens/balance");
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
