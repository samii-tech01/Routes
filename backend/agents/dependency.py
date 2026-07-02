from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.state import ErrandState, AgentProposal
from core.config import get_specialist_llm
from pydantic import BaseModel, Field
from typing import List

class DependencySequenceOutput(BaseModel):
    proposed_sequence: List[str] = Field(description="Ordered list of errand IDs that strictly obeys all dependencies.")
    rationale: str = Field(description="Explanation of the topological sort and dependency constraints.")

def dependency_agent(state: ErrandState) -> dict:
    """
    Schedules errands based purely on logical dependencies (e.g., must get cash before buying from cash-only store).
    Provides a route that has zero dependency violations.
    """
    llm = get_specialist_llm()
    parser = PydanticOutputParser(pydantic_object=DependencySequenceOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Dependency Agent. Your ONLY job is to sequence the provided errands to ensure no logical prerequisites are violated. If Errand B depends on Errand A, Errand A MUST appear before Errand B in the sequence. Ignore time windows and distance. You must output valid JSON matching the schema.\n{format_instructions}"),
        ("human", "Errands:\n{errands}")
    ])
    
    chain = prompt | llm | parser
    
    errands_str = "\n".join([
        f"ID: {e.id}, Description: {e.description}, Dependencies: {e.dependencies or 'None'}"
        for e in state['errands']
    ])
    
    if not errands_str:
        return {"proposals": []}

    try:
        output = chain.invoke({
            "errands": errands_str,
            "format_instructions": parser.get_format_instructions()
        })
        
        # Penalties for dependency violations are strictly handled by Orchestrator (Veto power).
        # We assume this sequence has 0 violations.
        proposal = AgentProposal(
            agent_name="Dependency",
            proposed_sequence=output.proposed_sequence,
            score_penalty=0,
            rationale=output.rationale
        )
        
        return {"proposals": [proposal]}
        
    except Exception as e:
        print(f"Dependency Agent Error: {e}")
        return {"proposals": []}
