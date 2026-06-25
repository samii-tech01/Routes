from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Dict
from core.state import ErrandState
from core.config import GEMINI_API_KEY
import json

class ReasonerOutput(BaseModel):
    inferred_constraints: Dict[str, List[str]] = Field(description="Map of errand ID to list of inferred constraints")
    dependency_graph: Dict[str, List[str]] = Field(description="Map of errand ID to list of errand IDs it depends on")

def reasoner_agent(state: ErrandState) -> ErrandState:
    """
    Agent 3: Dependency Reasoner
    Infers ordering constraints and dependencies.
    """
    print("Reasoner Agent: Analyzing logical dependencies and implicit time constraints...")
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=GEMINI_API_KEY)
    
    errands_json = json.dumps([e.model_dump() for e in state["errands"]], indent=2)
    
    prompt = f"""
    You are the Dependency Reasoner for an errand planning system.
    Analyze the following list of enriched errands.
    
    Identify:
    1. Implicit time constraints (e.g., "pharmacies process queues in the afternoon so do it early").
    2. Logical order dependencies (e.g., "buy groceries last so they don't melt in the car").
    
    Errands:
    {errands_json}
    
    Return a dependency graph where key is the errand ID, and value is a list of errand IDs it must happen AFTER.
    Also return a map of errand ID to a list of string explanations of inferred constraints.
    """
    
    structured_llm = llm.with_structured_output(ReasonerOutput)
    result = structured_llm.invoke(prompt)
    
    # Update state with inferred constraints
    errands = state["errands"]
    for errand in errands:
        if errand.id in result.inferred_constraints:
            errand.inferred_constraints.extend(result.inferred_constraints[errand.id])
            
    # Merge existing explicit dependencies with inferred ones
    dep_graph = state["dependency_graph"] or {}
    for errand_id, deps in result.dependency_graph.items():
        if errand_id not in dep_graph:
            dep_graph[errand_id] = []
        dep_graph[errand_id].extend(deps)
        # Deduplicate
        dep_graph[errand_id] = list(set(dep_graph[errand_id]))
        
    return {"errands": errands, "dependency_graph": dep_graph}
