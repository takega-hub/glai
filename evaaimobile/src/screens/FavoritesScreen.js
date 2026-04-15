import React from "react";
import { View, Text, FlatList, StyleSheet, TouchableOpacity, Image } from "react-native";
import { useFavoritesStore } from "../store/favoritesStore";
import { Heart } from "lucide-react-native";

const FavoritesScreen = ({ navigation }) => {
  const { favorites, toggleFavorite } = useFavoritesStore();

  const renderCharacter = ({ item }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate("Character", { characterId: item.id, characterName: item.name })}
    >
      <Image source={{ uri: `https://eva.midoma.ru${item.avatar_url}` }} style={styles.avatar} />
      <View style={styles.info}>
        <Text style={styles.name}>{item.name}</Text>
        <Text style={styles.description} numberOfLines={2}>{item.description}</Text>
      </View>
      <TouchableOpacity onPress={() => toggleFavorite(item)}>
        <Heart size={24} color="#ef4444" fill="#ef4444" />
      </TouchableOpacity>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {favorites.length > 0 ? (
        <FlatList
          data={favorites}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderCharacter}
          contentContainerStyle={styles.list}
        />
      ) : (
        <View style={styles.emptyContainer}>
          <Heart size={64} color="rgba(255,255,255,0.1)" />
          <Text style={styles.emptyText}>No favorites yet</Text>
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
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  avatar: { width: 60, height: 60, borderRadius: 30, backgroundColor: "#1e1b4b" },
  info: { flex: 1, marginLeft: 12 },
  name: { color: "white", fontSize: 18, fontWeight: "bold" },
  description: { color: "#94a3b8", fontSize: 14, marginTop: 2 },
  emptyContainer: { flex: 1, justifyContent: "center", alignItems: "center" },
  emptyText: { color: "#94a3b8", fontSize: 18, marginTop: 16 },
});

export default FavoritesScreen;
