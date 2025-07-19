import sys
import time
import logging
import uvicorn
import asyncio
import json
import os
import webbrowser
import threading
import re
from uuid import uuid4
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
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
from openai import OpenAI
from threading import Thread
from memory import log_memory

# ─── New: Simple‑input detector for context gating ───
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SIMPLE_GREETINGS = {"hi", "hello", "hey", "thanks", "bye"}

def isSimpleInput(text: str) -> bool:
    t = text.strip().lower()
    if len(t) < 5:
        return True
    words = t.split()
    if words[0] in SIMPLE_GREETINGS:
        return True
    if len(words) <= 2:
        return True
    return False

def simple_chat(text: str) -> str:
    resp = openai_client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[{"role": "user", "content": text}]
    )
    return resp.choices[0].message.content or ""

# ─── End of context‑gating helpers ───

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

# Wrap config in a mutable dict if it's not one already
mutable_config = dict(config)

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
    allow_self_eval = mutable_config.get("allow_self_eval", False)

    for key, expected in REQUIRED_KEYS.items():
        current = mutable_config.get(key)
        if key == "limiter_enabled" and current is False and allow_self_eval:
            logger.info(f"⚠️ {key.replace('_', ' ').title()}: Disabled due to self-eval mode enabled (allowed)")
            continue
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
    ui_path = Path(__file__).parent / "magistus-ui.html"
    if not ui_path.exists():
        print(f"❌ UI file not found at: {ui_path}")
        return HTMLResponse("<h1>UI file not found</h1>", status_code=404)
    return HTMLResponse(content=ui_path.read_text(encoding="utf-8"), status_code=200)

# 💬 Core chat endpoint
@app.post("/chat")
def chat_endpoint(payload: dict):
    user_input = payload.get("input", "")
    reasoning_enabled = payload.get("reasoning_enabled", True)
    allow_self_eval = mutable_config.get("allow_self_eval", False)

    if not user_input:
        return JSONResponse({"error": "Missing input"})

    # ─── Context‑gating: skip reasoning if simple ───
    if isSimpleInput(user_input):
        logger.debug("Bypassing Magistus reasoning for simple input in /chat.")
        try:
            response = simple_chat(user_input)
        except Exception as e:
            logger.error(f"simple_chat error: {e}")
            response = "Error processing simple input."
        return JSONResponse({
            "response": response,
            "agent_thoughts": [],
            "voice_output": mutable_config.get("voice_output", False),
            "cam_bypass": True
        })

    # ─── Limiter logic ───
    limiter_thought = evaluate_input(user_input, allow_self_eval=allow_self_eval)
    if limiter_thought.flags.get("execution_blocked"):
        return JSONResponse({
            "response": "[Blocked] " + limiter_thought.content,
            "agent_thoughts": [],
            "voice_output": mutable_config.get("voice_output", False),
            "cam_bypass": False
        })

    # ─── Critical‑action consent ───
    if is_critical_action("external_execution", allow_self_eval=allow_self_eval):
        if not request_user_consent(
            "external_execution",
            "This may trigger an irreversible system action."
        ):
            return JSONResponse({
                "response": "[Consent Denied] User did not approve action.",
                "agent_thoughts": [],
                "voice_output": mutable_config.get("voice_output", False),
                "cam_bypass": False
            })

    # ─── Reasoning toggle ───
    if not reasoning_enabled:
        response = generate_response(user_input)
        return JSONResponse({
            "response": response,
            "agent_thoughts": [],
            "voice_output": mutable_config.get("voice_output", False),
            "cam_bypass": False
        })

    # ─── Full Magistus pipeline ───
    context_bundle, agent_thoughts, final_response, debug_metadata, memory_entry = \
        run_magistus(user_input, allow_self_eval=allow_self_eval)
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
    logger.debug(f"Structured Agent Thoughts: {structured_agents}")

    # ─── Background log to Markdown + JSON ───
    def delayed_memory_log():
        try:
            log_memory(
                markdown_text=final_response,
                confidence="N/A",
                emotion="N/A",
                tags=["chat", "response"],
                insight=final_response,
                reflective_summary=explanation,
                context=user_input,
                behavioral_adjustment="Reflect on this outcome when similar topics are encountered.",
                relevance_score=1.0
            )
        except Exception as e:
            logger.warning(f"⚠️ Background memory log failed: {e}")

    Thread(target=delayed_memory_log).start()

    return JSONResponse({
        "response": final_response,
        "agent_thoughts": structured_agents,
        "voice_output": mutable_config.get("voice_output", False),
        "explanation": explanation,
        "cam_bypass": False
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

# 🪞 Reflection trigger
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

    def delayed_open():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:8000/")
    threading.Thread(target=delayed_open).start()

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)


@app.post("/toggle_self_eval")
def toggle_self_eval():
    current_self_eval = mutable_config.get("allow_self_eval", False)
    new_self_eval = not current_self_eval

    mutable_config["allow_self_eval"] = new_self_eval
    mutable_config["limiter_enabled"] = not new_self_eval

    logger.info(f"Toggled allow_self_eval to {new_self_eval}, limiter_enabled to {mutable_config['limiter_enabled']}")

    return JSONResponse({
        "allow_self_eval": new_self_eval,
        "limiter_enabled": mutable_config["limiter_enabled"],
        "message": f"Self-eval mode is now {'ON' if new_self_eval else 'OFF'}"
    })


if __name__ == "__main__":
    start_public_companion()