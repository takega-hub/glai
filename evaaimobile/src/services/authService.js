import { useAuthStore, forceLogout } from "../store/authStore";

const API_URL = "https://eva.midoma.ru/api";

const login = async (email, password) => {
  console.log("Attempting login for:", email);
  try {
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
      useAuthStore.getState().setAuth(data.access_token, data.user || null);
    }
    return data;
  } catch (error) {
    console.error("Login error:", error.message);
    throw error;
  }
};

const loginAsGuest = async () => {
  try {
    const response = await fetch(`${API_URL}/auth/guest`, {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Guest login failed");
    }

    if (data.access_token) {
      useAuthStore.getState().setAuth(data.access_token, data.user || null);
    }
    return data;
  } catch (error) {
    console.error("Guest login error:", error.message);
    throw error;
  }
};

const register = async (email, password, displayName) => {
  try {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        email,
        password,
        display_name: displayName,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Registration failed");
    }

    return await login(email, password);
  } catch (error) {
    console.error("Registration error:", error.message);
    throw error;
  }
};

const socialLogin = async (provider, token) => {
  try {
    const body = provider === 'google'
      ? { id_token: token }
      : { identity_token: token };

    console.log(`Social Login (${provider}): Sending token to server...`);

    const response = await fetch(`${API_URL}/auth/${provider}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(`${provider} login failed server-side:`, data);
      throw new Error(data.detail || `${provider} login failed`);
    }

    if (data.access_token) {
      console.log(`${provider} login success. Received access_token.`);
      useAuthStore.getState().setAuth(data.access_token, data.user || null);
    }
    return data;
  } catch (error) {
    console.error(`${provider} login error:`, error.message);
    throw error;
  }
};

const logout = async () => {
  console.log("authService: performing logout...");
  forceLogout();
};

const getCurrentUser = () => {
  const { token, user } = useAuthStore.getState();
  return token ? { token, user } : null;
};

export default {
  login,
  loginAsGuest,
  register,
  socialLogin,
  logout,
  getCurrentUser,
};
