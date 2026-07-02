"""
Full Graph Test for Errand Brain Agent Society
================================================
Run with: python tests/test_graph.py

This test runs the ACTUAL compiled LangGraph, which:
- Executes Geo, Temporal, and Dependency agents IN PARALLEL
- Merges all 3 proposals via the reducer
- Lets the Orchestrator evaluate ALL proposals and pick the best one

This is the real negotiation as it would run in production.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import validate_config
from agents.supervisor import build_graph

DIVIDER = "\n" + "=" * 60 + "\n"

TEST_INPUT = (
    "I need to: "
    "1) pick up a package from the post office (they close at 5pm), "
    "2) buy groceries at the supermarket, "
    "3) get cash from the ATM before the supermarket because they only take cash, "
    "4) pick up my prescription from the pharmacy (closes at 6pm). "
    "The post office and pharmacy are on the same side of town."
)

def run():
    print(DIVIDER)
    print("  ERRAND BRAIN - Full LangGraph Negotiation Test")
    print(DIVIDER)

    validate_config()

    # Build and compile the real LangGraph graph
    print("Building Agent Society graph...")
    graph = build_graph()
    print("Graph compiled. Running full pipeline...\n")

    # Initial state using the new schema
    initial_state = {
        "user_input": TEST_INPUT,
        "errands": [],
        "proposals": [],
        "final_plan_sequence": [],
        "final_plan_text": "",
        "explanation_trace": ""
    }

    print(f"INPUT:\n  {TEST_INPUT}\n")
    print("Running graph (this may take 20-40 seconds as agents run in parallel)...\n")

    try:
        final_state = graph.invoke(initial_state)

        print("\n" + "-" * 60)
        print("  ERRANDS PARSED")
        print("-" * 60)
        for e in final_state.get("errands", []):
            print(f"  [{e.id}] {e.description}")
            print(f"        time     : {e.time_constraint or '--'}")
            print(f"        depends  : {e.dependencies or '--'}")

        print("\n" + "-" * 60)
        print(f"  PROPOSALS RECEIVED ({len(final_state.get('proposals', []))} total)")
        print("-" * 60)
        for p in final_state.get("proposals", []):
            print(f"\n  [{p.agent_name}]")
            print("    Sequence : " + " -> ".join(p.proposed_sequence))
            print(f"    Penalty  : {p.score_penalty}")
            print(f"    Rationale: {p.rationale[:100]}...")

        print(DIVIDER)
        print("  FINAL NEGOTIATED PLAN")
        print(DIVIDER)
        print(final_state.get("final_plan_text", "No plan generated."))
        print(DIVIDER)

    except Exception as e:
        print(f"\nError running graph: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
