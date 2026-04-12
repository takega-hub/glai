import React, { useState } from "react";
import { View, Text, TextInput, Button, StyleSheet, Alert, TouchableOpacity, Platform } from "react-native";
import authService from "../services/authService";

const LoginScreen = ({ navigation }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    try {
      const data = await authService.login(email, password);
      console.log("Login successful:", data);
      navigation.navigate("Main");
    } catch (error) {
      Alert.alert("Login Failed", "Please check your credentials and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      const data = await authService.loginWithGoogle();
      console.log("Google login successful:", data);
      navigation.navigate("Main");
    } catch (error) {
      Alert.alert("Google Login Failed", error.message || "Failed to login with Google");
    } finally {
      setLoading(false);
    }
  };

  const handleAppleLogin = async () => {
    if (Platform.OS !== 'ios') {
      Alert.alert("Not Available", "Apple Sign-In is only available on iOS devices");
      return;
    }

    setLoading(true);
    try {
      const data = await authService.loginWithApple();
      console.log("Apple login successful:", data);
      navigation.navigate("Main");
    } catch (error) {
      Alert.alert("Apple Login Failed", error.message || "Failed to login with Apple");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome Back</Text>
      
      {/* Email Login */}
      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
        editable={!loading}
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        editable={!loading}
      />
      <Button title={loading ? "Logging in..." : "Login"} onPress={handleLogin} disabled={loading} />
      
      {/* Divider */}
      <View style={styles.dividerContainer}>
        <View style={styles.divider} />
        <Text style={styles.dividerText}>OR</Text>
        <View style={styles.divider} />
      </View>
      
      {/* Social Login Buttons */}
      <TouchableOpacity style={styles.googleButton} onPress={handleGoogleLogin} disabled={loading}>
        <Text style={styles.googleButtonText}>G Continue with Google</Text>
      </TouchableOpacity>
      
      {Platform.OS === 'ios' && (
        <TouchableOpacity style={styles.appleButton} onPress={handleAppleLogin} disabled={loading}>
          <Text style={styles.appleButtonText}>🍎 Continue with Apple</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 20,
  },
  input: {
    width: "100%",
    height: 40,
    borderColor: "gray",
    borderWidth: 1,
    borderRadius: 5,
    marginBottom: 10,
    paddingHorizontal: 10,
  },
  dividerContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginVertical: 20,
    width: "100%",
  },
  divider: {
    flex: 1,
    height: 1,
    backgroundColor: "#ccc",
  },
  dividerText: {
    marginHorizontal: 10,
    color: "#666",
    fontSize: 14,
  },
  googleButton: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 12,
    padding: 14,
    alignItems: "center",
    marginBottom: 10,
    width: "100%",
  },
  googleButtonText: {
    color: "#333",
    fontWeight: "600",
    fontSize: 16,
  },
  appleButton: {
    backgroundColor: "#000",
    borderRadius: 12,
    padding: 14,
    alignItems: "center",
    width: "100%",
  },
  appleButtonText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 16,
  },

export default LoginScreen;
