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



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

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

    # data = search_google_shopping(q, location)
    # parsed_data = parse_shopping_results(data)

    return {"results": mockdata}

@app.get("/products")
def products():
    return FileResponse(BASE_DIR / "static" / "products.html")

@app.get("/resorts")
def resorts():
    return FileResponse(BASE_DIR / "static" / "resorts.html")


app.mount("/static", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
