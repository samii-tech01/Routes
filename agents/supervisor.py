from langgraph.graph import StateGraph, END
from core.state import ErrandState
from agents.parser import parser_agent
from agents.enrichment import enrichment_agent
from agents.reasoner import reasoner_agent
from agents.optimizer import optimizer_agent
from agents.explainer import explainer_agent
from agents.evaluator import evaluator_agent

def should_retry(state: ErrandState):
    flags = state.get("eval_flags", [])
    retry_count = state.get("retry_count", 0)
    
    if flags and retry_count < 2:
        # If there are flags and we haven't maxed out retries, loop back to optimizer
        return "optimizer"
    
    # Otherwise finish
    return END

def increment_retry(state: ErrandState):
    return {"retry_count": state.get("retry_count", 0) + 1}

def build_graph():
    """
    Constructs the LangGraph supervisor workflow.
    """
    workflow = StateGraph(ErrandState)
    
    # Add nodes
    workflow.add_node("parser", parser_agent)
    workflow.add_node("enrichment", enrichment_agent)
    workflow.add_node("reasoner", reasoner_agent)
    workflow.add_node("optimizer", optimizer_agent)
    workflow.add_node("explainer", explainer_agent)
    workflow.add_node("evaluator", evaluator_agent)
    
    # Define edges
    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "enrichment")
    workflow.add_edge("enrichment", "reasoner")
    workflow.add_edge("reasoner", "optimizer")
    workflow.add_edge("optimizer", "explainer")
    workflow.add_edge("explainer", "evaluator")
    
    # Conditional edge for evaluation retry loop
    workflow.add_conditional_edges(
        "evaluator",
        should_retry,
        {
            "optimizer": "optimizer", # Loop back to fix issues
            END: END # Finish
        }
    )
    
    return workflow.compile()
