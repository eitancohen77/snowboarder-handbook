import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
print("Loaded DATABASE_URL:", repr(DATABASE_URL))

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class SearchCache(Base):
    __tablename__ = "search_cache"

    id = Column(Integer, primary_key=True)
    query = Column(String, nullable=False)
    normalized_query = Column(String, nullable=False, index=True)
    location = Column(String, nullable=True)
    results = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# this makes it so that we can track how many api calls have been made.
class ApiUsage(Base):
    __tablename__ = "api_usage"
    id = Column(Integer, primary_key=True)
    month = Column(String, unique=True)
    call_count = Column(Integer, default=0)

def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        # Enables fuzzy text matching ("infuse boots" ~ "vans infuse snowboard boots")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_search_cache_trgm "
            "ON search_cache USING gin (normalized_query gin_trgm_ops);"
        ))