import React from "react";
import { View, Text, FlatList, StyleSheet, TouchableOpacity, Image } from "react-native";
import { useFavoritesStore } from "../store/favoritesStore";
import { Heart, User } from "lucide-react-native";

const FavoritesScreen = ({ navigation }) => {
  const { favorites, toggleFavorite } = useFavoritesStore();

  const getFullImageUrl = (url) => {
    if (!url) return null;
    if (url.startsWith("http")) return url;
    return `https://eva.midoma.ru${url}`;
  };

  const renderCharacter = ({ item }) => {
    const charId = item.id || item._id;
    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => navigation.navigate("Character", {
          characterId: charId,
          characterName: item.display_name || item.name
        })}
      >
      {item.avatar_url ? (
        <Image source={{ uri: getFullImageUrl(item.avatar_url) }} style={styles.avatar} />
      ) : (
        <View style={styles.avatarPlaceholder}>
          <User size={30} color="rgba(255,255,255,0.4)" />
        </View>
      )}
      <View style={styles.info}>
        <Text style={styles.name}>{item.display_name || item.name}</Text>
        <Text style={styles.archetype}>{item.personality_type || item.archetype || "Character"}</Text>
      </View>
      <TouchableOpacity onPress={() => toggleFavorite(item)} style={styles.heartButton}>
        <Heart size={24} color="#ef4444" fill="#ef4444" />
      </TouchableOpacity>
    </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      {favorites && favorites.length > 0 ? (
        <FlatList
          data={favorites}
          keyExtractor={(item, index) => {
            const id = item?.id || item?._id;
            return id ? id.toString() : `fav-${index}`;
          }}
          renderItem={renderCharacter}
          contentContainerStyle={styles.list}
        />
      ) : (
        <View style={styles.emptyContainer}>
          <Heart size={64} color="rgba(255,255,255,0.05)" />
          <Text style={styles.emptyText}>No favorites yet</Text>
          <TouchableOpacity
            style={styles.exploreButton}
            onPress={() => navigation.navigate("Main")}
          >
            <Text style={styles.exploreText}>Explore Characters</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f172a" },
  list: { padding: 16 },
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(30, 41, 59, 0.5)",
    borderRadius: 16,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  avatar: { width: 60, height: 60, borderRadius: 30, backgroundColor: "#1e1b4b" },
  avatarPlaceholder: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "rgba(168, 85, 247, 0.2)",
    justifyContent: "center",
    alignItems: "center"
  },
  info: { flex: 1, marginLeft: 12 },
  name: { color: "white", fontSize: 18, fontWeight: "bold" },
  archetype: { color: "#d8b4fe", fontSize: 13, marginTop: 2 },
  heartButton: { padding: 8 },
  emptyContainer: { flex: 1, justifyContent: "center", alignItems: "center", padding: 20 },
  emptyText: { color: "#94a3b8", fontSize: 18, marginTop: 16, textAlign: "center" },
  exploreButton: {
    marginTop: 24,
    backgroundColor: "#a855f7",
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  exploreText: { color: "white", fontWeight: "bold", fontSize: 16 },
});

export default FavoritesScreen;
