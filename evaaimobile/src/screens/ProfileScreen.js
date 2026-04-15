import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  TextInput,
  Switch,
  Alert,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import {
  User,
  Mail,
  Edit,
  Save,
  X,
  Bell,
  Moon,
  Lock,
  CreditCard,
  History,
  ChevronRight,
  TrendingUp,
  MessageSquare,
  Heart,
  Smile,
  HelpCircle,
} from "lucide-react-native";
import { useAuthStore } from "../store/authStore";
import { launchImageLibrary } from "react-native-image-picker";
import userService from "../services/userService";
import authService from "../services/authService";
import chatService from "../services/chatService";

const ProfileScreen = () => {
  const { user, token, setAuth, logout } = useAuthStore();
  const [balance, setBalance] = useState(user?.tokens || 0);
  const clearAuth = logout;
  const [isEditing, setIsEditing] = useState(false);
  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const [about, setAbout] = useState(user?.about || "");
  const [emailNotifications, setEmailNotifications] = useState(user?.email_notifications ?? true);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [packages, setPackages] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const profileData = await userService.getUserProfile();
        setDisplayName(profileData.display_name || "");
        setAbout(profileData.about || "");
        setEmailNotifications(profileData.email_notifications ?? true);
      } catch (error) {
        console.error("Failed to fetch profile data", error);
      }

      try {
        const balanceData = await chatService.getBalance();
        setBalance(balanceData.balance);
      } catch (error) {
        console.error("Failed to fetch balance", error);
      }

      try {
        const historyData = await userService.getHistory();
        setHistory(Array.isArray(historyData) ? historyData : (historyData?.history || []));
      } catch (error) {
        console.error("Failed to fetch history", error);
        setHistory([]);
      }

      try {
        const packagesData = await userService.getPackages();
        setPackages(Array.isArray(packagesData) ? packagesData : (packagesData?.packages || []));
      } catch (error) {
        console.error("Failed to fetch packages", error);
        setPackages([]);
      }
    };

    fetchData();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      const response = await userService.updateUserProfile({
        display_name: displayName,
        about: about
      });
      const updatedUser = { ...user, ...response };
      setAuth(token, updatedUser);
      setIsEditing(false);
      Alert.alert("Success", "Profile updated successfully");
    } catch (error) {
      Alert.alert("Error", "Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarChange = () => {
    launchImageLibrary({ mediaType: "photo", quality: 0.8 }, async (response) => {
      if (response.assets && response.assets[0]) {
        const asset = response.assets[0];
        try {
          setLoading(true);
          const responseData = await userService.uploadAvatar(asset.uri);
          const updatedUser = { ...user, avatar_url: responseData.avatar_url };
          setAuth(token, updatedUser);
          Alert.alert("Success", "Avatar updated successfully");
        } catch (error) {
          Alert.alert("Error", "Failed to upload avatar");
        } finally {
          setLoading(false);
        }
      }
    });
  };

  const handleEmailNotificationsToggle = async (value) => {
    setEmailNotifications(value);
    try {
      await userService.updateEmailNotifications(value);
    } catch (error) {
      setEmailNotifications(!value);
      Alert.alert("Error", "Failed to update notification settings");
    }
  };

  if (!user) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#a855f7" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Profile Header Card */}
        <View style={styles.card}>
          <View style={styles.headerRow}>
            <Text style={styles.cardTitle}>Profile</Text>
            {!isEditing ? (
              <TouchableOpacity
                style={styles.editButton}
                onPress={() => setIsEditing(true)}
              >
                <Edit size={18} color="white" />
                <Text style={styles.editButtonText}>Edit</Text>
              </TouchableOpacity>
            ) : (
              <View style={styles.actionButtons}>
                <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
                  <Save size={18} color="white" />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={() => setIsEditing(false)}
                >
                  <X size={18} color="white" />
                </TouchableOpacity>
              </View>
            )}
          </View>

          <View style={styles.profileInfo}>
            <TouchableOpacity
              style={styles.avatarContainer}
              onPress={isEditing ? handleAvatarChange : null}
              disabled={!isEditing}
            >
              <View style={styles.avatarGradient}>
                {user.avatar_url ? (
                  <Image source={{ uri: user.avatar_url }} style={styles.avatarImage} />
                ) : (
                  <User size={48} color="white" />
                )}
              </View>
              {isEditing && (
                <View style={styles.avatarEditBadge}>
                  <Edit size={12} color="white" />
                </View>
              )}
            </TouchableOpacity>

            <View style={styles.nameContainer}>
              {isEditing ? (
                <View style={styles.inputWrapper}>
                  <Text style={styles.inputLabel}>Name</Text>
                  <TextInput
                    style={styles.textInput}
                    value={displayName}
                    onChangeText={setDisplayName}
                    placeholder="Your name"
                    placeholderTextColor="rgba(216, 180, 254, 0.5)"
                  />
                </View>
              ) : (
                <>
                  <Text style={styles.userName}>{user.display_name || "User"}</Text>
                  <View style={styles.emailRow}>
                    <Mail size={14} color="#d8b4fe" />
                    <Text style={styles.userEmail}>{user.email}</Text>
                  </View>
                </>
              )}
            </View>
          </View>
        </View>

        {/* Tokens Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <CreditCard size={20} color="#a855f7" />
            <Text style={styles.sectionTitle}>Tokens</Text>
          </View>
          <View style={styles.balanceCard}>
            <Text style={styles.balanceLabel}>Current balance</Text>
            <View style={styles.balanceRow}>
              <Text style={styles.balanceValue}>{balance}</Text>
              <Text style={styles.balanceUnit}>tokens</Text>
            </View>
            <Text style={styles.balanceSub}>1 token = 1 message</Text>
          </View>

          {/* Top up balance */}
          <Text style={styles.subSectionTitle}>Top up balance</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.packagesScroll}>
            {Array.isArray(packages) && packages.map((pkg) => (
              <View key={pkg.id || pkg._id} style={styles.packageCard}>
                <Text style={styles.packageName}>{pkg.name}</Text>
                <Text style={styles.packageTokens}>{pkg.token_amount}</Text>
                <Text style={styles.packageUnit}>tokens</Text>
                <Text style={styles.packagePrice}>${pkg.price_usd}</Text>
                <TouchableOpacity style={styles.buyButton}>
                  <Text style={styles.buyButtonText}>Buy</Text>
                </TouchableOpacity>
              </View>
            ))}
          </ScrollView>

          {/* Transaction History */}
          <View style={styles.historyContainer}>
            <View style={styles.historyHeader}>
              <History size={18} color="#a855f7" />
              <Text style={styles.historyTitle}>Transaction History</Text>
            </View>
            {!Array.isArray(history) || history.length === 0 ? (
              <Text style={styles.emptyHistory}>No transactions</Text>
            ) : (
              history.map((tx) => (
                <View key={tx.id || tx._id} style={styles.historyItem}>
                  <View>
                    <Text style={styles.historyDate}>{new Date(tx.created_at).toLocaleDateString()}</Text>
                    <Text style={styles.historyDesc}>{tx.description}</Text>
                  </View>
                  <Text style={[styles.historyAmount, tx.token_amount > 0 ? styles.positiveAmount : styles.negativeAmount]}>
                    {tx.token_amount > 0 ? `+${tx.token_amount}` : tx.token_amount}
                  </Text>
                </View>
              ))
            )}
          </View>
        </View>

        {/* Settings Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <View style={styles.headerAccent} />
            <Text style={styles.sectionTitle}>Settings</Text>
          </View>

          <View style={styles.settingsList}>
            <TouchableOpacity style={styles.settingItem}>
              <View style={styles.settingInfo}>
                <Lock size={20} color="#a855f7" />
                <View style={styles.settingTextContainer}>
                  <Text style={styles.settingTitle}>Change password</Text>
                  <Text style={styles.settingSub}>Update your password periodically</Text>
                </View>
              </View>
              <ChevronRight size={20} color="#475569" />
            </TouchableOpacity>

            <View style={styles.settingItem}>
              <View style={styles.settingInfo}>
                <Bell size={20} color="#a855f7" />
                <View style={styles.settingTextContainer}>
                  <Text style={styles.settingTitle}>Email notifications</Text>
                  <Text style={styles.settingSub}>Receive updates and news</Text>
                </View>
              </View>
              <Switch
                value={emailNotifications}
                onValueChange={handleEmailNotificationsToggle}
                trackColor={{ false: "#334155", true: "#a855f7" }}
                thumbColor="white"
              />
            </View>

            <TouchableOpacity style={styles.settingItem}>
              <View style={styles.settingInfo}>
                <Moon size={20} color="#a855f7" />
                <View style={styles.settingTextContainer}>
                  <Text style={styles.settingTitle}>Dark Theme</Text>
                  <Text style={styles.settingSub}>Switch between light and dark</Text>
                </View>
              </View>
              <Switch
                value={true}
                disabled
                trackColor={{ false: "#334155", true: "#a855f7" }}
                thumbColor="white"
              />
            </TouchableOpacity>
          </View>
        </View>

        {/* Trust Info Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <TrendingUp size={20} color="#a855f7" />
            <Text style={styles.sectionTitle}>How to increase trust?</Text>
          </View>
          <Text style={styles.sectionDescription}>
            Trust affects the depth of communication and exclusive content.
          </Text>
          <View style={styles.trustActionsGrid}>
            {[
              { icon: MessageSquare, text: "Regular message", points: "+3" },
              { icon: Heart, text: "Compliment", points: "+5" },
              { icon: Smile, text: "Showing empathy", points: "+8" },
              { icon: HelpCircle, text: "Deep question", points: "+10" },
            ].map((action, index) => {
              const IconComponent = action.icon;
              return (
                <View key={index} style={styles.trustActionItem}>
                  <View style={styles.trustActionLeft}>
                    {IconComponent ? <IconComponent size={18} color="#a855f7" /> : <View style={{width: 18, height: 18}} />}
                    <Text style={styles.trustActionText}>{action.text}</Text>
                  </View>
                  <Text style={styles.trustActionPoints}>{action.points}</Text>
                </View>
              );
            })}
          </View>
        </View>

        <TouchableOpacity
          style={styles.logoutButton}
          onPress={async () => {
            try {
              await authService.logout();
            } catch (error) {
              console.error("Logout error", error);
            } finally {
              clearAuth();
            }
          }}
        >
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>

        <View style={styles.footer}>
          <Text style={styles.footerText}>© 2026 GL AI. All rights reserved.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#0f172a",
  },
  card: {
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderRadius: 24,
    padding: 24,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
    marginBottom: 24,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 24,
  },
  cardTitle: {
    fontSize: 28,
    fontWeight: "bold",
    color: "white",
  },
  editButton: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#a855f7",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
    gap: 6,
  },
  editButtonText: {
    color: "white",
    fontWeight: "600",
  },
  actionButtons: {
    flexDirection: "row",
    gap: 8,
  },
  saveButton: {
    backgroundColor: "#22c55e",
    padding: 10,
    borderRadius: 12,
  },
  cancelButton: {
    backgroundColor: "rgba(255, 255, 255, 0.1)",
    padding: 10,
    borderRadius: 12,
  },
  profileInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 20,
  },
  avatarContainer: {
    position: "relative",
  },
  avatarGradient: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: "#581c87",
    justifyContent: "center",
    alignItems: "center",
    overflow: "hidden",
  },
  avatarImage: {
    width: "100%",
    height: "100%",
  },
  avatarEditBadge: {
    position: "absolute",
    bottom: 0,
    right: 0,
    backgroundColor: "#a855f7",
    padding: 6,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: "#0f172a",
  },
  nameContainer: {
    flex: 1,
  },
  userName: {
    fontSize: 24,
    fontWeight: "bold",
    color: "white",
    marginBottom: 4,
  },
  emailRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  userEmail: {
    color: "#d8b4fe",
    fontSize: 16,
  },
  inputWrapper: {
    gap: 4,
  },
  inputLabel: {
    color: "#d8b4fe",
    fontSize: 12,
  },
  textInput: {
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.2)",
    borderRadius: 12,
    color: "white",
    paddingHorizontal: 12,
    height: 44,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginBottom: 16,
  },
  headerAccent: {
    width: 4,
    height: 24,
    backgroundColor: "#a855f7",
    borderRadius: 2,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: "bold",
    color: "white",
  },
  balanceCard: {
    backgroundColor: "rgba(168, 85, 247, 0.1)",
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: "rgba(168, 85, 247, 0.2)",
  },
  balanceLabel: {
    color: "#d8b4fe",
    fontSize: 14,
    marginBottom: 8,
  },
  balanceRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 8,
    marginBottom: 4,
  },
  balanceValue: {
    fontSize: 36,
    fontWeight: "bold",
    color: "white",
  },
  balanceUnit: {
    fontSize: 18,
    color: "#d8b4fe",
  },
  balanceSub: {
    color: "rgba(216, 180, 254, 0.6)",
    fontSize: 12,
  },
  subSectionTitle: {
    color: "white",
    fontSize: 18,
    fontWeight: "600",
    marginTop: 20,
    marginBottom: 12,
  },
  packagesScroll: {
    marginHorizontal: -16,
    paddingHorizontal: 16,
  },
  packageCard: {
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderRadius: 16,
    padding: 16,
    width: 140,
    marginRight: 12,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  packageName: {
    color: "white",
    fontSize: 14,
    fontWeight: "bold",
  },
  packageTokens: {
    color: "#a855f7",
    fontSize: 24,
    fontWeight: "bold",
    marginTop: 8,
  },
  packageUnit: {
    color: "#d8b4fe",
    fontSize: 12,
  },
  packagePrice: {
    color: "white",
    fontSize: 18,
    fontWeight: "bold",
    marginVertical: 12,
  },
  buyButton: {
    backgroundColor: "#a855f7",
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    width: "100%",
    alignItems: "center",
  },
  buyButtonText: {
    color: "white",
    fontWeight: "bold",
  },
  historyContainer: {
    marginTop: 24,
  },
  historyHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 12,
  },
  historyTitle: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  emptyHistory: {
    color: "#94a3b8",
    textAlign: "center",
    paddingVertical: 20,
  },
  historyItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255, 255, 255, 0.05)",
  },
  historyDate: {
    color: "#94a3b8",
    fontSize: 12,
  },
  historyDesc: {
    color: "white",
    fontSize: 14,
    marginTop: 2,
  },
  historyAmount: {
    fontWeight: "bold",
    fontSize: 16,
  },
  positiveAmount: {
    color: "#4ade80",
  },
  negativeAmount: {
    color: "#f87171",
  },
  settingsList: {
    gap: 12,
  },
  settingItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    padding: 16,
    borderRadius: 16,
  },
  settingInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    flex: 1,
  },
  settingTextContainer: {
    flex: 1,
  },
  settingTitle: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  settingSub: {
    color: "#94a3b8",
    fontSize: 12,
  },
  sectionDescription: {
    color: "#d8b4fe",
    fontSize: 14,
    marginBottom: 16,
  },
  trustActionsGrid: {
    gap: 10,
  },
  trustActionItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "rgba(255, 255, 255, 0.03)",
    padding: 14,
    borderRadius: 12,
  },
  trustActionLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  trustActionText: {
    color: "white",
    fontSize: 14,
  },
  trustActionPoints: {
    color: "#4ade80",
    fontWeight: "bold",
    fontSize: 14,
  },
  logoutButton: {
    marginTop: 20,
    padding: 16,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(239, 68, 68, 0.3)",
    borderRadius: 16,
  },
  logoutText: {
    color: "#f87171",
    fontSize: 16,
    fontWeight: "bold",
  },
  footer: {
    marginTop: 32,
    alignItems: "center",
  },
  footerText: {
    color: "rgba(216, 180, 254, 0.5)",
    fontSize: 12,
  },
});

export default ProfileScreen;
