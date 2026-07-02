from core.state import ErrandState
from mcp.supabase_tool import get_user_preference

def memory_agent(state: ErrandState) -> dict:
    """
    Simulates looking up past user preferences from the database.
    Injects known locations into the errands based on the errand_type.
    """
    errands = state.get('errands', [])
    
    # We will assume a hardcoded user_id for the hackathon demo
    # In a real app, this would come from the auth context
    USER_ID = "demo-user-123"
    
    for errand in errands:
        # Ask Database MCP if we have a preferred location for this errand type
        preferred = get_user_preference(USER_ID, errand.errand_type)
        if preferred:
            errand.preferred_location = preferred
            
    return {"errands": errands}
