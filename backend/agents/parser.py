from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from core.state import ErrandState, Errand
from core.config import get_specialist_llm

class ParserOutput(BaseModel):
    errands: List[Errand] = Field(description="List of extracted errands")

def parser_agent(state: ErrandState) -> dict:
    """
    Agent 1: Parser Agent
    Extracts structured errand data from raw natural language input.
    """
    user_input = state.get("user_input", "")
    llm = get_specialist_llm()
    parser = PydanticOutputParser(pydantic_object=ParserOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert natural language parser for an errand planning system.\n"
                   "Your job is to extract individual errands from the user's input.\n\n"
                   "For each distinct errand, identify:\n"
                   "1. A short, unique ID (e.g., e1, e2, e3 in order mentioned).\n"
                   "2. A brief description of the errand.\n"
                   "3. The type of errand (e.g., hospital, grocery, repair_service, pharmacy, atm).\n"
                   "4. Any SPECIFIC location hints mentioned (e.g., 'Hora Hospital', 'Gurdawar Road').\n"
                   "5. Any EXPLICIT time constraints (e.g., 'by 8am', 'closes at 6pm').\n"
                   "6. ONLY add a dependency if the user uses explicit prerequisite language such as\n"
                   "   'before', 'after', 'first then', 'must go to X before Y', 'need X first'.\n"
                   "   DO NOT add dependencies just because the user says 'then' or lists things in order.\n"
                   "   'then' means preference of order only, NOT a hard dependency.\n\n"
                   "{format_instructions}"),
        ("human", "User Input: {user_input}\nUser City: {user_location}")
    ])
    
    # Use raw string output so we can manually retry parsing
    chain = prompt | llm
    print("Parser Agent: Extracting structured data...")
    
    for attempt in range(3):
        try:
            raw_response = chain.invoke({
                "user_input": user_input,
                "user_location": state.get("user_location", ""),
                "format_instructions": parser.get_format_instructions()
            })
            # Langchain LLMs return AIMessage, extract the content
            content = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)
            result = parser.parse(content)
            
            print(f"Parser Agent: Extracted {len(result.errands)} errands.")
            return {"errands": result.errands}
        except Exception as e:
            if attempt == 2:
                print(f"Parser Agent Error after 3 attempts: {e}")
                return {"errands": []}
            print(f"  [Parser] JSON error, retrying... ({attempt+1}/3)")
