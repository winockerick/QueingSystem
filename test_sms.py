import os
from dotenv import load_dotenv
import briq
import time

# Load environment variables
load_dotenv()

# Initialize Briq client
client = briq.Client()
client.set_api_key(os.getenv("BRIQ_API_KEY"))

def send_sms(phone_number, message, max_retries=3):
    try:
        # Ensure phone number is in international format (+255 for Tanzania)
        if not phone_number.startswith("+"):
            phone_number = f"+255{phone_number[-9:]}"
        for attempt in range(max_retries):
            try:
                result = client.message.send_instant(
                    content=message,
                    recipients=[phone_number],
                    sender_id="BRIQ"
                )
                print(f"SMS sent to {phone_number}: {result}")
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed to send SMS to {phone_number} after {max_retries} attempts: {e}")
                    return None
                time.sleep(1)
    except Exception as e:
        print(f"Failed to process SMS for {phone_number}: {e}")
        return None

if __name__ == "__main__":
    # Test SMS
    test_phone = "0712345678"  # Replace with your test phone number
    test_message = "This is a test SMS from Briq."
    send_sms(test_phone, test_message)