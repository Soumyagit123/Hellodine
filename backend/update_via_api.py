
import requests
import json
import base64

BASE_URL = "http://localhost:8000/api"

def update_via_api():
    # 1. Login
    login_data = {
        "username": "+91 0000000000",
        "password": "owner123"
    }
    print("Logging in...")
    resp = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # 2. Find Big King
    print("Fetching restaurants...")
    resp = requests.get(f"{BASE_URL}/admin/restaurants", headers=headers)
    if resp.status_code != 200:
        print(f"Failed to fetch restaurants: {resp.text}")
        return
    
    restaurants = resp.json()
    big_king = next((r for r in restaurants if r['name'] == 'Big King'), None)
    
    if not big_king:
        print("Big King not found in:")
        for r in restaurants:
            print(f"- {r['name']}")
        return

    print(f"Found Big King ID: {big_king['id']}")

    # 3. Update
    update_payload = {
        "whatsapp_phone_number_id": "+1 555 153 9633",
        "whatsapp_display_number": "BigKing",
        "whatsapp_access_token": "EAANNT1FcZBDMBQ378GbPG7fY5skKH9rZCrpoAQlgEtX6ZAvnyRgOJbkcOfxGZAOjwqRO1Dq3gCRyBjmAOEhYyReMVMZCBut66g5E9bN7ZA8lKTH2dXpaZCB3vINhWHlctft1jRPK2iQcNySLVUNxpfAYEalZCGjZCgV4KVzv8FPRwDpCS6eT9FzqUKUlFyrMg4ueiU6mUoVGPLi21ucN1mQlFpxGbyzEmB14palKxcywrzmWABB0YZBQDo9IjovSLCEMV5eIb06ZArheMh8lXjF3AEtWo1iuLlN",
        "whatsapp_verify_token": "hellodine_verify_token_123",
        "whatsapp_app_id": "929427992934451",
        "whatsapp_app_secret": "67a16d5ae79f444c918be1fb7d316ed6"
    }
    
    print("Updating credentials...")
    resp = requests.patch(f"{BASE_URL}/admin/restaurants/{big_king['id']}", json=update_payload, headers=headers)
    
    if resp.status_code == 200:
        print("Update successful!")
        print(json.dumps(resp.json(), indent=2))
    else:
        print(f"Update failed: {resp.text}")

if __name__ == "__main__":
    update_via_api()
