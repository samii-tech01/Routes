from core.state import ErrandState
from tools.maps_api import resolve_location, estimate_duration
from core.memory import get_user_profile

def enrichment_agent(state: ErrandState) -> ErrandState:
    """
    Agent 2: Enrichment Agent
    Connects to Maps API (or mock) to resolve locations and estimate durations.
    """
    print("Enrichment Agent: Resolving real-world coordinates and durations...")
    errands = state["errands"]
    user_profile = get_user_profile()
    home_location = user_profile.get("home_location", "Sukkur, Pakistan")
    
    for errand in errands:
        # Check user profile for known locations
        location_query = errand.location_hint or errand.errand_type
        if errand.errand_type.lower() in user_profile.get("saved_places", {}):
            location_query = user_profile["saved_places"][errand.errand_type.lower()]
            
        # Resolve location
        location_data = resolve_location(location_query, home_location)
        errand.resolved_location = location_data["address"]
        
        # Estimate duration
        errand.estimated_duration_mins = estimate_duration(errand.errand_type)
        
        # Mock opening hours for capstone prototype
        if "pharmacy" in errand.errand_type.lower():
            errand.opening_hours = "09:00 - 18:00"
        else:
            errand.opening_hours = "08:00 - 20:00"
            
    return {"errands": errands}
