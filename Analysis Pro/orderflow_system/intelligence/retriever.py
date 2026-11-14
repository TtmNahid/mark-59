"""
Knowledge Retrieval and RAG Engine for Trading Intelligence.
Retrieves approved lessons and document excerpts to answer trading questions with citations.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from orderflow_system.intelligence.database import IntelligenceDatabase
from orderflow_system.intelligence.extractor import _get_gemini_client

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    def __init__(self, db: Optional[IntelligenceDatabase] = None):
        self.db = db or IntelligenceDatabase()

    def query(
        self,
        question: str,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Search knowledge base, build grounded prompt with citations, and generate answer.
        """
        # 1. Retrieve matching items from persistent database
        search_results = self.db.search_knowledge(question, category=category, limit=top_k)
        
        # 2. Also retrieve top approved lessons in the category for general context
        approved_lessons = self.db.get_lessons(category=category, status="approved")[:4]

        # Assemble grounding context
        context_blocks = []
        sources = []

        for res in search_results:
            entity_type = res["entity_type"]
            title = res["title"]
            cat = res["category"]
            details = res.get("details", {})

            if entity_type == "lesson":
                rules = "; ".join(details.get("trading_rules", []))
                context_blocks.append(
                    f"--- [APPROVED LESSON: '{title}'] (Category: {cat}) ---\n"
                    f"Understanding: {details.get('ai_understanding', '')}\n"
                    f"Rules: {rules}\n"
                    f"Examples: {'; '.join(details.get('practical_examples', []))}"
                )
                sources.append({"type": "Approved Lesson", "title": title, "category": cat, "id": res["id"]})

            elif entity_type == "concept":
                rules = "; ".join(details.get("trading_rules", []))
                ref = details.get("source_reference", title)
                context_blocks.append(
                    f"--- [SOURCE DOCUMENT CONCEPT: '{title}'] (Reference: {ref}) ---\n"
                    f"Explanation: {details.get('explanation', '')}\n"
                    f"Rules: {rules}"
                )
                sources.append({"type": "Document Concept", "title": title, "reference": ref, "id": res["id"]})

            elif entity_type == "document":
                context_blocks.append(
                    f"--- [DOCUMENT SUMMARY: '{title}'] (Category: {cat}) ---\n"
                    f"Summary: {details.get('summary', '')}"
                )
                sources.append({"type": "Document", "title": title, "category": cat, "id": res["id"]})

        # Append any approved lessons if context is sparse
        if len(context_blocks) < 3 and approved_lessons:
            for l in approved_lessons:
                if not any(s.get("title") == l.title for s in sources):
                    context_blocks.append(
                        f"--- [APPROVED LESSON: '{l.title}'] (Category: {l.category}) ---\n"
                        f"Understanding: {l.ai_understanding}\n"
                        f"Rules: {'; '.join(l.trading_rules)}"
                    )
                    sources.append({"type": "Approved Lesson", "title": l.title, "category": l.category, "id": l.id})

        context_str = "\n\n".join(context_blocks)

        # 3. If no knowledge exists, admit it honestly
        if not context_blocks:
            return {
                "question": question,
                "answer": (
                    "I currently do not have any approved lessons or uploaded reference documents covering this specific concept. "
                    "You can teach me this methodology in **Teach Mode** or upload a PDF/trading guide to the **Knowledge Library**."
                ),
                "sources": [],
                "has_knowledge": False,
            }

        client = _get_gemini_client()
        if client:
            answer = self._ai_answer_question(question, context_str)
        else:
            answer = self._fallback_answer_question(question, context_blocks)

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "has_knowledge": True,
        }

    def _ai_answer_question(self, question: str, context: str) -> str:
        prompt = f"""
You are the AI Trading Intelligence Engine for JARVIS MARK 59.
Answer the trader's question strictly grounded in the approved trading lessons and documented concepts below.

GROUNDED KNOWLEDGE BASE:
\"\"\"{context}\"\"\"

TRADER'S QUESTION:
\"\"\"{question}\"\"\"

MANDATORY RESPONSE RULES:
1. Cite your sources using exact inline references like [Lesson: Title] or [Doc: Filename, Page #].
2. Distinguish clearly between:
   - **Established Approved Rules**: Rules explicitly taught and approved.
   - **Contextual Observations / Invalidation Criteria**: Secondary conditions.
3. If there is conflicting information or nuance between different sources, explicitly highlight it.
4. If the provided knowledge base does NOT contain the answer, state clearly: "Our approved knowledge base does not specify [X] yet." Never fabricate unverified rules.
5. Provide a direct, professional, institutional answer formatted in clean GitHub markdown.
"""
        models_to_try = ["gemini-3.1-flash-lite", "gemini-3.8-flash"]
        for m in models_to_try:
            try:
                client = _get_gemini_client()
                resp = client.models.generate_content(model=m, contents=prompt)
                return resp.text.strip()
            except Exception as e:
                logger.warning(f"RAG query generation error with {m}: {e}")
                continue

        return self._fallback_answer_question(question, [context])

    def _fallback_answer_question(self, question: str, context_blocks: List[str]) -> str:
        snippet = "\n\n".join(context_blocks[:3])
        return (
            f"### Grounded Knowledge Retrieval\n\n"
            f"Based on your approved lessons and documents:\n\n"
            f"{snippet}\n\n"
            f"> *Note: Real-time neural synthesis model was unreachable; raw verified source excerpts are shown above.*"
        )
