import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from core.config import validate_config
from core.state import ErrandState
from agents.supervisor import build_graph

app = FastAPI(
    title="Errand Brain Agent Society",
    description="Backend API for Kaggle VibeCoding Capstone",
    version="1.0.0"
)

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compile graph once at startup
workflow = build_graph()

class ChatRequest(BaseModel):
    user_input: str
    user_location: str = ""

class ChatResponse(BaseModel):
    final_plan_text: str
    proposals: list
    errands: list

@app.on_event("startup")
async def startup_event():
    validate_config()
    print("Agent Society backend is ready!")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.user_input.strip():
        raise HTTPException(status_code=400, detail="Input cannot be empty.")
        
    state = ErrandState(
        user_input=request.user_input,
        user_location=request.user_location,
        errands=[],
        dependency_graph={},
        optimized_sequence=[],
        final_plan_text="",
        eval_flags=[],
        retry_count=0,
        proposals=[]
    )
    
    try:
        final_state = workflow.invoke(state)
        
        # Serialize the pydantic models into dicts for the JSON response
        errands_dict = [e.model_dump() for e in final_state.get("errands", [])]
        proposals_dict = [p.model_dump() for p in final_state.get("proposals", [])]
        
        return ChatResponse(
            final_plan_text=final_state.get("final_plan_text", "No plan generated."),
            proposals=proposals_dict,
            errands=errands_dict
        )
    except Exception as e:
        print(f"Graph Execution Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
