"""Quick test: send a WhatsApp test message using Meta Cloud API."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import httpx
from app.config import settings


async def test_send():
    phone_number_id = "1004593176074926"
    access_token = settings.WA_ACCESS_TOKEN
    
    print(f"Phone Number ID: {phone_number_id}")
    print(f"Access Token (first 20 chars): {access_token[:20]}...")
    print(f"API URL: {settings.WA_API_URL}/{phone_number_id}/messages")
    
    # Send hello_world template to the test recipient
    if len(sys.argv) < 2:
        print("Usage: python test_wa_send.py <recipient_phone>")
        print("Example: python test_wa_send.py 919876543210")
        return
    to = sys.argv[1]
    
    url = f"{settings.WA_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {"code": "en_US"}
        }
    }
    
    print(f"\nSending to: {to}")
    print(f"URL: {url}")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        print(f"\nStatus: {resp.status_code}")
        print(f"Response: {resp.text}")


if __name__ == "__main__":
    asyncio.run(test_send())
