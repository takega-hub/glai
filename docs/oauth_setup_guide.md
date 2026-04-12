# Настройка Google и Apple авторизации

## 📋 Требования

### Google Sign-In
- Google Developer Console проект
- OAuth 2.0 клиентские ID для iOS и Android
- Web Client ID для backend

### Apple Sign-In
- Apple Developer аккаунт
- iOS 13.0+ (Apple Sign-In требуется iOS 13 или выше)
- Xcode 11+

## 🔧 Настройка Google Sign-In

### 1. Создание проекта в Google Cloud Console

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google+ API
4. Создайте OAuth 2.0 клиентские ID:
   - Для iOS: Укажите Bundle ID вашего приложения
   - Для Android: Укажите SHA-1 fingerprint и package name
   - Для Web: Укажите authorized redirect URIs

### 2. Обновление конфигурации

Замените `YOUR_GOOGLE_WEB_CLIENT_ID`, `YOUR_IOS_CLIENT_ID`, и `YOUR_ANDROID_CLIENT_ID` в файле `/src/services/authService.js`:

```javascript
GoogleSignin.configure({
  webClientId: "YOUR_ACTUAL_WEB_CLIENT_ID.apps.googleusercontent.com",
  iosClientId: "YOUR_ACTUAL_IOS_CLIENT_ID.apps.googleusercontent.com",
  androidClientId: "YOUR_ACTUAL_ANDROID_CLIENT_ID.apps.googleusercontent.com",
  offlineAccess: false,
});
```

### 3. Настройка iOS (дополнительно)

Добавьте в `ios/YourApp/Info.plist`:

```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array>
      <string>com.googleusercontent.apps.YOUR_IOS_CLIENT_ID</string>
    </array>
  </dict>
</array>
```

### 4. Настройка Android (дополнительно)

Убедитесь, что `android/app/google-services.json` существует и содержит правильную конфигурацию.

## 🍎 Настройка Apple Sign-In

### 1. Настройка в Apple Developer Console

1. Перейдите в [Apple Developer Portal](https://developer.apple.com/)
2. Создайте App ID с включенной capability "Sign In with Apple"
3. Создайте Provisioning Profile с этим App ID

### 2. Настройка Xcode

1. Откройте проект в Xcode
2. Выберите ваш target
3. Перейдите в "Signing & Capabilities"
4. Нажмите "+ Capability" и добавьте "Sign In with Apple"

### 3. Настройка entitlements

Убедитесь, что `ios/YourApp/YourApp.entitlements` содержит:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.developer.applesignin</key>
    <array>
        <string>Default</string>
    </array>
</dict>
</plist>
```

## 🔧 Настройка Backend

### 1. Обновление переменных окружения

Добавьте в `.env` файл:

```env
GOOGLE_CLIENT_ID=your_google_web_client_id.apps.googleusercontent.com
APPLE_TEAM_ID=your_apple_team_id
APPLE_KEY_ID=your_apple_key_id
APPLE_PRIVATE_KEY_PATH=path/to/your/apple/private/key
```

### 2. Обновление Google Client ID в коде

В файле `/api/auth/oauth_service.py` замените:

```python
self.google_client_id = "YOUR_ACTUAL_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
```

## 🚀 Установка зависимостей

### Установка React Native зависимостей

```bash
cd evaaimobile
npm install

# Для iOS
cd ios && pod install && cd ..

# Для Android
# Ничего дополнительного не требуется
```

### Установка Python зависимостей

```bash
cd api
pip install -r requirements.txt
```

## 🧪 Тестирование

### Тест Google Sign-In

1. Запустите приложение
2. Нажмите кнопку "Continue with Google"
3. Выберите Google аккаунт
4. Подтвердите разрешения

### Тест Apple Sign-In (только iOS)

1. Запустите приложение на iOS устройстве/симуляторе
2. Нажмите кнопку "Continue with Apple"
3. Войдите с помощью Apple ID
4. Подтвердите двухфакторную аутентификацию

## 🔒 Безопасность

### Важные моменты:

1. **Всегда проверяйте токены на backend** - никогда не доверяйте клиентской стороне
2. **Используйте HTTPS** для всех API запросов
3. **Храните client secrets безопасно** - не коммитьте в репозиторий
4. **Используйте правильную валидацию** для всех OAuth токенов
5. **Обновляйте зависимости** регулярно

### Проверка токенов:

Backend автоматически проверяет:
- Подпись токена
- Срок действия токена
- Client ID
- Issuer (Google/Apple)

## 🐛 Решение проблем

### Google Sign-In проблемы:

1. **DEVELOPER_ERROR**: Проверьте client ID и SHA-1 fingerprint
2. **SIGN_IN_CANCELLED**: Пользователь отменил вход
3. **NETWORK_ERROR**: Проверьте интернет соединение

### Apple Sign-In проблемы:

1. **1000**: Неизвестная ошибка, проверьте настройки в Apple Developer Console
2. **1001**: Отменено пользователем
3. **1003**: Неверные credentials

## 📚 Полезные ссылки:

- [Google Sign-In for React Native](https://github.com/react-native-google-signin/google-signin)
- [Apple Sign-In for React Native](https://github.com/invertase/react-native-apple-authentication)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Apple Sign-In Documentation](https://developer.apple.com/documentation/authenticationservices)