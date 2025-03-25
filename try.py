import requests

API_KEY="sk-138969bfac054dc697e640f5a1da4181"
API_URL="https://api.deepseek.com/v1/chat/completions"

headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
payload = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Hello, are you working?"}]
}

response = requests.post(API_URL, json=payload, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
