import React, { useEffect } from 'react';
import RootNavigator from './src/navigation/RootNavigator';
import pushNotificationService from './src/services/pushNotificationService';
import { useAuthStore } from './src/store/authStore';

const App = () => {
  const { token } = useAuthStore();

  useEffect(() => {
    // Инициализируем пуши только если пользователь авторизован
    if (token) {
      pushNotificationService.requestUserPermission();

      const unsubscribe = pushNotificationService.onMessageReceived();
      return () => {
        if (unsubscribe) unsubscribe();
      };
    }
  }, [token]);

  return <RootNavigator />;
};

export default App;
