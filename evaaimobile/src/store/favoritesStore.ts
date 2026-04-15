import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuthStore } from './authStore';

export interface Character {
  id: string | number;
  name?: string;
  display_name?: string;
  description?: string;
  avatar_url?: string;
  [key: string]: any;
}

interface FavoritesState {
  favorites: Character[];
  toggleFavorite: (character: Character) => void;
  isFavorite: (characterId: string | number | undefined) => boolean;
}

const getFavoritesStorageName = () => {
  const userId = useAuthStore.getState().user?.id;
  return userId ? `favorites-storage-${userId}` : 'favorites-storage-guest';
};

export const useFavoritesStore = create<FavoritesState>()(
  persist(
    (set, get) => ({
      favorites: [],
      
      isFavorite: (characterId: string | number | undefined) => {
        if (!characterId) return false;
        const currentFavorites = get().favorites || [];
        return currentFavorites.some(char =>
          char && (char.id || char._id) && (char.id || char._id).toString() === characterId.toString()
        );
      },
      
      toggleFavorite: (character: Character) => {
        const charId = character?.id || character?._id;
        if (!charId) return;

        const isCurrentlyFavorite = get().isFavorite(charId);
        if (isCurrentlyFavorite) {
          set((state) => ({
            favorites: state.favorites.filter(char => {
              const id = char?.id || char?._id;
              return id && id.toString() !== charId.toString();
            }),
          }));
        } else {
          set((state) => ({
            favorites: [...state.favorites, character],
          }));
        }
      },
    }),
    {
      name: getFavoritesStorageName(),
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
