import { useEffect, useRef } from 'react';
import { Platform, PermissionsAndroid, Alert } from 'react-native';
import messaging from '@react-native-firebase/messaging';
import userService from '../services/userService';
import { useAuthStore } from '../store/authStore';
import { navigationRef } from '../navigation/RootNavigator';

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

  const handleNotificationTap = (remoteMessage) => {
    const { data } = remoteMessage;
    console.log('Notification tapped:', data);

    if (data?.character_id && data?.type === 're_engagement') {
      const nav = navigationRef.current;
      if (nav) {
        nav.navigate('Chat', {
          characterId: data.character_id,
          characterName: remoteMessage.notification?.title || 'Character',
        });
      }
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

      const unsubscribe = messaging().onMessage(async remoteMessage => {
        console.log('A new FCM message arrived!', JSON.stringify(remoteMessage));
        Alert.alert(
          remoteMessage.notification?.title || 'New Message',
          remoteMessage.notification?.body || '',
          [
            { text: 'Ignore', style: 'cancel' },
            {
              text: 'Open',
              onPress: () => handleNotificationTap(remoteMessage),
            },
          ]
        );
      });

      messaging().onNotificationOpenedApp(handleNotificationTap);

      const checkInitialNotification = async () => {
        const initialNotification = await messaging().getInitialNotification();
        if (initialNotification) {
          handleNotificationTap(initialNotification);
        }
      };
      checkInitialNotification();

      return unsubscribe;
    }
  }, [isAuthenticated]);
};
