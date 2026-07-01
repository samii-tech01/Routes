"""
MCP: Maps Tool
Wraps the Google Maps Geocoding and Directions APIs.
Used by the Geo-Clustering Agent to resolve addresses and compute drive times.
"""
import googlemaps
from core.config import GOOGLE_MAPS_API_KEY

_client = None

def _get_client():
    global _client
    if _client is None:
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("GOOGLE_MAPS_API_KEY is not set.")
        _client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    return _client

def geocode_address(address: str) -> dict:
    """
    Converts a plain text address or location hint into coordinates.
    Returns a dict with 'formatted_address' and 'lat_lng'.
    """
    try:
        client = _get_client()
        result = client.geocode(address)
        if result:
            loc = result[0]["geometry"]["location"]
            return {
                "formatted_address": result[0]["formatted_address"],
                "lat": loc["lat"],
                "lng": loc["lng"]
            }
    except Exception as e:
        print(f"[Maps MCP] Geocoding failed for '{address}': {e}")
    return {"formatted_address": address, "lat": None, "lng": None}

def get_drive_time_minutes(origin: str, destination: str) -> int:
    """
    Returns estimated drive time in minutes between two address strings.
    Falls back to 15 minutes if the API fails.
    """
    try:
        client = _get_client()
        result = client.directions(origin, destination, mode="driving")
        if result:
            duration_secs = result[0]["legs"][0]["duration"]["value"]
            return max(1, duration_secs // 60)
    except Exception as e:
        print(f"[Maps MCP] Directions failed ({origin} -> {destination}): {e}")
    return 15  # Default fallback

def build_distance_matrix(locations: list[str]) -> list[list[int]]:
    """
    Builds a full NxN matrix of drive times in minutes between a list of locations.
    Used by the Geo-Clustering agent to find the shortest route.
    """
    n = len(locations)
    matrix = [[0] * n for _ in range(n)]
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
                    matrix[i][j] = 30  # Fallback for unknown routes
    except Exception as e:
        print(f"[Maps MCP] Distance matrix failed: {e}")
        # Fill with reasonable fallback
        for i in range(n):
            for j in range(n):
                matrix[i][j] = 0 if i == j else 20
    return matrix
