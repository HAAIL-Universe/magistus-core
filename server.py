# server.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from dotenv import load_dotenv
from datetime import datetime
import uvicorn

from central_hub import run_magistus
from context_types import AgentThought
from debug_logger import log_debug

# Optional: store last agent thoughts for dev mode
last_agent_thoughts: List[AgentThought] = []

# --- Load environment variables ---
load_dotenv()

# --- FastAPI setup ---
app = FastAPI(title="Magistus API", version="0.1")

# --- CORS (for frontend dev testing) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic schema for input ---
class AskRequest(BaseModel):
    input: str

# --- Pydantic schema for response ---
class AskResponse(BaseModel):
    response: str
    agent_thoughts: List[Dict[str, Any]]
    timestamp: str

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(payload: AskRequest):
    global last_agent_thoughts

    user_input = payload.input
    log_debug(f"Received user input via /ask: {user_input}")

    try:
        context, agent_thoughts, final_response = run_magistus(user_input)
        last_agent_thoughts = agent_thoughts

        thoughts_serialized = [thought.__dict__ for thought in agent_thoughts]
        return {
            "response": final_response,
            "agent_thoughts": thoughts_serialized,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        log_debug(f"Error in /ask: {str(e)}")
        return {
            "response": "An internal error occurred while processing your request.",
            "agent_thoughts": [],
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/agents/thoughts")
async def get_last_agent_thoughts():
    return {
        "agent_thoughts": [thought.__dict__ for thought in last_agent_thoughts],
        "timestamp": datetime.utcnow().isoformat()
    }

# --- Optional audio output endpoint ---
# from voice_output import speak_response
# @app.post("/speak")
# async def speak(payload: AskRequest):
#     audio_path = speak_response(payload.input)
#     return FileResponse(audio_path, media_type="audio/mpeg")

# --- Uvicorn Entry Point ---
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
