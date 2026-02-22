"""WhatsApp Cloud API outbound message sender."""
import httpx
from app.config import settings

def get_whatsapp_url(phone_number_id: str):
    return f"{settings.WA_API_URL}/{phone_number_id}/messages"

def get_headers(access_token: str):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


async def send_text(to: str, text: str, phone_number_id: str, access_token: str):
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    async with httpx.AsyncClient() as client:
        await client.post(get_whatsapp_url(phone_number_id), json=payload, headers=get_headers(access_token))


async def send_interactive_buttons(to: str, body: str, buttons: list[dict], phone_number_id: str, access_token: str):
    """buttons: [{"id": "...", "title": "..."}]"""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"][:20]}}
                    for b in buttons[:3]
                ]
            },
        },
    }
    async with httpx.AsyncClient() as client:
        await client.post(get_whatsapp_url(phone_number_id), json=payload, headers=get_headers(access_token))


async def send_interactive_list(to: str, body: str, button_label: str, sections: list[dict], phone_number_id: str, access_token: str):
    """sections: [{"title": "...", "rows": [{"id": "...", "title": "...", "description": "..."}]}]"""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body},
            "action": {
                "button": button_label,
                "sections": sections,
            },
        },
    }
    async with httpx.AsyncClient() as client:
        await client.post(get_whatsapp_url(phone_number_id), json=payload, headers=get_headers(access_token))
