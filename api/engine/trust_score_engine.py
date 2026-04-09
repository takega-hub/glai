class TrustScoreEngine:
    SCORES = {
        # Базовые
        'message': 3,
        'daily_login': 5,
        
        # Качественные
        'compliment': 5,      # комплимент внешности/характеру
        'empathy': 8,         # эмпатия, поддержка
        'flirt_match': 6,     # флирт, который попал в тон персонажа
        'deep_question': 10,   # вопрос о прошлом/чувствах
        
        # Негативные
        'pressure': -10,      # требование контента
        'rudeness': -15,      # грубость
        'spam': -5,           # флуд сообщениями
        
        # Монетизация
        'gift_small': 10,     # подарок за 50 токенов
        'gift_medium': 30,    # подарок за 150 токенов
        'gift_large': 50,     # подарок за 300 токенов
        
        # Лимиты
        'max_daily_from_messages': 20,
    }

    def analyze_message(self, message: str, context: dict) -> dict:
        """
        Анализирует сообщение и возвращает:
        - тип взаимодействия
        - количество очков
        - флаги для AI
        """
        
        # Эвристический анализ (можно заменить на LLM-классификатор)
        result = {
            'type': 'message',
            'points': 3,
            'flags': []
        }
        
        message_lower = message.lower()

        # Комплименты
        if any(word in message_lower for word in ['красивая', 'секси', 'милая', 'шикарная']):
            result['type'] = 'compliment'
            result['points'] = self.SCORES['compliment']
            result['flags'].append('compliment_received')
        
        # Эмпатия
        if any(phrase in message_lower for phrase in ['понимаю', 'сочувствую', 'держись', 'я с тобой']):
            result['type'] = 'empathy'
            result['points'] = self.SCORES['empathy']
            result['flags'].append('empathy_detected')
        
        # Давление (требование контента)
        if any(phrase in message_lower for phrase in ['покажи фото', 'скинь видео', 'раздевайся']):
            result['type'] = 'pressure'
            result['points'] = self.SCORES['pressure']
            result['flags'].append('pressure_detected')
        
        # Глубокие вопросы
        if any(phrase in message_lower for phrase in ['почему', 'расскажи о себе', 'что случилось', 'твое прошлое']):
            result['type'] = 'deep_question'
            result['points'] = self.SCORES['deep_question']
            result['flags'].append('curiosity_detected')
        
        return result

    def update_trust_score(self, user_id: str, interaction: dict):
        """
        Обновляет trust_score пользователя
        (здесь будет логика обновления в БД)
        """
        print(f"Updating trust score for user {user_id} with {interaction['points']} points for {interaction['type']}")
        # TODO: Implement database update logic
        pass

    def check_layer_transition(self, user_id: str):
        """
        Проверяет условия для перехода на следующий слой
        (здесь будет логика проверки и перехода)
        """
        print(f"Checking layer transition for user {user_id}")
        # TODO: Implement layer transition logic
        pass
