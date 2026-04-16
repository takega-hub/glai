import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import AsyncStorage from "@react-native-async-storage/async-storage";

export const useAuthStore = create(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      balance: 0,
      setAuth: (token, user) => set({ token, user, balance: user?.tokens || 0 }),
      clearAuth: () => set({ token: null, user: null, balance: 0 }),
      updateBalance: (newBalance) =>
        set((state) => ({
          ...state,
          balance: newBalance,
          user: state.user ? { ...state.user, tokens: newBalance } : null,
        })),
      forceLogout: () => {
        console.log("authStore: forceLogout action triggered");
        set({
          token: null,
          user: null,
          balance: 0,
          _hasHydrated: true
        });
      },
    }),
    {
      name: "auth-storage",
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
