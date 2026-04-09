import React, { useState, useEffect } from "react";
import { View, ActivityIndicator } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import authService from "../services/authService";

import LoginScreen from "../screens/LoginScreen";
import MainScreen from "../screens/MainScreen";
import CharacterScreen from "../screens/CharacterScreen";
import ChatScreen from "../screens/ChatScreen";

const Stack = createNativeStackNavigator();

const RootNavigator = () => {
  const [loading, setLoading] = useState(true);
  const [initialRoute, setInitialRoute] = useState("Login");

  useEffect(() => {
    const checkToken = async () => {
      const token = await authService.getCurrentUser();
      if (token) {
        setInitialRoute("Main");
      }
      setLoading(false);
    };

    checkToken();
  }, []);

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName={initialRoute}>
        <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
        <Stack.Screen name="Main" component={MainScreen} options={{ title: "Characters" }} />
        <Stack.Screen 
          name="Character" 
          component={CharacterScreen} 
          options={({ route }) => ({ title: route.params.characterName || "Character" })} 
        />
        <Stack.Screen 
          name="Chat" 
          component={ChatScreen} 
          options={({ route }) => ({ title: route.params.characterName || "Chat" })} 
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default RootNavigator;
