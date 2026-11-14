"""
Trading Intelligence Learning Engine Plugin for Mark LVI.
Queries the local OrderFlow Intelligence Engine (http://127.0.0.1:8080) for
approved institutional trading lessons, verified rules, and document knowledge.
"""
from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_INTELLIGENCE_URL = "http://127.0.0.1:8080/api/intelligence/query"

PLUGIN = {
    "name": "trading_intelligence",
    "description": (
        "Queries the persistent JARVIS Trading Intelligence Learning Engine for approved "
        "institutional trading lessons, verified rules, and knowledge extracted from documents and trader lessons. "
        "Use when the user asks what rules or lessons we have learned, asks about Footprint, GEX, or Volume Profile "
        "methodologies, asks to verify a trading setup against our playbook, or asks what our approved rules are."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "question": {
                "type": "STRING",
                "description": "The trading question, setup query, or rule to retrieve from the learning memory."
            },
            "category": {
                "type": "STRING",
                "description": "Optional category filter: 'Footprint Analysis', 'GEX Analysis', 'Volume Profile', or empty."
            }
        },
        "required": ["question"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    question = parameters.get("question", "").strip()
    category = parameters.get("category", "").strip()

    if not question:
        return "Please specify what trading concept or rule you would like me to retrieve from our learning engine."

    payload = {"question": question, "top_k": 4}
    if category:
        payload["category"] = category

    try:
        req = urllib.request.Request(
            DEFAULT_INTELLIGENCE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Mark-LVI/IntelligenceClient"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        answer = data.get("answer", "")
        sources = data.get("sources", [])

        if not answer:
            return "I could not find any approved trading lessons or reference documents answering that query."

        # Format spoken output for JARVIS
        if sources:
            source_names = [s.get("title") or s.get("reference") for s in sources[:3]]
            formatted = f"{answer}\n\n[Grounded Sources: {', '.join(source_names)}]"
        else:
            formatted = answer

        if player:
            try:
                player.write_log(f"[TradingIntelligence]: {question}")
            except Exception:
                pass

        return formatted

    except urllib.error.URLError as e:
        logger.warning(f"Failed to connect to Trading Intelligence backend: {e}")
        return (
            "I could not connect to the local Trading Intelligence Engine on port 8080. "
            "Please ensure the OrderFlow Analysis Pro dashboard is running."
        )
    except Exception as e:
        logger.error(f"Trading Intelligence query error: {e}")
        return f"Error retrieving trading intelligence: {str(e)}"
