import requests
import json

BASE_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    url = f"{BASE_URL}/auth/register"
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = requests.post(url, json=data)
    print(f"Registration Response: {response.status_code}")
    if response.status_code == 200:
        print(f"User created: {response.json()}")
    else:
        print(f"Error: {response.text}")
    
    return response

def test_login():
    """Test user login"""
    url = f"{BASE_URL}/auth/token"
    data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = requests.post(url, data=data)
    print(f"\nLogin Response: {response.status_code}")
    if response.status_code == 200:
        token_data = response.json()
        print(f"Token received: {token_data['access_token'][:20]}...")
        return token_data['access_token']
    else:
        print(f"Error: {response.text}")
        return None

def test_get_user_info(token):
    """Test getting current user info"""
    url = f"{BASE_URL}/auth/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    print(f"\nUser Info Response: {response.status_code}")
    if response.status_code == 200:
        print(f"User info: {response.json()}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("Testing Authentication System")
    print("=" * 30)
    
    # Test registration
    reg_response = test_registration()
    
    # Test login
    token = test_login()
    
    # Test getting user info
    if token:
        test_get_user_info(token)