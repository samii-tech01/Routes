import json
import os
from typing import Dict, Any

MEMORY_FILE = os.path.join(os.path.dirname(__file__), '..', 'user_profile.json')

def get_user_profile() -> Dict[str, Any]:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {
        "home_location": "Sukkur, Pakistan",
        "saved_places": {
            "pharmacy": "Al-Shifa Pharmacy, MA Jinnah Road, Sukkur",
            "grocery": "Imtiaz Super Market, Sukkur"
        }
    }

def update_user_profile(new_data: Dict[str, Any]):
    profile = get_user_profile()
    profile.update(new_data)
    with open(MEMORY_FILE, 'w') as f:
        json.dump(profile, f, indent=4)
