"""WhatsApp Webhook router — /api/webhook"""
from fastapi import APIRouter, Request, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.bot.graph import compiled_graph
from app.database import AsyncSessionLocal
from app.models.logs import WhatsAppMessageLog, MessageDirection
from app.bot.wa_sender import send_text, send_interactive_buttons, send_interactive_list
from sqlalchemy.exc import IntegrityError
import uuid

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


@router.get("")
async def verify_webhook(request: Request):
    """Meta webhook verification handshake."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == settings.WA_WEBHOOK_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(403, "Verification failed")


@router.post("")
async def receive_webhook(request: Request):
    """Inbound WhatsApp messages → LangGraph bot."""
    payload = await request.json()

    # Quick dedup + log
    try:
        entry = payload.get("entry", [{}])[0]
        value = entry.get("changes", [{}])[0].get("value", {})
        messages = value.get("messages", [])
        phone_number_id = value.get("metadata", {}).get("phone_number_id", "")

        if not messages:
            return {"status": "ok"}  # status update (delivered/read), ignore

        msg = messages[0]
        wa_message_id = msg.get("id", str(uuid.uuid4()))
        wa_user_id = msg.get("from", "")

        # Save inbound log (unique constraint on wa_message_id = dedup)
        async with AsyncSessionLocal() as db:
            from app.models.tenancy import Restaurant
            from sqlalchemy import select
            rest_result = await db.execute(
                select(Restaurant).where(Restaurant.whatsapp_phone_number_id == phone_number_id)
            )
            restaurant = rest_result.scalar_one_or_none()
            if restaurant:
                try:
                    log = WhatsAppMessageLog(
                        restaurant_id=restaurant.id,
                        wa_message_id=wa_message_id,
                        direction=MessageDirection.INBOUND,
                        message_type=msg.get("type", "text"),
                        raw_payload=payload,
                    )
                    db.add(log)
                    await db.commit()
                except IntegrityError:
                    # Duplicate message — already processed
                    return {"status": "duplicate"}

    except Exception:
        pass  # Don't let logging failure block processing

    # Run LangGraph bot
    initial_state = {"raw_message": payload}
    state = await compiled_graph.ainvoke(initial_state)

    # Send reply
    final = state.get("final_response")
    to = state.get("wa_user_id", "")

    if final and to:
        msg_type = final.get("type", "text")
        if msg_type == "text":
            await send_text(to, final["body"])
        elif msg_type == "buttons":
            await send_interactive_buttons(to, final["body"], final["buttons"])
        elif msg_type == "list":
            await send_interactive_list(to, final["body"], final.get("button_label", "View"), final["sections"])

    return {"status": "ok"}
