import { useEffect } from 'react';
import { Platform, PermissionsAndroid } from 'react-native';
import messaging from '@react-native-firebase/messaging';
import userService from '../services/userService';
import { useAuthStore } from '../store/authStore';

export const useNotifications = () => {
  const { isAuthenticated } = useAuthStore();

  const requestUserPermission = async () => {
    if (Platform.OS === 'android' && Platform.Version >= 33) {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    }

    const authStatus = await messaging().requestPermission();
    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    return enabled;
  };

  const getFCMToken = async () => {
    try {
      const token = await messaging().getToken();
      if (token) {
        console.log('FCM Token:', token);
        await userService.registerDevice(token);
      }
    } catch (error) {
      console.error('Error getting FCM token:', error);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      const setupNotifications = async () => {
        const hasPermission = await requestUserPermission();
        if (hasPermission) {
          await getFCMToken();
        }
      };

      setupNotifications();

      // Слушатель сообщений, когда приложение открыто
      const unsubscribe = messaging().onMessage(async remoteMessage => {
        console.log('A new FCM message arrived!', JSON.stringify(remoteMessage));
        // Здесь можно показать локальное уведомление, если нужно
      });

      // Слушатель нажатия на уведомление, когда приложение в фоне
      messaging().onNotificationOpenedApp(remoteMessage => {
        console.log('Notification caused app to open from background state:', remoteMessage.notification);
      });

      return unsubscribe;
    }
  }, [isAuthenticated]);
};
