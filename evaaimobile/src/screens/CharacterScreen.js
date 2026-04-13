import React, { useState, useEffect } from "react";
import { View, Text, StyleSheet, ActivityIndicator, Image, ScrollView, Button } from "react-native";
import characterService from "../services/characterService";

const CharacterScreen = ({ route, navigation }) => {
  const { characterId, characterName } = route.params;
  const [character, setCharacter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

    fetchCharacter();
  }, [characterId]);

  useEffect(() => {
    // Set the header title
    navigation.setOptions({ title: characterName });
  }, [characterName, navigation]);

  if (loading) {
    return <ActivityIndicator size="large" style={styles.loader} />;
  }

  if (error) {
    return <Text style={styles.error}>Error: {error}</Text>;
  }

  if (!character) {
    return null;
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Image source={{ uri: character.avatar_url }} style={styles.avatar} />
      <Text style={styles.name}>{character.name}</Text>
      <Text style={styles.archetype}>{character.archetype}</Text>
      <Text style={styles.bio}>{character.biography}</Text>
      <Button 
        title="Start Chat" 
        onPress={() => navigation.navigate("Chat", { characterId: character.id, characterName: character.name })} 
      />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    padding: 20,
  },
  avatar: {
    width: 150,
    height: 150,
    borderRadius: 75,
    marginBottom: 20,
  },
  name: {
    fontSize: 28,
    fontWeight: "bold",
  },
  archetype: {
    fontSize: 18,
    color: "gray",
    marginBottom: 20,
  },
  bio: {
    fontSize: 16,
    textAlign: "center",
    marginBottom: 20,
  },
  loader: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  error: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    textAlign: "center",
    color: "red",
    fontSize: 16,
  },
});

export default CharacterScreen;
