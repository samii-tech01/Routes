from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List
from core.state import ErrandState
from core.config import GEMINI_API_KEY
import json

class OptimizerOutput(BaseModel):
    optimized_sequence: List[str] = Field(description="List of errand IDs in the optimal sequence")
    reasoning: str = Field(description="Brief explanation of why this sequence was chosen")

def optimizer_agent(state: ErrandState) -> ErrandState:
    """
    Agent 4: Route Optimizer
    Produces the optimal sequence of errands given constraints.
    """
    print("Optimizer Agent: Calculating optimal route sequence...")
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=GEMINI_API_KEY)
    
    errands_json = json.dumps([e.model_dump() for e in state["errands"]], indent=2)
    deps_json = json.dumps(state["dependency_graph"], indent=2)
    
    prompt = f"""
    You are the Route Optimizer for an errand planning system.
    Your goal is to sequence the errands to minimize travel and satisfy all time/dependency constraints.
    
    Errands with Enriched Data:
    {errands_json}
    
    Dependency Graph (A depends on B means B must happen before A):
    {deps_json}
    
    Provide the optimal sequence of errand IDs, and a brief reasoning for this sequence.
    """
    
    structured_llm = llm.with_structured_output(OptimizerOutput)
    result = structured_llm.invoke(prompt)
    
    return {"optimized_sequence": result.optimized_sequence}
