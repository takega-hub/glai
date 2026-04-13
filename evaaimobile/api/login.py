
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def login(email, password):
    """Login user and return JWT token"""
    url = f"{BASE_URL}/auth/token"
    data = {
        "username": email,
        "password": password
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(url, data=data)
    print(f"Login Response: {response.status_code}")
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"Token: {token}")
        return token
    else:
        print(f"Error: {response.text}")
        return None

if __name__ == "__main__":
    admin_email = "admin@example.com"
    admin_password = "admin123"
    login(admin_email, admin_password)
