import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  Image,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Dimensions,
  Modal,
} from "react-native";
import { MessageCircle, Image as ImageIcon, Video, Lock, Eye, Flame, Heart, X } from "lucide-react-native";
import characterService from "../services/characterService";
import { useFavoritesStore } from "../store/favoritesStore";

const { width, height } = Dimensions.get("window");

const CharacterScreen = ({ route, navigation }) => {
  const { characterId, characterName } = route.params;
  const [character, setCharacter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("public");
  const { isFavorite, toggleFavorite } = useFavoritesStore();
  const [photos, setPhotos] = useState([]);
  const [personalPhotos, setPersonalPhotos] = useState([]);
  const [loadingPhotos, setLoadingPhotos] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [isViewerVisible, setIsViewerVisible] = useState(false);

  const getFullImageUrl = (url) => {
    if (!url) return null;
    if (url.startsWith("http")) return url;
    return `https://eva.midoma.ru${url}`;
  };

  const openImageViewer = (url) => {
    setSelectedImage(getFullImageUrl(url));
    setIsViewerVisible(true);
  };

  useEffect(() => {
    const fetchCharacter = async () => {
      try {
        const data = await characterService.getCharacterById(characterId);
        setCharacter(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    const fetchPhotos = async () => {
      setLoadingPhotos(true);
      try {
        const contentResponse = await characterService.getCharacterContent(characterId);
        if (contentResponse && Array.isArray(contentResponse.content)) {
          setPhotos(contentResponse.content);
        }

        const personalResponse = await characterService.getPersonalGallery(characterId);
        if (personalResponse && Array.isArray(personalResponse.data)) {
          setPersonalPhotos(personalResponse.data);
        } else if (Array.isArray(personalResponse)) {
          setPersonalPhotos(personalResponse);
        }
      } catch (err) {
        console.error("Failed to fetch photos", err);
      } finally {
        setLoadingPhotos(false);
      }
    };

    fetchCharacter();
    fetchPhotos();
  }, [characterId]);

  useEffect(() => {
    navigation.setOptions({
      headerTitle: characterName,
      headerStyle: { backgroundColor: "#1e1b4b" }, // indigo-950
      headerTintColor: "#fff",
    });
  }, [characterName, navigation]);

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
      </View>
    );
  }

  if (!character) return null;

  const trustPercentage = Math.min(Math.round((character.trust_score || 0) / 10), 100);
  const favorite = isFavorite(character.id);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatarContainer}>
            <Image source={{ uri: getFullImageUrl(character.avatar_url) }} style={styles.avatar} />
            <TouchableOpacity
              style={[styles.favoriteButton, favorite && styles.favoriteButtonActive]}
              onPress={() => toggleFavorite(character.id)}
            >
              <Heart size={24} color={favorite ? "#ef4444" : "white"} fill={favorite ? "#ef4444" : "transparent"} />
            </TouchableOpacity>
          </View>
          <View style={styles.infoContainer}>
            <View style={styles.nameRow}>
              <Text style={styles.name}>{character.display_name || character.name}</Text>
              {character.is_hot && (
                <View style={styles.hotBadge}>
                  <Flame size={14} color="#fca5a5" />
                  <Text style={styles.hotText}>Hot</Text>
                </View>
              )}
            </View>
            <Text style={styles.archetype}>{character.archetype}</Text>
            <Text style={styles.bio}>{character.biography}</Text>

            {/* Trust Bar */}
            <View style={styles.trustContainer}>
              <View style={styles.trustHeader}>
                <Text style={styles.trustLabel}>Trust</Text>
                <Text style={styles.trustValue}>{trustPercentage}%</Text>
              </View>
              <View style={styles.progressBar}>
                <View style={[styles.progressFill, { width: `${trustPercentage}%` }]} />
              </View>
            </View>

            <TouchableOpacity
              style={styles.chatButton}
              onPress={() =>
                navigation.navigate("Chat", {
                  characterId: character.id,
                  characterName: character.display_name || character.name,
                })
              }
            >
              <MessageCircle size={20} color="white" style={{ marginRight: 8 }} />
              <Text style={styles.chatButtonText}>Chat</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Tabs */}
        <View style={styles.tabContainer}>
          <TouchableOpacity
            onPress={() => setActiveTab("public")}
            style={[styles.tab, activeTab === "public" && styles.activeTab]}
          >
            <Text style={[styles.tabText, activeTab === "public" && styles.activeTabText]}>
              Gallery ({photos.length})
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => setActiveTab("private")}
            style={[styles.tab, activeTab === "private" && styles.activeTab]}
          >
            <Text style={[styles.tabText, activeTab === "private" && styles.activeTabText]}>
              Private Gallery ({personalPhotos.length})
            </Text>
          </TouchableOpacity>
        </View>

        {/* Gallery Content */}
        <View style={styles.galleryContainer}>
          {loadingPhotos ? (
            <ActivityIndicator size="small" color="#a855f7" />
          ) : (
            <View style={styles.photoGrid}>
              {activeTab === "public" ? (
                photos.length > 0 ? (
                  photos.map((item) => (
                    <TouchableOpacity
                      key={item.id}
                      style={styles.photoWrapper}
                      onPress={() => !item.is_locked && openImageViewer(item.thumbnail_url || item.media_url)}
                      activeOpacity={item.is_locked ? 1 : 0.7}
                    >
                      <Image
                        source={{ uri: getFullImageUrl(item.thumbnail_url || item.media_url) }}
                        style={styles.photo}
                        blurRadius={item.is_locked ? 15 : 0}
                      />
                      {item.is_locked && (
                        <View style={styles.lockOverlay}>
                          <View style={styles.lockCircle}>
                            <Lock size={20} color="white" />
                          </View>
                          <Text style={styles.lockText}>{item.unlock_requirement}</Text>
                        </View>
                      )}
                      <View style={styles.typeIcon}>
                        {item.type === "video" ? <Video size={12} color="white" /> : <ImageIcon size={12} color="white" />}
                      </View>
                    </TouchableOpacity>
                  ))
                ) : (
                  <View style={styles.emptyGallery}>
                    <ImageIcon size={48} color="rgba(168, 85, 247, 0.4)" />
                    <Text style={styles.emptyText}>No available content yet</Text>
                  </View>
                )
              ) : (
                personalPhotos.length > 0 ? (
                  personalPhotos.map((imgUrl, index) => (
                    <TouchableOpacity
                      key={index}
                      style={styles.photoWrapper}
                      onPress={() => openImageViewer(imgUrl)}
                    >
                      <Image source={{ uri: getFullImageUrl(imgUrl) }} style={styles.photo} />
                    </TouchableOpacity>
                  ))
                ) : (
                  <View style={styles.emptyGallery}>
                    <ImageIcon size={48} color="rgba(168, 85, 247, 0.4)" />
                    <Text style={styles.emptyText}>Engage with the character in chat to generate photos!</Text>
                  </View>
                )
              )}
            </View>
          )}
        </View>
      </ScrollView>

      {/* Full Screen Image Viewer */}
      <Modal
        visible={isViewerVisible}
        transparent={true}
        onRequestClose={() => setIsViewerVisible(false)}
        animationType="fade"
      >
        <SafeAreaView style={styles.viewerContainer}>
          <TouchableOpacity
            style={styles.closeButton}
            onPress={() => setIsViewerVisible(false)}
          >
            <X size={30} color="white" />
          </TouchableOpacity>
          {selectedImage && (
            <Image
              source={{ uri: selectedImage }}
              style={styles.fullImage}
              resizeMode="contain"
            />
          )}
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#0f172a",
  },
  profileHeader: {
    padding: 20,
    flexDirection: "column",
    alignItems: "center",
  },
  avatar: {
    width: width - 40,
    height: width - 40,
    borderRadius: 20,
    marginBottom: 20,
  },
  avatarContainer: {
    position: "relative",
  },
  favoriteButton: {
    position: "absolute",
    top: 15,
    right: 15,
    backgroundColor: "rgba(0, 0, 0, 0.4)",
    padding: 10,
    borderRadius: 25,
    zIndex: 10,
  },
  favoriteButtonActive: {
    backgroundColor: "rgba(255, 255, 255, 0.9)",
  },
  infoContainer: {
    width: "100%",
  },
  nameRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 4,
    gap: 8,
  },
  name: {
    fontSize: 32,
    fontWeight: "bold",
    color: "white",
  },
  hotBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(239, 68, 68, 0.2)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "rgba(239, 68, 68, 0.3)",
  },
  hotText: {
    color: "#fca5a5",
    fontSize: 12,
    fontWeight: "bold",
    marginLeft: 4,
  },
  archetype: {
    fontSize: 18,
    color: "#d8b4fe",
    marginBottom: 12,
  },
  bio: {
    fontSize: 16,
    color: "#cbd5e1",
    lineHeight: 24,
    marginBottom: 20,
  },
  trustContainer: {
    marginBottom: 20,
  },
  trustHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  trustLabel: {
    color: "#d8b4fe",
    fontSize: 14,
  },
  trustValue: {
    color: "white",
    fontWeight: "bold",
  },
  progressBar: {
    height: 12,
    backgroundColor: "rgba(255, 255, 255, 0.1)",
    borderRadius: 6,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#a855f7",
    borderRadius: 6,
  },
  chatButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#a855f7",
    paddingVertical: 14,
    borderRadius: 16,
    marginTop: 8,
  },
  chatButtonText: {
    color: "white",
    fontSize: 18,
    fontWeight: "bold",
  },
  tabContainer: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255, 255, 255, 0.1)",
    marginTop: 20,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center",
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: "#a855f7",
  },
  tabText: {
    color: "#94a3b8",
    fontSize: 16,
    fontWeight: "500",
  },
  activeTabText: {
    color: "white",
  },
  galleryContainer: {
    padding: 20,
    minHeight: 200,
  },
  emptyGallery: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 40,
  },
  emptyText: {
    color: "#94a3b8",
    textAlign: "center",
    marginTop: 12,
    fontSize: 14,
  },
  photoGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "flex-start",
    gap: 8,
  },
  photoWrapper: {
    width: (width - 40 - 16) / 3,
    aspectRatio: 1,
    borderRadius: 8,
    overflow: "hidden",
    backgroundColor: "rgba(255, 255, 255, 0.05)",
  },
  photo: {
    width: "100%",
    height: "100%",
  },
  lockOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0, 0, 0, 0.6)",
    justifyContent: "center",
    alignItems: "center",
    padding: 4,
  },
  lockText: {
    color: "white",
    fontSize: 8,
    textAlign: "center",
    marginTop: 4,
  },
  typeIcon: {
    position: "absolute",
    top: 4,
    left: 4,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    borderRadius: 4,
    padding: 2,
  },
  errorText: {
    color: "#f87171",
    fontSize: 16,
  },
  viewerContainer: {
    flex: 1,
    backgroundColor: "black",
    justifyContent: "center",
    alignItems: "center",
  },
  closeButton: {
    position: "absolute",
    top: 40,
    right: 20,
    zIndex: 10,
    padding: 10,
  },
  fullImage: {
    width: width,
    height: height,
  },
  lockCircle: {
    backgroundColor: "rgba(168, 85, 247, 0.6)",
    padding: 12,
    borderRadius: 30,
    marginBottom: 8,
  },
});

export default CharacterScreen;
