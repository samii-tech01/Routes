from langgraph.graph import StateGraph, START, END
from core.state import ErrandState
from agents.parser import parser_agent
from agents.memory_agent import memory_agent
from agents.geo_clustering import geo_clustering_agent
from agents.temporal_constraint import temporal_constraint_agent
from agents.dependency import dependency_agent
from agents.orchestrator import orchestrator_agent

def build_graph():
    """
    Constructs the Agent Society negotiation graph using LangGraph.
    """
    workflow = StateGraph(ErrandState)
    
    # Add nodes for each agent
    workflow.add_node("parser", parser_agent)
    workflow.add_node("memory", memory_agent)
    workflow.add_node("geo", geo_clustering_agent)
    workflow.add_node("temporal", temporal_constraint_agent)
    workflow.add_node("dependency", dependency_agent)
    workflow.add_node("orchestrator", orchestrator_agent)
    
    # Define the flow
    # 1. Parse the input
    workflow.add_edge(START, "parser")
    
    # 2. Extract memory context
    workflow.add_edge("parser", "memory")
    
    # 3. Parallel dispatch to specialist agents
    workflow.add_edge("memory", "geo")
    workflow.add_edge("memory", "temporal")
    workflow.add_edge("memory", "dependency")
    
    # 4. Gather proposals at Orchestrator
    workflow.add_edge("geo", "orchestrator")
    workflow.add_edge("temporal", "orchestrator")
    workflow.add_edge("dependency", "orchestrator")
    
    workflow.add_edge("orchestrator", END)
    
    return workflow.compile()
