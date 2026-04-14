import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { GoogleSignin } from "@react-native-google-signin/google-signin";
import { appleAuth } from "@invertase/react-native-apple-authentication";

const API_URL = "https://eva.midoma.ru/api";

// ...

const login = async (email, password) => {
  try {
    // Используем URLSearchParams и явно переводим в строку для корректной передачи в RN
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);

    const response = await axios.post(`${API_URL}/auth/token`, params.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
      }
    });
    
    if (response.data.access_token) {
      await AsyncStorage.setItem("@user_token", response.data.access_token);
      await AsyncStorage.setItem("@user_data", JSON.stringify(response.data.user));
    }
    return response.data;
  } catch (error) {
    console.error("Login failed:", error.response?.data || error.message);
    throw error;
  }
};

const loginWithGoogle = async () => {
  try {
    // Check if Google Play Services are available
    await GoogleSignin.hasPlayServices();
    
    // Get user info from Google
    const userInfo = await GoogleSignin.signIn();
    
    if (userInfo.idToken) {
      // Send token to backend
      const response = await axios.post(`${API_URL}/auth/google`, {
        id_token: userInfo.idToken,
      });
      
      if (response.data.access_token) {
        await AsyncStorage.setItem("@user_token", response.data.access_token);
        await AsyncStorage.setItem("@user_data", JSON.stringify(response.data.user));
      }
      
      return response.data;
    } else {
      throw new Error("No ID token received from Google");
    }
  } catch (error) {
    console.error("Google login failed:", error);
    throw error;
  }
};

const loginWithApple = async () => {
  try {
    // Check if Apple Sign-In is available
    const appleAuthAvailable = await appleAuth.isSupported;
    
    if (!appleAuthAvailable) {
      throw new Error("Apple Sign-In is not supported on this device");
    }
    
    // Start Apple Sign-In
    const appleAuthRequestResponse = await appleAuth.performRequest({
      requestedOperation: appleAuth.Operation.LOGIN,
      requestedScopes: [appleAuth.Scope.EMAIL, appleAuth.Scope.FULL_NAME],
    });
    
    // Get identity token
    const credentialState = await appleAuth.getCredentialStateForUser(appleAuthRequestResponse.user);
    
    if (credentialState === appleAuth.State.AUTHORIZED) {
      // Send token to backend
      const response = await axios.post(`${API_URL}/auth/apple`, {
        identity_token: appleAuthRequestResponse.identityToken,
        full_name: appleAuthRequestResponse.fullName 
          ? `${appleAuthRequestResponse.fullName.givenName} ${appleAuthRequestResponse.fullName.familyName}`.trim()
          : null,
        email: appleAuthRequestResponse.email,
      });
      
      if (response.data.access_token) {
        await AsyncStorage.setItem("@user_token", response.data.access_token);
        await AsyncStorage.setItem("@user_data", JSON.stringify(response.data.user));
      }
      
      return response.data;
    } else {
      throw new Error("Apple authorization failed");
    }
  } catch (error) {
    console.error("Apple login failed:", error);
    throw error;
  }
};

const logout = async () => {
  try {
    // Sign out from Google if needed
    try {
      await GoogleSignin.signOut();
    } catch (googleError) {
      // Ignore Google logout errors
    }
    
    // Sign out from Apple if needed
    try {
      await appleAuth.performRequest({
        requestedOperation: appleAuth.Operation.LOGOUT,
      });
    } catch (appleError) {
      // Ignore Apple logout errors
    }
    
    // Clear local storage
    await AsyncStorage.removeItem("@user_token");
    await AsyncStorage.removeItem("@user_data");
  } catch (error) {
    console.error("Logout error:", error);
    throw error;
  }
};

const getCurrentUser = async () => {
  try {
    const token = await AsyncStorage.getItem("@user_token");
    const userData = await AsyncStorage.getItem("@user_data");
    
    if (token && userData) {
      return {
        token,
        user: JSON.parse(userData)
      };
    }
    
    return null;
  } catch (error) {
    console.error("Get current user error:", error);
    return null;
  }
};

const isAuthenticated = async () => {
  try {
    const token = await AsyncStorage.getItem("@user_token");
    return !!token;
  } catch (error) {
    console.error("Check auth error:", error);
    return false;
  }
};

export default {
  login,
  loginWithGoogle,
  loginWithApple,
  logout,
  getCurrentUser,
  isAuthenticated,
};
