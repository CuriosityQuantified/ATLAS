import psycopg2
import os
import time
from typing import Dict, Any, Tuple

# In-memory cache with a Time-To-Live (TTL)
_pricing_cache: Dict[str, Any] = {}
_cache_expiry = 0
CACHE_TTL_SECONDS = 300  # 5 minutes

def _get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg2.connect(
        dbname=os.getenv("ATLAS_DB_NAME", "atlas_main"),
        user=os.getenv("ATLAS_DB_USER", "atlas_main_user"),
        password=os.getenv("ATLAS_DB_PASSWORD", "atlas_main_password"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

def _load_pricing_from_db() -> None:
    """
    Loads pricing data from the database into the in-memory cache.
    """
    global _pricing_cache, _cache_expiry
    print("Fetching latest pricing data from database...")
    
    conn = None
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT model_name, provider, input_cost_per_million_tokens, output_cost_per_million_tokens FROM model_pricing")
        rows = cur.fetchall()
        
        temp_cache = {}
        for row in rows:
            temp_cache[row[0]] = {
                "provider": row[1],
                "input_cost_per_million_tokens": float(row[2]),
                "output_cost_per_million_tokens": float(row[3])
            }
        _pricing_cache = temp_cache
        _cache_expiry = time.time() + CACHE_TTL_SECONDS
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error fetching pricing data: {error}")
        # In case of DB error, use an empty cache to prevent stale data
        _pricing_cache = {}
    finally:
        if conn is not None:
            conn.close()

def get_cost_and_pricing_details(model_name: str, input_tokens: int, output_tokens: int) -> Tuple[float, Dict[str, Any]]:
    """
    Calculates cost by fetching live pricing data from the database.
    Uses a time-based cache to optimize performance.
    """
    # Check if cache is expired
    if time.time() > _cache_expiry:
        _load_pricing_from_db()

    default_pricing = _pricing_cache.get("default", {})
    pricing = _pricing_cache.get(model_name, default_pricing)
    
    input_cost_per_mil = pricing.get("input_cost_per_million_tokens", 0)
    output_cost_per_mil = pricing.get("output_cost_per_million_tokens", 0)

    final_cost = ((input_tokens / 1_000_000) * input_cost_per_mil) + \
                 ((output_tokens / 1_000_000) * output_cost_per_mil)
    
    pricing_details = {
        "provider": pricing.get("provider", "Unknown"),
        "input_cost_per_million_tokens": input_cost_per_mil,
        "output_cost_per_million_tokens": output_cost_per_mil
    }
    
    return final_cost, pricing_details
