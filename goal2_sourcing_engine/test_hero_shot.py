import asyncio
import json
import logging
from photo_director import PhotoDirector
from generation_router import GenerationRouter

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def test_main_account():
    # 1. Use Photo Director to get prompts
    director = PhotoDirector()
    shoot = director.plan_shoot(
        product_name="Flame Print Washed Denim Set",
        garment_type="set",
        style="streetwear",
        companion_items=["khaki cargo shorts", "studded star belt", "red Dunk Low sneakers"],
    )
    
    # 2. Extract Hero and Flatlay shots
    hero_shot = next((s for s in shoot if s["name"] == "hero"), None)
    flatlay_shot = next((s for s in shoot if s["name"] == "flatlay"), None)
    
    if not hero_shot:
        logging.error("Hero shot not found in shoot plan.")
        return

    logging.info(f"🚀 Testing Main Account with Hero Shot:\n{hero_shot['prompt']}\n")
    
    try:
        # Call generation router (which calls the local bridge)
        logging.info("Sending request to generation router...")
        router = GenerationRouter()
        result = await router.generate_image(
            prompt=hero_shot["prompt"], 
            reference_image_url=None,
            aspect="3:4"
        )
        
        if result:
            logging.info(f"✅ SUCCESS! Image saved to: {result}")
        else:
            logging.error("❌ FAILED: Received None. Check bridge logs.")
            
    except Exception as e:
        logging.error(f"❌ Error during generation test: {e}")

if __name__ == "__main__":
    asyncio.run(test_main_account())
