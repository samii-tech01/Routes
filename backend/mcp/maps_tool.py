"""
MCP: Maps Tool
Wraps the Google Maps Geocoding and Directions APIs.
Used by the Geo-Clustering Agent to resolve addresses and compute drive times.

Set MOCK_MAPS=true in .env to bypass real API calls (useful before billing is enabled).
"""
import os
import googlemaps
from core.config import GOOGLE_MAPS_API_KEY

# Set MOCK_MAPS=true in .env to skip real API calls
MOCK_MAPS = os.getenv("MOCK_MAPS", "false").lower() == "true"

_client = None

# Simulated drive times (minutes) between generic errand types — used in mock mode
MOCK_DRIVE_TIMES = {
    ("post_office",  "grocery"):   12,
    ("post_office",  "atm"):        8,
    ("post_office",  "pharmacy"):   5,
    ("grocery",      "post_office"):12,
    ("grocery",      "atm"):        7,
    ("grocery",      "pharmacy"):  10,
    ("atm",          "post_office"): 8,
    ("atm",          "grocery"):    7,
    ("atm",          "pharmacy"):   9,
    ("pharmacy",     "post_office"): 5,
    ("pharmacy",     "grocery"):   10,
    ("pharmacy",     "atm"):        9,
}

def _get_client():
    global _client
    if _client is None:
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("GOOGLE_MAPS_API_KEY is not set.")
        _client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    return _client

def geocode_address(address: str, user_location: str = "") -> dict:
    """
    Converts a plain text address or location hint into coordinates.
    Returns a dict with 'formatted_address' and optional lat/lng.
    Falls back to mock data if MOCK_MAPS=true or API fails.
    """
    search_query = f"{address}, {user_location}" if user_location else address
    
    if MOCK_MAPS:
        return {"formatted_address": f"[MOCK] {search_query}", "lat": None, "lng": None}
    try:
        client = _get_client()
        result = client.geocode(search_query)
        if result:
            loc = result[0]["geometry"]["location"]
            return {
                "formatted_address": result[0]["formatted_address"],
                "lat": loc["lat"],
                "lng": loc["lng"]
            }
    except Exception as e:
        print(f"[Maps MCP] Geocoding failed for '{search_query}': {e}")
    return {"formatted_address": search_query, "lat": None, "lng": None}

def get_drive_time_minutes(origin: str, destination: str) -> int:
    """
    Returns estimated drive time in minutes between two addresses.
    Falls back to 15 minutes if the API fails or mock mode is on.
    """
    if MOCK_MAPS:
        return 15
    try:
        client = _get_client()
        result = client.directions(origin, destination, mode="driving")
        if result:
            duration_secs = result[0]["legs"][0]["duration"]["value"]
            return max(1, duration_secs // 60)
    except Exception as e:
        print(f"[Maps MCP] Directions failed ({origin} -> {destination}): {e}")
    return 15

def build_distance_matrix(locations: list) -> list:
    """
    Builds a full NxN matrix of drive times in minutes between a list of locations.
    Falls back to a uniform mock matrix if MOCK_MAPS=true or API fails.
    """
    n = len(locations)
    matrix = [[0] * n for _ in range(n)]

    if MOCK_MAPS:
        # Use a simple mock: 10-20 mins between any two locations
        for i in range(n):
            for j in range(n):
                matrix[i][j] = 0 if i == j else (10 + (i + j) % 10)
        return matrix

    try:
        client = _get_client()
        result = client.distance_matrix(
            origins=locations,
            destinations=locations,
            mode="driving"
        )
        for i, row in enumerate(result["rows"]):
            for j, element in enumerate(row["elements"]):
                if element["status"] == "OK":
                    matrix[i][j] = max(1, element["duration"]["value"] // 60)
                else:
                    matrix[i][j] = 20
    except Exception as e:
        print(f"[Maps MCP] Distance matrix failed: {e}")
        for i in range(n):
            for j in range(n):
                matrix[i][j] = 0 if i == j else 20
    return matrix
