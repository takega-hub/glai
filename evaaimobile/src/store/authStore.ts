import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface User {
  id: string;
  email: string;
  display_name?: string;
  role: string;
  tokens: number;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  _hasHydrated: boolean;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
  setHasHydrated: (state: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      _hasHydrated: false,
      setAuth: (token, user) => set({ token, user, isAuthenticated: true }),
      logout: () => {
        console.log("AuthStore: Logging out...");
        set({ token: null, user: null, isAuthenticated: false });
      },
      setHasHydrated: (state) => set({ _hasHydrated: state }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => AsyncStorage),
      onRehydrateStorage: () => (state) => {
        if (state) state.setHasHydrated(true);
      },
    }
  )
);

// Функция для принудительного сброса из любого места
export const forceLogout = () => {
  useAuthStore.setState({ token: null, user: null, isAuthenticated: true, _hasHydrated: true });
  // Мы ставим isAuthenticated: true только чтобы пробиться через спиннер, если нужно,
  // но лучше просто обнулить токен.
  useAuthStore.setState({ token: null, isAuthenticated: false, _hasHydrated: true });
};
