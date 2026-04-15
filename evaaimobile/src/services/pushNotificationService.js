import firebase from "@react-native-firebase/app";
import messaging from "@react-native-firebase/messaging";
import apiClient from "./apiClient";
import { Platform, Alert } from "react-native";

class PushNotificationService {
  // Безопасное получение объекта messaging
  getMessaging() {
    try {
      // В RN Firebase 15+ проверка идет через firebase.apps.length
      if (firebase.apps && firebase.apps.length > 0) {
        return messaging();
      }
      console.log("Firebase: No apps initialized yet.");
      return null;
    } catch (error) {
      console.log("Firebase: Messaging not available", error);
      return null;
    }
  }

  async requestUserPermission() {
    const msg = this.getMessaging();
    if (!msg) return;

    try {
      const authStatus = await msg.requestPermission();
      const enabled =
        authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
        authStatus === messaging.AuthorizationStatus.PROVISIONAL;

      if (enabled) {
        await this.getToken();
      }
    } catch (error) {
      console.log("Push permission error:", error);
    }
  }

  async getToken() {
    const msg = this.getMessaging();
    if (!msg) return;

    try {
      const fcmToken = await msg.getToken();
      if (fcmToken) {
        console.log("FCM Token:", fcmToken);
        await this.sendTokenToServer(fcmToken);
      }
    } catch (error) {
      console.log("FCM Token error:", error);
    }
  }

  async sendTokenToServer(token) {
    try {
      await apiClient.post("/notifications/register-device", {
        device_token: token,
        device_type: Platform.OS, // 'android' or 'ios'
      });
      console.log("Push token registered successfully");
    } catch (error) {
      console.error("API error registering push token:", error.response?.data || error.message);
    }
  }

  onMessageReceived() {
    const msg = this.getMessaging();
    if (!msg) return () => {};

    try {
      return msg.onMessage(async (remoteMessage) => {
        Alert.alert(
          remoteMessage.notification?.title || "New Message",
          remoteMessage.notification?.body || ""
        );
      });
    } catch (e) {
      return () => {};
    }
  }
}

export default new PushNotificationService();
