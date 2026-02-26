"""Bot node — restaurant_chat for general Q&A."""
import uuid
from app.bot.state import BotState
from app.database import AsyncSessionLocal
from app.models.tenancy import Restaurant, Branch
from sqlalchemy import select
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7,
)

async def restaurant_chat(state: BotState) -> BotState:
    """Answers general questions about the restaurant using LLM + DB context."""
    restaurant_id = state.get("restaurant_id")
    branch_id = state.get("branch_id")
    message = state.get("message_text", "")

    if not restaurant_id:
        return state

    async with AsyncSessionLocal() as db:
        # Fetch restaurant and branch info for context
        res = await db.execute(select(Restaurant).where(Restaurant.id == uuid.UUID(restaurant_id)))
        restaurant = res.scalar_one_or_none()
        
        branch_info = ""
        if branch_id:
            br_res = await db.execute(select(Branch).where(Branch.id == uuid.UUID(branch_id)))
            branch = br_res.scalar_one_or_none()
            if branch:
                branch_info = f"This branch is located at {branch.address}, {branch.city}, {branch.state} - {branch.pincode}."

        restaurant_name = restaurant.name if restaurant else "our restaurant"
        
        system_prompt = f"""You are a helpful, friendly, and professional AI assistant for {restaurant_name}.
{branch_info}

Guidelines:
1. Answer questions about the restaurant, its food, culture, and services.
2. If asked about ratings or staff, be polite and say we strive for excellence.
3. Keep answers concise (max 2-3 sentences).
4. Do NOT make up specific menu prices if you don't have them, but you can say we have a variety of items.
5. If the user wants to order, guide them to say "show menu" or "list items".
6. Use emojis to be friendly.
"""

        try:
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=message)
            ])
            state["final_response"] = {
                "type": "text",
                "body": response.content.strip()
            }
        except Exception as e:
            print(f"Chat node error: {e}")
            state["final_response"] = {
                "type": "text",
                "body": f"I'm here to help! Feel free to ask about {restaurant_name} or just say 'menu' to see our delicious food! 🥗"
            }

    return state
