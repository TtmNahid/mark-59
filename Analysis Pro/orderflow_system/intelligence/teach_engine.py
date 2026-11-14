"""
Teach Mode Engine for Trading Intelligence.
Provides conversational AI teaching: analysis, cross-referencing against existing knowledge,
clarification questions, and explicit user approval workflow.
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from orderflow_system.intelligence.database import IntelligenceDatabase
from orderflow_system.intelligence.models import (
    LessonRecord,
    KnowledgeCategory,
)
from orderflow_system.intelligence.extractor import _get_gemini_client

logger = logging.getLogger(__name__)


class TeachModeEngine:
    def __init__(self, db: Optional[IntelligenceDatabase] = None):
        self.db = db or IntelligenceDatabase()

    def analyze_teaching(
        self,
        user_explanation: str,
        category: str = KnowledgeCategory.FOOTPRINT,
        chart_image_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Step 1 of Teach Mode:
        1. Analyzes user explanation & optional chart.
        2. Cross-references previously approved lessons in the database.
        3. Identifies agreements, expansions, or potential conflicts.
        4. Asks clarification questions if ambiguous.
        5. Drafts a formal lesson proposal awaiting user approval.
        """
        # Fetch existing approved lessons for comparison
        existing_lessons = self.db.get_lessons(category=category, status="approved")
        existing_context = ""
        if existing_lessons:
            existing_context = "\n".join([
                f"- Existing Rule '{l.title}': {l.ai_understanding} | Rules: {'; '.join(l.trading_rules)}"
                for l in existing_lessons[:5]
            ])
        else:
            existing_context = "No previous approved rules in this category yet."

        client = _get_gemini_client()
        if client:
            return self._ai_analyze_teaching(user_explanation, category, existing_context, chart_image_path)
        else:
            return self._fallback_analyze_teaching(user_explanation, category, existing_context, chart_image_path)

    def _ai_analyze_teaching(
        self,
        explanation: str,
        category: str,
        existing_context: str,
        chart_image_path: Optional[Path]
    ) -> Dict[str, Any]:
        prompt = f"""
You are the AI Trading Intelligence Learning Engine for JARVIS MARK 59.
The user (a human institutional trader) is teaching you a new trading concept, rule, or correction.

USER EXPLANATION:
\"\"\"{explanation}\"\"\"

CATEGORY: {category}

PREVIOUSLY LEARNED & APPROVED LESSONS IN THIS CATEGORY:
\"\"\"{existing_context}\"\"\"

YOUR MISSION:
1. Explain exactly what you understood from the user's explanation.
2. Compare this with previously learned concepts. Does this reinforce, expand, or contradict existing rules?
3. If anything is ambiguous (e.g. entry trigger, stop loss placement, timeframe, volume threshold), formulate 1 or 2 targeted clarification questions. If the explanation is clear, clarifications can be empty.
4. Formulate concrete, actionable trading rules derived from what the user said.
5. Create a clean lesson proposal awaiting the user's approval.

Return strictly valid JSON with this schema:
{{
  "title": "Concise Descriptive Lesson Title (e.g. Delta Absorption at Key Support)",
  "ai_understanding": "2-4 sentence summary of what you understood from the trader.",
  "comparison_notes": "How this relates to previously learned knowledge (reinforces, modifies, or adds new methodology).",
  "clarifications_asked": [
    "Optional question if something needs user confirmation"
  ],
  "proposed_rules": [
    "Rule 1: Concrete condition",
    "Rule 2: Execution or invalidation rule"
  ],
  "proposed_examples": [
    "Practical example or scenario described by user"
  ]
}}
"""
        models_to_try = ["gemini-3.1-flash-lite", "gemini-3.8-flash"]
        for m in models_to_try:
            try:
                contents = [prompt]
                if chart_image_path and chart_image_path.exists():
                    from google.genai import types
                    mime = "image/jpeg" if chart_image_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
                    part = types.Part.from_bytes(data=chart_image_path.read_bytes(), mime_type=mime)
                    contents.append(part)

                client = _get_gemini_client()
                resp = client.models.generate_content(model=m, contents=contents)
                clean_json = self._clean_json(resp.text)
                parsed = json.loads(clean_json)

                return {
                    "ok": True,
                    "title": parsed.get("title", f"{category} Lesson"),
                    "category": category,
                    "user_explanation": explanation,
                    "ai_understanding": parsed.get("ai_understanding", ""),
                    "comparison_notes": parsed.get("comparison_notes", "Synthesized with current knowledge base."),
                    "clarifications_asked": parsed.get("clarifications_asked", []),
                    "proposed_rules": parsed.get("proposed_rules", []),
                    "proposed_examples": parsed.get("proposed_examples", []),
                    "chart_image_path": str(chart_image_path) if chart_image_path else None,
                    "ready_for_approval": True,
                }
            except Exception as e:
                logger.warning(f"Teach mode analysis error with {m}: {e}")
                continue

        return self._fallback_analyze_teaching(explanation, category, existing_context, chart_image_path)

    def _fallback_analyze_teaching(
        self,
        explanation: str,
        category: str,
        existing_context: str,
        chart_image_path: Optional[Path]
    ) -> Dict[str, Any]:
        """Local parsing when AI model is temporarily unavailable."""
        title = f"{category} Rule: {explanation[:30]}..."
        return {
            "ok": True,
            "title": title,
            "category": category,
            "user_explanation": explanation,
            "ai_understanding": f"Understood rule: {explanation}. This concept has been parsed and prepared for your confirmation.",
            "comparison_notes": "Added to institutional trading playbook pending your explicit approval.",
            "clarifications_asked": [],
            "proposed_rules": [explanation],
            "proposed_examples": ["User-defined market observation."],
            "chart_image_path": str(chart_image_path) if chart_image_path else None,
            "ready_for_approval": True,
        }

    def approve_lesson(
        self,
        title: str,
        category: str,
        user_explanation: str,
        ai_understanding: str,
        trading_rules: List[str],
        practical_examples: List[str],
        comparison_notes: str = "",
        chart_image_path: Optional[str] = None
    ) -> LessonRecord:
        """
        Step 2 of Teach Mode: User explicitly approves the lesson.
        Commits to persistent database as an APPROVED LESSON with version 1.
        """
        now = datetime.utcnow().isoformat()
        lesson_id = str(uuid.uuid4())

        lesson = LessonRecord(
            id=lesson_id,
            title=title.strip() or f"{category} Lesson",
            category=category,
            user_explanation=user_explanation,
            ai_understanding=ai_understanding,
            trading_rules=trading_rules,
            practical_examples=practical_examples,
            comparison_notes=comparison_notes,
            clarifications_asked=[],
            status="approved",  # Approved by user
            version=1,
            source_document_id=None,
            chart_image_path=chart_image_path,
            created_at=now,
            updated_at=now,
            approved_at=now,
        )

        self.db.insert_lesson(lesson)
        return lesson

    def _clean_json(self, text: str) -> str:
        raw = text.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```JSON"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        return raw.strip()
