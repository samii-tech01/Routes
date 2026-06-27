from langchain_core.prompts import ChatPromptTemplate
from core.state import ErrandState
from core.config import get_orchestrator_llm

def orchestrator_agent(state: ErrandState) -> dict:
    """
    Evaluates the proposals from Geo, Temporal, and Dependency agents.
    Selects the best sequence based on the Negotiation Protocol and outputs the final plan.
    """
    llm = get_orchestrator_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Orchestrator Agent for Errand Brain. Your job is to evaluate competing errand sequences proposed by specialist agents and select the absolute best one based on the Negotiation Protocol.\n\n"
                   "RULES:\n"
                   "1. Hard Constraints (VETO): You MUST reject any proposal that violates dependency rules or hard deadlines.\n"
                   "2. Soft Constraints (PENALTY): Proposals lose points for extra drive time (1 pt/min) or missed preferred time windows (10 pts/miss).\n"
                   "3. Tie-Breaking: If scores are tied, select the sequence that finishes earliest. If still tied, select the shortest distance.\n\n"
                   "You must output the final selected sequence of IDs and an explanation trace showing how you scored the proposals."),
        ("human", "Errands:\n{errands}\n\nProposals:\n{proposals}")
    ])
    
    chain = prompt | llm
    
    errands_str = "\n".join([
        f"ID: {e.id}, Description: {e.description}, Dependencies: {e.dependencies}, Time: {e.time_constraint}"
        for e in state['errands']
    ])
    
    proposals_str = "\n\n".join([
        f"Agent: {p.agent_name}\nSequence: {p.proposed_sequence}\nPenalty Score: {p.score_penalty}\nRationale: {p.rationale}"
        for p in state.get('proposals', [])
    ])
    
    if not proposals_str:
        return {"final_plan_text": "No proposals received to orchestrate.", "explanation_trace": ""}

    try:
        response = chain.invoke({
            "errands": errands_str,
            "proposals": proposals_str
        })
        
        return {
            "final_plan_text": response.content,
            "explanation_trace": "See final plan text for the detailed scoring breakdown."
        }
        
    except Exception as e:
        print(f"Orchestrator Agent Error: {e}")
        return {"final_plan_text": "Error during orchestration.", "explanation_trace": ""}
