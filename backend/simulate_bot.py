import asyncio
import json
from app.bot.graph import compiled_graph

async def simulate():
    restaurant_id = "8584d86d-b191-4a9c-9b7f-a54f17a7abc7"
    branch_id = "70d0ca23-a03a-4d7b-a262-f075593cdde7"
    token = "MPcB_UtFl7DHSEfiso_m4LiGZRlspdi8Jl9XML7fno4"
    
    text = (
        f"HELLODINE_START\n"
        f"branch={branch_id}\n"
        f"table=1\n"
        f"token={token}"
    )
    
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "metadata": {"phone_number_id": "1004593176074926"},
                    "messages": [{
                        "from": "919090851660",
                        "id": "test_id_123",
                        "type": "text",
                        "text": {"body": text}
                    }]
                }
            }]
        }]
    }
    
    initial_state = {
        "raw_message": payload,
        "restaurant_id": restaurant_id,
        "access_token": "dummy_token",
        "phone_number_id": "1004593176074926"
    }
    
    print("Running graph simulation...")
    state = await compiled_graph.ainvoke(initial_state)
    
    print("\n--- Final State ---")
    print(f"Intent: {state.get('intent')}")
    print(f"Error: {state.get('error')}")
    print(f"Response: {json.dumps(state.get('final_response'), indent=2)}")

if __name__ == "__main__":
    asyncio.run(simulate())
