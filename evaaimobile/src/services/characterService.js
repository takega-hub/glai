import apiClient from "./apiClient";

const getCharacters = async () => {
  try {
    console.log("Fetching characters...");
    const response = await apiClient.get("/characters/");
    return response.data;
  } catch (error) {
    console.error("Failed to get characters:", error.response?.data || error.message);
    throw error;
  }
};

const getCharacterById = async (id) => {
  try {
    const response = await apiClient.get(`/characters/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to get character ${id}:`, error.response?.data || error.message);
    throw error;
  }
};

const getCharacterContent = async (characterId) => {
  try {
    const response = await apiClient.get(`/content/character/${characterId}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to get character content ${characterId}:`, error.response?.data || error.message);
    throw error;
  }
};

const getPersonalGallery = async (characterId) => {
  try {
    const response = await apiClient.get(`/characters/${characterId}/personal-gallery`);
    return response.data;
  } catch (error) {
    console.error(`Failed to get personal gallery ${characterId}:`, error.response?.data || error.message);
    throw error;
  }
};

const getCharacterPhotos = getCharacterContent;

export default {
  getCharacters,
  getCharacterById,
  getCharacterContent,
  getPersonalGallery,
  getCharacterPhotos,
};
