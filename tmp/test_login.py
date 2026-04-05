import requests
import json

def test_login():
    url = "http://localhost:8000/auth/login"
    payload = {
        "email": "demo@demodata.com",
        "password": "Password123!"
    }
    headers = {
        "Content-Type": "application/json"
    }
    print(f"Sending login to {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_login()
