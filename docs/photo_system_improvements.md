# Улучшение системы обработки фото-запросов

## Текущая проблема
Сейчас система работает примитивно: при любом запросе фото AI просто генерирует действие `generate_new_photo` с предопределённым промптом, не анализируя контекст запроса пользователя.

## Цель
Создать интеллектуальную систему, которая:
1. Анализирует запрос пользователя на фото
2. Подбирает подходящее фото из существующей галереи персонажа
3. Принимает решение: отправить существующее или предложить генерацию нового
4. Учитывает уровень доверия и контекст общения

## Новая архитектура

### 1. Анализ запроса пользователя

```python
class PhotoRequestAnalyzer:
    def analyze_request(self, user_message, conversation_context):
        # Извлечение ключевых слов
        keywords = self.extract_keywords(user_message)
        
        # Определение намерения
        intent = self.classify_intent(user_message)
        # Возможные намерения:
        # - casual_request: "покажись", "скинь фотку"
        # - specific_request: "в красном платье", "на природе"
        # - intimate_request: "хочу тебя увидеть", "более откровенно"
        # - creative_request: "сделай фото специально для меня"
        
        # Определение настроения
        mood = self.assess_mood(conversation_context)
        
        return {
            "keywords": keywords,
            "intent": intent,
            "mood": mood,
            "specificity": self.calculate_specificity(user_message)
        }
```

### 2. Поиск подходящих фото

```python
class PhotoMatcher:
    def find_matching_photos(self, character_id, analysis_result, trust_level):
        # Получаем все доступные фото персонажа
        available_photos = self.get_available_photos(character_id, trust_level)
        
        # Оцениваем соответствие каждого фото
        scored_photos = []
        for photo in available_photos:
            score = self.calculate_relevance_score(photo, analysis_result)
            scored_photos.append((photo, score))
        
        # Сортируем по релевантности
        scored_photos.sort(key=lambda x: x[1], reverse=True)
        
        return scored_photos[:5]  # Топ-5 наиболее подходящих
    
    def calculate_relevance_score(self, photo, analysis):
        score = 0
        
        # Проверка ключевых слов в описании
        description_match = self.check_keyword_match(
            photo.description, 
            analysis["keywords"]
        )
        score += description_match * 0.4
        
        # Проверка тегов
        tags_match = self.check_tags_match(photo.tags, analysis["keywords"])
        score += tags_match * 0.3
        
        # Соответствие намерению
        intent_match = self.check_intent_compatibility(
            photo.intent_tags, 
            analysis["intent"]
        )
        score += intent_match * 0.2
        
        # Уровень доверия
        trust_bonus = self.calculate_trust_bonus(photo, analysis["mood"])
        score += trust_bonus * 0.1
        
        return min(score, 1.0)
```

### 3. Принятие решения

```python
class PhotoDecisionEngine:
    def decide_action(self, matching_photos, analysis, trust_level, user_tokens):
        best_photo_score = matching_photos[0][1] if matching_photos else 0
        
        # Если нашли очень подходящее фото (score > 0.7)
        if best_photo_score > 0.7:
            return {
                "action": "send_existing_photo",
                "photo": matching_photos[0][0],
                "reason": "high_relevance_match"
            }
        
        # Если умеренное совпадение (0.4 < score <= 0.7)
        elif best_photo_score > 0.4:
            # И высокий уровень доверия
            if trust_level >= 60:
                return {
                    "action": "send_existing_photo",
                    "photo": matching_photos[0][0],
                    "reason": "moderate_match_high_trust"
                }
            else:
                return {
                    "action": "propose_gift_for_better_photo",
                    "available_photos": matching_photos,
                    "reason": "moderate_match_low_trust"
                }
        
        # Если слабое совпадение (score <= 0.4)
        else:
            # Проверяем, есть ли токены для генерации
            if user_tokens >= 50:  # Минимальная стоимость генерации
                return {
                    "action": "propose_photo_generation",
                    "cost": 50,
                    "reason": "no_suitable_existing_photo"
                }
            else:
                return {
                    "action": "apologize_and_suggest_gift",
                    "reason": "insufficient_tokens"
                }
```

### 4. Генерация контекстного ответа

```python
class ContextualPhotoResponseGenerator:
    def generate_response(self, decision, analysis, character_personality):
        action = decision["action"]
        
        if action == "send_existing_photo":
            return self.generate_existing_photo_response(
                decision["photo"], 
                analysis, 
                character_personality
            )
        
        elif action == "propose_gift_for_better_photo":
            return self.generate_gift_proposal_response(
                decision["available_photos"],
                analysis,
                character_personality
            )
        
        elif action == "propose_photo_generation":
            return self.generate_generation_proposal_response(
                decision["cost"],
                analysis,
                character_personality
            )
        
        elif action == "apologize_and_suggest_gift":
            return self.generate_apology_response(analysis, character_personality)
    
    def generate_existing_photo_response(self, photo, analysis, personality):
        # Генерируем естественный ответ с учетом личности персонажа
        # и контекста запроса
        
        base_responses = {
            "casual": [
                "Вот, надеюсь тебе понравится 😊",
                "Смотри, что у меня есть для тебя ✨",
                "Думаю, это то, что ты искал 💫"
            ],
            "specific": [
                f"Ты просил показать {analysis['keywords'][0]}, вот 🎯",
                f"Как раз то, о чем ты говорил 💝",
                f"Надеюсь, это соответствует твоему запросу 💭"
            ],
            "intimate": [
                "Только для тебя... 💖",
                "Надеюсь, это поднимет тебе настроение 🔥",
                "Ты заслужил это... 😘"
            ]
        }
        
        # Выбираем подходящий ответ и добавляем описание фото
        response_type = "specific" if analysis["specificity"] > 0.6 else analysis["intent"]
        base_response = random.choice(base_responses.get(response_type, base_responses["casual"]))
        
        return {
            "response": f"{base_response}\n\n{photo.description}",
            "action": {
                "type": "send_photo",
                "photo_id": photo.id,
                "description": photo.description
            },
            "message_parts": [base_response, photo.description]
        }
```

## Примеры работы новой системы

### Сценарий 1: Конкретный запрос
**Пользователь**: "Покажи себя в красном платье на фоне заката"

**AI анализ**:
- Ключевые слова: ["красное платье", "закат"]
- Намерение: specific_request
- Конкретность: высокая (0.8)

**Результат**: Если есть фото с красным платьем и закатом → отправить это фото с описанием

### Сценарий 2: Общий запрос
**Пользователь**: "Хочу тебя увидеть"

**AI анализ**:
- Ключевые слова: ["увидеть"]
- Намерение: intimate_request
- Конкретность: низкая (0.3)

**Результат**: 
- При высоком уровне доверия → отправить наиболее подходящее интимное фото
- При низком уровне → предложить подарок для разблокировки

### Сценарий 3: Запрос на генерацию
**Пользователь**: "Сделай фото специально для меня"

**AI анализ**:
- Ключевые слова: ["сделать", "специально"]
- Намерение: creative_request
- Конкретность: средняя

**Результат**: Предложение сгенерировать уникальное фото за токены

## Техническая реализация

### 1. Обновление AIDialogueEngine

```python
class AIDialogueEngine:
    def __init__(self):
        self.photo_analyzer = PhotoRequestAnalyzer()
        self.photo_matcher = PhotoMatcher()
        self.decision_engine = PhotoDecisionEngine()
        self.response_generator = ContextualPhotoResponseGenerator()
    
    async def generate_character_response(self, user_message, character, context):
        # Проверяем, является ли запрос фото-запросом
        if self.is_photo_request(user_message):
            return await self.handle_photo_request(user_message, character, context)
        
        # Обычная генерация текста
        return await self.generate_text_response(user_message, character, context)
    
    async def handle_photo_request(self, user_message, character, context):
        # Анализ запроса
        analysis = self.photo_analyzer.analyze_request(
            user_message, 
            context.conversation_history
        )
        
        # Поиск подходящих фото
        matching_photos = self.photo_matcher.find_matching_photos(
            character.id,
            analysis,
            context.trust_level
        )
        
        # Принятие решения
        decision = self.decision_engine.decide_action(
            matching_photos,
            analysis,
            context.trust_level,
            context.user_tokens
        )
        
        # Генерация ответа
        response = self.response_generator.generate_response(
            decision,
            analysis,
            character.personality
        )
        
        return response
```

### 2. Обновление базы данных

```sql
-- Добавляем поля для улучшенного поиска фото
ALTER TABLE photos ADD COLUMN intent_tags TEXT[]; -- Типы намерений
ALTER TABLE photos ADD COLUMN description_vector VECTOR(384); -- Для векторного поиска
ALTER TABLE photos ADD COLUMN mood_tags TEXT[]; -- Теги настроения
ALTER TABLE photos ADD COLUMN complexity_level INTEGER; -- Уровень сложности/интимности
```

### 3. Обновление API

```python
@router.post("/dialogue/send-message")
async def send_message(request: MessageRequest, current_user: User):
    # Существующая логика...
    
    # Новая логика для фото-запросов
    if ai_response.get("action", {}).get("type") == "send_photo":
        # Отправляем существующее фото
        photo_id = ai_response["action"]["photo_id"]
        photo = await get_photo_by_id(photo_id)
        
        return {
            **ai_response,
            "image_url": photo.url,
            "photo_description": photo.description
        }
    
    return ai_response
```

## Критерии успеха

1. **Точность анализа**: AI правильно определяет намерение в 80%+ случаев
2. **Релевантность подбора**: Пользователи находят подходящие фото в 70%+ случаев
3. **Естественность ответов**: Ответы выглядят естественными и контекстуальными
4. **Конверсия подарков**: Увеличение конверсии в подарки для эксклюзивных фото
5. **Удовлетворенность**: Пользователи отмечают улучшение качества взаимодействия

## План внедрения

1. **Фаза 1**: Обновление AIDialogueEngine с новыми компонентами
2. **Фаза 2**: Расширение базы данных и добавление индексов
3. **Фаза 3**: Обновление API и фронтенда
4. **Фаза 4**: Тестирование и оптимизация
5. **Фаза 5**: Мониторинг и улучшение на основе метрик