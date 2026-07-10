import asyncio
import sys
from social_autoposter import SocialPoster

async def main():
    print("=======================================")
    print("📱 SINGLE-BRAND ACCOUNT LINKING WIZARD")
    print("=======================================")
    print("This connects your AI Engine to your social accounts securely.")
    print("It uses your local home IP (safe for a single brand).")
    print("")
    print("Which platform do you want to link?")
    print("1) TikTok")
    print("2) Instagram")
    print("3) Pinterest")
    print("4) Exit")
    
    choice = input("\nEnter choice (1-4): ")
    
    mapping = {"1": "tiktok", "2": "instagram", "3": "pinterest"}
    
    if choice in mapping:
        platform = mapping[choice]
        print(f"\nLaunching secure browser for {platform.title()}...")
        poster = SocialPoster(headless=False)
        await poster.login_platform(platform)
        print(f"\n✅ {platform.title()} linked successfully!")
    elif choice == "4":
        sys.exit(0)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    asyncio.run(main())
