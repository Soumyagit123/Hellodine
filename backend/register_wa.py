import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def request_code():
    token = os.getenv("WA_ACCESS_TOKEN")
    phone_id = os.getenv("WA_PHONE_NUMBER_ID")
    
    url = f"https://graph.facebook.com/v19.0/{phone_id}/request_code"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "code_method": "SMS",
        "language": "en"
    }
    
    print(f"Requesting SMS code for Phone ID: {phone_id}...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, data=data)
        if resp.status_code == 200:
            print("SUCCESS: Code requested successfully! Please check your phone for an SMS from Meta.")
        else:
            print(f"ERROR: {resp.status_code}")
            print(resp.text)

async def verify_code(code: str):
    token = os.getenv("WA_ACCESS_TOKEN")
    phone_id = os.getenv("WA_PHONE_NUMBER_ID")
    
    url = f"https://graph.facebook.com/v19.0/{phone_id}/register"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "messaging_product": "whatsapp",
        "pin": code  # Note: Meta calls it pin sometimes but it's the SMS code for registration
    }
    
    print(f"Registering number with code: {code}...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, data=data)
        if resp.status_code == 200:
            print("SUCCESS: Registration Successful! Your number is now LIVE.")
        else:
            print(f"ERROR: Registration Error: {resp.status_code}")
            print(resp.text)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        asyncio.run(verify_code(sys.argv[1]))
    else:
        asyncio.run(request_code())
