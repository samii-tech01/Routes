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
        ("system", "You are the Temporal-Constraint Agent. Your ONLY job is to sequence the provided errands to ensure hard deadlines (e.g., appointments) and operating hours are met. Ignore physical travel distance. If soft preferred times must be missed to meet hard deadlines, do so and count them. You must output valid JSON matching the schema.\n{format_instructions}"),
        ("human", "Errands:\n{errands}")
    ])
    
    chain = prompt | llm | parser
    
    errands_str = "\n".join([
        f"ID: {e.id}, Description: {e.description}, "
        f"Constraint: {e.time_constraint or 'None'}, Hours: {e.opening_hours or 'None'}, "
        f"Duration: {e.estimated_duration_mins or 30} mins" 
        for e in state['errands']
    ])
    
    if not errands_str:
        return {"proposals": []}

    try:
        output = chain.invoke({
            "errands": errands_str,
            "format_instructions": parser.get_format_instructions()
        })
        
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
        print(f"Temporal-Constraint Agent Error: {e}")
        return {"proposals": []}
