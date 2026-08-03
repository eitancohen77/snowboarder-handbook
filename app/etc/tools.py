def parse_shopping_results(data: dict) -> list[dict]:
    results = []
    for item in  data.get("shopping_results", []):
        results.append({
            "title": item.get("title"),
            "store": item.get("source"),
            "price": item.get("price"),
            "extracted_price": item.get("extracted_price"),
            "old_price": item.get("old_price"),
            "rating": item.get("rating"),
            "reviews": item.get("reviews"),
            "link": item.get("product_link"),
            "thumbnail": item.get("thumbnail"),
            "delivery": item.get("delivery"),
            "tag": item.get("tag"),  # e.g. "30% OFF"
        })
    return results