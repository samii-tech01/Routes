import os
os.environ["PYTHONIOENCODING"] = "utf-8"

from mcp.maps_tool import geocode_city, geocode_address, build_distance_matrix

print("=== Test 1: City Geocoding ===")
city = geocode_city("Khairpur")
# Print only ASCII-safe parts
print("City:", city.get("city"))
print("Formatted:", city.get("formatted"))
print("Lat/Lng:", city.get("lat"), city.get("lng"))
print("BBox:", city.get("bbox"))

print()
print("=== Test 2: Landmark Geocoding ===")
bbox = city["bbox"]
blat, blng = city["lat"], city["lng"]

r1 = geocode_address("Radio Pakistan", city_hint="Khairpur", city_bbox=bbox, bias_lat=blat, bias_lng=blng)
r2 = geocode_address("Shah Abdul Latif University", city_hint="Khairpur", city_bbox=bbox, bias_lat=blat, bias_lng=blng)
r3 = geocode_address("Mumtaz College", city_hint="Khairpur", city_bbox=bbox, bias_lat=blat, bias_lng=blng)

for label, r in [("Radio Pakistan", r1), ("Shah Latif Uni", r2), ("Mumtaz College", r3)]:
    print(label, "->", r.get("formatted_address"), "| lat:", r.get("lat"), "| lng:", r.get("lng"), "| source:", r.get("source"))

print()
print("=== Test 3: Distance Matrix ===")
coords = [
    {"lat": city["lat"], "lng": city["lng"]},
    {"lat": r1.get("lat"), "lng": r1.get("lng")},
    {"lat": r2.get("lat"), "lng": r2.get("lng")},
    {"lat": r3.get("lat"), "lng": r3.get("lng")},
]
print("Coords being fed to matrix:")
for i, c in enumerate(coords):
    print(f"  [{i}]", c)

matrix = build_distance_matrix(coords)
print("Matrix (minutes):")
for row in matrix:
    print(" ", row)
