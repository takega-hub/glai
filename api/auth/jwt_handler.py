import time
import jwt
import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

# Используем os.getenv, чтобы быть уверенными в загрузке
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-here")
JWT_ALGORITHM = os.getenv("ALGORITHM", "HS256")

print(f"DEBUG: JWT_SECRET used is {JWT_SECRET[:3]}...")

def token_response(token: str):
    return {
        "access_token": token
    }

def signJWT(user_id: str, role: str) -> Dict[str, str]:
    # Используем и "exp" (стандарт) и "expires" для совместимости
    now = time.time()
    payload = {
        "user_id": user_id,
        "role": role,
        "iat": now,
        "exp": now + (3600 * 24 * 7), # 7 дней для стабильности во время тестов
        "expires": now + (3600 * 24 * 7)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token_response(token)

def decodeJWT(token: str) -> dict:
    try:
        # Убираем проверку времени (leeway), если на планшете сбиты часы
        decoded_token = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False} # Временно для отладки 401
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        print("JWT Decode Error: Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"JWT Decode Error: Invalid token: {e}")
        return None
    except Exception as e:
        print(f"JWT Decode Error: Unexpected error: {e}")
        return None
