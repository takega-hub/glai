
import asyncio
import aiohttp
import uuid

# --- Конфигурация ---
# Замените на реальный ID персонажа из вашей базы данных
CHARACTER_ID = "aae583a0-890c-42d9-babc-96130efc4616"
# Замените на реальный JWT токен авторизации
AUTH_TOKEN = ""
# URL вашего запущенного сервера
SERVER_URL = "http://localhost:8002"
# Путь к тестовому изображению
IMAGE_PATH = "uploads/test_face.jpg"
# Промпт для генерации
PROMPT = "A photo of a beautiful woman, professional portrait, 8k, photorealistic"
# Данные для входа (из fix_auth_schema.py)
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "opexoboe"

async def get_auth_token(session):
    """Автоматически получает токен аутентификации."""
    login_url = f"{SERVER_URL}/auth/token"
    login_data = {
        'username': ADMIN_EMAIL,
        'password': ADMIN_PASSWORD
    }
    print(f"Попытка аутентификации на {login_url} с пользователем {ADMIN_EMAIL}")
    try:
        async with session.post(login_url, data=login_data) as response:
            if response.status == 200:
                token_data = await response.json()
                token = token_data.get('access_token')
                print("Аутентификация прошла успешно, токен получен.")
                return token
            else:
                print(f"Ошибка аутентификации: {response.status}")
                print(await response.text())
                return None
    except Exception as e:
        print(f"Исключение во время аутентификации: {e}")
        return None


async def main():
    """Основная функция для тестирования генерации."""
    headers = {}
    auth_token = None

    # Используем один менеджер контекста для сессии
    async with aiohttp.ClientSession() as session:
        # 1. Получаем токен, если он не задан
        if not AUTH_TOKEN:
            auth_token = await get_auth_token(session)
            if not auth_token:
                print("\n--- Тест не может быть продолжен без токена аутентификации. ---")
                return
        else:
            auth_token = AUTH_TOKEN

        headers["Authorization"] = f"Bearer {auth_token}"

        # 2. Формируем и отправляем основной запрос
        endpoint_url = f"{SERVER_URL}/dialogue/generate-image-with-face"
        
        data = aiohttp.FormData()
        data.add_field('character_id', CHARACTER_ID)
        data.add_field('prompt', PROMPT)
        try:
            data.add_field('face_image',
                        open(IMAGE_PATH, 'rb'),
                        filename='test_face.jpg',
                        content_type='image/jpeg')
        except FileNotFoundError:
            print(f"Ошибка: Тестовое изображение не найдено по пути {IMAGE_PATH}")
            print("Пожалуйста, убедитесь, что файл существует.")
            return

        print(f"Отправка запроса на: {endpoint_url}")
        try:
            async with session.post(endpoint_url, data=data, headers=headers) as response:
                print(f"Статус ответа: {response.status}")
                response_data = await response.json()
                print("Ответ сервера:")
                print(response_data)

                if response.status == 200 and response_data.get('image_url'):
                    print("\n--- Тест пройден успешно! ---")
                    print(f"URL сгенерированного изображения: {SERVER_URL}{response_data['image_url']}")
                else:
                    print("\n--- Тест не удался. ---")
                    print("Проверьте сообщение об ошибке выше.")
                    # Более детальные подсказки
                    if response.status == 401:
                        print("Подсказка: Проблема с аутентификацией. Токен устарел или недействителен.")
                    elif response.status == 404:
                        print(f"Подсказка: Эндпоинт не найден или CHARACTER_ID '{CHARACTER_ID}' не существует.")
                    elif response.status == 500:
                        print("Подсказка: Внутренняя ошибка сервера. Проверьте логи FastAPI и ComfyUI.")

        except aiohttp.ClientConnectorError as e:
            print(f"\nОшибка подключения: Не удалось подключиться к {SERVER_URL}.")
            print("Убедитесь, что ваш FastAPI сервер запущен.")
        except Exception as e:
            print(f"\nПроизошла непредвиденная ошибка: {e}")

if __name__ == "__main__":
    # Генерируем тестовый CHARACTER_ID, если он не задан
    if "a1b2c3d4" in CHARACTER_ID:
        new_uuid = str(uuid.uuid4())
        print(f"Используется сгенерированный тестовый CHARACTER_ID: {new_uuid}")
        CHARACTER_ID = new_uuid
        
    if AUTH_TOKEN == "your_jwt_token_here":
        print("\nINFO: AUTH_TOKEN не указан, будет произведена попытка автоматической аутентификации.")
    
    asyncio.run(main())

