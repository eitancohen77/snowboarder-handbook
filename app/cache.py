import re
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from app.db import SessionLocal, SearchCache
from app.db import ApiUsage

CACHE_TTL_DAYS = 30           # how long a cached search stays "fresh" (changed it to 30 from 3 because the api gets refreshed every 30 days)
SIMILARITY_THRESHOLD = 0.45   # 0-1, higher = stricter fuzzy match
MONTHLY_BUDGET = 230

def get_current_month_usage(db):
    month = datetime.now().strftime("%Y-%m")
    row = db.query(ApiUsage).filter_by(month=month).first()
    if not row:
        row = ApiUsage(month=month, call_count =0)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row

def increment_usage(db):
    row = get_current_month_usage(db)
    row.call_count += 1
    db.commit()

def budget_remaining(db):
    row = get_current_month_usage(db)
    return MONTHLY_BUDGET - row.call_count

def normalize(q: str) -> str:
    q = q.lower().strip()
    q = re.sub(r"[^a-z0-9\s]", "", q)
    q = re.sub(r"\s+", " ", q)
    return q


def get_cached_results(query: str, location: str | None):
    norm = normalize(query)
    cutoff = datetime.now(timezone.utc) - timedelta(days=CACHE_TTL_DAYS)

    with SessionLocal() as db:
        # 1. Exact normalized match — cheapest, most common case
        row = (
            db.query(SearchCache)
            .filter(SearchCache.normalized_query == norm)
            .filter(SearchCache.created_at >= cutoff)
            .order_by(SearchCache.created_at.desc())
            .first()
        )
        if row:
            return row.results, "exact"

        # 2. Fuzzy match — catches "infuse boots" matching a cached
        #    "vans infuse snowboard boots" search
        result = db.execute(
            text("""
                SELECT results, similarity(normalized_query, :q) AS sim
                FROM search_cache
                WHERE created_at >= :cutoff
                  AND similarity(normalized_query, :q) > :threshold
                ORDER BY sim DESC
                LIMIT 1
            """),
            {"q": norm, "cutoff": cutoff, "threshold": SIMILARITY_THRESHOLD},
        ).first()

        if result:
            return result.results, "fuzzy"

    return None, None


def save_to_cache(query: str, location: str | None, results: list):
    with SessionLocal() as db:
        db.add(SearchCache(
            query=query,
            normalized_query=normalize(query),
            location=location,
            results=results,
        ))
        db.commit()