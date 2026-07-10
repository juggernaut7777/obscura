import timeit
import random
import string
import copy

def generate_data(num_items):
    final_products = []
    product_groups = {}
    for i in range(num_items):
        slug = f"prod-{i}"
        final_products.append({
            "id": slug,
            "name": f"Product {i}",
            "price": random.randint(10, 100),
            "category": "shoe" if i % 10 == 0 else "clothing",
            "colors": [{"name": "black"}]
        })
        product_groups[slug] = {
            "slug": slug,
            "name": f"Product {i}",
            "is_set": i % 5 == 0  # 20% are sets
        }
    return final_products, product_groups

def original_logic(final_products, product_groups):
    for group_key, group in product_groups.items():
        if group.get("is_set"):
            this_product = next((p for p in final_products if p["id"] == group["slug"]), None)
            if not this_product:
                continue

def optimized_logic(final_products, product_groups):
    final_products_dict = {p["id"]: p for p in final_products}
    for group_key, group in product_groups.items():
        if group.get("is_set"):
            this_product = final_products_dict.get(group["slug"])
            if not this_product:
                continue

if __name__ == "__main__":
    final_products, product_groups = generate_data(5000)

    t_orig = timeit.timeit(lambda: original_logic(final_products, product_groups), number=10)
    print(f"Original: {t_orig:.4f} seconds")

    t_opt = timeit.timeit(lambda: optimized_logic(final_products, product_groups), number=10)
    print(f"Optimized: {t_opt:.4f} seconds")

    if t_opt > 0:
        print(f"Improvement: {t_orig / t_opt:.2f}x faster")
