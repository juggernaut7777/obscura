import os
import sys
import httpx
import asyncio
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Safe print for Windows
def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

async def purge_messages(limit: int = 100):
    token = os.getenv("DISCORD_TOKEN", "")
    channel_id = os.getenv("DISCORD_REVIEW_CHANNEL", "")
    
    if not token or not channel_id:
        safe_print("[!] Error: DISCORD_TOKEN or DISCORD_REVIEW_CHANNEL is missing from .env file.")
        return

    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit={limit}"
    
    safe_print(f"[*] Fetching last {limit} messages from Discord channel {channel_id}...")
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                safe_print(f"[!] Failed to fetch messages ({resp.status_code}): {resp.text}")
                return
            
            messages = resp.json()
            safe_print(f"[*] Found {len(messages)} messages total.")
            
            # Fetch bot's application info to know our own ID
            bot_info_resp = await client.get("https://discord.com/api/v10/users/@me", headers=headers)
            bot_id = ""
            if bot_info_resp.status_code == 200:
                bot_id = bot_info_resp.json().get("id", "")
                safe_print(f"[*] Identified bot user ID: {bot_id}")

            deleted_count = 0
            for msg in messages:
                msg_id = msg.get("id")
                author = msg.get("author", {})
                author_id = author.get("id")
                content = msg.get("content", "")
                
                # Check if it was sent by our bot, or if it is a review post
                is_bot = author_id == bot_id or author.get("bot", False)
                is_review = "REVIEW:" in content or "Reply with image numbers" in content or "Kakobuy" in content
                
                if is_bot or is_review:
                    del_url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{msg_id}"
                    del_resp = await client.delete(del_url, headers=headers)
                    if del_resp.status_code in [200, 204]:
                        deleted_count += 1
                        safe_print(f"   [-] Deleted review message: {msg_id} (Content summary: {content[:30]}...)")
                    else:
                        # If we have Manage Messages permission, we can delete user replies too
                        if is_review:
                            safe_print(f"   [!] Failed to delete message {msg_id}: {del_resp.status_code}")
                    # Sleep slightly to respect Discord rate limits
                    await asyncio.sleep(0.5)
            
            safe_print(f"[+] Clean-up complete. Deleted {deleted_count} messages.")
            
        except Exception as e:
            safe_print(f"[!] Exception during Discord cleaning: {e}")

if __name__ == "__main__":
    limit = 100
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
    asyncio.run(purge_messages(limit))
