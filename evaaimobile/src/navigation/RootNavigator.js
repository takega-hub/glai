import React from "react";
import { View, ActivityIndicator, TouchableOpacity } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { User } from "lucide-react-native";
import { useAuthStore } from "../store/authStore";

import LoginScreen from "../screens/LoginScreen";
import MainScreen from "../screens/MainScreen";
import CharacterScreen from "../screens/CharacterScreen";
import ChatScreen from "../screens/ChatScreen";
import ProfileScreen from "../screens/ProfileScreen";
import FavoritesScreen from "../screens/FavoritesScreen";
import { Heart, User } from "lucide-react-native";

const Stack = createNativeStackNavigator();

const RootNavigator = () => {
  const { token } = useAuthStore();

  return (
    <NavigationContainer>
      <Stack.Navigator>
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
                headerTitle: "GL AI",
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
            <Stack.Screen
              name="Favorites"
              component={FavoritesScreen}
              options={{
                title: "Favorites",
                headerStyle: { backgroundColor: "#1e1b4b" },
                headerTintColor: "#fff",
              }}
            />
            <Stack.Screen
              name="Character"
              component={CharacterScreen}
              options={({ route }) => ({
                title: route.params.characterName || "Character",
                headerStyle: { backgroundColor: "#1e1b4b" },
                headerTintColor: "#fff",
              })}
            />
            <Stack.Screen
              name="Chat"
              component={ChatScreen}
              options={({ route }) => ({
                title: route.params.characterName || "Chat",
                headerStyle: { backgroundColor: "#1e1b4b" },
                headerTintColor: "#fff",
              })}
            />
            <Stack.Screen
              name="Profile"
              component={ProfileScreen}
              options={{
                title: "Profile",
                headerStyle: { backgroundColor: "#1e1b4b" },
                headerTintColor: "#fff",
              }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default RootNavigator;
