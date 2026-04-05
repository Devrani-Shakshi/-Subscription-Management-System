import httpx
import sys

res_login = httpx.post('http://localhost:8000/api/auth/login', json={'email': 'company@acme.com', 'password': 'company123'})
if res_login.status_code != 200:
    print("Login failed:", res_login.text)
    sys.exit()
    
token = res_login.json()['access_token']
res = httpx.get('http://localhost:8000/api/company/subscriptions?page=1&limit=10', headers={'Authorization': f'Bearer {token}'})
print("STATUS:", res.status_code)
print("BODY:", res.text)
