import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL = "https://eva.midoma.ru/api";

const getAuthHeaders = async () => {
  const token = await AsyncStorage.getItem("@user_token");
  return { Authorization: `Bearer ${token}` };
};

const getCharacters = async () => {
  try {
    const headers = await getAuthHeaders();
    const response = await axios.get(`${API_URL}/characters`, { headers });
    return response.data;
  } catch (error) {
    console.error("Failed to get characters:", error.response?.data || error.message);
    throw error;
  }
};

const getCharacterById = async (id) => {
  try {
    const headers = await getAuthHeaders();
    const response = await axios.get(`${API_URL}/characters/${id}`, { headers });
    return response.data;
  } catch (error) {
    console.error(`Failed to get character ${id}:`, error.response?.data || error.message);
    throw error;
  }
};

export default {
  getCharacters,
  getCharacterById,
};
