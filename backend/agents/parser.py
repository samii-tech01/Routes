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
                   "1. A short, unique ID (e.g., e1, e2).\n"
                   "2. A brief description of the errand.\n"
                   "3. The type of errand (e.g., pharmacy, grocery, drop-off).\n"
                   "4. Any location hints provided.\n"
                   "5. Any explicit time constraints.\n"
                   "6. Any explicit dependencies on other errands.\n\n"
                   "{format_instructions}"),
        ("human", "User Input: {user_input}")
    ])
    
    chain = prompt | llm | parser
    print("Parser Agent: Extracting structured data...")
    try:
        result = chain.invoke({
            "user_input": user_input,
            "format_instructions": parser.get_format_instructions()
        })
        print(f"Parser Agent: Extracted {len(result.errands)} errands.")
        return {"errands": result.errands}
    except Exception as e:
        print(f"Parser Agent Error: {e}")
        return {"errands": []}
