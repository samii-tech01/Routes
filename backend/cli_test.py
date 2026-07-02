import sys
import json
from core.config import validate_config
from core.state import ErrandState
from agents.supervisor import build_graph
from mcp.maps_tool import geocode_address

def main():
    print("======================================================")
    print("  Local Terminal Testing - Errand Brain Agent Society ")
    print("======================================================")
    validate_config()
    
    print("\n[READY] The AI models (Qwen) and MCPs (Supabase + Google Maps) are active.")
    
    # Get and validate user location context
    while True:
        raw_location = input("What city/neighborhood are you in right now? (e.g. 'Brooklyn, NY' or 'Khairpur'): ").strip()
        if not raw_location:
            continue
            
        print("🌍 Checking Google Maps...")
        geo_result = geocode_address(raw_location)
        formatted_address = geo_result.get("formatted_address")
        
        if not geo_result.get("lat"):
            print(f"❌ Could not find '{raw_location}' on Google Maps. Please try again.")
            continue
            
        confirm = input(f"📍 I found: '{formatted_address}'. Is this correct? (y/n): ").strip().lower()
        if confirm == 'y':
            user_location = formatted_address
            print(f"\nAwesome! I will map all your errands within '{user_location}'.")
            break
        else:
            print("Let's try again.\n")
    
    print("Type your errands naturally. The system will figure out the rest.")
    print("Type 'exit' to quit.\n")
    
    workflow = build_graph()
    
    while True:
        try:
            user_input = input("\nYour errands (or 'exit'): ").strip()
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input:
                continue
                
            print("\n[Processing] Running multi-agent negotiation...")
            
            state = ErrandState(
                user_input=user_input,
                user_location=user_location,
                errands=[],
                dependency_graph={},
                optimized_sequence=[],
                final_plan_text="",
                eval_flags=[],
                retry_count=0,
                proposals=[]
            )
            
            final_state = workflow.invoke(state)
            
            print("\n" + "="*54)
            print("  AGENT NEGOTIATION COMPLETE")
            print("="*54 + "\n")
            
            print("📝 THE PLAN:")
            print(final_state.get("final_plan_text", "No plan generated."))
            print("\n------------------------------------------------------")
            print("📍 EXTRACTED ERRANDS:")
            for e in final_state.get("errands", []):
                print(f"  - [{e.id}] {e.description}")
                print(f"      Type: {e.errand_type}")
                print(f"      Location: {e.resolved_location or e.preferred_location or 'N/A'}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n[ERROR] An error occurred: {e}")

if __name__ == "__main__":
    main()
