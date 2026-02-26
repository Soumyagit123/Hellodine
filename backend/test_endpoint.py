import httpx
import asyncio
import json

async def test_webhook():
    url = "https://hellodine-api.onrender.com/api/webhook/8584d86d-b191-4a9c-9b7f-a54f17a7abc7"
    
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "1359859199307784",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "919090851660",
                                "phone_number_id": "1001763716355748"
                            },
                            "contacts": [{"profile": {"name": "Test User"}, "wa_id": "919090851660"}],
                            "messages": [
                                {
                                    "from": "919090851660",
                                    "id": "test_id_123",
                                    "timestamp": "1772112670",
                                    "text": {"body": "DIAGNOSTIC_TEST"},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    print(f"Sending diagnostic webhook to {url}...")
    async with httpx.AsyncClient() as client:
        # Note: We skip the signature verification for this test if app_secret is enabled 
        # but the endpoint should still LOG the received payload before verification.
        resp = await client.post(url, json=payload)
        print(f"Response Status: {resp.status_code}")
        print(f"Response Body: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test_webhook())
