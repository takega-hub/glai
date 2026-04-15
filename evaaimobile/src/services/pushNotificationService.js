import firebase from "@react-native-firebase/app";
import messaging from "@react-native-firebase/messaging";
import apiClient from "./apiClient";
import { Platform, Alert } from "react-native";

class PushNotificationService {
  getMessaging() {
    try {
      if (firebase.apps && firebase.apps.length > 0) {
        return messaging();
      }
      return null;
    } catch (error) {
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
        await this.sendTokenToServer(fcmToken);
      }
    } catch (error) {
      console.log("FCM Token error:", error);
    }
  }

  async sendTokenToServer(token) {
    try {
      // Ждем 2 секунды, чтобы сервер успел обновить сессию после логина
      console.log("PushNotificationService: Waiting 2s before registering token...");
      await new Promise(resolve => setTimeout(resolve, 2000));

      await apiClient.post("/notifications/register-device", {
        device_token: token,
        device_type: Platform.OS,
      }, { skipAuthError: true });
      console.log("Push token registered successfully");
    } catch (error) {
      console.log("Push token registration failed (ignored):", error.message);
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
