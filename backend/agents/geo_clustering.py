from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.state import ErrandState, AgentProposal
from core.config import get_specialist_llm
from mcp.maps_tool import geocode_address, build_distance_matrix
from pydantic import BaseModel, Field
from typing import List

class GeoSequenceOutput(BaseModel):
    proposed_sequence: List[str] = Field(description="Ordered list of errand IDs minimizing travel distance.")
    rationale: str = Field(description="Explanation of the clustering and routing logic.")

def geo_clustering_agent(state: ErrandState) -> dict:
    """
    Groups errands by physical proximity using real Google Maps data.
    Resolves locations via Geocoding API and builds a distance matrix
    via the Distance Matrix API before asking the LLM to sequence the route.
    """
    llm = get_specialist_llm()
    parser = PydanticOutputParser(pydantic_object=GeoSequenceOutput)
    errands = state.get('errands', [])

    if not errands:
        return {"proposals": []}

    # --- Step 1: Geocode all errand locations via Maps MCP ---
    resolved_locations = {}
    user_location = state.get('user_location', '')
    for errand in errands:
        hint = errand.resolved_location or errand.preferred_location or errand.description
        geo = geocode_address(hint, user_location)
        resolved_locations[errand.id] = geo.get("formatted_address", hint)
        # Mutate in place so downstream agents can see resolved addresses
        errand.resolved_location = resolved_locations[errand.id]

    # --- Step 2: Build drive-time matrix via Maps MCP ---
    errand_ids = [e.id for e in errands]
    location_list = [resolved_locations[eid] for eid in errand_ids]
    drive_matrix = build_distance_matrix(location_list)  # NxN minutes

    # Format for LLM prompt
    matrix_str = "\n".join([
        f"  {errand_ids[i]} -> {errand_ids[j]}: {drive_matrix[i][j]} mins"
        for i in range(len(errand_ids))
        for j in range(len(errand_ids))
        if i != j
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Geo-Clustering Agent. Your ONLY job is to sequence errands to minimize total travel distance. "
                   "You are given a real drive-time matrix in minutes. Find the shortest path (nearest-neighbor heuristic is fine). "
                   "Output valid JSON matching the schema.\n{format_instructions}"),
        ("human", "Errand IDs and resolved locations:\n{locations}\n\nDrive-time matrix (minutes):\n{matrix}")
    ])

    chain = prompt | llm | parser

    locations_str = "\n".join([f"  {eid}: {resolved_locations[eid]}" for eid in errand_ids])

    try:
        output = chain.invoke({
            "locations": locations_str,
            "matrix": matrix_str,
            "format_instructions": parser.get_format_instructions()
        })

        # Calculate actual total drive time for the proposed sequence as penalty
        total_drive_time = 0
        seq = output.proposed_sequence
        for k in range(len(seq) - 1):
            i = errand_ids.index(seq[k]) if seq[k] in errand_ids else 0
            j = errand_ids.index(seq[k + 1]) if seq[k + 1] in errand_ids else 0
            total_drive_time += drive_matrix[i][j]

        proposal = AgentProposal(
            agent_name="Geo-Clustering",
            proposed_sequence=output.proposed_sequence,
            score_penalty=total_drive_time,
            rationale=output.rationale
        )
        return {"proposals": [proposal]}

    except Exception as e:
        print(f"Geo-Clustering Agent Error: {e}")
        return {"proposals": []}
