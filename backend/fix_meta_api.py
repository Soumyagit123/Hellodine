import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def fix_meta_config():
    # Credentials from .env
    token = os.getenv("WA_ACCESS_TOKEN")
    app_id = os.getenv("WA_APP_ID")
    waba_id = os.getenv("WA_Business_Account_ID")
    callback_url = "https://hellodine-api.onrender.com/api/webhook/8584d86d-b191-4a9c-9b7f-a54f17a7abc7"
    verify_token = "hellodine_verify_token_123"

    print(f"--- Meta API Handshake Fix ---")
    print(f"App ID: {app_id}")
    print(f"WABA ID: {waba_id}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Update the App's Webhook Subscription
        # Using App Access Token (ID|Secret) instead of User Token
        app_secret = os.getenv("WA_APP_SECRET")
        app_access_token = f"{app_id}|{app_secret}"
        
        sub_url = f"https://graph.facebook.com/v19.0/{app_id}/subscriptions"
        sub_params = {
            "object": "whatsapp_business_account",
            "callback_url": callback_url,
            "verify_token": verify_token,
            "fields": "messages",
            "access_token": app_access_token
        }
        
        print("\nStep 1: Updating App Webhook Subscription (using App Token)...")
        resp1 = await client.post(sub_url, params=sub_params)
        if resp1.status_code == 200:
            print("SUCCESS: Webhook URL and Verify Token set at App level.")
        else:
            print(f"ERROR: {resp1.status_code}")
            print(resp1.text)

        # 2. Subscribe the WABA (WhatsApp Business Account) to the App
        # This "wires" the specific business account to use this App's webhooks.
        waba_sub_url = f"https://graph.facebook.com/v19.0/{waba_id}/subscribed_apps"
        waba_params = {
            "access_token": token
        }
        
        print("\nStep 2: Subscribing Business Account to App...")
        resp2 = await client.post(waba_sub_url, params=waba_params)
        if resp2.status_code == 200:
            print("SUCCESS: Business Account is now subscribed to the App.")
        else:
            print(f"ERROR: {resp2.status_code}")
            print(resp2.text)

        # 3. Verify current subscriptions
        print("\nStep 3: Verifying Subscriptions...")
        verify_url = f"https://graph.facebook.com/v19.0/{app_id}/subscriptions"
        v_params = {"access_token": app_access_token}
        resp3 = await client.get(verify_url, params=v_params)
        if resp3.status_code == 200:
            print("Current Subscriptions Data:")
            print(resp3.json())
        else:
            print(f"Failed to fetch subscriptions: {resp3.status_code}")
            print(resp3.text)

if __name__ == "__main__":
    asyncio.run(fix_meta_config())
