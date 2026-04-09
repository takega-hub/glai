# **AI СЦЕНАРИСТ НА БАЗЕ DEEPSEEK**

## **Полное описание функционала для плана реализации**

***

## **📋 ОБЩЕЕ ОПИСАНИЕ**

**AI Сценарист** — это модуль на базе **DeepSeek API**, который автоматически генерирует полную концепцию персонажа: биографию, тайну, типаж, внешность, разбивку по слоям доверия, промпты для диалогов, сценарии для медиаконтента, настройки голоса и дополнительные условия.

**Зачем нужен:** Ускоряет создание персонажей в 10+ раз, обеспечивает консистентность истории, позволяет масштабировать библиотеку персонажей без найма большой команды сценаристов.

***

## **🏗️ АРХИТЕКТУРА МОДУЛЯ**

text

```
┌─────────────────────────────────────────────────────────────────┐
│                      АДМИН-ПАНЕЛЬ                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Кнопка: 🤖 Создать персонажа через AI                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI SCENARIST MODULE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  1. PROMPT GENERATOR                                     │    │
│  │     → Формирует запрос для DeepSeek на основе параметров │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  2. DEEPSEEK API CALL                                    │    │
│  │     → model: deepseek-chat или deepseek-coder           │    │
│  │     → temperature: 0.8 (для креативности)               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  3. RESPONSE PARSER                                      │    │
│  │     → Извлекает JSON из ответа DeepSeek                 │    │
│  │     → Валидация структуры                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  4. PREVIEW & EDIT                                      │    │
│  │     → Показывает результат человеку для утверждения    │    │
│  │     → Возможность ручной правки                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  5. SAVE TO DATABASE                                    │    │
│  │     → Сохраняет персонажа в БД                          │    │
│  │     → Запускает генерацию контента (опционально)        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

***

## **🎭 ПРОМПТ ДЛЯ DEEPSEEK (СИСТЕМНЫЙ)**

markdown

```
# SYSTEM PROMPT: AI СЦЕНАРИСТ

Ты — профессиональный сценарист интерактивных историй для приложения с AI-персонажами. 
Твоя задача — создавать детализированных персонажей с богатой биографией, тайной и 
системой слоев доверия.

## ТВОИ ПРИНЦИПЫ:
1. Персонаж должен быть сексуально привлекательным, но не вульгарным
2. Тайна должна быть эмоциональной, вызывать эмпатию
3. Слои доверия раскрывают историю постепенно, от поверхностного к глубокому
4. Каждый слой имеет четкую эмоциональную拱ку
5. Контент (фото/видео) соответствует этапу отношений

## ВЫХОДНОЙ ФОРМАТ (ТОЛЬКО JSON, БЕЗ ПОЯСНЕНИЙ):
{
  "character": {
    "name": "string",
    "age": number,
    "archetype": "string",
    "sexuality_level": number (1-10),
    "visual_description": {
      "face": "string",
      "body": "string",
      "hair": "string",
      "eyes": "string",
      "distinctive_features": "string",
      "style": "string",
      "color_palette": "string"
    },
    "biography": "string",
    "secret": "string",
    "voice_settings": {
      "provider": "elevenlabs",
      "voice_id": "string",
      "stability": number,
      "similarity_boost": number,
      "emotional_presets": {
        "neutral": "string",
        "sad": "string",
        "playful": "string",
        "intimate": "string"
      }
    }
  },
  "layers": [
    {
      "layer_number": number,
      "name": "string",
      "min_trust": number,
      "max_trust": number,
      "emotional_state": "string",
      "what_is_revealed": "string",
      "initiator_prompt": "string",
      "system_prompt_override": "string",
      "requirements": {
        "night_conversation": boolean,
        "gift_required": boolean,
        "min_days": number
      },
      "content_plan": {
        "photos": [
          {
            "description": "string",
            "prompt": "string",
            "is_erotic": boolean
          }
        ],
        "videos": [
          {
            "description": "string",
            "prompt": "string",
            "duration_seconds": number
          }
        ],
        "audio": [
          {
            "description": "string",
            "text": "string",
            "emotion": "string"
          }
        ]
      }
    }
  ]
}
```

***

## **📝 ПРИМЕР ЗАПРОСА К DEEPSEEK**

json

```
{
  "model": "deepseek-chat",
  "messages": [
    {
      "role": "system",
      "content": "Ты — профессиональный сценарист... [системный промпт выше]"
    },
    {
      "role": "user",
      "content": "Создай персонажа для приложения знакомств с AI. Девушка, таинственная, с музыкальным прошлым. 8 слоев доверия. Имя должно начинаться на Е."
    }
  ],
  "temperature": 0.8,
  "max_tokens": 4000
}
```

### **Ответ DeepSeek (пример):**

json

```
{
  "character": {
    "name": "Ева",
    "age": 24,
    "archetype": "Таинственная музыкантша",
    "sexuality_level": 7,
    "visual_description": {
      "face": "Овальное лицо, теплые карие глаза, легкая россыпь веснушек на переносице",
      "body": "Хрупкое телосложение, скрытая сила в движениях",
      "hair": "Темные вьющиеся волосы до плеч",
      "eyes": "Карие, глубокие, с легкой грустинкой",
      "distinctive_features": "Тонкий шрам на левом запястье",
      "style": "Уютные свитера, облегающие платья, натуральные ткани",
      "color_palette": "Терракотовый, бордовый, темно-синий, кремовый"
    },
    "biography": "Ева была профессиональной пианисткой, подававшей большие надежды. Год назад она попала в аварию, в которой серьезно повредила левую руку. Она больше не может играть так, как раньше, и скрывает это, потому что музыка была ее идентичностью.",
    "secret": "Она тайно записала альбом одной правой рукой, используя технологии, но боится его показать.",
    "voice_settings": {
      "provider": "elevenlabs",
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "stability": 0.5,
      "similarity_boost": 0.75,
      "emotional_presets": {
        "neutral": "Низкий голос с легкой хрипотцой",
        "sad": "Чуть медленнее, с вздохами",
        "playful": "Повышенная интонация, легкий смех",
        "intimate": "Шепот, паузы между словами"
      }
    }
  },
  "layers": [
    {
      "layer_number": 0,
      "name": "Знакомство",
      "min_trust": 0,
      "max_trust": 50,
      "emotional_state": "Легкая, отстраненная, поверхностный флирт",
      "what_is_revealed": "Только имя и базовые факты",
      "initiator_prompt": "Привет! Я Ева. Расскажи о себе?",
      "system_prompt_override": "Ты только знакомишься. Не раскрывай ничего личного.",
      "requirements": {
        "night_conversation": false,
        "gift_required": false,
        "min_days": 0
      },
      "content_plan": {
        "photos": [
          {
            "description": "Ева в кафе с чашкой кофе",
            "prompt": "Young woman with dark wavy hair, brown eyes, light freckles, wearing cream sweater, sitting in coffee shop, soft morning light, holding coffee cup, slight shy smile",
            "is_erotic": false
          },
          {
            "description": "Ева на осенней прогулке",
            "prompt": "Young woman with dark wavy hair, camel coat, walking on autumn street with fallen leaves, melancholy expression, soft overcast light",
            "is_erotic": false
          }
        ],
        "videos": [],
        "audio": []
      }
    },
    {
      "layer_number": 3,
      "name": "Шрам",
      "min_trust": 301,
      "max_trust": 450,
      "emotional_state": "Уязвимость, страх отвержения, надежда на принятие",
      "what_is_revealed": "Показывает шрам, говорит о 'несчастном случае'",
      "initiator_prompt": "Ты единственный, кто спросил об этом не из жалости. Смотри...",
      "system_prompt_override": "На этом слое ты впервые показываешь шрам. Говори уязвимо, но не драматично. Если собеседник проявляет эмпатию — открывайся чуть больше.",
      "requirements": {
        "night_conversation": true,
        "gift_required": false,
        "min_days": 3
      },
      "content_plan": {
        "photos": [
          {
            "description": "Крупный план шрама на фоне клавиш рояля",
            "prompt": "Close-up of young woman's left wrist with thin scar, resting on piano keys, soft window light, shallow depth of field, melancholic mood, warm sepia tone",
            "is_erotic": false
          }
        ],
        "videos": [
          {
            "description": "Пальцы играют на столе, будто на рояле",
            "prompt": "Close-up of slender fingers with scar on wrist, gently tapping on wooden table as if playing piano, slow melancholic movement, soft natural light",
            "duration_seconds": 5
          }
        ],
        "audio": []
      }
    }
  ]
}
```

***

## **🔧 ТЕХНИЧЕСКАЯ РЕАЛИЗАЦИЯ**

### **API Endpoint для AI генерации**

python

```
@router.post("/api/admin/characters/generate-with-ai")
async def generate_character_with_ai(
    request: AICharacterRequest,
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Генерирует полного персонажа через DeepSeek API
    """
    
    # 1. Формируем промпт для DeepSeek
    deepseek_prompt = f"""
    Создай персонажа со следующими параметрами:
    - Пол: {request.gender}
    - Типаж: {request.archetype or "любой"}
    - Количество слоев: {request.number_of_layers or 8}
    - Дополнительно: {request.additional_instructions or ""}
    """
    
    # 2. Вызов DeepSeek API
    response = await deepseek_client.chat_completion(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_AI_SCENARIST},
            {"role": "user", "content": deepseek_prompt}
        ],
        temperature=0.8,
        max_tokens=8000
    )
    
    # 3. Парсим JSON из ответа
    character_data = parse_deepseek_response(response.choices[0].message.content)
    
    # 4. Сохраняем в БД
    character_id = await save_character(character_data["character"])
    
    for layer_data in character_data["layers"]:
        await save_layer(character_id, layer_data)
    
    # 5. Возвращаем результат для предпросмотра
    return {
        "character_id": character_id,
        "preview": character_data,
        "message": "Персонаж создан. Проверьте и утвердите."
    }
```

***

## **🎛️ UI КОМПОНЕНТ (АДМИН-ПАНЕЛЬ)**

text

```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI СЦЕНАРИСТ — СОЗДАНИЕ ПЕРСОНАЖА                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Базовые параметры:                                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Пол: [Женский ▼]                                         │    │
│  │ Типаж: [Таинственная ▼] [Свой вариант...]                │    │
│  │ Количество слоев: [8 ▼] (4-12)                          │    │
│  │ Дополнительные инструкции:                               │    │
│  │ ┌─────────────────────────────────────────────────────┐ │    │
│  │ │ Должна быть связана с музыкой, иметь травму...      │ │    │
│  │ └─────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [🎲 Случайный]           [✨ Сгенерировать персонажа]          │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  РЕЗУЛЬТАТ ГЕНЕРАЦИИ:                                           │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ✅ Персонаж "Ева" создан                                 │    │
│  │                                                          │    │
│  │ 📋 ПРОФИЛЬ                                               │    │
│  │ ├─ Возраст: 24                                          │    │
│  │ ├─ Типаж: Таинственная музыкантша                       │    │
│  │ └─ Тайна: Не может играть из-за травмы руки             │    │
│  │                                                          │    │
│  │ 🎚️ СЛОИ: 8 слоев                                        │    │
│  │ ├─ Слой 0: Знакомство (0-50)                            │    │
│  │ ├─ Слой 1: Первая искра (51-150)                        │    │
│  │ ├─ Слой 2: Ночная откровенность (151-300)               │    │
│  │ └─ ...                                                  │    │
│  │                                                          │    │
│  │ 🖼️ КОНТЕНТ: 15 фото, 4 видео, 3 аудио                   │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [Редактировать вручную]     [✅ Утвердить и сохранить]         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

***

## **⚙️ НАСТРОЙКИ AI СЦЕНАРИСТА**

python

```
# config/ai_scenarist.py

AI_SCENARIST_CONFIG = {
    "deepseek": {
        "model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
        "temperature": 0.8,
        "max_tokens": 8000,
        "timeout": 120
    },
    "personality_presets": {
        "mysterious": "Таинственная, скрытная, говорит загадками",
        "playful": "Игривая, кокетливая, любит дразнить",
        "romantic": "Романтичная, мечтательная, ищет глубокую связь",
        "dominant": "Уверенная, доминантная, берет инициативу",
        "shy": "Застенчивая, стеснительная, раскрывается медленно"
    },
    "layer_defaults": {
        "min_layers": 5,
        "max_layers": 12,
        "trust_increment": 150  # примерный шаг между слоями
    }
}
```

***

## **📊 МЕТРИКИ КАЧЕСТВА AI СЦЕНАРИСТА**

**Метрика**

**Целевое значение**

Время генерации персонажа

< 30 секунд

Консистентность тайны (сквозь слои)

\> 95%

Приемлемость результата (человеком)

\> 85%

Количество правок после генерации

< 5 на персонажа

***

## **🔄 ИНТЕГРАЦИЯ С ДРУГИМИ МОДУЛЯМИ**

text

```
AI Сценарист
     │
     ├──→ Characters (сохранение персонажа)
     │
     ├──→ Layers (создание слоев)
     │
     ├──→ Content (генерация промптов для медиа)
     │         │
     │         └──→ AI Image Generator (Midjourney/SD)
     │
     └──→ Voice (настройка TTS параметров)
```

***

## **✅ ЧЕК-ЛИСТ РЕАЛИЗАЦИИ**

**Компонент**

**Статус**

DeepSeek API интеграция

⬜️

Системный промпт для AI сценариста

⬜️

Парсер JSON ответа

⬜️

UI форма для параметров

⬜️

Кнопка "Сгенерировать персонажа"

⬜️

Предпросмотр результата

⬜️

Сохранение в БД

⬜️

Ручное редактирование после генерации

⬜️

Генерация промптов для контента

⬜️
