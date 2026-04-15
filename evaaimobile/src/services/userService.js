import apiClient from "./apiClient";

const getUserProfile = async () => {
  try {
    const response = await apiClient.get("/user/profile/");
    return response.data;
  } catch (error) {
    console.error("Failed to get user profile:", error.response?.data || error.message);
    throw error;
  }
};

const updateUserProfile = async (profileData) => {
  try {
    const response = await apiClient.put("/user/profile/", profileData);
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

    const response = await apiClient.post("/user/profile/avatar/", formData, {
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
    const response = await apiClient.get("/tokens/history/");
    return response.data;
  } catch (error) {
    console.error("Failed to get token history:", error.response?.data || error.message);
    throw error;
  }
};

const getPackages = async () => {
  try {
    const response = await apiClient.get("/tokens/packages/");
    return response.data;
  } catch (error) {
    console.error("Failed to get token packages:", error.response?.data || error.message);
    throw error;
  }
};

const updateEmailNotifications = async (enabled) => {
  try {
    const response = await apiClient.put("/profile/notifications/", { enabled });
    return response.data;
  } catch (error) {
    console.error("Failed to update email notifications:", error.response?.data || error.message);
    throw error;
  }
};

const changePassword = async (currentPassword, newPassword) => {
  try {
    const response = await apiClient.put(
      "/profile/change-password/",
      { current_password: currentPassword, new_password: newPassword }
    );
    return response.data;
  } catch (error) {
    console.error("Failed to change password:", error.response?.data || error.message);
    throw error;
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
};
