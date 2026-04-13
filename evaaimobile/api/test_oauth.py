"""
Тесты для OAuth аутентификации (Google и Apple)
Эти тесты можно запускать без запущенного сервера
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.auth.oauth_service import oauth_service
from api.auth.oauth_models import GoogleAuthRequest, AppleAuthRequest

class TestOAuthService:
    
    @pytest.mark.asyncio
    async def test_google_token_verification_mock(self):
        """Test Google token verification with mock"""
        # Mock Google token verification
        mock_token_data = {
            "sub": "123456789",
            "email": "test@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg"
        }
        
        with patch('google.oauth2.id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_token_data
            
            result = await oauth_service.verify_google_token("fake_token")
            
            assert result.provider == "google"
            assert result.provider_id == "123456789"
            assert result.email == "test@gmail.com"
            assert result.name == "Test User"
            assert result.avatar_url == "https://example.com/photo.jpg"
    
    @pytest.mark.asyncio
    async def test_apple_token_verification_mock(self):
        """Test Apple token verification with mock"""
        # Mock Apple token data
        mock_token_data = {
            "sub": "apple_user_123",
            "email": "test@icloud.com"
        }
        
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = mock_token_data
            
            result = await oauth_service.verify_apple_token("fake_apple_token")
            
            assert result.provider == "apple"
            assert result.provider_id == "apple_user_123"
            assert result.email == "test@icloud.com"
    
    def test_oauth_models_validation(self):
        """Test OAuth models validation"""
        # Test Google Auth Request
        google_request = GoogleAuthRequest(id_token="test_token")
        assert google_request.id_token == "test_token"
        
        # Test Apple Auth Request
        apple_request = AppleAuthRequest(
            identity_token="apple_token",
            full_name="Test User",
            email="test@example.com"
        )
        assert apple_request.identity_token == "apple_token"
        assert apple_request.full_name == "Test User"
        assert apple_request.email == "test@example.com"
        
        # Test with minimal Apple data
        apple_minimal = AppleAuthRequest(identity_token="minimal_token")
        assert apple_minimal.full_name is None
        assert apple_minimal.email is None

    @pytest.mark.asyncio
    async def test_invalid_google_token(self):
        """Test invalid Google token handling"""
        with patch('google.oauth2.id_token.verify_oauth2_token') as mock_verify:
            mock_verify.side_effect = ValueError("Invalid token")
            
            with pytest.raises(ValueError, match="Invalid Google token"):
                await oauth_service.verify_google_token("invalid_token")

    @pytest.mark.asyncio
    async def test_invalid_apple_token(self):
        """Test invalid Apple token handling"""
        with patch('jwt.decode') as mock_decode:
            mock_decode.side_effect = Exception("Invalid JWT")
            
            with pytest.raises(ValueError, match="Error verifying Apple token"):
                await oauth_service.verify_apple_token("invalid_token")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])