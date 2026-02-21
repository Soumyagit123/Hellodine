"""WhatsApp Cloud API outbound message sender."""
import httpx
from app.config import settings


BASE_URL = f"{settings.WA_API_URL}/{settings.WA_PHONE_NUMBER_ID}/messages"
HEADERS = {
    "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}


async def send_text(to: str, text: str):
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    async with httpx.AsyncClient() as client:
        await client.post(BASE_URL, json=payload, headers=HEADERS)


async def send_interactive_buttons(to: str, body: str, buttons: list[dict]):
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
        await client.post(BASE_URL, json=payload, headers=HEADERS)


async def send_interactive_list(to: str, body: str, button_label: str, sections: list[dict]):
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
        await client.post(BASE_URL, json=payload, headers=HEADERS)
