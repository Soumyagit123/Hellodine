import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def live_send_test(to_phone: str):
    token = os.getenv("WA_ACCESS_TOKEN")
    phone_id = os.getenv("WA_PHONE_NUMBER_ID")
    
    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try sending a simple text message
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": "🚀 Hello! This is a production test from your bot. If you see this, your credentials are workng!"}
    }
    
    print(f"Sending test message from {phone_id} to {to_phone}...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code == 200:
            print("SUCCESS: Message sent! Meta accepted it.")
            print(f"Response: {resp.json()}")
        else:
            print(f"ERROR: {resp.status_code}")
            print(resp.text)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        asyncio.run(live_send_test(sys.argv[1]))
    else:
        # Default to yours for testing if none provided
        asyncio.run(live_send_test("919090851660"))
