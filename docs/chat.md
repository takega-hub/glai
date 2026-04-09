## 📋 Система Общения EVA AI - Полное Описание

### 🏗️ Архитектура Системы

Backend Stack:

- FastAPI - основной веб-фреймворк
- PostgreSQL - база данных с асинхронным драйвером asyncpg
- JWT - аутентификация и авторизация
- OpenRouter API - интеграция с AI моделями (Google Gemini Flash)
  Frontend Stack:
- React + TypeScript - основной интерфейс
- React Router - навигация
- Tailwind CSS - стилизация
- Zustand - управление состоянием

### 🔗 API Эндпоинты для Общения Основные Эндпоинты:

1. Отправка Сообщения

```
POST /api/dialogue/send-message
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "character_id": "uuid",
  "message": "string",
  "conversation_id": "string" // 
  опционально
}
```

Ответ:

```
{
  "id": 1,
  "character_id": "uuid",
  "user_id": "uuid", 
  "message": "user message",
  "response": "character response",
  "trust_score_change": 1,
  "layer_unlocked": false,
  "created_at": 
  "2024-01-01T12:00:00"
}
```

1. История Переписки

```
GET /api/dialogue/history/
{character_id}?limit=50&offset=0
Authorization: Bearer {JWT_TOKEN}
```

Ответ:

```
{
  "messages": [...],
  "trust_score": 25,
  "current_layer": 1,
  "character_info": {
    "id": "uuid",
    "name": "Eva",
    "display_name": "Ева",
    "personality_type": 
    "adventurous"
  }
}
```

1. Проактивные Сообщения

```
POST /api/dialogue/proactive-message
Authorization: Bearer {JWT_TOKEN}

{
  "character_id": "uuid",
  "message_type": "greeting|photo|
  flirt|story",
  "context": "optional context"
}
```

1. Генерация Промптов для Изображений

```
POST /api/dialogue/
generate-image-prompt/
{character_id}?style=realistic
Authorization: Bearer {JWT_TOKEN}

{
  "user_request": "user's image 
  request"
}
```

### 🗄️ Схема Базы Данных Таблицы для Общения:

1. messages - история сообщений

```
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    character_id UUID REFERENCES 
    characters(id),
    user_id UUID REFERENCES users
    (id),
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    trust_score_change INTEGER 
    DEFAULT 0,
    layer_unlocked BOOLEAN DEFAULT 
    FALSE,
    created_at TIMESTAMPTZ DEFAULT 
    NOW()
);
```

1. user\_character\_state - состояние взаимоотношений

```
CREATE TABLE user_character_state (
    user_id UUID REFERENCES users
    (id),
    character_id UUID REFERENCES 
    characters(id),
    trust_score INTEGER DEFAULT 0,
    current_layer INTEGER DEFAULT 0,
    conversation_history JSONB 
    DEFAULT '[]',
    last_message_date TIMESTAMPTZ,
    PRIMARY KEY (user_id, 
    character_id)
);
```

1. trust\_score\_history - история изменений доверия

```
CREATE TABLE trust_score_history (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users
    (id),
    character_id UUID REFERENCES 
    characters(id),
    points INTEGER NOT NULL,
    reason VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT 
    NOW()
);
```

1. character\_llm\_prompts - промпты для AI

```
CREATE TABLE character_llm_prompts (
    character_id UUID REFERENCES 
    characters(id),
    system_prompt TEXT,
    context_instructions TEXT,
    PRIMARY KEY (character_id)
);
```

### 🤖 Логика Работы AI Поток Обработки Сообщения:

1. Аутентификация → JWT токен проверяется
2. Проверка Пользователя → Создается запись в БД если новый
3. Загрузка Состояния → Получаем trust\_score и историю
4. Формирование Промпта → Подставляем переменные в системный промпт
5. Генерация Ответа → Отправляем в OpenRouter API
6. Обновление Состояния → Увеличиваем trust\_score, обновляем историю
7. Сохранение → Сохраняем сообщение и состояние в БД Система Доверия (Trust Score):

- Начальный уровень : 0
- Максимальный : 100
- Увеличение : +1 за сообщение, +1 за длинные сообщения (>50 символов), +1 за вопросы
- Уменьшение : -1 за короткие сообщения (<10 символов)
- Уровни Доступа : Каждый персонаж имеет слои контента с минимальными требованиями к trust\_score Динамические Промпты:
  Система использует промпты из БД с подстановкой переменных:
- {{current\_layer}} - текущий уровень доступа
- {{trust\_score}} - текущий балл доверия
- {{user\_name}} - имя пользователя (если известно)

### 🎨 Frontend Компоненты Основные Компоненты:

1. CharacterPage.tsx - страница персонажа с вкладками 2. Dialogue.tsx - компонент чата (нуждается в доработке) 3. AuthPage.tsx - страница авторизации
   Текущая Реализация Чата:

- ✅ Сообщения отображаются хронологически
- ✅ Пользователь и персонаж на разных сторонах экрана
- ❌ Нет автоматической прокрутки к новым сообщениям
- ❌ Нет индикатора набора текста
- ❌ Нет возможности редактировать/удалять сообщения

### 🔧 Точки Расширения для Будущей Разработки 1. Улучшение Чата :

- Автоматическая прокрутка
- Индикатор набора текста
- Возможность отправки изображений
- Статусы сообщений (отправлено/доставлено/прочитано) 2. Расширенные Функции AI :
- Контекст персонажа (возраст, интересы, биография)
- Эмоциональные состояния персонажа
- Проактивные инициативы от персонажа
- Мультимедиа ответы (изображения, голос) 3. Аналитика и Метрики :
- Время ответа персонажа
- Частота сообщений
- Типы контента, вызывающие наибольший trust\_score
- А/Б тестирование промптов 4. Масштабируемость :
- Кэширование ответов AI
- Очередь сообщений
- WebSocket для реального времени
- Rate limiting

### 📁 Структура Проекта

```
/opt/EVA_AI/
├── api/                          # 
Backend
│   ├── routers/
│   │   ├── dialogue.py          # 
Основные эндпоинты общения
│   │   ├── auth.py              # 
Аутентификация
│   │   └── characters.py        # 
Управление персонажами
│   ├── services/
│   │   └── ai_dialogue.py      # 
Логика AI общения
│   ├── auth/
│   │   ├── jwt_handler.py       # 
JWT обработка
│   │   └── security.py          # 
Безопасность
│   ├── migrations/              # 
SQL миграции
│   └── main.py                  # 
Точка входа
├── admin/                       # 
Frontend админка
│   └── src/
│       ├── pages/
│       │   ├── CharacterPage.tsx # 
Страница персонажа
│       │   └── AuthPage.tsx      # 
Авторизация
│       └── components/
│           └── character/
│               └── Dialogue.tsx  # 
Компонент чата
└── .env                         # 
Конфигурация
```

Эта система обеспечивает гибкую и масштабируемую архитектуру для развития AI-общения с персонажами.
