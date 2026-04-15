import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  Image,
  TouchableOpacity,
  SafeAreaView,
  Dimensions,
} from "react-native";
import { Star, Heart, Flame, User as UserIcon } from "lucide-react-native";
import characterService from "../services/characterService";
import { useFavoritesStore } from "../store/favoritesStore";
import { useAuthStore } from "../store/authStore";

const { width } = Dimensions.get("window");
const COLUMN_COUNT = 2;
const CARD_MARGIN = 8;
const CARD_WIDTH = (width - 32 - CARD_MARGIN * 2) / COLUMN_COUNT;

const MainScreen = ({ navigation }) => {
  const [characters, setCharacters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { toggleFavorite, isFavorite } = useFavoritesStore();

  const getFullImageUrl = (url) => {
    if (!url) return null;
    if (url.startsWith("http")) return url;
    return `https://eva.midoma.ru${url}`;
  };

  useEffect(() => {
    // Небольшая задержка перед первым запросом, чтобы дать сессии установиться
    const timer = setTimeout(() => {
      fetchCharacters();
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  const fetchCharacters = async () => {
    try {
      setLoading(true);
      const response = await characterService.getCharacters();

      // Handle different response formats (array or object with characters array)
      if (Array.isArray(response)) {
        setCharacters(response);
      } else if (response && Array.isArray(response.characters)) {
        setCharacters(response.characters);
      } else if (response && response.data && Array.isArray(response.data)) {
        setCharacters(response.data);
      } else {
        console.error("Unexpected API response format:", response);
        setCharacters([]);
      }

      setError(null);
    } catch (err) {
      console.error("Fetch characters error:", err);
      setError(err.message);

      // Глобальный логаут при любой 401 ошибке
      if (err.response?.status === 401 || err.message?.includes("401")) {
        console.log("MainScreen detected 401. Force logout.");
        useAuthStore.getState().logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const renderCharacterCard = ({ item }) => {
    const charId = item.id || item._id;
    const trustPercentage = Math.min(Math.round((item.trust_score || 0) / 10), 100);
    const favorite = isFavorite(charId);

    return (
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() =>
          navigation.navigate("Character", {
            characterId: charId,
            characterName: item.display_name || item.name,
          })
        }
        style={styles.cardContainer}
      >
        <View style={styles.card}>
          {/* Character Image */}
          <View style={styles.imageContainer}>
            {item.avatar_url ? (
              <Image
                source={{ uri: getFullImageUrl(item.avatar_url) }}
                style={styles.avatar}
                resizeMode="cover"
              />
            ) : (
              <View style={styles.avatarPlaceholder}>
                <UserIcon size={60} color="rgba(255,255,255,0.6)" />
              </View>
            )}

            {/* Hot Badge */}
            {item.is_hot && (
              <View style={styles.hotBadge}>
                <Flame size={16} color="white" />
              </View>
            )}

            {/* Favorite Button */}
            <TouchableOpacity
              style={[styles.favoriteButton, favorite && styles.favoriteButtonActive]}
              onPress={() => toggleFavorite(item)}
            >
              <Heart size={20} color={favorite ? "#ef4444" : "white"} fill={favorite ? "#ef4444" : "transparent"} />
            </TouchableOpacity>

            {/* Gradient Overlay Placeholder (using semi-transparent view) */}
            <View style={styles.imageOverlay}>
              <Text style={styles.charName}>{item.display_name || item.name}</Text>
              <View style={styles.charSubInfo}>
                <Text style={styles.charArchetype}>
                  {item.personality_type || item.archetype || "Character"}
                </Text>
                {item.age && (
                  <>
                    <Text style={styles.dot}>•</Text>
                    <Text style={styles.charAge}>{item.age} years</Text>
                  </>
                )}
              </View>
            </View>
          </View>

          {/* Card Content */}
          <View style={styles.cardContent}>
            <View style={styles.badgesRow}>
              {item.status === "active" && (
                <View style={[styles.badge, styles.onlineBadge]}>
                  <View style={styles.onlineDot} />
                  <Text style={styles.onlineText}>Online</Text>
                </View>
              )}
              <View style={[styles.badge, styles.trustBadge]}>
                <Heart size={12} color="#d8b4fe" style={{ marginRight: 4 }} />
                <Text style={styles.trustText}>{trustPercentage}% trust</Text>
              </View>
              <View style={[styles.badge, styles.subBadge]}>
                <UserIcon size={12} color="#93c5fd" style={{ marginRight: 4 }} />
                <Text style={styles.subText}>{item.subscribers || 0}</Text>
              </View>
            </View>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#a855f7" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>Error: {error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={fetchCharacters}>
          <Text style={styles.retryText}>Try again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={characters}
        renderItem={renderCharacterCard}
        keyExtractor={(item) => (item.id || item._id || Math.random()).toString()}
        numColumns={COLUMN_COUNT}
        columnWrapperStyle={styles.columnWrapper}
        contentContainerStyle={styles.listContent}
        ListHeaderComponent={
          <View style={styles.header}>
            <Star size={24} color="#facc15" fill="#facc15" />
            <Text style={styles.headerTitle}>Available Characters</Text>
          </View>
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <UserIcon size={64} color="rgba(168, 85, 247, 0.4)" />
            <Text style={styles.emptyTitle}>Characters not found</Text>
            <Text style={styles.emptySub}>Try refreshing the page later</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a", // slate-900
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#0f172a",
  },
  listContent: {
    padding: 16,
    paddingBottom: 32,
  },
  columnWrapper: {
    justifyContent: "space-between",
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 20,
    gap: 10,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: "bold",
    color: "white",
  },
  cardContainer: {
    width: CARD_WIDTH,
    marginBottom: 16,
  },
  card: {
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
    overflow: "hidden",
  },
  imageContainer: {
    height: 380,
    position: "relative",
    overflow: "hidden",
  },
  avatar: {
    width: "100%",
    height: "125%",
    position: "absolute",
    top: 0,
  },
  avatarPlaceholder: {
    width: "100%",
    height: "100%",
    backgroundColor: "rgba(168, 85, 247, 0.2)", // matches web gradient feel
    justifyContent: "center",
    alignItems: "center",
  },
  hotBadge: {
    position: "absolute",
    top: 8,
    left: 8,
    backgroundColor: "rgba(239, 68, 68, 0.8)",
    padding: 4,
    borderRadius: 8,
    zIndex: 10,
  },
  favoriteButton: {
    position: "absolute",
    top: 8,
    right: 8,
    backgroundColor: "rgba(0, 0, 0, 0.3)",
    padding: 6,
    borderRadius: 20,
    zIndex: 10,
  },
  favoriteButtonActive: {
    backgroundColor: "rgba(255, 255, 255, 0.9)",
  },
  imageOverlay: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: 12,
    backgroundColor: "rgba(0,0,0,0.6)",
  },
  charName: {
    fontSize: 18,
    fontWeight: "bold",
    color: "white",
    marginBottom: 2,
  },
  charSubInfo: {
    flexDirection: "row",
    alignItems: "center",
    flexWrap: "wrap",
  },
  charArchetype: {
    color: "#d8b4fe",
    fontSize: 11,
  },
  dot: {
    color: "#a855f7",
    marginHorizontal: 4,
  },
  charAge: {
    color: "#d8b4fe",
    fontSize: 11,
  },
  cardContent: {
    padding: 8,
  },
  badgesRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 4,
  },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 12,
    borderWidth: 1,
  },
  onlineBadge: {
    backgroundColor: "rgba(34, 197, 94, 0.15)",
    borderColor: "rgba(74, 222, 128, 0.3)",
  },
  onlineDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: "#4ade80",
    marginRight: 4,
  },
  onlineText: {
    color: "#86efac",
    fontSize: 9,
    fontWeight: "600",
  },
  trustBadge: {
    backgroundColor: "rgba(168, 85, 247, 0.15)",
    borderColor: "rgba(192, 132, 252, 0.3)",
  },
  trustText: {
    color: "#d8b4fe",
    fontSize: 9,
    fontWeight: "600",
  },
  subBadge: {
    backgroundColor: "rgba(59, 130, 246, 0.15)",
    borderColor: "rgba(96, 165, 250, 0.3)",
  },
  subText: {
    color: "#93c5fd",
    fontSize: 9,
    fontWeight: "600",
  },
  errorText: {
    color: "#f87171",
    fontSize: 16,
    textAlign: "center",
    marginBottom: 20,
    paddingHorizontal: 20,
  },
  retryButton: {
    backgroundColor: "#a855f7",
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  retryText: {
    color: "white",
    fontWeight: "bold",
  },
  emptyContainer: {
    padding: 48,
    alignItems: "center",
    backgroundColor: "rgba(255,255,255,0.05)",
    borderRadius: 20,
    marginTop: 40,
  },
  emptyTitle: {
    color: "white",
    fontSize: 18,
    fontWeight: "semibold",
    marginTop: 16,
    marginBottom: 4,
  },
  emptySub: {
    color: "#d8b4fe",
    fontSize: 14,
  },
});

export default MainScreen;
