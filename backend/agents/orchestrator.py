from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from core.state import ErrandState
from core.config import get_orchestrator_llm

class OrchestratorOutput(BaseModel):
    selected_sequence: List[str] = Field(
        description="The final winning ordered list of errand IDs, e.g. ['e1', 'e3', 'e2']"
    )
    explanation_trace: str = Field(
        description="Detailed markdown explanation of scoring, vetoes, and final decision"
    )

def orchestrator_agent(state: ErrandState) -> dict:
    """
    Evaluates the proposals from Geo, Temporal, and Dependency agents.
    Selects the best sequence based on the Negotiation Protocol and outputs
    BOTH the structured optimized_sequence AND a human-readable final_plan_text.
    """
    llm = get_orchestrator_llm()
    parser = PydanticOutputParser(pydantic_object=OrchestratorOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are the Orchestrator Agent for Errand Brain. Evaluate competing errand sequences "
         "proposed by specialist agents and select the absolute best one.\n\n"
         "RULES:\n"
         "1. Hard Constraints (VETO): Reject any proposal violating dependency rules or hard deadlines.\n"
         "2. Soft Constraints (PENALTY): Proposals lose points for extra drive time (1 pt/min) or "
         "   missed preferred time windows (10 pts/miss).\n"
         "3. Tie-Breaking: If scores are tied, select the sequence that finishes earliest. "
         "   If still tied, select shortest distance.\n\n"
         "Output valid JSON matching this schema:\n{format_instructions}"),
        ("human", "Errands:\n{errands}\n\nProposals:\n{proposals}")
    ])



    errands_str = "\n".join([
        f"ID: {e.id}, Description: {e.description}, "
        f"Dependencies: {e.dependencies or 'none'}, Time: {e.time_constraint or 'none'}"
        for e in state['errands']
    ])

    proposals_str = "\n\n".join([
        f"Agent: {p.agent_name}\nSequence: {p.proposed_sequence}\n"
        f"Penalty Score: {p.score_penalty}\nRationale: {p.rationale}"
        for p in state.get('proposals', [])
    ])

    if not proposals_str:
        return {
            "final_plan_text": "No proposals received.",
            "optimized_sequence": [e.id for e in state['errands']],
        }


    errand_map = {e.id: e for e in state['errands']}
    chain = prompt | llm
    
    for attempt in range(3):
        try:
            raw_response = chain.invoke({
                "errands": errands_str,
                "proposals": proposals_str,
                "format_instructions": parser.get_format_instructions()
            })
            content = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)
            output = parser.parse(content)
            
            plan_lines = ["Here is your optimised errand route:\n"]
            for step, eid in enumerate(output.selected_sequence, 1):
                e = errand_map.get(eid)
                if e:
                    loc = e.resolved_location or e.preferred_location or "location to be confirmed"
                    time_note = f"  (by {e.time_constraint})" if e.time_constraint else ""
                    plan_lines.append(f"  Step {step}: {e.description}{time_note}")
                    plan_lines.append(f"           --> {loc}")

            return {
                "final_plan_text": "\n".join(plan_lines) + "\n\nReasoning:\n" + output.explanation_trace,
                "optimized_sequence": output.selected_sequence,
            }
        except Exception as e:
            if attempt == 2:
                print(f"Orchestrator Agent Error after 3 attempts: {e}")
                return {
                    "final_plan_text": "Failed to parse orchestrator output.",
                    "optimized_sequence": [e.id for e in state['errands']],
                }
            print(f"  [Orchestrator] JSON error, retrying... ({attempt+1}/3)")
