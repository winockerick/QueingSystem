import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Briq API settings
api_key = os.getenv("BRIQ_API_KEY")
url = "https://karibu.briq.tz/v1/message/send-instant"
headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json",
    "Accept": "application/json"
}
payload = {
    "content": "This is a test SMS from Briq.",
    "recipients": ["+255612685335"],
    "sender_id": "BRIQ"
}

# Send POST request
try:
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    print(f"SMS sent successfully: {response.json()}")
except requests.exceptions.HTTPError as e:
    print(f"Failed to send SMS: {e}")
    print(f"Response: {response.text}")
    print(f"Headers: {response.headers}")
except Exception as e:
    print(f"Error: {e}")
