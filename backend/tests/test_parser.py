import os
import sys

# Add the parent directory to sys.path so we can import from core and agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.parser import parser_agent
from core.state import ErrandState
from core.config import validate_config

def main():
    validate_config()
    
    # Test Input with dependencies, locations, and times
    test_input = "I need to pick up my prescription, buy groceries, drop a parcel at the post office, and be at the dentist at 3pm. The pharmacy closes at 6pm. I must go to the ATM before buying groceries."
    
    # Initialize mock state
    state = ErrandState(
        user_input=test_input,
        user_location="New York",
        errands=[],
        dependency_graph={},
        optimized_sequence=[],
        final_plan_text="",
        eval_flags=[],
        retry_count=0,
        proposals=[]
    )
    
    print("======================================================")
    print("PARSER AGENT DEMONSTRATION")
    print("======================================================")
    print(f"\nRAW USER INPUT:\n\"{test_input}\"\n")
    print("PARSING (Sending to Qwen Model via LangChain)...\n")
    
    try:
        new_state = parser_agent(state)
        
        print("EXTRACTION COMPLETE! Here is the structured JSON output:\n")
        for errand in new_state["errands"]:
            print(f"Errand: {errand.id.upper()}")
            print(f"   * Type         : {errand.errand_type}")
            print(f"   * Description  : {errand.description}")
            if errand.preferred_location:
                print(f"   * Location Hint: {errand.preferred_location}")
            if errand.time_constraint:
                print(f"   * Time Limit   : {errand.time_constraint}")
            if errand.dependencies:
                print(f"   * Dependencies : Must happen AFTER {errand.dependencies}")
            print()
            
    except Exception as e:
        print(f"Error running parser agent: {e}")

if __name__ == "__main__":
    main()
