from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List
from core.state import ErrandState, Errand
from core.config import GEMINI_API_KEY

class ParserOutput(BaseModel):
    errands: List[Errand] = Field(description="List of extracted errands")

def parser_agent(state: ErrandState) -> ErrandState:
    """
    Agent 1: Parser Agent
    Extracts structured errand data from raw natural language input.
    """
    user_input = state["user_input"]
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Cannot run parser agent.")
    
    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=GEMINI_API_KEY)
    
    prompt = f"""
    You are an expert natural language parser for an errand planning system.
    Your job is to extract individual errands from the user's input.
    
    For each distinct errand, identify:
    1. A short, unique ID (e.g., e1, e2).
    2. A brief description of the errand.
    3. The type of errand (e.g., pharmacy, grocery, drop-off).
    4. Any location hints provided (e.g., 'Main Street', 'near home').
    5. Any explicit time constraints (e.g., 'by 3pm', 'before lunch').
    6. Any explicit dependencies on other errands mentioned by the user.

    User Input:
    "{user_input}"
    """
    
    print("Parser Agent: Extracting structured data...")
    # Force the LLM to return data matching our Pydantic schema
    structured_llm = llm.with_structured_output(ParserOutput)
    
    result = structured_llm.invoke(prompt)
    
    print(f"Parser Agent: Extracted {len(result.errands)} errands.")
    # Update the state with the extracted errands
    return {"errands": result.errands}
