from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.state import ErrandState, AgentProposal
from core.config import get_specialist_llm
from pydantic import BaseModel, Field
from typing import List

class TemporalSequenceOutput(BaseModel):
    proposed_sequence: List[str] = Field(description="Ordered list of errand IDs prioritizing strict deadlines and opening hours.")
    missed_soft_windows: int = Field(description="Number of preferred but non-mandatory time windows missed.")
    rationale: str = Field(description="Explanation of the scheduling logic and any necessary compromises.")

def temporal_constraint_agent(state: ErrandState) -> dict:
    """
    Schedules errands based on opening hours and deadlines.
    Provides a route that minimizes time violations regardless of physical distance.
    """
    llm = get_specialist_llm()
    parser = PydanticOutputParser(pydantic_object=TemporalSequenceOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Temporal-Constraint Agent. Your ONLY job is to sequence the provided errands to ensure hard deadlines (e.g., appointments) and operating hours are met, while accounting for physical travel times.\n"
                   "You are provided with a drive-time matrix (in minutes). You MUST factor this travel time into your schedule to ensure it is physically possible to reach each destination before its deadline.\n"
                   "If soft preferred times must be missed to meet hard deadlines, do so and count them.\n"
                   "You must output valid JSON matching the schema.\n{format_instructions}"),
        ("human", "Errands:\n{errands}\n\nDrive-time matrix (minutes):\n{matrix}")
    ])
    

    
    errands_str = "\n".join([
        f"ID: {e.id}, Description: {e.description}, "
        f"Constraint: {e.time_constraint or 'None'}, Hours: {e.opening_hours or 'None'}, "
        f"Duration: {e.estimated_duration_mins or 30} mins" 
        for e in state['errands']
    ])
    
    if not errands_str:
        return {"proposals": []}

    matrix = state.get("drive_matrix", {})
    matrix_str = "Drive Times:\n"
    for src, targets in matrix.items():
        for tgt, mins in targets.items():
            if src != tgt:
                matrix_str += f"  {src} -> {tgt}: {mins} mins\n"

    chain = prompt | llm
    
    for attempt in range(3):
        try:
            raw_response = chain.invoke({
                "errands": errands_str,
                "matrix": matrix_str,
                "format_instructions": parser.get_format_instructions()
            })
            content = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)
            output = parser.parse(content)
            
            # Penalty: 10 points per missed soft window
            penalty = output.missed_soft_windows * 10
            
            proposal = AgentProposal(
                agent_name="Temporal-Constraint",
                proposed_sequence=output.proposed_sequence,
                score_penalty=penalty,
                rationale=output.rationale
            )
            
            return {"proposals": [proposal]}
            
        except Exception as e:
            if attempt == 2:
                print(f"Temporal-Constraint Agent Error after 3 attempts: {e}")
                return {"proposals": []}
            print(f"  [Temporal] JSON error, retrying... ({attempt+1}/3)")
