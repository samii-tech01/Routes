from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

class Errand(BaseModel):
    id: str = Field(description="Unique identifier for the errand (e.g., 'e1', 'e2')")
    description: str = Field(description="Original description of the errand")
    errand_type: str = Field(description="Type of errand (e.g., 'grocery', 'pharmacy', 'post_office')")
    location_hint: Optional[str] = Field(None, description="Any location details mentioned by user")
    time_constraint: Optional[str] = Field(None, description="Explicit time constraints (e.g., 'before 3pm')")
    dependencies: List[str] = Field(default_factory=list, description="IDs of other errands that must be done before this one")

    # Enriched fields (populated by Agent 2)
    resolved_location: Optional[str] = Field(None, description="Resolved address or coordinates")
    estimated_duration_mins: Optional[int] = Field(None, description="Estimated time spent at the location in minutes")
    opening_hours: Optional[str] = Field(None, description="Opening hours if applicable")
    
    # Inferred constraints (populated by Agent 3)
    inferred_constraints: List[str] = Field(default_factory=list, description="Inferred time or ordering constraints")

class ErrandState(TypedDict):
    """
    Represents the session memory for the LangGraph pipeline.
    """
    user_input: str
    errands: List[Errand]
    dependency_graph: Dict[str, List[str]] # errand_id -> list of errand_ids it depends on
    optimized_sequence: List[str] # List of errand_ids in order
    final_plan_text: str
    eval_flags: List[str] # Any issues flagged by the evaluator
    retry_count: int
