"""
MCP: Maps Tool  —  OpenRouteService (primary) + Nominatim (fallback)
ORS Free Tier: 3,000 geocoding req/day, 500 matrix req/day
Set ORS_API_KEY in .env to activate.
https://openrouteservice.org
"""
import os
import time
import requests

ORS_API_KEY = os.getenv("ORS_API_KEY", "")

ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
ORS_GEOCODE_STRUCTURED_URL = "https://api.openrouteservice.org/geocode/search/structured"
ORS_MATRIX_URL  = "https://api.openrouteservice.org/v2/matrix/driving-car"

# ─────────────────────────────────────────────────────────────────────────────
# Nominatim (OpenStreetMap) — free fallback, no API key needed
# ─────────────────────────────────────────────────────────────────────────────

def _geocode_nominatim(address: str, city_hint: str = "", city_bbox: list = None) -> dict:
    query = f"{address}, {city_hint}" if city_hint and city_hint.lower() not in address.lower() else address
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        if city_bbox:
            lon1, lat1, lon2, lat2 = city_bbox
            params["viewbox"] = f"{lon1},{lat1},{lon2},{lat2}"
            params["bounded"] = 1

        headers = {"User-Agent": "RouteBrain/1.0 (route planning app)"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data:
            result    = data[0]
            addr_info = result.get("address", {})
            name = (result.get("name") or
                    addr_info.get("road") or
                    result.get("display_name", "").split(",")[0].strip())
            city = (addr_info.get("city") or addr_info.get("town") or
                    addr_info.get("village") or city_hint)
            country = addr_info.get("country", "Pakistan")
            parts   = [p for p in [name, city, country] if p]
            friendly = ", ".join(parts) if parts else result.get("display_name", query)
            # POST-filter check for bbox
            outside_city = False
            lat_f = float(result["lat"])
            lng_f = float(result["lon"])
            if city_bbox:
                lon1, lat1b, lon2, lat2b = city_bbox
                if not (lon1 <= lng_f <= lon2 and lat1b <= lat_f <= lat2b):
                    outside_city = True

            return {
                "formatted_address": friendly,
                "name":   name,
                "city":   city,
                "lat":    lat_f,
                "lng":    lng_f,
                "source": "nominatim",
                "outside_city": outside_city,
            }
    except Exception:
        pass
    return {"formatted_address": address, "lat": None, "lng": None, "outside_city": False}


# ─────────────────────────────────────────────────────────────────────────────
# City Geocoding  —  returns center + bounding box for the city
# ─────────────────────────────────────────────────────────────────────────────

def _is_latin(s: str) -> bool:
    """Returns True if the string contains mostly ASCII/Latin characters."""
    if not s:
        return False
    latin = sum(1 for c in s if ord(c) < 0x0600)  # below Arabic Unicode block
    return latin / len(s) > 0.5


def geocode_city(city_name: str) -> dict:
    """
    Geocodes a city name to get its center coordinates AND bounding box.
    Returns: { "city", "formatted", "lat", "lng", "bbox" }
    """
    if ORS_API_KEY:
        try:
            params = {
                "api_key": ORS_API_KEY,
                "text": f"{city_name}, Pakistan",
                "size": 3,
                "layers": "locality,county,region",
                "boundary.country": "PAK",
                "lang": "en",
            }
            resp = requests.get(ORS_GEOCODE_URL, params=params, timeout=8)
            resp.raise_for_status()
            features = resp.json().get("features", [])
            
            for feature in features:
                props  = feature["properties"]
                coords = feature["geometry"]["coordinates"]  # [lng, lat]
                lng, lat = coords[0], coords[1]
                label = props.get("label", "")
                
                # ORS may return Urdu name fields but label is always English
                # Use the original input city_name as canonical English name
                display = city_name.title()
                formatted = f"{display}, Pakistan" if "Pakistan" not in label else label
                
                # Build a generous ~50 km bounding box
                delta = 0.5
                bbox = [lng - delta, lat - delta, lng + delta, lat + delta]
                return {
                    "city":      display,
                    "formatted": formatted,
                    "lat":       lat,
                    "lng":       lng,
                    "bbox":      bbox,
                }
        except Exception:
            pass

    # Nominatim fallback
    nom = _geocode_nominatim(f"{city_name}, Pakistan")
    if nom.get("lat"):
        lat, lng = nom["lat"], nom["lng"]
        delta = 0.5
        return {
            "city":      nom.get("city") or city_name.title(),
            "formatted": f"{city_name.title()}, Pakistan",
            "lat":       lat,
            "lng":       lng,
            "bbox":      [lng - delta, lat - delta, lng + delta, lat + delta],
        }

    return {"city": city_name.title(), "formatted": f"{city_name.title()}, Pakistan", "lat": None, "lng": None, "bbox": None}


# ─────────────────────────────────────────────────────────────────────────────
# Address Geocoding  —  landmark/address → lat/lng
# ─────────────────────────────────────────────────────────────────────────────

def geocode_address(address: str, user_location: str = "", city_hint: str = "",
                    bias_lat: float = None, bias_lng: float = None,
                    city_bbox: list = None) -> dict:
    """
    Geocodes an address using ORS (primary) then Nominatim (fallback).
    Uses focus point for bias — bbox is used only as a POST-filter.
    """
    if city_hint and city_hint.lower() not in address.lower():
        search_query = f"{address}, {city_hint}, Pakistan"
    elif user_location and user_location.lower() not in address.lower():
        search_query = f"{address}, {user_location}"
    else:
        search_query = address

    if ORS_API_KEY:
        try:
            params = {
                "api_key": ORS_API_KEY,
                "text": search_query,
                "size": 1,
                "boundary.country": "PAK",
                "lang": "en",
            }
            # Use focus point (soft bias) instead of boundary.rect (hard cut-off)
            if bias_lat is not None and bias_lng is not None:
                params["focus.point.lat"] = bias_lat
                params["focus.point.lon"] = bias_lng
                params["boundary.circle.lat"] = bias_lat
                params["boundary.circle.lon"] = bias_lng
                params["boundary.circle.radius"] = 60  # km — generous enough for all city landmarks

            resp = requests.get(ORS_GEOCODE_URL, params=params, timeout=8)
            resp.raise_for_status()
            features = resp.json().get("features", [])
            if features:
                props  = features[0]["properties"]
                coords = features[0]["geometry"]["coordinates"]
                lng, lat = coords[0], coords[1]

                raw_name = props.get("name") or address
                label    = props.get("label") or f"{raw_name}, {city_hint}, Pakistan"

                # ORS returns Urdu name fields for Pakistan — use input address as English name
                label_parts   = [p.strip() for p in label.split(",")]
                english_name  = raw_name if _is_latin(raw_name) else address.title()
                english_city  = label_parts[1].strip() if len(label_parts) > 1 else ""
                clean_label   = f"{english_name}, {english_city}, Pakistan" if english_city else f"{english_name}, Pakistan"

                # POST-filter: flag results outside city bbox instead of dropping them
                # The caller can then ask the user for confirmation
                outside_city = False
                if city_bbox:
                    lon1, lat1b, lon2, lat2b = city_bbox
                    if not (lon1 <= lng <= lon2 and lat1b <= lat <= lat2b):
                        outside_city = True

                return {
                    "formatted_address": clean_label,
                    "name":         english_name,
                    "city":         english_city or city_hint,
                    "lat":          lat,
                    "lng":          lng,
                    "source":       "ors",
                    "outside_city": outside_city,  # True = found somewhere else, needs user confirmation
                }
        except Exception:
            pass

    # Nominatim fallback
    time.sleep(1)  # respect Nominatim rate limit
    nom = _geocode_nominatim(search_query, city_hint=city_hint, city_bbox=city_bbox)
    # If Nominatim also found nothing but we have city coords, return None gracefully
    return nom


# ─────────────────────────────────────────────────────────────────────────────
# Distance Matrix  —  NxN drive-time table (minutes)
# ─────────────────────────────────────────────────────────────────────────────

def build_distance_matrix(coords: list) -> list:
    """
    Builds an NxN drive-time matrix (minutes) using ORS Matrix API.
    coords: list of {"lat": float, "lng": float} dicts.
    Returns: NxN list of lists (durations in minutes).
    Falls back to straight-line Haversine distances if ORS fails.
    """
    n = len(coords)
    if n < 2:
        return [[0]]

    if ORS_API_KEY:
        try:
            locations = [[c["lng"], c["lat"]] for c in coords]
            payload = {
                "locations": locations,
                "metrics":   ["duration"],
                "units":     "m",
            }
            headers = {
                "Authorization": ORS_API_KEY,
                "Content-Type":  "application/json",
            }
            resp = requests.post(ORS_MATRIX_URL, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            durations = data.get("durations", [])
            if durations:
                # Convert seconds to minutes, round to 1 decimal
                return [[round(d / 60, 1) if d is not None else 9999 for d in row]
                        for row in durations]
        except Exception as e:
            print(f"[Maps MCP] ORS Matrix API failed: {e}")

    # Haversine fallback (straight-line, assumes ~40 km/h average speed)
    import math
    def haversine_minutes(c1, c2):
        if c1["lat"] is None or c2["lat"] is None:
            return 9999  # unknown — treat as very far away
        R = 6371
        lat1, lon1 = math.radians(c1["lat"]), math.radians(c1["lng"])
        lat2, lon2 = math.radians(c2["lat"]), math.radians(c2["lng"])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        dist_km = 2 * R * math.asin(math.sqrt(a))
        return round((dist_km / 40) * 60, 1)

    return [[0 if i == j else haversine_minutes(coords[i], coords[j])
             for j in range(n)] for i in range(n)]
