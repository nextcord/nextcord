import requests

url = "webhook url"

embed = {
    "description": "text in embed",
    "title": "embed title"
    }

data = {
    "content": "message content",
    "username": "custom username",
    "embeds": [
        embed
        ],
}

headers = {
    "Content-Type": "application/json"
}

result = requests.post(url, json=data, headers=headers)
if 200 <= result.status_code < 300:
    print(f"Webhook sent {result.status_code}")
else:
    print(f"Not sent with {result.status_code}, response:\n{result.json()}")
