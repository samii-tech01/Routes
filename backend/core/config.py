import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

GMI_API_KEY = os.getenv("GMI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_orchestrator_llm():
    """
    Returns the reasoning model for the Orchestrator.
    Using Qwen3.6-Max-Preview via GMI Cloud.
    """
    if GMI_API_KEY:
        return ChatOpenAI(
            api_key=GMI_API_KEY,
            base_url="https://api.gmi-serving.com/v1",
            model="Qwen/Qwen3.6-Max-Preview",
            max_retries=3,
        )
    raise ValueError("No LLM API Key found")

def get_specialist_llm():
    """
    Returns the narrow task model for Specialist Agents.
    Using Qwen3.6-Plus via GMI Cloud.
    """
    if GMI_API_KEY:
        return ChatOpenAI(
            api_key=GMI_API_KEY,
            base_url="https://api.gmi-serving.com/v1",
            model="Qwen/Qwen3.6-Plus",
            max_retries=3,
        )
    raise ValueError("No LLM API Key found")

def validate_config():
    if not GMI_API_KEY:
        print("Warning: No GMI API key set. System will fail.")
    if not GOOGLE_MAPS_API_KEY:
        print("Warning: GOOGLE_MAPS_API_KEY is not set. MCP will need to mock data.")
