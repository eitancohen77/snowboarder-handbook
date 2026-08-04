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



app = FastAPI()

SNOW_KEYWORDS = [
    "snowboard", "board", "binding", "boots", "goggles",
    "jacket", "pants", "gloves", "helmet", "splitboard", "base layer",
    "ski"
]

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


serpapi_key = os.getenv("SERPAPI")

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
    


@app.get("/get_products")
def get_products(q: str, location: str = None):

    query = q.strip().lower()

    if not any(keyword in query for keyword in SNOW_KEYWORDS):
        raise HTTPException(
            status_code=400,
            detail="This search is limited to snowboarding/ski gear."
        )

    # data = search_google_shopping(q, location)
    # parsed_data = parse_shopping_results(data)

    return {"results": mockdata}

@app.get("/products")
def products():
    return FileResponse(BASE_DIR / "static" / "products.html")

@app.get("/resorts")
def resorts():
    return FileResponse(BASE_DIR / "static" / "resorts.html")



