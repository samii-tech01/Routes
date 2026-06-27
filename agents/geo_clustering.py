from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.state import ErrandState, AgentProposal
from core.config import get_specialist_llm
from pydantic import BaseModel, Field
from typing import List

class GeoSequenceOutput(BaseModel):
    proposed_sequence: List[str] = Field(description="Ordered list of errand IDs minimizing travel distance.")
    estimated_drive_time_mins: int = Field(description="Total estimated drive time for this sequence.")
    rationale: str = Field(description="Explanation of the clustering and routing logic.")

def geo_clustering_agent(state: ErrandState) -> dict:
    """
    Groups errands by physical proximity and estimates drive segments.
    Provides a route that minimizes distance regardless of time/dependencies.
    """
    llm = get_specialist_llm()
    parser = PydanticOutputParser(pydantic_object=GeoSequenceOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Geo-Clustering Agent. Your ONLY job is to sequence the provided errands to minimize physical travel distance and time. Ignore time windows and dependencies (the other agents handle those). You must output valid JSON matching the schema.\n{format_instructions}"),
        ("human", "Current Location: User Home.\nErrands: {errands}")
    ])
    
    chain = prompt | llm | parser
    
    # Format the errands for the prompt
    errands_str = "\n".join([f"ID: {e.id}, Description: {e.description}, Location: {e.resolved_location or 'Unknown'}" for e in state['errands']])
    
    if not errands_str:
        return {"proposals": []}

    try:
        output = chain.invoke({
            "errands": errands_str,
            "format_instructions": parser.get_format_instructions()
        })
        
        # We assign a penalty based on drive time to let Orchestrator weigh it
        # Penalty: 1 point per minute of drive time
        penalty = output.estimated_drive_time_mins
        
        proposal = AgentProposal(
            agent_name="Geo-Clustering",
            proposed_sequence=output.proposed_sequence,
            score_penalty=penalty,
            rationale=output.rationale
        )
        
        return {"proposals": [proposal]}
        
    except Exception as e:
        print(f"Geo-Clustering Agent Error: {e}")
        return {"proposals": []}
