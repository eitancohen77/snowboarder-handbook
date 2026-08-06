from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import requests
import os
from dotenv import load_dotenv
from pathlib import Path
from parsedmockdata import mockdata
from app.etc.tools import parse_shopping_results
from fastapi import HTTPException
from app.db import init_db
from app.cache import get_cached_results, save_to_cache



app = FastAPI()

SNOW_KEYWORDS = [
    "snowboard", "board", "binding", "boots", "goggles",
    "jacket", "pants", "gloves", "helmet", "splitboard", "base layer",
    "ski"
]


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
serpapi_key = os.getenv("SERPAPI")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()

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
    

@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "home.html")


@app.get("/get_products")
def get_products(q: str, location: str = None):
    query = q.strip().lower()

    if not any(keyword in query for keyword in SNOW_KEYWORDS):
        raise HTTPException(
            status_code=400,
            detail="This search is limited to snowboarding/ski gear."
        )

    cached, match_type = get_cached_results(q, location)
    if cached is not None:
        return {"results": cached, "source": match_type}  # no SerpApi call


    data = search_google_shopping(q, location)
    parsed_data = parse_shopping_results(data)
    save_to_cache(q, location, parsed_data)

    return {"results": parsed_data, "source": "live"}

@app.get("/products")
def products():
    return FileResponse(BASE_DIR / "static" / "products.html")

@app.get("/resorts")
def resorts():
    return FileResponse(BASE_DIR / "static" / "resorts.html")



