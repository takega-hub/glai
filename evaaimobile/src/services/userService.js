import apiClient from "./apiClient";
import { Platform } from "react-native";

const getUserProfile = async () => {
  try {
    const response = await apiClient.get("/user/profile");
    return response.data;
  } catch (error) {
    console.error("Failed to get user profile:", error.response?.data || error.message);
    throw error;
  }
};

const updateUserProfile = async (profileData) => {
  try {
    const response = await apiClient.put("/user/profile", profileData);
    return response.data;
  } catch (error) {
    console.error("Failed to update user profile:", error.response?.data || error.message);
    throw error;
  }
};

const uploadAvatar = async (fileUri) => {
  try {
    const formData = new FormData();
    formData.append("file", {
      uri: fileUri,
      name: "avatar.jpg",
      type: "image/jpeg",
    });

    const response = await apiClient.post("/user/profile/avatar", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Failed to upload avatar:", error.response?.data || error.message);
    throw error;
  }
};

const getHistory = async () => {
  try {
    const response = await apiClient.get("/tokens/history");
    return response.data;
  } catch (error) {
    console.error("Failed to get token history:", error.response?.data || error.message);
    throw error;
  }
};

const getPackages = async () => {
  try {
    const response = await apiClient.get("/tokens/packages");
    return response.data;
  } catch (error) {
    console.error("Failed to get token packages:", error.response?.data || error.message);
    throw error;
  }
};

const updateEmailNotifications = async (enabled) => {
  try {
    const response = await apiClient.put("/profile/notifications", { enabled });
    return response.data;
  } catch (error) {
    console.error("Failed to update email notifications:", error.response?.data || error.message);
    throw error;
  }
};

const changePassword = async (currentPassword, newPassword) => {
  try {
    const response = await apiClient.put(
      "/profile/change-password",
      { current_password: currentPassword, new_password: newPassword }
    );
    return response.data;
  } catch (error) {
    console.error("Failed to change password:", error.response?.data || error.message);
    throw error;
  }
};

const registerDevice = async (deviceToken) => {
  try {
    const response = await apiClient.post("/notifications/register-device", {
      device_token: deviceToken,
      device_type: Platform.OS,
    });
    return response.data;
  } catch (error) {
    console.error("Failed to register device:", error.response?.data || error.message);
    throw error;
  }
};

const getUnreadStatus = async () => {
  try {
    const response = await apiClient.get("/admin/user-state/unread-status");
    return response.data;
  } catch (error) {
    console.error("Failed to get unread status:", error.response?.data || error.message);
    return [];
  }
};

const markCharacterViewed = async (characterId) => {
  try {
    const response = await apiClient.post(`/admin/user-state/mark-viewed?character_id=${characterId}`);
    return response.data;
  } catch (error) {
    console.error("Failed to mark character viewed:", error.response?.data || error.message);
  }
};

export default {
  getUserProfile,
  updateUserProfile,
  uploadAvatar,
  getHistory,
  getPackages,
  updateEmailNotifications,
  changePassword,
  registerDevice,
  getUnreadStatus,
  markCharacterViewed,
};
