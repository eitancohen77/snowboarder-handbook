# Snowboarder Handbook

<video controls src="snowboard guide.mp4" title="Title"></video>

A FastAPI app that lets users search for snowboarding/ski gear and compare prices
across retailers (via SerpApi's Google Shopping engine), plus a US ski resort
map with Peak Rating data. Search results are cached in Postgres so repeated or
similar searches don't burn API credits.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL (via Docker), with `pg_trgm` for fuzzy text matching
- **ORM:** SQLAlchemy
- **Product data:** SerpApi (Google Shopping engine)
- **Frontend:** Static HTML/JS served directly by FastAPI

## Prerequisites

- Python 3.11+ (project was built/tested on 3.13)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Postgres)
- A [SerpApi](https://serpapi.com/) account and API key

## Project Structure

```
snowboarder-handbook/
├── app/
│   ├── main.py              # FastAPI app, routes
│   ├── db.py                 # Database connection + SearchCache table
│   ├── cache.py               # Cache lookup (exact + fuzzy match) and save logic
│   ├── .env                   # API keys and DB connection string (not committed)
│   ├── etc/
│   │   └── tools.py           # parse_shopping_results() and helpers
│   └── static/
│       ├── products.html      # Product search UI
│       ├── resorts.html       # Ski resort map UI
│       └── js/
├── docker-compose.yml         # Postgres container definition
├── venv/                      # Python virtual environment (not committed)
└── requirements.txt
```

## Setup

### 1. Clone the repo and create a virtual environment

```bash
git clone <your-repo-url>
cd snowboarder-handbook
python -m venv venv
```

Activate it:

```powershell
# Windows (PowerShell)
venv\Scripts\activate
```

```bash
# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a file at `app/.env` (same folder as `main.py` and `db.py`) with:

```
SERPAPI=your_serpapi_key_here
DATABASE_URL=postgresql+psycopg2://snowboarder:snowboarder_dev_pw@localhost:5432/snowboarder
```

> **Note:** `.env` must live inside `app/`, not the project root — that's where
> `db.py` and `main.py` both look for it (`Path(__file__).resolve().parent / ".env"`).

Get your SerpApi key from [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key).

### 4. Start the database

From the project root (where `docker-compose.yml` lives):

```bash
docker compose up -d
```

This starts a Postgres 16 container named `snowboarder_db`, exposed on
`localhost:5432`, with data persisted in a named Docker volume
(`snowboarder_pgdata`) so it survives container restarts.

Check it's running:

```bash
docker ps
```

### 5. Run the app

From the project root:

```bash
uvicorn app.main:app --reload
```

On startup, `init_db()` automatically creates the `search_cache` table and
enables the `pg_trgm` Postgres extension if they don't already exist — no
manual migration step needed.

The app will be available at:

- `http://localhost:8000/products` — gear search UI
- `http://localhost:8000/resorts` — ski resort map
- `http://localhost:8000/get_products?q=...&location=...` — raw API endpoint

## How Search Caching Works

1. A search request first checks Postgres for a cached result:
   - **Exact match** — the normalized query matches a cached entry exactly.
   - **Fuzzy match** — if no exact match, `pg_trgm` similarity scoring finds a
     close-enough previous search (e.g. "infuse boots" matching a cached
     "Vans Infuse Snowboard Boots" search).
2. If either match is found (and isn't older than the cache TTL — 3 days by
   default), the cached results are returned and **no SerpApi call is made**.
3. If nothing matches, SerpApi is called live, and the parsed results are
   saved to the cache for future searches to reuse.

The API response includes a `"source"` field (`"exact"`, `"fuzzy"`, or
`"live"`) so you can see in the browser network tab whether a search hit the
cache or went out to SerpApi.

Tuning knobs (in `app/cache.py`):

- `CACHE_TTL_DAYS` — how long a cached result stays valid before being treated
  as stale (prices/stock drift over time).
- `SIMILARITY_THRESHOLD` — how loose or strict fuzzy matching is (0–1; higher
  = stricter).

## Search Scope

`/get_products` rejects queries that don't contain a snow-sports-related
keyword (see `SNOW_KEYWORDS` in `main.py`), returning a `400` error. This
keeps the endpoint from being used as a general-purpose product search proxy,
since it's a public GET endpoint that can be called directly, not just
through the frontend.

## Troubleshooting

**`ModuleNotFoundError: No module named 'urllib3.packages.six.moves'`**
Corrupted/mismatched `requests`/`urllib3` install. Fix:
```bash
pip uninstall requests urllib3 -y
pip install requests
```

**`sqlalchemy.exc.ArgumentError: Expected string or URL object, got None`**
`DATABASE_URL` isn't being loaded. Usually means:
- `.env` is in the wrong folder (must be `app/.env`)
- The `DATABASE_URL` line is missing or misspelled in `.env`
- `load_dotenv()` is pointed at the wrong path in `db.py`/`main.py`

**`RuntimeError: Directory 'static' does not exist`**
Uvicorn was started from a different working directory than expected.
Run `uvicorn app.main:app --reload` from the project root, and make sure
`StaticFiles` is mounted using an absolute path
(`Path(__file__).resolve().parent / "static"`), not a relative `"static"` string.

**`{"status":429,"body":"local_rate_limited"}` when hitting a store's own
`/products.json` directly (not via this app)**
Unrelated to this project's SerpApi flow — that's a Shopify/Cloudflare
anti-bot rate limit on datacenter IPs, not something fixable with headers or
retries.

## Resetting the Database

To wipe cached search data and start fresh:

```bash
docker compose down -v
docker compose up -d
```

The `-v` flag removes the named volume, so Postgres starts with an empty
database and `init_db()` recreates the schema on the next app startup.