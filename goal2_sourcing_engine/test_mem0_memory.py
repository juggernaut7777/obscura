import pytest
import sqlite3
import os
import json
import time
from mem0_memory import Mem0Memory

def test_add_products_batch_sql_injection_fix():
    db_path = "/tmp/test_mem0.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    mem = Mem0Memory(db_path)

    # Insert some valid products to ensure batch processing works
    products = [
        {"productName": "Valid Product", "productUrl": "http://example.com/valid", "price": 10},
        {"productName": "Another Product", "productUrl": "http://example.com/another", "price": 20},
    ]
    mem.add_products_batch(products)

    # Sleep to get different timestamps for prod id
    time.sleep(1.1)

    # Try an injection in URL
    # This might have worked previously if string interpolation was used unsafely but placeholders prevent it
    # We just want to ensure we don't crash when passing these strings.
    malicious_products = [
        {"productName": "Evil", "productUrl": "http://example.com/evil') OR 1=1 --", "price": 10}
    ]
    mem.add_products_batch(malicious_products)

    time.sleep(1.1)
    # Test batch processing again
    mem.add_products_batch(products)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 3
