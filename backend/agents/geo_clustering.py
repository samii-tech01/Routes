from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.types import interrupt
from core.state import ErrandState, AgentProposal
from core.config import get_specialist_llm
from mcp.maps_tool import geocode_address, build_distance_matrix
from pydantic import BaseModel, Field
from typing import List
import itertools

class GeoSequenceOutput(BaseModel):
    proposed_sequence: List[str] = Field(description="Ordered list of errand IDs minimizing travel distance.")
    rationale: str = Field(description="Explanation of the clustering and routing logic.")

def geo_clustering_agent(state: ErrandState) -> dict:
    """
    Groups errands by physical proximity using real Google Maps data.
    Resolves locations via Geocoding API and builds a distance matrix
    via the Distance Matrix API before asking the LLM to sequence the route.
    """
    errands = state.get('errands', [])

    if not errands:
        return {"proposals": []}

    # --- Step 1: Geocode all errand locations via Maps MCP ---
    resolved_locations = {}
    user_location  = state.get('user_location', '')
    user_city      = state.get('user_city', '')
    user_city_lat  = state.get('user_city_lat')
    user_city_lng  = state.get('user_city_lng')
    user_city_bbox = state.get('user_city_bbox')
    
    # Initial geocode for all errands
    errand_geos = {}
    for errand in errands:
        hint = errand.resolved_location or errand.preferred_location or errand.description
        geo = geocode_address(
            hint,
            city_hint=user_city,
            city_bbox=user_city_bbox,
            bias_lat=user_city_lat,
            bias_lng=user_city_lng,
        )
        errand_geos[errand.id] = geo  # Store temporarily

    while True:
        # Build summary text
        summary = f"I have mapped your errands in {user_city} as follows:\n\n"
        for i, errand in enumerate(errands, 1):
            geo = errand_geos.get(errand.id, {})
            desc = errand.description
            if not geo.get("lat"):
                summary += f"  {i}. {desc} --> [Not Found]\n"
            else:
                addr = geo.get("formatted_address")
                warn = " [OUTSIDE CITY]" if geo.get("outside_city") else ""
                summary += f"  {i}. {desc} --> {addr}{warn}\n"
                
        summary += "\nDoes this look correct?\n(Reply 'yes' to proceed, or tell me what to fix, e.g. 'errand 2 is near mumtaz colony', 'skip 3')"
        
        ans = interrupt(summary)
        ans_str = str(ans).strip()
        
        if not ans_str or ans_str.lower() in ("yes", "y", "yep", "yeah", "ok", "okay", "sure", "fine", "alright"):
            break
            
        # Parse conversational corrections
        llm = get_specialist_llm()
        from pydantic import BaseModel, Field
        from typing import Optional
        
        class ErrandCorrection(BaseModel):
            errand_index: int = Field(description="The 1-based index of the errand to fix")
            new_hint: Optional[str] = Field(None, description="The new specific landmark or street provided by the user")
            skip: bool = Field(False, description="True if the user wants to skip this errand")
            
        class CorrectionOutput(BaseModel):
            corrections: List[ErrandCorrection]
            
        prompt = f"You are a geocoding assistant. The user provided corrections for their mapped errands.\nUser input: \"{ans_str}\"\nErrands:\n"
        for i, errand in enumerate(errands, 1):
            prompt += f"{i}. {errand.description}\n"
            
        parser = PydanticOutputParser(pydantic_object=CorrectionOutput)
        messages = [
            {"role": "system", "content": "Extract the user's location corrections."},
            {"role": "user", "content": prompt + f"\n\nFormat:\n{parser.get_format_instructions()}"}
        ]
        
        print("  Processing your corrections...")
        try:
            res = llm.invoke(messages)
            parsed = parser.parse(res.content)
            
            # If LLM finds no corrections, the user must have approved it (e.g. "yes all correct")
            if not parsed.corrections:
                break
                
            for corr in parsed.corrections:
                idx = corr.errand_index - 1
                if 0 <= idx < len(errands):
                    if corr.skip:
                        errand_geos[errands[idx].id] = {"lat": None, "lng": None}
                    elif corr.new_hint:
                        print(f"  Re-checking map for '{corr.new_hint}' (Errand {corr.errand_index})...")
                        errand_geos[errands[idx].id] = geocode_address(
                            corr.new_hint, city_hint=user_city, city_bbox=user_city_bbox, 
                            bias_lat=user_city_lat, bias_lng=user_city_lng
                        )
        except Exception as e:
            print("  I didn't quite catch that. Please try rephrasing your corrections.")
            continue

    # Finalize mapped locations
    for errand in errands:
        geo = errand_geos.get(errand.id, {})
        hint = errand.resolved_location or errand.preferred_location or errand.description
        if not geo.get("lat"):
            display_name = errand.description.title()
            errand.lat = user_city_lat
            errand.lng = user_city_lng
        else:
            display_name = geo.get("name") or hint.title()
            errand.lat = geo.get("lat")
            errand.lng = geo.get("lng")
            
        if user_city and user_city.lower() not in display_name.lower():
            resolved_locations[errand.id] = f"{display_name}, {user_city}, Pakistan"
        else:
            resolved_locations[errand.id] = f"{display_name}, Pakistan"
            
        errand.resolved_location = resolved_locations[errand.id]

    user_lat       = state.get('user_lat')
    user_lng       = state.get('user_lng')
    user_city_lat  = state.get('user_city_lat')
    
    # --- Step 2: Build drive-time matrix via Maps MCP (including START) ---
    errand_ids = [e.id for e in errands]
    
    # Index 0 is the starting location (use exact location, fallback to city center)
    start_lat = user_lat if user_lat is not None else user_city_lat
    start_lng = user_lng if user_lng is not None else user_city_lng
    coords_list = [{"lat": start_lat, "lng": start_lng}]
    
    for e in errands:
        # Guard: if errand geocoding failed, approximate to city center
        lat = e.lat if e.lat is not None else user_city_lat
        lng = e.lng if e.lng is not None else user_city_lng
        coords_list.append({"lat": lat, "lng": lng})
        
    matrix_data = build_distance_matrix(coords_list)  # (N+1)x(N+1) minutes
    
    # Store matrix in state for other agents
    drive_matrix = {}
    drive_matrix["START"] = {}
    for j, eid in enumerate(errand_ids, 1):
        drive_matrix["START"][eid] = matrix_data[0][j]
        
    for i, eid1 in enumerate(errand_ids, 1):
        drive_matrix[eid1] = {}
        for j, eid2 in enumerate(errand_ids, 1):
            drive_matrix[eid1][eid2] = matrix_data[i][j]

    # --- Step 3: Deterministic Shortest Path Solver ---
    best_seq = []
    best_time = float('inf')
    
    # Brute force all permutations (N is small, usually < 8)
    for perm in itertools.permutations(errand_ids):
        current_time = drive_matrix["START"][perm[0]]
        for k in range(len(perm) - 1):
            current_time += drive_matrix[perm[k]][perm[k+1]]
            
        if current_time < best_time:
            best_time = current_time
            best_seq = list(perm)

    proposal = AgentProposal(
        agent_name="Geo-Clustering",
        proposed_sequence=best_seq,
        score_penalty=best_time,
        rationale=f"Deterministically calculated shortest physical route (Total drive time: {best_time} mins)."
    )

    return {"proposals": [proposal], "drive_matrix": drive_matrix, "errands": errands}
