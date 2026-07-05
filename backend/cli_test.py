"""
Route Brain - Interactive CLI
A conversational interface that:
  1. Greets the user
  2. Confirms their city via Geoapify Maps
  3. Accepts natural language routes
  4. Runs the multi-agent negotiation
  5. Shows the optimized plan + a clickable Google Maps route link
"""
import sys
import os
import urllib.parse
import uuid
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.types import Command

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import validate_config, get_specialist_llm
from core.state import ErrandState
from agents.supervisor import build_graph
from mcp.maps_tool import geocode_address, geocode_city

# ─────────────────────────────────────────────
# Schema: Conversational Location Parser
# ─────────────────────────────────────────────
class LocationConfirmation(BaseModel):
    is_confirmed: bool = Field(description="True if the user confirmed the location, False if they rejected or corrected it.")
    extracted_location: str = Field(description="The actual location string to search for, stripping all conversational filler. Empty if confirmed.", default="")

class UnifiedInputParser(BaseModel):
    has_location: bool = Field(description="True if the user's input contains or implies a physical starting location or address.")
    has_errands: bool = Field(description="True if the user's input contains places they want to visit or tasks they need to do.")
    starting_location: str = Field(description="The clean starting location to search for, stripping conversational filler. Empty if not found.", default="")
    errands_text: str = Field(description="The exact text describing the errands or places to visit. Empty if not found.", default="")
    chat_reply: str = Field(description="A friendly reply to send back if the input has NO location AND NO errands (just greeting/chat).", default="")

class ParsedLocation(BaseModel):
    city: str = Field(description="The city name extracted from the user's input. E.g. 'Khairpur', 'Sukkur'. Empty if not found.", default="")
    landmark: str = Field(description="The specific landmark, street, or place within the city. E.g. 'Khaki Shah Pul', 'Radio Pakistan'. Empty if not found.", default="")

# ─────────────────────────────────────────────
# Helper: build a Google Maps Directions URL
# ─────────────────────────────────────────────
def build_maps_url(origin: str, stops: list[str]) -> str:
    """
    Builds a Google Maps multi-stop directions URL.
    origin  : the user's confirmed city / starting point
    stops   : ordered list of resolved addresses (from optimized sequence)
    """
    if not stops:
        return ""

    base = "https://www.google.com/maps/dir/"

    # First element is origin, last is destination, middle are waypoints
    all_points = [origin] + stops
    encoded = [urllib.parse.quote(p) for p in all_points]
    return base + "/".join(encoded)


# ─────────────────────────────────────────────
# Helper: separator line
# ─────────────────────────────────────────────
def sep(char="=", width=56):
    print(char * width)


# ─────────────────────────────────────────────
# Main conversational loop
# ─────────────────────────────────────────────
def main():
    sep()
    print("        ROUTE BRAIN  -  Agent Society")
    sep()
    print()
    print("Hello! I am your AI route planner.")
    print("I will find the smartest route for all your stops")
    print("so you spend less time on the road.\n")

    validate_config()

    # Initialize LLM
    llm = get_specialist_llm()

    # ── Step 1: Ask for city (locked in for the whole session) ───────────
    user_location = None
    user_city = ""
    user_city_lat = None
    user_city_lng = None
    user_city_bbox = None
    user_lat = None
    user_lng = None

    print("First, what city are you currently in?")
    while True:
        city_raw = input("  > ").strip()
        if not city_raw:
            continue
        if city_raw.lower() in ("exit", "quit", "q"):
            return

        print(f"  Locating {city_raw}...")
        city_geo = geocode_city(city_raw)
        if city_geo.get("lat"):
            user_city     = city_geo["city"]
            user_city_lat = city_geo["lat"]
            user_city_lng = city_geo["lng"]
            user_city_bbox = city_geo.get("bbox")
            
            # Use the fully formatted string so the user sees province/country
            formatted_city = city_geo.get("formatted") or f"{user_city}, Pakistan"
            
            print(f"  I found: {formatted_city}")
            
            while True:
                confirm = input("  Is this correct? (yes/no): ").strip().lower()
                if confirm in ("y", "yes", "yep", "yeah", "ok", "okay", "sure", "fine", "alright", ""):
                    confirm = "yes"
                    break
                elif confirm in ("n", "no", "nope", "nah"):
                    confirm = "no"
                    break
                else:
                    print("  Please answer 'yes' or 'no'.")
                    
            if confirm == "no":
                print("  Okay, let's try again. Please be more specific (e.g. 'Khairpur, Sindh').\n")
                continue
                
            user_location = formatted_city
            user_lat = user_city_lat
            user_lng = user_city_lng
            print(f"  Got it! I'll keep '{user_city}' in mind for all your stops today.\n")
            
            print("  Are you near any specific landmark or building? (Press Enter to skip)")
            landmark_raw = input("  > ").strip()
            while landmark_raw:
                print(f"  Locating {landmark_raw}...")
                lm_geo = geocode_address(
                    landmark_raw, 
                    city_hint=user_city, 
                    city_bbox=user_city_bbox, 
                    bias_lat=user_city_lat, 
                    bias_lng=user_city_lng
                )
                if lm_geo.get("lat"):
                    outside_warn = " (OUTSIDE CITY)" if lm_geo.get("outside_city") else ""
                    print(f"  I found: {lm_geo['formatted_address']}{outside_warn}")
                    
                    while True:
                        confirm = input("  Is this correct? (yes/no): ").strip().lower()
                        if confirm in ("y", "yes", "yep", "yeah", "ok", "okay", "sure", "fine", "alright", ""):
                            confirm = "yes"
                            break
                        elif confirm in ("n", "no", "nope", "nah"):
                            confirm = "no"
                            break
                        else:
                            print("  Please answer 'yes' or 'no'.")
                            
                    if confirm == "yes":
                        user_location = lm_geo["formatted_address"]
                        user_lat = lm_geo["lat"]
                        user_lng = lm_geo["lng"]
                        print(f"  Locked in your start location: {user_location}\n")
                        break
                    else:
                        print("  Okay, let's try again. Please provide a more specific landmark (or press Enter to skip).")
                        landmark_raw = input("  > ").strip()
                        if not landmark_raw:
                            print("  We'll stick to the city center.\n")
                else:
                    print(f"  Couldn't pinpoint '{landmark_raw}'.")
                    print("  Please provide a more specific landmark (or press Enter to skip).")
                    landmark_raw = input("  > ").strip()
                    if not landmark_raw:
                        print("  We'll stick to the city center.\n")
            break
        else:
            print(f"  Sorry, I couldn't find '{city_raw}' on the map.")
            print("  Please try again (e.g. 'Khairpur', 'Karachi', 'Lahore').\n")

    # ── Step 2: Ask for errands ───────────────────────────────────────────
    print("Now tell me the places you need to visit today.")
    print("Type 'exit' to quit.\n")
    sep("-")
    user_input = input("\nWhere do you need to go today?\n> ").strip()


    # Initialize the LangGraph
    from agents.supervisor import build_graph
    workflow = build_graph()

    while True:
        try:
            if user_input.lower() in ("exit", "quit", "bye", "q"):
                print("\nGood luck with your routes! Goodbye.\n")
                break
            if not user_input:
                user_input = input("\nWhere do you need to go today?\n> ").strip()
                continue

            print("\nThinking... (agents are negotiating your best route)\n")

            state = ErrandState(
                user_input=user_input,
                user_location=user_location,
                user_lat=user_lat,
                user_lng=user_lng,
                user_city=user_city,
                user_city_lat=user_city_lat,
                user_city_lng=user_city_lng,
                user_city_bbox=user_city_bbox,
                drive_matrix=None,
                errands=[],
                proposals=[],
                final_plan_sequence=[],
                final_plan_text="",
                explanation_trace="",
            )
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            final_state = workflow.invoke(state, config=config)

            # Handle LangGraph interrupts (Human-in-the-Loop)
            while True:
                current_state = workflow.get_state(config)
                if current_state.next and current_state.tasks and current_state.tasks[0].interrupts:
                    question = current_state.tasks[0].interrupts[0].value
                    print(f"\n  [Agent] {question}")
                    ans = input("  > ").strip()
                    print("\nThinking... (agents are resuming the route)\n")
                    final_state = workflow.invoke(Command(resume=ans), config=config)
                elif current_state.next:
                    # Paused but no interrupts? Safety break
                    break
                else:
                    break

            errands      = final_state.get("errands", [])
            sequence_ids = final_state.get("optimized_sequence", [])
            plan_text    = final_state.get("final_plan_text", "")

            # ── Print plan ─────────────────────
            sep()
            print("  YOUR OPTIMISED ROUTE PLAN")
            sep()
            print()
            print(plan_text or "No plan was generated.")

            # ── Print stop-by-stop list ─────────
            # Build id -> errand lookup
            errand_map = {e.id: e for e in errands}

            if sequence_ids:
                print()
                sep("-")
                print("  STOP-BY-STOP ROUTE:")
                sep("-")
                ordered_locations = []
                for step, eid in enumerate(sequence_ids, 1):
                    e = errand_map.get(eid)
                    if e:
                        loc = e.resolved_location or e.preferred_location or f"{e.errand_type} in {user_location}"
                        ordered_locations.append(loc)
                        time_note = f"  [by {e.time_constraint}]" if e.time_constraint else ""
                        dep_note  = f"  [after {e.dependencies}]"  if e.dependencies  else ""
                        print(f"  Stop {step}: {e.description}")
                        print(f"    Location : {loc}")
                        if time_note: print(f"    Deadline : {e.time_constraint}")
                        if dep_note:  print(f"    Depends on: {e.dependencies}")
                        print()

                # ── Google Maps route link ──────
                if ordered_locations:
                    maps_url = build_maps_url(user_location, ordered_locations)
                    sep("-")
                    print("  OPEN YOUR ROUTE IN GOOGLE MAPS:")
                    print()
                    print(f"  {maps_url}")
                    sep("-")
                    print()
                    print("  Copy the link above and paste it in your browser")
                    print("  (or on your phone) to get turn-by-turn directions!")

            print()
            sep()
            another = input("Do you have more routes? (y/n): ").strip().lower()
            if another != "y":
                print("\nAll done! Have a productive day.\n")
                break

        except KeyboardInterrupt:
            print("\n\nSession ended. Goodbye!\n")
            break
        except Exception as exc:
            print(f"\n[ERROR] Something went wrong: {exc}\n")
            user_input = "" # Clear input so it pauses and asks again on the next loop


if __name__ == "__main__":
    main()
