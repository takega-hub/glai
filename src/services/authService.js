import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { GoogleSignin } from "@react-native-google-signin/google-signin";
import { appleAuth } from "@invertase/react-native-apple-authentication";

const API_URL = "https://eva.midoma.ru/api";

const login = async (email, password) => {
  console.log("Attempting login for:", email);
  try {
    // Для FastAPI OAuth2PasswordRequestForm ОБЯЗАТЕЛЬНО использовать application/x-www-form-urlencoded
    const body = `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;

    const response = await fetch(`${API_URL}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
      },
      body: body,
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("Login failed with status:", response.status, data);
      throw new Error(data.detail || 'Login failed');
    }

    if (data.access_token) {
      await AsyncStorage.setItem("@user_token", data.access_token);
      if (data.user) {
        await AsyncStorage.setItem("@user_data", JSON.stringify(data.user));
      }
    }
    return data;
  } catch (error) {
    console.error("Login error:", error.message);
    throw error;
  }
};

const loginWithGoogle = async () => {
  try {
    await GoogleSignin.hasPlayServices();
    const userInfo = await GoogleSignin.signIn();
    
    if (userInfo.idToken) {
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
    const appleAuthAvailable = await appleAuth.isSupported;
    if (!appleAuthAvailable) {
      throw new Error("Apple Sign-In is not supported on this device");
    }
    
    const appleAuthRequestResponse = await appleAuth.performRequest({
      requestedOperation: appleAuth.Operation.LOGIN,
      requestedScopes: [appleAuth.Scope.EMAIL, appleAuth.Scope.FULL_NAME],
    });
    
    const credentialState = await appleAuth.getCredentialStateForUser(appleAuthRequestResponse.user);
    
    if (credentialState === appleAuth.State.AUTHORIZED) {
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
    try { await GoogleSignin.signOut(); } catch (e) {}
    try {
      await appleAuth.performRequest({ requestedOperation: appleAuth.Operation.LOGOUT });
    } catch (e) {}
    
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
    return (token && userData) ? { token, user: JSON.parse(userData) } : null;
  } catch (error) {
    return null;
  }
};

const isAuthenticated = async () => {
  const token = await AsyncStorage.getItem("@user_token");
  return !!token;
};

export default {
  login,
  loginWithGoogle,
  loginWithApple,
  logout,
  getCurrentUser,
  isAuthenticated,
};
