import sys
import time
import logging
import uvicorn
import asyncio
import json
import os
import webbrowser
import threading
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from uuid import uuid4

from meta_learning.meta_learning_supervisor import MetaLearningSupervisor
from meta_learning.memory_store import get_latest_memory_entry
from config_loader import load_config
from context_types import UserInput
from central_hub import run_magistus
from consent_manager import request_user_consent
from synthetic_limiter import evaluate_input
from policy_engine import is_critical_action
from transparency_layer import generate_explanation
from voice_output import speak_text
from llm_wrapper import generate_response, stream_response
from meta_learning.memory_index_entry import MemoryIndexEntry
from meta_learning.utils import append_memory_entry_to_store

# Init FastAPI app
app = FastAPI()

# CORS for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("magistus_launch")

# Load config
config = load_config()

REQUIRED_KEYS = {
    "manifesto_enabled": True,
    "consent_enabled": True,
    "limiter_enabled": True,
    "policy_engine_enabled": True,
    "transparency_enabled": True
}

def validate_launch_config() -> bool:
    logger.info("🔍 Validating Magistus v1.0 Launch Configuration:")
    all_good = True
    for key, expected in REQUIRED_KEYS.items():
        current = config.get(key)
        if current == expected:
            logger.info(f"✅ {key.replace('_', ' ').title()}: Enabled")
        else:
            logger.error(f"❌ {key.replace('_', ' ').title()}: MISSING or DISABLED")
            all_good = False
    if not all_good:
        logger.error("🚫 Launch aborted: critical safeguards are not active.")
    return all_good

def print_system_ready_banner():
    print("\n" + "=" * 50)
    print("🧠 Magistus v1.0 Companion Ready")
    print("🌍 Public Mode: LIMITED")
    print("✅ Ethics: Active | ✅ Consent: Enforced | ✅ Reflection: Enabled")
    print("🎤 Voice: On     | 🛡️  Limiter: On     | 🧠 Fusion Core: Active")
    print("=" * 50 + "\n")

# 🌐 Serve static UI
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    try:
        with open("magistus_ui.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>UI file not found</h1>", status_code=404)

# 💬 Core chat endpoint
@app.post("/chat")
async def chat_endpoint(payload: dict):
    config = load_config()
    user_input = payload.get("input", "")
    reasoning_enabled = payload.get("reasoning_enabled", True)

    if not user_input:
        return JSONResponse({"error": "Missing input"})

    limiter_thought = evaluate_input(user_input)
    if limiter_thought.flags.get("execution_blocked"):
        return JSONResponse({
            "response": "[Blocked] " + limiter_thought.content,
            "agent_thoughts": [],
            "voice_output": config.get("voice_output", False)
        })

    if is_critical_action("external_execution"):
        if not request_user_consent("external_execution", "This may trigger an irreversible system action."):
            return JSONResponse({
                "response": "[Consent Denied] User did not approve action.",
                "agent_thoughts": [],
                "voice_output": config.get("voice_output", False)
            })

    if not reasoning_enabled:
        response = generate_response(user_input)
        return JSONResponse({
            "response": response,
            "agent_thoughts": [],
            "voice_output": config.get("voice_output", False)
        })

    context_bundle, agent_thoughts, final_response, debug_metadata, memory_entry = run_magistus(user_input)
    explanation = generate_explanation(agent_thoughts, final_response, verbosity="brief")

    structured_agents = [
        {
            "agent_name": t.agent_name,
            "content": t.content,
            "confidence": t.confidence,
            "flags": t.flags,
            "reasons": t.reasons
        }
        for t in agent_thoughts
    ]

    try:
        if not memory_entry:
            tags = debug_metadata.get("tags", []) if isinstance(debug_metadata, dict) else []
            memory_entry = MemoryIndexEntry(
                id=f"mem_{uuid4()}",
                context=user_input,
                insight=final_response,
                behavioral_adjustment="Reflect on this outcome when similar topics are encountered.",
                reflective_summary=explanation,
                relevance_score=1.0,
                tags=tags,
                meta_reflection=None
            )
        append_memory_entry_to_store(memory_entry)
    except Exception as e:
        logger.warning(f"⚠️ Memory save failed: {e}")

    try:
        supervisor = MetaLearningSupervisor()
        context = get_latest_memory_entry()
        reflection = supervisor.run(context=context, prior_thoughts=[])
        reflection_data = json.loads(reflection.content)
        os.makedirs("profile", exist_ok=True)
        profile_path = "profile/magistus_profile.json"

        if os.path.exists(profile_path):
            with open(profile_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
        else:
            existing_data = []

        existing_data.append(reflection_data)
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2)
    except Exception as e:
        logger.warning(f"⚠️ Reflection failed: {e}")

    return JSONResponse({
        "response": final_response,
        "agent_thoughts": structured_agents,
        "voice_output": config.get("voice_output", False),
        "explanation": explanation
    })

# 🔄 Stream endpoint
@app.post("/chat_stream")
async def chat_stream_endpoint(payload: dict):
    user_input = payload.get("input", "")
    if not user_input:
        return StreamingResponse((chunk for chunk in ["Missing input"]), media_type="text/plain")

    async def token_generator():
        for chunk in stream_response(user_input):
            yield chunk
            await asyncio.sleep(0.01)

    return StreamingResponse(token_generator(), media_type="text/plain")

# 🧠 Diagnostics only
@app.post("/think")
async def think_endpoint(user_input: UserInput):
    context_bundle, agent_thoughts, final_response, debug_metadata, _ = run_magistus(user_input.input)
    return {
        "response": final_response,
        "agent_names": [t.agent_name for t in agent_thoughts],
        "diagnostics": debug_metadata
    }

# 🪞Reflection trigger
@app.post("/reflect")
async def reflect_endpoint():
    try:
        memory_entry = get_latest_memory_entry()
        if memory_entry is None:
            return JSONResponse({"reflection": "[No recent memory entry found]"}, status_code=404)

        supervisor = MetaLearningSupervisor()
        reflection = supervisor.run(context=memory_entry, prior_thoughts=[])
        reflection_data = json.loads(reflection.content)

        os.makedirs("profile", exist_ok=True)
        profile_path = "profile/magistus_profile.json"

        if os.path.exists(profile_path):
            with open(profile_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
        else:
            existing_data = []

        existing_data.append(reflection_data)
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2)

        return JSONResponse({
            "reflection": reflection_data,
            "reasoning": reflection_data
        })

    except Exception as e:
        logger.error(f"⚠️ Reflection error: {e}")
        return JSONResponse({"error": "Reflection failed."}, status_code=500)

# 🚀 Launcher
def start_public_companion():
    if not validate_launch_config():
        sys.exit(1)
    print_system_ready_banner()

    # Launch browser after delay (so server is live)
    def delayed_open():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:8000/")
    threading.Thread(target=delayed_open).start()

    uvicorn.run("launch_v1:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_public_companion()
