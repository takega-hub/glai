import messaging from "@react-native-firebase/messaging";
import apiClient from "./apiClient";
import { Platform, Alert } from "react-native";

class PushNotificationService {
  async requestUserPermission() {
    const authStatus = await messaging().requestPermission();
    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    if (enabled) {
      console.log("Authorization status:", authStatus);
      await this.getToken();
    }
  }

  async getToken() {
    try {
      const fcmToken = await messaging().getToken();
      if (fcmToken) {
        console.log("FCM Token:", fcmToken);
        await this.sendTokenToServer(fcmToken);
      }
    } catch (error) {
      console.error("Failed to get FCM token:", error);
    }
  }

  async sendTokenToServer(token) {
    try {
      await apiClient.post("/user/push-token", {
        token: token,
        platform: Platform.OS,
      });
      console.log("Push token sent to server successfully");
    } catch (error) {
      console.error("Failed to send push token to server:", error);
    }
  }

  // Обработка уведомлений, когда приложение открыто
  onMessageReceived() {
    return messaging().onMessage(async (remoteMessage) => {
      Alert.alert(
        remoteMessage.notification?.title || "New Message",
        remoteMessage.notification?.body || ""
      );
    });
  }

  // Обработка клика по уведомлению (когда приложение было закрыто)
  async checkInitialNotification(navigation) {
    const remoteMessage = await messaging().getInitialNotification();
    if (remoteMessage) {
      console.log("Notification caused app to open from quit state:", remoteMessage);
      // Здесь можно добавить навигацию в конкретный чат:
      // if (remoteMessage.data.characterId) navigation.navigate('Chat', { ... })
    }
  }
}

export default new PushNotificationService();
