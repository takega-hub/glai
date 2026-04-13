# **МОДУЛЬ АВТОРИЗАЦИИ И ПРОФИЛЯ**

## **Полная спецификация для клиентского приложения**

***

## **📱 ЭКРАН 1: ОНБОРДИНГ (ПЕРВЫЙ ЗАПУСК)**

### **Показывается только один раз при первом запуске**

text

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                         ┌─────────┐                              │
│                         │  🤖     │                              │
│                         │  LOGO   │                              │
│                         └─────────┘                              │
│                                                                  │
│                     ДОБРО ПОЖАЛОВАТЬ                              │
│                                                                  │
│              Погрузись в мир живых AI-персонажей,                │
│              которые раскрывают свои тайны только                │
│                    самым близким.                                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                              ││
│  │  ●─────────●─────────○                                       ││
│  │   Общайся    Флиртуй    Раскрывай                            ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│         ┌─────────────────────────────────────┐                 │
│         │         ▶  ПРОДОЛЖИТЬ                │                 │
│         └─────────────────────────────────────┘                 │
│                                                                  │
│         Уже есть аккаунт? [Войти]                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Слайды онбординга (3-4 шт):**

**Слайд**

**Заголовок**

**Описание**

1

**Общайся**

Начни диалог с AI-персонажем. Каждое сообщение укрепляет вашу связь

2

**Флиртуй**

Будь собой. Искренность и флирт открывают новые горизонты

3

**Раскрывай**

По мере доверия персонаж показывает фото, видео и делится тайнами

4

**Будь близким**

Только избранные узнают самые сокровенные секреты

***

## **🔐 ЭКРАН 2: ВЫБОР МЕТОДА ВХОДА**

text

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                         ┌─────────┐                              │
│                         │  🤖     │                              │
│                         │  LOGO   │                              │
│                         └─────────┘                              │
│                                                                  │
│                   ВОЙДИ ИЛИ ЗАРЕГИСТРИРУЙСЯ                       │
│                                                                  │
│              Продолжив, вы соглашаетесь с нашими                 │
│              [Условиями использования] и [Политикой]             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  🍎           Продолжить с Apple ID                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  G           Продолжить с Google                            ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  ✉️           Продолжить с Email                            ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│         ┌─────────────────────────────────────┐                 │
│         │         ВОЙТИ ПО ГОСТЮ               │                 │
│         └─────────────────────────────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

***

## **👤 ЭКРАН 3: СОЗДАНИЕ ПРОФИЛЯ**

### **После успешной авторизации (первые 10 минут)**

text

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                  СОЗДАЙ СВОЙ ПРОФИЛЬ                              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                              ││
│  │                      ┌─────────┐                            ││
│  │                      │  👤     │                            ││
│  │                      │Добавить │                            ││
│  │                      │ фото    │                            ││
│  │                      └─────────┘                            ││
│  │                                                              ││
│  │   Имя или псевдоним:                                        ││
│  │   ┌─────────────────────────────────────────────────────┐   ││
│  │   │ [Алексей___________________________]                 │   ││
│  │   └─────────────────────────────────────────────────────┘   ││
│  │                                                              ││
│  │   Как к вам обращаться:                                     ││
│  │   ┌─────────────────────────────────────────────────────┐   ││
│  │   │ [Алексей___________________________]                 │   ││
│  │   └─────────────────────────────────────────────────────┘   ││
│  │                                                              ││
│  │   Дата рождения:                                            ││
│  │   ┌─────────────────────────────────────────────────────┐   ││
│  │   │ [15 мая 1995_________________________]               │   ││
│  │   └─────────────────────────────────────────────────────┘   ││
│  │                                                              ││
│  │   О себе (необязательно):                                   ││
│  │   ┌─────────────────────────────────────────────────────┐   ││
│  │   │ [Люблю музыку, путешествия и...]                    │   ││
│  │   └─────────────────────────────────────────────────────┘   ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│         ┌─────────────────────────────────────┐                 │
│         │           ПРОДОЛЖИТЬ                 │                 │
│         └─────────────────────────────────────┘                 │
│                                                                  │
│         ⚠️ Возраст 18+ обязательно для доступа к контенту       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

***

## **🎭 ЭКРАН 4: ВЫБОР ПЕРСОНАЖА (ПОСЛЕ РЕГИСТРАЦИИ)**

text

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                  ВЫБЕРИ СВОЮ ИСТОРИЮ                              │
│                                                                  │
│              Каждый персонаж хранит уникальную тайну             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                              ││
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐                  ││
│  │  │         │    │         │    │         │                  ││
│  │  │   Ева   │    │   Луна  │    │   Макс  │                  ││
│  │  │ Таинств.│    │ Ночная  │    │ Загад.  │                  ││
│  │  │   🎹    │    │   🌙    │    │   🎸    │                  ││
│  │  │ [Выбрать]│    │ [Выбрать]│    │ [Скоро] │                  ││
│  │  └─────────┘    └─────────┘    └─────────┘                  ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 📖 О Еве:                                                   ││
│  │ Бывшая пианистка. Её руки помнят клавиши, но шрам на        ││
│  │ запястье скрывает историю, которую она никому не            ││
│  │ рассказывала... Готова ли ты узнать правду?                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

***

## **📱 ЭКРАН 5: ОСНОВНОЙ ИНТЕРФЕЙС (ПОСЛЕ ВЫБОРА ПЕРСОНАЖА)**

text

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ←  Чат с Евой                                    ● ● ●          │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                              ││
│  │  ┌─────────────────────────────────────────────────────┐    ││
│  │  │                                                     │    ││
│  │  │  Ева: Привет! Я рада, что ты выбрал меня...         │    ││
│  │  │                                     [💬]             │    ││
│  │  └─────────────────────────────────────────────────────┘    ││
│  │                                                              ││
│  │  ┌─────────────────────────────────────────────────────┐    ││
│  │  │  [Фото: Ева в кафе]                                 │    ││
│  │  │  [Фото: Ева на прогулке]                            │    ││
│  │  └─────────────────────────────────────────────────────┘    ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ [Сообщение...                                    ] [📎] [➤] ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  [🏠] [💬] [🖼️] [🎁] [👤]                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

***

## **🗄️ СТРУКТУРА БАЗЫ ДАННЫХ (ПОЛЬЗОВАТЕЛИ)**

sql

```
-- Пользователи
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Авторизация
    auth_provider VARCHAR(20) NOT NULL, -- 'apple', 'google', 'email', 'guest'
    auth_provider_id VARCHAR(255),      -- ID от Apple/Google
    email VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    
    -- Профиль
    display_name VARCHAR(100),
    nickname VARCHAR(50),                -- как обращаться к пользователю
    avatar_url VARCHAR(500),
    birth_date DATE,
    about TEXT,
    
    -- Возрастная верификация
    is_adult BOOLEAN DEFAULT FALSE,      -- подтвержденный 18+
    age_verified_at TIMESTAMP,
    
    -- Статус
    status VARCHAR(20) DEFAULT 'active', -- active, blocked, deleted
    is_guest BOOLEAN DEFAULT FALSE,
    
    -- Системное
    created_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP DEFAULT NOW(),
    last_ip INET,
    
    -- Уникальность
    UNIQUE(auth_provider, auth_provider_id),
    UNIQUE(email)
);

-- Сессии пользователей
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET
);

-- Выбор персонажа пользователем
CREATE TABLE user_characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    character_id UUID REFERENCES characters(id),
    is_active BOOLEAN DEFAULT FALSE,     -- текущий активный персонаж
    selected_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, character_id)
);

-- Прогресс пользователя по персонажу
CREATE TABLE user_progress (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    character_id UUID REFERENCES characters(id),
    trust_score INTEGER DEFAULT 0,
    current_layer INTEGER DEFAULT 0,
    tokens_balance INTEGER DEFAULT 0,
    last_message_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, character_id)
);
```

***

## **🔐 API ENDPOINTS (АВТОРИЗАЦИЯ)**

python

```
# Apple Sign-In
POST   /api/auth/apple              # авторизация через Apple
GET    /api/auth/apple/callback     # колбэк после Apple

# Google Sign-In
POST   /api/auth/google             # авторизация через Google
GET    /api/auth/google/callback    # колбэк после Google

# Email (опционально)
POST   /api/auth/email/register     # регистрация по email
POST   /api/auth/email/login        # вход по email
POST   /api/auth/email/verify       # подтверждение email
POST   /api/auth/email/reset        # сброс пароля

# Guest режим
POST   /api/auth/guest              # создание гостевого аккаунта

# Общие
POST   /api/auth/logout             # выход
POST   /api/auth/refresh            # обновление токена
GET    /api/auth/me                 # получить текущего пользователя

# Профиль
PUT    /api/users/profile           # обновить профиль
POST   /api/users/avatar            # загрузить аватар
DELETE /api/users/account           # удалить аккаунт
```

***

## **🍎 APPLE SIGN-IN ИНТЕГРАЦИЯ**

### **Настройка (iOS/macOS)**

swift

```
// AppDelegate.swift
import AuthenticationServices

func setupAppleSignIn() {
    let provider = ASAuthorizationAppleIDProvider()
    let request = provider.createRequest()
    request.requestedScopes = [.fullName, .email]
    
    let controller = ASAuthorizationController(authorizationRequests: [request])
    controller.delegate = self
    controller.performRequests()
}
```

### **Backend верификация**

python

```
from apple_sign_in import verify_apple_token

@router.post("/api/auth/apple")
async def apple_auth(request: AppleAuthRequest):
    # 1. Верифицируем токен от Apple
    payload = await verify_apple_token(request.identity_token)
    
    # 2. Получаем или создаем пользователя
    user = await get_or_create_user(
        provider="apple",
        provider_id=payload["sub"],
        email=payload.get("email"),
        name=request.full_name
    )
    
    # 3. Создаем сессию
    tokens = await create_session(user.id)
    
    return {"access_token": tokens.access, "refresh_token": tokens.refresh}
```

***

## **G SIGN-IN ИНТЕГРАЦИЯ**

### **Настройка (клиент)**

javascript

```
// React Native / Expo
import * as Google from 'expo-auth-session/providers/google';

const [request, response, promptAsync] = Google.useAuthRequest({
  clientId: 'YOUR_GOOGLE_CLIENT_ID',
  iosClientId: 'YOUR_IOS_CLIENT_ID',
  androidClientId: 'YOUR_ANDROID_CLIENT_ID',
});

// Вызов
await promptAsync();
// Получаем id_token и отправляем на бэкенд
```

### **Backend верификация**

python

```
from google.oauth2 import id_token
from google.auth.transport import requests

@router.post("/api/auth/google")
async def google_auth(request: GoogleAuthRequest):
    # 1. Верифицируем токен
    try:
        info = id_token.verify_oauth2_token(
            request.id_token,
            requests.Request(),
            "YOUR_GOOGLE_CLIENT_ID"
        )
    except ValueError:
        raise HTTPException(401, "Invalid token")
    
    # 2. Получаем или создаем пользователя
    user = await get_or_create_user(
        provider="google",
        provider_id=info["sub"],
        email=info["email"],
        name=info.get("name")
    )
    
    # 3. Создаем сессию
    tokens = await create_session(user.id)
    
    return {"access_token": tokens.access, "refresh_token": tokens.refresh}
```

***

## **👤 ГОСТЕВОЙ РЕЖИМ**

python

```
@router.post("/api/auth/guest")
async def guest_auth(request: Request):
    # 1. Создаем временного пользователя
    user_id = str(uuid.uuid4())
    
    user = await create_user({
        "id": user_id,
        "auth_provider": "guest",
        "is_guest": True,
        "display_name": f"Guest_{user_id[:8]}"
    })
    
    # 2. Создаем сессию (ограниченную по времени)
    tokens = await create_session(
        user_id=user.id,
        expires_in=86400  # 24 часа для гостей
    )
    
    # 3. Отмечаем, что нужен апгрейд
    return {
        "access_token": tokens.access,
        "refresh_token": tokens.refresh,
        "is_guest": True,
        "upgrade_hint": "Register to save progress"
    }
```

***

## **📱 UI КОМПОНЕНТЫ ДЛЯ АВТОРИЗАЦИИ**

### **Кнопка Apple Sign-In**

jsx

```
<AppleSignInButton
  onSuccess={(token) => handleAppleAuth(token)}
  onError={(error) => console.error(error)}
  style={{
    backgroundColor: '#000',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  }}
>
  <Text style={{ color: '#fff', fontWeight: '600' }}>
    🍎 Продолжить с Apple ID
  </Text>
</AppleSignInButton>
```

### **Кнопка Google Sign-In**

jsx

```
<GoogleSignInButton
  onSuccess={(token) => handleGoogleAuth(token)}
  onError={(error) => console.error(error)}
  style={{
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  }}
>
  <Text style={{ color: '#333', fontWeight: '600' }}>
    G Продолжить с Google
  </Text>
</GoogleSignInButton>
```

***

## **🔄 FLOW ДИАГРАММА**

text

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER JOURNEY (ПЕРВЫЙ ЗАПУСК)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐                                                  │
│  │  ЗАПУСК  │                                                  │
│  └────┬─────┘                                                  │
│       ▼                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │  Онбординг   │────▶│   Выбор      │────▶│   Создание   │    │
│  │  (1 раз)     │     │   входа      │     │   профиля    │    │
│  └──────────────┘     └──────────────┘     └──────┬───────┘    │
│                                                    ▼             │
│                              ┌──────────────┐     ┌──────────────┐
│                              │   Выбор      │────▶│   Основной   │
│                              │  персонажа   │     │     чат      │
│                              └──────────────┘     └──────────────┘
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

***

## **✅ ЧЕК-ЛИСТ РЕАЛИЗАЦИИ**

**Компонент**

**Статус**

Онбординг (4 слайда)

⬜️

Apple Sign-In интеграция

⬜️

Google Sign-In интеграция

⬜️

Email регистрация (опционально)

⬜️

Guest режим

⬜️

Экран создания профиля

⬜️

Экран выбора персонажа

⬜️

JWT токены (access + refresh)

⬜️

User sessions в БД

⬜️

Age verification (18+)

⬜️
