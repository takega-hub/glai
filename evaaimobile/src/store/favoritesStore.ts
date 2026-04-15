import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuthStore } from './authStore';

interface FavoritesState {
  favoriteCharacterIds: string[];
  addFavorite: (characterId: string) => void;
  removeFavorite: (characterId: string) => void;
  isFavorite: (characterId: string) => boolean;
  toggleFavorite: (characterId: string) => void;
}

const getFavoritesStorageName = () => {
  const userId = useAuthStore.getState().user?.id;
  return userId ? `favorites-storage-${userId}` : 'favorites-storage-guest';
};

export const useFavoritesStore = create<FavoritesState>()(
  persist(
    (set, get) => ({
      favoriteCharacterIds: [],
      
      addFavorite: (characterId: string) => {
        set((state) => ({
          favoriteCharacterIds: [...state.favoriteCharacterIds, characterId],
        }));
      },
      
      removeFavorite: (characterId: string) => {
        set((state) => ({
          favoriteCharacterIds: state.favoriteCharacterIds.filter(id => id !== characterId),
        }));
      },
      
      isFavorite: (characterId: string) => {
        return get().favoriteCharacterIds.includes(characterId);
      },
      
      toggleFavorite: (characterId: string) => {
        const isCurrentlyFavorite = get().isFavorite(characterId);
        if (isCurrentlyFavorite) {
          get().removeFavorite(characterId);
        } else {
          get().addFavorite(characterId);
        }
      },
    }),
    {
      name: getFavoritesStorageName(),
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);

// Subscribe to auth changes to reload favorites when user changes
useAuthStore.subscribe(
  (state, prevState) => {
    if (state.user?.id !== prevState.user?.id) {
      useFavoritesStore.persist.rehydrate();
    }
  }
);