import React, { useEffect, createRef } from "react";
import { View, ActivityIndicator, Text, TouchableOpacity } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { Heart, User } from "lucide-react-native";
import { useAuthStore } from "../store/authStore";
import { useNotifications } from "../hooks/useNotifications";
import apiClient from "../services/apiClient";
import { GoogleSignin } from '@react-native-google-signin/google-signin';

import LoginScreen from "../screens/LoginScreen";
import MainScreen from "../screens/MainScreen";
import CharacterScreen from "../screens/CharacterScreen";
import ChatScreen from "../screens/ChatScreen";
import ProfileScreen from "../screens/ProfileScreen";
import FavoritesScreen from "../screens/FavoritesScreen";

const Stack = createNativeStackNavigator();

export const navigationRef = createRef();

const RootNavigator = () => {
  const token = useAuthStore(state => state.token);
  const hydrated = useAuthStore(state => state._hasHydrated);

  // Initialize notifications
  useNotifications();

  useEffect(() => {
    GoogleSignin.configure({
      webClientId: "915322282890-icdovedtf3n5rvl4ues81l205qcb3mhu.apps.googleusercontent.com",
      scopes: ["profile", "email"],
    });
    console.log("RootNavigator: Google Sign-In configured");
  }, []);

  useEffect(() => {
    console.log("RootNavigator Status: hydrated =", hydrated, "hasToken =", !!token);

    // Аварийный пропуск загрузки
    const t = setTimeout(() => {
      if (!hydrated) {
        console.log("RootNavigator: Auto-starting after timeout");
        useAuthStore.setState({ _hasHydrated: true });
      }
    }, 2000);

    return () => clearTimeout(t);
  }, [hydrated]);

  useEffect(() => {
    if (hydrated && token) {
      apiClient.get("/auth/me")
        .catch(err => {
          if (err.response?.status === 401) {
            console.log("RootNavigator: 401 on /auth/me, forcing logout");
            useAuthStore.getState().forceLogout();
          }
        });
    }
  }, [hydrated, token]);

  // Вместо early return мы всегда рендерим NavigationContainer,
  // но внутри него показываем либо загрузку, либо основные экраны.
  return (
    <NavigationContainer ref={navigationRef}>
      {!hydrated ? (
        <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0f172a" }}>
          <ActivityIndicator size="large" color="#a855f7" />
          <Text style={{ color: "white", marginTop: 20 }}>EVA AI</Text>
        </View>
      ) : (
        <Stack.Navigator screenOptions={{ animation: "fade" }}>
          {!token ? (
            <Stack.Screen
              name="Login"
              component={LoginScreen}
              options={{ headerShown: false }}
            />
          ) : (
            <>
              <Stack.Screen
                name="Main"
                component={MainScreen}
                options={({ navigation }) => ({
                  headerTitle: "EVA AI",
                  headerStyle: { backgroundColor: "#1e1b4b" },
                  headerTintColor: "#fff",
                  headerTitleStyle: { fontWeight: "bold", fontSize: 20 },
                  headerRight: () => (
                    <View style={{ flexDirection: "row", alignItems: "center" }}>
                      <TouchableOpacity
                        onPress={() => navigation.navigate("Favorites")}
                        style={{ marginRight: 15 }}
                      >
                        <Heart color="#fff" size={24} />
                      </TouchableOpacity>
                      <TouchableOpacity
                        onPress={() => navigation.navigate("Profile")}
                        style={{ marginRight: 10 }}
                      >
                        <User color="#fff" size={24} />
                      </TouchableOpacity>
                    </View>
                  ),
                })}
              />
              <Stack.Screen name="Favorites" component={FavoritesScreen} options={{ title: "Favorites", headerStyle: { backgroundColor: "#1e1b4b" }, headerTintColor: "#fff" }} />
              <Stack.Screen name="Character" component={CharacterScreen} options={({ route }) => ({ title: route.params.characterName || "Character", headerStyle: { backgroundColor: "#1e1b4b" }, headerTintColor: "#fff" })} />
              <Stack.Screen name="Chat" component={ChatScreen} options={({ route }) => ({ title: route.params.characterName || "Chat", headerStyle: { backgroundColor: "#1e1b4b" }, headerTintColor: "#fff" })} />
              <Stack.Screen name="Profile" component={ProfileScreen} options={{ title: "Profile", headerStyle: { backgroundColor: "#1e1b4b" }, headerTintColor: "#fff" }} />
            </>
          )}
        </Stack.Navigator>
      )}
    </NavigationContainer>
  );
};

export default RootNavigator;
