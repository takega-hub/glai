from pydantic import BaseModel, EmailStr
from typing import Optional

class GoogleAuthRequest(BaseModel):
    id_token: str
    
class AppleAuthRequest(BaseModel):
    identity_token: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class OAuthUserInfo(BaseModel):
    provider: str
    provider_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None