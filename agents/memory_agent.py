from langchain_core.prompts import ChatPromptTemplate
from core.state import ErrandState
from core.config import get_specialist_llm

def memory_agent(state: ErrandState) -> dict:
    """
    Extracts cross-session memory from the user input (e.g., "my usual pharmacy").
    In a real system, this would write to Postgres/AlloyDB using the Database MCP.
    """
    llm = get_specialist_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Memory Agent. Your job is to extract user preferences from their input, such as their 'usual' locations for specific errands. Extract any location hints."),
        ("human", "User Input: {user_input}")
    ])
    
    chain = prompt | llm
    
    try:
        # In Phase 3, we will wire this to the Database MCP to persist the state.
        # For now, we simulate extraction.
        response = chain.invoke({"user_input": state.get("user_input", "")})
        
        # We don't alter proposals here. We just return state updates if any.
        return {}
    except Exception as e:
        print(f"Memory Agent Error: {e}")
        return {}
