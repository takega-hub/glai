import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  SafeAreaView,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Image,
} from "react-native";
import { Sparkles, Mail, Lock, User as UserIcon } from "lucide-react-native";
import authService from "../services/authService";
import { GoogleSignin, statusCodes } from "@react-native-google-signin/google-signin";
import appleAuth from "@invertase/react-native-apple-authentication";

const LoginScreen = ({ navigation }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    GoogleSignin.configure({
      webClientId: "915322282890-icdovedtf3n5rvl4ues81l205qcb3mhu.apps.googleusercontent.com",
      scopes: ["profile", "email"],
    });
  }, []);

  const handleAuth = async () => {
    if (!email || !password || (!isLogin && !name)) {
      Alert.alert("Error", "Please fill in all fields");
      return;
    }

    setLoading(true);
    try {
      if (isLogin) {
        await authService.login(email, password);
      } else {
        await authService.register(email, password, name);
      }
      navigation.replace("Main");
    } catch (error) {
      console.error("Auth error:", error);
      Alert.alert("Authentication Failed", error.message || "Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    setLoading(true);
    try {
      await authService.loginAsGuest();
      navigation.replace("Main");
    } catch (error) {
      Alert.alert("Error", "Failed to log in as guest");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      await GoogleSignin.hasPlayServices();
      const userInfo = await GoogleSignin.signIn();
      console.log("Google Sign-In response:", JSON.stringify(userInfo));

      const token = userInfo.idToken || (userInfo.data && userInfo.data.idToken);

      if (!token) {
        throw new Error("No ID Token received from Google. Check your Firebase configuration.");
      }

      await authService.socialLogin("google", token);
      navigation.replace("Main");
    } catch (error) {
      if (error.code === statusCodes.SIGN_IN_CANCELLED) {
        console.log("User cancelled Google Sign-in");
      } else if (error.code === statusCodes.IN_PROGRESS) {
        console.log("Google Sign-in already in progress");
      } else if (error.code === statusCodes.PLAY_SERVICES_NOT_AVAILABLE) {
        Alert.alert("Error", "Google Play Services not available or outdated");
      } else if (error.code === statusCodes.DEVELOPER_ERROR) {
        console.error("DEVELOPER_ERROR: Check SHA-1 and Web Client ID in Firebase console");
        Alert.alert("Configuration Error", "Google Sign-In is not configured correctly. Check SHA-1 and Web Client ID.");
      } else {
        console.error("Google login error detail:", JSON.stringify(error));
        Alert.alert("Google Login Error", error.message || "An unexpected error occurred.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAppleLogin = async () => {
    setLoading(true);
    try {
      const appleAuthRequestResponse = await appleAuth.performRequest({
        requestedOperation: appleAuth.Operation.LOGIN,
        requestedScopes: [appleAuth.Scope.EMAIL, appleAuth.Scope.FULL_NAME],
      });

      const { identityToken } = appleAuthRequestResponse;
      if (identityToken) {
        await authService.socialLogin("apple", identityToken);
        navigation.replace("Main");
      }
    } catch (error) {
      if (error.code !== appleAuth.Error.CANCELED) {
        console.error("Apple login error:", error);
        Alert.alert("Error", "Apple login failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
      >
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.card}>
            <View style={styles.header}>
              <View style={styles.logoContainer}>
                <Sparkles size={32} color="white" />
              </View>
              <Text style={styles.title}>
                {isLogin ? "Sign in to account" : "Create an account"}
              </Text>
              <Text style={styles.subtitle}>
                By continuing, you agree to our{" "}
                <Text style={styles.link}>Terms of Use</Text> and{" "}
                <Text style={styles.link}>Privacy Policy</Text>
              </Text>
            </View>

            {/* Social Logins */}
            <View style={styles.socialContainer}>
              {Platform.OS === "ios" && (
                <TouchableOpacity style={styles.socialButton} onPress={handleAppleLogin} disabled={loading}>
                  <Text style={styles.socialButtonText}>Continue with Apple ID</Text>
                </TouchableOpacity>
              )}
              <TouchableOpacity style={[styles.socialButton, styles.googleButton]} onPress={handleGoogleLogin} disabled={loading}>
                <Text style={styles.googleButtonText}>Sign in with Google</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.dividerContainer}>
              <View style={styles.divider} />
              <Text style={styles.dividerText}>or</Text>
              <View style={styles.divider} />
            </View>

            <View style={styles.form}>
              {!isLogin && (
                <View style={styles.inputContainer}>
                  <UserIcon size={20} color="#d8b4fe" style={styles.inputIcon} />
                  <TextInput
                    style={styles.input}
                    placeholder="Name"
                    placeholderTextColor="rgba(216, 180, 254, 0.5)"
                    value={name}
                    onChangeText={setName}
                    editable={!loading}
                  />
                </View>
              )}
              <View style={styles.inputContainer}>
                <Mail size={20} color="#d8b4fe" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Email"
                  placeholderTextColor="rgba(216, 180, 254, 0.5)"
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  editable={!loading}
                />
              </View>
              <View style={styles.inputContainer}>
                <Lock size={20} color="#d8b4fe" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Password"
                  placeholderTextColor="rgba(216, 180, 254, 0.5)"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  editable={!loading}
                />
              </View>

              <TouchableOpacity
                style={[styles.submitButton, loading && styles.disabledButton]}
                onPress={handleAuth}
                disabled={loading}
              >
                <Text style={styles.submitButtonText}>
                  {loading
                    ? isLogin
                      ? "Signing in..."
                      : "Creating..."
                    : isLogin
                    ? "Continue with Email"
                    : "Create account"}
                </Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={styles.guestButton}
              onPress={handleGuestLogin}
              disabled={loading}
            >
              <Text style={styles.guestButtonText}>Log in as guest</Text>
            </TouchableOpacity>

            <View style={styles.footer}>
              <Text style={styles.footerText}>
                {isLogin ? "Don't have an account? " : "Already have an account? "}
              </Text>
              <TouchableOpacity onPress={() => setIsLogin(!isLogin)}>
                <Text style={styles.footerLink}>{isLogin ? "Sign up" : "Sign in"}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a", // slate-900
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 20,
  },
  card: {
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderRadius: 24,
    padding: 24,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  header: {
    alignItems: "center",
    marginBottom: 24,
  },
  logoContainer: {
    padding: 12,
    backgroundColor: "#a855f7", // purple-500 equivalent
    borderRadius: 16,
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    color: "white",
    textAlign: "center",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: "#d8b4fe",
    textAlign: "center",
    lineHeight: 20,
  },
  link: {
    textDecorationLine: "underline",
    color: "white",
  },
  socialContainer: {
    gap: 12,
    marginBottom: 24,
  },
  socialButton: {
    backgroundColor: "rgba(0, 0, 0, 0.3)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.2)",
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: "center",
  },
  socialButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "500",
  },
  googleButton: {
    backgroundColor: "white",
  },
  googleButtonText: {
    color: "#1f2937",
    fontSize: 16,
    fontWeight: "500",
  },
  dividerContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 24,
  },
  divider: {
    flex: 1,
    height: 1,
    backgroundColor: "rgba(255, 255, 255, 0.1)",
  },
  dividerText: {
    marginHorizontal: 12,
    color: "#d8b4fe",
    fontSize: 14,
  },
  form: {
    gap: 16,
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.2)",
    borderRadius: 12,
    paddingHorizontal: 12,
  },
  inputIcon: {
    marginRight: 10,
  },
  input: {
    flex: 1,
    height: 48,
    color: "white",
    fontSize: 16,
  },
  submitButton: {
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.2)",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 8,
  },
  disabledButton: {
    opacity: 0.5,
  },
  submitButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "bold",
  },
  guestButton: {
    marginTop: 24,
    alignItems: "center",
  },
  guestButtonText: {
    color: "#e9d5ff",
    fontSize: 16,
    fontWeight: "600",
  },
  footer: {
    flexDirection: "row",
    justifyContent: "center",
    marginTop: 16,
  },
  footerText: {
    color: "#d8b4fe",
    fontSize: 14,
  },
  footerLink: {
    color: "#e9d5ff",
    fontSize: 14,
    fontWeight: "bold",
  },
});

export default LoginScreen;
