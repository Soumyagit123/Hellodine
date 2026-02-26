"""WhatsApp Webhook router — /api/webhook"""
from fastapi import APIRouter, Request, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.bot.graph import compiled_graph
from app.database import AsyncSessionLocal
from app.models.logs import WhatsAppMessageLog, MessageDirection
from app.bot.wa_sender import send_text, send_interactive_buttons, send_interactive_list
from app.models.tenancy import Restaurant
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import hmac
import hashlib
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


def verify_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """Verify Meta's X-Hub-Signature-256."""
    if not signature or not signature.startswith("sha256="):
        return False
    
    expected = hmac.new(
        app_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)


@router.get("/{restaurant_id}")
async def verify_webhook(restaurant_id: uuid.UUID, request: Request):
    """Meta webhook verification handshake per restaurant."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
        restaurant = result.scalar_one_or_none()
        if not restaurant:
            raise HTTPException(404, "Restaurant not found")

    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    # Use restaurant-specific verify token, fallback to global settings
    verify_token = restaurant.whatsapp_verify_token or settings.WA_WEBHOOK_VERIFY_TOKEN
    if mode == "subscribe" and token == verify_token:
        return Response(content=challenge, media_type="text/plain")
    
    raise HTTPException(403, "Verification failed")


@router.post("/{restaurant_id}")
async def receive_webhook(restaurant_id: uuid.UUID, request: Request):
    """Inbound WhatsApp messages per restaurant → LangGraph bot."""
    body_raw = await request.body()
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "reason": "invalid_json"}
        
    signature = request.headers.get("X-Hub-Signature-256")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
        restaurant = result.scalar_one_or_none()
        if not restaurant:
            raise HTTPException(404, "Restaurant not found")
        
        access_token = restaurant.whatsapp_access_token
        app_secret = restaurant.whatsapp_app_secret

        if not access_token:
            logger.error(f"Missing WhatsApp Access Token for restaurant {restaurant_id}")
            return {"status": "ignored", "reason": "missing_credentials"}

        # Verify signature if secret is provided
        if app_secret:
            if not verify_signature(body_raw, signature, app_secret):
                raise HTTPException(401, "Invalid signature")

        # Run LangGraph bot
        try:
            initial_state = {
                "raw_message": payload,
                "restaurant_id": str(restaurant_id)
            }
            initial_state["access_token"] = access_token
            initial_state["phone_number_id"] = restaurant.whatsapp_phone_number_id
            
            logger.info(f"Invoking graph for restaurant {restaurant.name} ({restaurant_id})")
            state = await compiled_graph.ainvoke(initial_state)
            logger.info(f"Graph execution finished. Intent: {state.get('intent')}, Error: {state.get('error')}")

            # Send reply using restaurant credentials (NO FALLBACKS)
            final = state.get("final_response")
            to = state.get("wa_user_id", "")
            p_id = restaurant.whatsapp_phone_number_id
            token = restaurant.whatsapp_access_token

            if final and to and p_id and token:
                msg_type = final.get("type", "text")
                logger.info(f"Sending {msg_type} reply to {to} via {p_id}")
                try:
                    if msg_type == "text":
                        resp = await send_text(to, final["body"], p_id, token)
                    elif msg_type == "buttons":
                        resp = await send_interactive_buttons(to, final["body"], final["buttons"], p_id, token)
                    elif msg_type == "list":
                        resp = await send_interactive_list(to, final["body"], final.get("button_label", "View"), final["sections"], p_id, token)
                    
                    logger.info(f"WhatsApp API response: {resp}")
                except Exception as e:
                    logger.exception(f"Failed to send WhatsApp message: {str(e)}")
            elif final and to:
                logger.error(f"Cannot send reply: Missing credentials (p_id={p_id}, token={'set' if token else 'missing'})")
            else:
                logger.warning(f"No response prepared for message from {to}")
                
        except Exception as e:
            logger.exception(f"Error in LangGraph execution: {str(e)}")
            # Optional: send a generic error message to the user?
            # await send_text(to, "Sorry, I'm having trouble processing your request. Please try again later.", p_id, token)

    return {"status": "ok"}
