import json
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from google.oauth2 import id_token
from google.auth.transport import requests
from pydantic import ValidationError
from api.auth.oauth_models import OAuthUserInfo, GoogleAuthRequest, AppleAuthRequest

class OAuthService:
    def __init__(self):
        self.google_client_id = "YOUR_GOOGLE_CLIENT_ID"  # Замените на ваш реальный client ID
        
    async def verify_google_token(self, id_token_string: str) -> OAuthUserInfo:
        """Verify Google ID token and extract user information"""
        try:
            # Verify the token
            id_info = id_token.verify_oauth2_token(
                id_token_string, 
                requests.Request(), 
                self.google_client_id
            )
            
            # Extract user information
            return OAuthUserInfo(
                provider="google",
                provider_id=id_info["sub"],
                email=id_info.get("email"),
                name=id_info.get("name"),
                avatar_url=id_info.get("picture")
            )
            
        except ValueError as e:
            raise ValueError(f"Invalid Google token: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error verifying Google token: {str(e)}")
    
    async def verify_apple_token(self, identity_token: str) -> OAuthUserInfo:
        """Verify Apple identity token and extract user information"""
        try:
            # For Apple, we need to verify the JWT token
            # This is a simplified version - в продакшене нужно использовать полную верификацию
            
            # Разбираем токен без верификации (только для тестирования)
            # В продакшене нужно использовать apple's public keys для верификации
            import jwt
            
            # Декодируем токен без верификации (только для разработки!)
            payload = jwt.decode(identity_token, options={"verify_signature": False})
            
            return OAuthUserInfo(
                provider="apple",
                provider_id=payload.get("sub", ""),
                email=payload.get("email"),
                name=None  # Apple не предоставляет имя в токене
            )
            
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid Apple token: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error verifying Apple token: {str(e)}")

# Создаем глобальный экземпляр
oauth_service = OAuthService()