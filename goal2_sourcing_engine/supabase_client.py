import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[!] ERROR: Supabase URL or Key is missing from .env")
    supabase = None
else:
    # Initialize client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_product_to_storefront(product_data: dict):
    """
    Uploads a new product to the Supabase database.
    Expects product_data to have: title, description, price, category, images (list), source_url
    """
    if supabase is None:
        print("[-] Skipping upload: Supabase client is not initialized.")
        return False

    try:
        # Format the data for the database
        db_payload = {
            "title": product_data.get("title", "Unknown Product"),
            "description": product_data.get("description", ""),
            "price": float(product_data.get("price", 0.0)),
            "category": product_data.get("category", "streetwear"),
            "images": product_data.get("images", []),
            "source_url": product_data.get("productUrl", ""),
            "supplier_price": float(product_data.get("supplier_cost", 0.0))
        }

        # Insert into 'products' table
        response = supabase.table("products").insert(db_payload).execute()
        
        if response.data:
            print(f"[+] Successfully uploaded to Storefront DB: {db_payload['title']}")
            return True
        else:
            print(f"[-] Failed to upload: {db_payload['title']}")
            return False

    except Exception as e:
        print(f"[!] Error syncing to Supabase: {e}")
        return False

if __name__ == "__main__":
    # Test connection
    print(f"Testing connection to {SUPABASE_URL}...")
    try:
        res = supabase.table("products").select("id").limit(1).execute()
        print("[+] Connection successful!")
    except Exception as e:
        print(f"[-] Connection failed or table 'products' does not exist yet. Error: {e}")
