import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

AIML_API_KEY = os.getenv("AIML_API_KEY")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_orchestrator_llm():
    """
    Returns the reasoning model for the Orchestrator.
    Currently using AIML API as a fallback until Qwen DashScope is available.
    """
    if AIML_API_KEY:
        return ChatOpenAI(
            api_key=AIML_API_KEY,
            base_url="https://api.aimlapi.com/v1",
            model="gpt-4o", # Simulating qwen-max
            max_retries=3,
        )
    # When Qwen is ready, replace above with ChatTongyi(model="qwen-max")
    raise ValueError("No LLM API Key found")

def get_specialist_llm():
    """
    Returns the narrow task model for Specialist Agents.
    Currently using AIML API as a fallback until Qwen DashScope is available.
    """
    if AIML_API_KEY:
        return ChatOpenAI(
            api_key=AIML_API_KEY,
            base_url="https://api.aimlapi.com/v1",
            model="gpt-4o-mini", # Simulating qwen-turbo
            max_retries=3,
        )
    # When Qwen is ready, replace above with ChatTongyi(model="qwen-turbo")
    raise ValueError("No LLM API Key found")

def validate_config():
    if not AIML_API_KEY and not DASHSCOPE_API_KEY:
        print("Warning: No LLM API key set. System will fail.")
    if not GOOGLE_MAPS_API_KEY:
        print("Warning: GOOGLE_MAPS_API_KEY is not set. MCP will need to mock data.")
