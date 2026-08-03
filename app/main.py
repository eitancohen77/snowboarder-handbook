from fastapi import FastAPI
import requests
import os
from dotenv import load_dotenv
from pathlib import Path


app = FastAPI()
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

serpapi_key = os.getenv("SERPAPI")

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

def search_google_shopping(query: str, location: str):
    # THIS WORKS CUT IT OFF TO SAFE SEARCHES.
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": serpapi_key,
    }
    if location:
        params["location"] = location
    response = requests.get("https://serpapi.com/search", params=params)
    return response.json()
    

@app.get("/products")
def get_products():
    data = "HELLO THERE"

    data = search_google_shopping("Vans Infuse Snowboard Boot", "New York")
    parsed_data = parse_shopping_results(data)

    return parsed_data


@app.get("/")
def home():
    return {
        "message": "Snowboard API running"
    }