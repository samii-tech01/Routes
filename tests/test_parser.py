import os
import sys

# Add the parent directory to sys.path so we can import from core and agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.parser import parser_agent
from core.state import ErrandState
from core.config import validate_config

def main():
    validate_config()
    
    # Test Input
    test_input = "I need to pick up my prescription, buy groceries, drop a parcel at the post office, and be at the dentist at 3pm. The pharmacy closes at 6pm."
    
    # Initialize mock state
    state = ErrandState(
        user_input=test_input,
        errands=[],
        dependency_graph={},
        optimized_sequence=[],
        final_plan_text="",
        eval_flags=[],
        retry_count=0
    )
    
    print(f"Testing Parser Agent with input: '{test_input}'\n")
    try:
        new_state = parser_agent(state)
        
        print("\n--- Parsed Errands ---")
        for errand in new_state["errands"]:
            print(f"- ID: {errand.id}")
            print(f"  Type: {errand.errand_type}")
            print(f"  Desc: {errand.description}")
            if errand.location_hint:
                print(f"  Location Hint: {errand.location_hint}")
            if errand.time_constraint:
                print(f"  Time Constraint: {errand.time_constraint}")
            if errand.dependencies:
                print(f"  Dependencies: {errand.dependencies}")
            print()
            
    except Exception as e:
        print(f"Error running parser agent: {e}")

if __name__ == "__main__":
    main()
