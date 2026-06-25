import sys
from core.config import validate_config
from core.state import ErrandState
from agents.supervisor import build_graph

def main():
    print("Welcome to Routes (Errand Brain) Planner!\n")
    validate_config()
    
    # Simple CLI loop
    print("\nPlease describe your errands in plain English.")
    print("Example: 'I need to pick up a package from the post office, then get groceries. The post office closes at 5pm.'")
    print("(Type 'exit' or 'quit' to stop)\n")
    
    workflow = build_graph()
    
    while True:
        user_input = input("Your errands: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
        if not user_input:
            continue
            
        print("\n--- Planning your route ---\n")
        
        # Initialize state
        state = ErrandState(
            user_input=user_input,
            errands=[],
            dependency_graph={},
            optimized_sequence=[],
            final_plan_text="",
            eval_flags=[],
            retry_count=0
        )
        
        try:
            # Run the graph
            final_state = workflow.invoke(state)
            
            print("\n================ FINAL PLAN ================\n")
            print(final_state.get("final_plan_text", "No plan generated."))
            print("\n============================================\n")
            
            if final_state.get("eval_flags"):
                print("Note: The evaluator flagged the following potential issues:")
                for flag in final_state["eval_flags"]:
                    print(f"- {flag}")
                    
        except Exception as e:
            print(f"\nAn error occurred during planning: {e}")
            print("Please check your API keys or try a simpler prompt.")

if __name__ == "__main__":
    main()
