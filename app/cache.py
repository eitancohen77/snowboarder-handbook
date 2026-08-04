import re
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from app.db import SessionLocal, SearchCache

CACHE_TTL_DAYS = 3            # how long a cached search stays "fresh" (prices drift)
SIMILARITY_THRESHOLD = 0.45   # 0-1, higher = stricter fuzzy match


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