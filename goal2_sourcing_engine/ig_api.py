"""
OBSCURA IG Intelligence API (instagrapi wrapper)
================================================
Replaces slow browser scraping with direct API calls for faster,
deeper intelligence gathering (Brand Scouting, Competitor Analysis).
"""
import os
import json
import random
import time
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

BASE_DIR = Path(__file__).parent
# Use a specific session file for the API to avoid mixing with Playwright
SESSION_FILE = BASE_DIR / "ig_api_session.json"

class IGApi:
    def __init__(self):
        self.client = Client()
        self.logged_in = False
        
        # Load proxy if available (crucial for API scraping)
        proxy = os.getenv("IG_PROXY")
        if proxy:
            self.client.set_proxy(proxy)
            
        # Add random delay between requests to avoid rate limits
        self.client.delay_range = [3, 7] 

    def login(self):
        """Login using session file or environment variables."""
        if self.logged_in:
            return True
            
        print("[IG API] Authenticating...")
        try:
            if SESSION_FILE.exists():
                self.client.load_settings(SESSION_FILE)
                self.client.login(os.getenv("IG_USERNAME"), os.getenv("IG_PASSWORD"))
                self.logged_in = True
                print("[+] Logged in via session.")
                return True
        except Exception as e:
            print(f"[-] Session login failed: {e}")
            
        # Fallback to fresh login
        username = os.getenv("IG_USERNAME")
        password = os.getenv("IG_PASSWORD")
        
        if not username or not password:
            print("[!] IG_USERNAME or IG_PASSWORD not set in environment.")
            return False
            
        try:
            self.client.login(username, password)
            self.client.dump_settings(SESSION_FILE)
            self.logged_in = True
            print("[+] Fresh login successful.")
            return True
        except Exception as e:
            print(f"[!] Login completely failed: {e}")
            return False

    def get_brand_intel(self, username):
        """Get deep intelligence on a brand/user."""
        if not self.login():
            return None
            
        try:
            user_id = self.client.user_id_from_username(username)
            info = self.client.user_info(user_id)
            
            # Calculate engagement rate from last 12 posts
            medias = self.client.user_medias(user_id, 12)
            total_likes = 0
            total_comments = 0
            
            for m in medias:
                total_likes += m.like_count
                total_comments += m.comment_count
                
            avg_engagement = 0
            if info.follower_count > 0 and len(medias) > 0:
                avg_likes = total_likes / len(medias)
                avg_comments = total_comments / len(medias)
                avg_engagement = ((avg_likes + avg_comments) / info.follower_count) * 100
                
            # Analyze recent content tags/types
            content_types = [m.media_type for m in medias]
            has_reels = 2 in content_types  # 2 usually denotes video/reel
            
            return {
                "username": info.username,
                "full_name": info.full_name,
                "followers": info.follower_count,
                "following": info.following_count,
                "biography": info.biography,
                "external_url": info.external_url,
                "is_business": info.is_business,
                "post_count": info.media_count,
                "avg_engagement_rate": round(avg_engagement, 2),
                "uses_reels": has_reels,
                "contact_phone": info.contact_phone_number,
                "public_email": info.public_email
            }
            
        except Exception as e:
            print(f"[!] Failed to get intel for {username}: {e}")
            return None

    def search_users_by_keyword(self, keyword, limit=10):
        """Search for users by keyword."""
        if not self.login():
            return []
            
        try:
            results = self.client.search_users(keyword)
            # Filter and return the top matches
            return [u.username for u in results[:limit]]
        except Exception as e:
            print(f"[!] Search failed for {keyword}: {e}")
            return []

if __name__ == "__main__":
    api = IGApi()
    # Test
    # print(api.get_brand_intel("craftythrift_"))
