import googlemaps
from typing import Dict, Any, Optional
from core.config import GOOGLE_MAPS_API_KEY

def get_maps_client() -> Optional[googlemaps.Client]:
    if GOOGLE_MAPS_API_KEY and GOOGLE_MAPS_API_KEY != "your_google_maps_api_key_here":
        return googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    return None

def resolve_location(query: str, user_location: str = "Sukkur, Pakistan") -> Dict[str, Any]:
    """
    Mockable wrapper around Google Places API to resolve an address.
    """
    client = get_maps_client()
    if client:
        # Live API Call
        try:
            places = client.places(query, location=user_location)
            if places and 'results' in places and len(places['results']) > 0:
                best_result = places['results'][0]
                return {
                    "address": best_result.get("formatted_address", query),
                    "lat": best_result['geometry']['location']['lat'],
                    "lng": best_result['geometry']['location']['lng'],
                    "is_mock": False
                }
        except Exception as e:
            print(f"Maps API Error: {e}")
            
    # Mock fallback
    return {
        "address": f"Resolved Mock Address for: {query}",
        "lat": 27.7128,
        "lng": 68.8359,
        "is_mock": True
    }

def estimate_duration(errand_type: str) -> int:
    """
    Returns estimated duration in minutes based on errand type.
    """
    estimates = {
        "grocery": 45,
        "pharmacy": 15,
        "post_office": 10,
        "dentist": 60,
        "bank": 20
    }
    for key, val in estimates.items():
        if key in errand_type.lower():
            return val
    return 30 # default 30 mins
