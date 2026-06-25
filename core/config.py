import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def validate_config():
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY is not set. System will not be able to call the LLM.")
    if not GOOGLE_MAPS_API_KEY:
        print("Warning: GOOGLE_MAPS_API_KEY is not set. Enrichment agent will need to use mock data.")
