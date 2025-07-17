# agents/cluster_bridge.py

import uuid
from typing import List, Dict, Any
from datetime import datetime
import logging

from context_types import AgentThought
from user_profile import get_instance_id
from magistus_manifesto import passes_manifesto_filter

logger = logging.getLogger(__name__)

# Assign unique instance ID
SENDER_ID = get_instance_id() or f"magistus_instance_{uuid.uuid4().hex[:6]}"

def sanitize_thought(thought: AgentThought) -> Dict[str, Any]:
    """
    Sanitize an AgentThought for safe sharing across Magistus clusters.
    Removes user-specific context while preserving reasoning structure.
    """
    if not passes_manifesto_filter(thought):
        logger.debug(f"[ClusterBridge] Thought from {thought.agent_name} failed manifesto filter.")
        return {}

    sanitized = {
        "agent_name": thought.agent_name,
        "core_strategy": thought.content.strip(),
        "reasons": thought.reasons or [],
        "confidence": round(thought.confidence, 2),
        "flags": {
            k: v for k, v in (thought.flags or {}).items()
            if k in {"insight", "ethical_warning", "pattern_recognition"}
        }
    }

    return sanitized

def export_sanitized_packet(thoughts: List[AgentThought]) -> Dict[str, Any]:
    """
    Export a bundle of sanitized agent strategies for opt-in cross-instance sharing.
    """
    bundle = [sanitize_thought(th) for th in thoughts if sanitize_thought(th)]
    logger.debug(f"[ClusterBridge] Exporting {len(bundle)} sanitized thoughts.")

    return {
        "sender_id": SENDER_ID,
        "timestamp": datetime.utcnow().isoformat(),
        "strategy_bundle": bundle
    }

def import_sanitized_packet(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Receives external strategy bundles from other Magistus instances.
    Currently read-only: logs and optionally validates.
    """
    strategies = packet.get("strategy_bundle", [])
    logger.debug(f"[ClusterBridge] Imported packet with {len(strategies)} strategies from {packet.get('sender_id')}.")
    return strategies
