import requests

BASE = "http://127.0.0.1:8000/api"

# Register
print("Registering...")
res = requests.post(f"{BASE}/register", json={"name": "Test User", "email": "testvercel@gmail.com", "password": "password"})
print("Register:", res.status_code, res.text)

# Login
print("Logging in...")
res = requests.post(f"{BASE}/login", json={"email": "testvercel@gmail.com", "password": "password"})
print("Login:", res.status_code)
token = res.json().get("token")
headers = {"Authorization": f"Bearer {token}"}

# Generate Data
print("Generating data...")
res = requests.post(f"{BASE}/generate", headers=headers)
print("Generate:", res.status_code, res.text)

# Fetch correlation (requires data)
print("Fetching correlation...")
res = requests.get(f"{BASE}/correlation", headers=headers)
print("Correlation:", res.status_code, str(res.text)[:100])
