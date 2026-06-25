from langchain_google_genai import ChatGoogleGenerativeAI
from core.state import ErrandState
from core.config import GEMINI_API_KEY
import json

def explainer_agent(state: ErrandState) -> ErrandState:
    """
    Agent 5: Explainer Agent
    Transforms the optimized sequence into a human-readable plan with reasoning.
    """
    print("Explainer Agent: Generating human-readable plan...")
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=GEMINI_API_KEY)
    
    errands_json = json.dumps([e.model_dump() for e in state["errands"]], indent=2)
    sequence = state["optimized_sequence"]
    
    prompt = f"""
    You are the Explainer Agent. The Optimizer has finalized the errand sequence.
    Your job is to present this plan to the user in a clear, friendly, human-readable format.
    
    Explain *why* this order was chosen (referencing location clustering, time constraints, or inferred logical rules).
    Also, highlight any risks (e.g. "You only have 15 mins before the pharmacy closes").
    
    Errands data:
    {errands_json}
    
    Optimized Sequence (Order of execution):
    {sequence}
    
    Output the final plan in plain text (Markdown formatting is okay). Do not output JSON.
    """
    
    result = llm.invoke(prompt)
    
    return {"final_plan_text": result.content}
