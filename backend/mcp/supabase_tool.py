"""
MCP: Database Tool (Supabase)
Provides a connection to the Supabase Postgres database.
Used by the Memory Agent to persist and retrieve user preferences.
"""
import os
from supabase import create_client, Client

_supabase: Client = None

def get_supabase_client() -> Client:
    """Returns a singleton Supabase client."""
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        _supabase = create_client(url, key)
    return _supabase

def get_user_preference(user_id: str, errand_type: str) -> str:
    """
    Retrieves the preferred location for a specific errand type for a user.
    """
    try:
        client = get_supabase_client()
        response = client.table("user_preferences").select("preferred_location").eq("user_id", user_id).eq("errand_type", errand_type).execute()
        data = response.data
        if data and len(data) > 0:
            return data[0]["preferred_location"]
    except Exception:
        # Silently fail on network/database issues for graceful degradation
        pass
    return None

def set_user_preference(user_id: str, errand_type: str, preferred_location: str):
    """
    Sets or updates the preferred location for a specific errand type for a user.
    """
    try:
        client = get_supabase_client()
        data = {
            "user_id": user_id,
            "errand_type": errand_type,
            "preferred_location": preferred_location
        }
        # Upsert requires a unique constraint on (user_id, errand_type)
        client.table("user_preferences").upsert(data).execute()
    except Exception:
        # Silently fail on network/database issues for graceful degradation
        pass

