"""
Multimodal Document & Image Knowledge Extractor for Trading Intelligence.
Processes PDF, DOCX, TXT, CSV, and Charts/Screenshots with structured concept extraction.
"""
from __future__ import annotations

import os
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

from orderflow_system.intelligence.models import (
    DocumentRecord,
    ExtractedConcept,
    KnowledgeCategory,
)

logger = logging.getLogger(__name__)

# Uploads directory inside Analysis Pro
INTELLIGENCE_UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "intelligence"


def get_gemini_api_key() -> str:
    """Find Gemini API key across environment, .env, or Mark-LVI config."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key

    # Check Analysis Pro/.env
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    k = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if k:
                        return k
        except Exception:
            pass

    # Check Mark-LVI/config/api_keys.json
    mark_lvi_config = Path(__file__).resolve().parent.parent.parent.parent / "Mark-LVI" / "config" / "api_keys.json"
    if mark_lvi_config.exists():
        try:
            data = json.loads(mark_lvi_config.read_text(encoding="utf-8"))
            k = data.get("gemini_api_key") or data.get("gemini")
            if k and str(k).strip():
                return str(k).strip()
        except Exception:
            pass

    return ""


def _get_gemini_client(timeout_ms: int = 15000):
    key = get_gemini_api_key()
    if not key:
        return None
    try:
        from google import genai
        from google.genai import types
        return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=timeout_ms))
    except Exception as e:
        logger.warning(f"Could not initialize Gemini Client: {e}")
        return None


class DocumentExtractor:
    def __init__(self, upload_dir: Optional[Path] = None):
        self.upload_dir = upload_dir or INTELLIGENCE_UPLOADS_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_uploaded_file(self, filename: str, content_bytes: bytes) -> Path:
        """Save file with a collision-free safe path."""
        stem = Path(filename).stem
        ext = Path(filename).suffix.lower()
        safe_stem = "".join(c for c in stem if c.isalnum() or c in ("-", "_")).strip() or "upload"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dest_filename = f"{safe_stem}_{timestamp}_{uuid.uuid4().hex[:6]}{ext}"
        dest_path = self.upload_dir / dest_filename
        dest_path.write_bytes(content_bytes)
        return dest_path

    def process_file(
        self,
        filepath: Path,
        original_name: str,
        user_category: Optional[str] = None
    ) -> Tuple[DocumentRecord, List[ExtractedConcept]]:
        """
        Extract knowledge, trading rules, concepts, and relationships from file.
        Returns DocumentRecord and list of ExtractedConcept.
        """
        ext = filepath.suffix.lower().lstrip(".")
        size_bytes = filepath.stat().st_size
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        # 1. Image / Trading Screenshot
        if ext in ("png", "jpg", "jpeg", "webp", "bmp"):
            return self._process_image(doc_id, filepath, original_name, user_category, size_bytes, now)

        # 2. PDF Document
        elif ext == "pdf":
            return self._process_pdf(doc_id, filepath, original_name, user_category, size_bytes, now)

        # 3. Text / Markdown
        elif ext in ("txt", "md", "csv", "log"):
            return self._process_text(doc_id, filepath, original_name, user_category, size_bytes, now)

        # 4. Fallback / generic
        else:
            return self._process_generic(doc_id, filepath, original_name, user_category, size_bytes, now)

    # ── PDF Processing ────────────────────────────────────────────────────────

    def _process_pdf(
        self, doc_id: str, filepath: Path, original_name: str,
        user_category: Optional[str], size_bytes: int, now: str
    ) -> Tuple[DocumentRecord, List[ExtractedConcept]]:
        page_count = 1
        page_texts: Dict[int, str] = {}
        raw_text = ""

        # Extract text page by page using pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(str(filepath))
            page_count = len(reader.pages)
            for idx, p in enumerate(reader.pages):
                ptxt = p.extract_text() or ""
                page_texts[idx + 1] = ptxt
                raw_text += f"\n--- Page {idx + 1} ---\n{ptxt}"
        except Exception as e:
            logger.warning(f"pypdf extraction failed on {filepath}: {e}")

        # Auto-detect category if not specified
        category = user_category or self._detect_category(raw_text or original_name)

        # Gemini structured concept extraction
        summary, concepts_data = self._ai_extract_document_knowledge(
            filepath, raw_text, original_name, category, is_pdf=True
        )

        doc_record = DocumentRecord(
            id=doc_id,
            filename=filepath.name,
            original_name=original_name,
            file_type="pdf",
            file_path=str(filepath),
            category=category,
            size_bytes=size_bytes,
            upload_date=now,
            summary=summary,
            page_count=page_count,
            metadata={
                "extracted_concepts_count": len(concepts_data),
                "has_raw_text": bool(raw_text.strip()),
            }
        )

        concepts: List[ExtractedConcept] = []
        for c in concepts_data:
            concepts.append(ExtractedConcept(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                category=category,
                concept_name=c.get("concept_name", "Trading Concept"),
                explanation=c.get("explanation", ""),
                trading_rules=c.get("trading_rules", []),
                practical_examples=c.get("practical_examples", []),
                relationships=c.get("relationships", []),
                source_page=c.get("source_page"),
                source_reference=f"{original_name} (Page {c.get('source_page', 'N/A')})" if c.get("source_page") else original_name,
                confidence=float(c.get("confidence", 0.95)),
                created_at=now,
            ))

        return doc_record, concepts

    # ── Image / Screenshot Processing ─────────────────────────────────────────

    def _process_image(
        self, doc_id: str, filepath: Path, original_name: str,
        user_category: Optional[str], size_bytes: int, now: str
    ) -> Tuple[DocumentRecord, List[ExtractedConcept]]:
        category = user_category or KnowledgeCategory.FOOTPRINT
        summary, concepts_data = self._ai_extract_image_knowledge(filepath, original_name, category)

        doc_record = DocumentRecord(
            id=doc_id,
            filename=filepath.name,
            original_name=original_name,
            file_type="image",
            file_path=str(filepath),
            category=category,
            size_bytes=size_bytes,
            upload_date=now,
            summary=summary,
            page_count=1,
            metadata={"chart_image": True}
        )

        concepts: List[ExtractedConcept] = []
        for c in concepts_data:
            concepts.append(ExtractedConcept(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                category=category,
                concept_name=c.get("concept_name", "Visual Chart Pattern"),
                explanation=c.get("explanation", ""),
                trading_rules=c.get("trading_rules", []),
                practical_examples=c.get("practical_examples", []),
                relationships=c.get("relationships", []),
                source_page=1,
                source_reference=f"Screenshot: {original_name}",
                confidence=float(c.get("confidence", 0.95)),
                created_at=now,
            ))

        return doc_record, concepts

    # ── Text / CSV Processing ─────────────────────────────────────────────────

    def _process_text(
        self, doc_id: str, filepath: Path, original_name: str,
        user_category: Optional[str], size_bytes: int, now: str
    ) -> Tuple[DocumentRecord, List[ExtractedConcept]]:
        try:
            text = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""

        category = user_category or self._detect_category(text or original_name)
        summary, concepts_data = self._ai_extract_document_knowledge(
            filepath, text, original_name, category, is_pdf=False
        )

        doc_record = DocumentRecord(
            id=doc_id,
            filename=filepath.name,
            original_name=original_name,
            file_type=filepath.suffix.lower().lstrip("."),
            file_path=str(filepath),
            category=category,
            size_bytes=size_bytes,
            upload_date=now,
            summary=summary,
            page_count=1,
            metadata={"char_count": len(text)}
        )

        concepts: List[ExtractedConcept] = []
        for c in concepts_data:
            concepts.append(ExtractedConcept(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                category=category,
                concept_name=c.get("concept_name", "Trading Method"),
                explanation=c.get("explanation", ""),
                trading_rules=c.get("trading_rules", []),
                practical_examples=c.get("practical_examples", []),
                relationships=c.get("relationships", []),
                source_page=1,
                source_reference=f"Doc: {original_name}",
                confidence=float(c.get("confidence", 0.95)),
                created_at=now,
            ))

        return doc_record, concepts

    def _process_generic(
        self, doc_id: str, filepath: Path, original_name: str,
        user_category: Optional[str], size_bytes: int, now: str
    ) -> Tuple[DocumentRecord, List[ExtractedConcept]]:
        category = user_category or KnowledgeCategory.GENERAL
        summary = f"Uploaded document: {original_name} ({size_bytes} bytes)."
        doc = DocumentRecord(
            id=doc_id,
            filename=filepath.name,
            original_name=original_name,
            file_type=filepath.suffix.lower().lstrip(".") or "file",
            file_path=str(filepath),
            category=category,
            size_bytes=size_bytes,
            upload_date=now,
            summary=summary,
            page_count=1,
            metadata={}
        )
        return doc, []

    # ── AI Extraction Implementations ─────────────────────────────────────────

    def _ai_extract_document_knowledge(
        self, filepath: Path, text: str, original_name: str, category: str, is_pdf: bool
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Call Gemini to extract structured trading intelligence from text or PDF bytes."""
        client = _get_gemini_client()
        if not client:
            return self._fallback_text_extraction(text, original_name, category)

        extraction_prompt = f"""
You are the AI Trading Intelligence Engine for JARVIS MARK 59.
Analyze this trading document '{original_name}' categorized under '{category}'.

CRITICAL RULES:
1. Distinguish strictly between what the document states vs assumptions. Do NOT invent missing details.
2. Identify core methodologies, exact trading rules, practical setup examples, and relationships between concepts.
3. If page numbers or sections are discernible, cite them accurately.
4. Output valid JSON adhering exactly to the following schema:

{{
  "summary": "Concise 2-4 sentence executive overview of what this document teaches and its primary methodology.",
  "concepts": [
    {{
      "concept_name": "Name of concept (e.g. Absorption at Key Levels, Gamma Flip Dynamics, Value Area Rejection)",
      "explanation": "Clear, precise explanation of what the concept means according to the document.",
      "trading_rules": [
        "Rule 1: Exact condition required for entry/exit",
        "Rule 2: Invalidation or risk management condition"
      ],
      "practical_examples": [
        "Example 1: Description of scenario, price behavior, delta or volume confirmation mentioned in text"
      ],
      "relationships": [
        "Relates to Volume Profile VAL/VAH",
        "Interacts with GEX Call Wall"
      ],
      "source_page": 1,
      "confidence": 0.95
    }}
  ]
}}
"""
        models_to_try = ["gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash-lite"]
        for m in models_to_try:
            try:
                contents = []
                if is_pdf and filepath.stat().st_size <= 25 * 1024 * 1024:
                    from google.genai import types
                    part = types.Part.from_bytes(data=filepath.read_bytes(), mime_type="application/pdf")
                    contents = [extraction_prompt, part]
                else:
                    contents = [extraction_prompt, f"Document Text:\n{text[:60000]}"]

                resp = client.models.generate_content(model=m, contents=contents)
                clean_json = self._clean_json_response(resp.text)
                parsed = json.loads(clean_json)
                summary = parsed.get("summary", f"Knowledge extracted from {original_name}.")
                concepts = parsed.get("concepts", [])
                return summary, concepts
            except Exception as e:
                logger.warning(f"Gemini model {m} extraction error: {e}")
                continue

        # If all AI models fail or quota hit
        return self._fallback_text_extraction(text, original_name, category)

    def _ai_extract_image_knowledge(
        self, filepath: Path, original_name: str, category: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Analyze trading screenshots/charts for setups, footprint clusters, GEX walls."""
        client = _get_gemini_client()
        if not client:
            return f"Chart screenshot: {original_name}", []

        prompt = f"""
You are the AI Trading Intelligence Engine for JARVIS MARK 59.
Analyze this trading screenshot / chart image: '{original_name}'. Category: '{category}'.

Identify:
1. Chart type (Footprint, Candlestick, GEX levels, Volume Profile, Heatmap, Tape).
2. Visible price action, support/resistance, key levels, delta imbalances, POC/VAH/VAL, or GEX lines.
3. Practical trading lesson or setup shown in the screenshot.

Return strictly valid JSON:
{{
  "summary": "2-3 sentence explanation of the chart structure, setup, and key observations.",
  "concepts": [
    {{
      "concept_name": "Key Pattern or Setup Name",
      "explanation": "What this chart demonstrates (e.g. Delta absorption at support, rejection from Call Wall)",
      "trading_rules": [
        "Visible entry trigger or setup rule",
        "Stop placement / invalidation level"
      ],
      "practical_examples": [
        "Observed price reaction and confirmation signals"
      ],
      "relationships": [
        "Associated trading concepts"
      ],
      "confidence": 0.95
    }}
  ]
}}
"""
        models_to_try = ["gemini-3.8-flash", "gemini-3.1-flash-lite"]
        for m in models_to_try:
            try:
                from google.genai import types
                part = types.Part.from_bytes(data=filepath.read_bytes(), mime_type="image/jpeg" if filepath.suffix.lower() in (".jpg", ".jpeg") else "image/png")
                resp = client.models.generate_content(model=m, contents=[prompt, part])
                clean_json = self._clean_json_response(resp.text)
                parsed = json.loads(clean_json)
                summary = parsed.get("summary", f"Visual chart analysis of {original_name}.")
                concepts = parsed.get("concepts", [])
                return summary, concepts
            except Exception as e:
                logger.warning(f"Gemini vision error with {m}: {e}")
                continue

        return f"Chart screenshot: {original_name}. Multimodal vision unavailable.", []

    def _detect_category(self, text: str) -> str:
        """Infer category based on trading vocabulary."""
        low = text.lower()
        if any(w in low for w in ("footprint", "bid/ask", "imbalance", "absorption", "delta", "cvd", "tick volume")):
            return KnowledgeCategory.FOOTPRINT
        elif any(w in low for w in ("gex", "gamma", "call wall", "put wall", "dealer", "gamma flip", "spot", "sigma")):
            return KnowledgeCategory.GEX
        elif any(w in low for w in ("volume profile", "poc", "vah", "val", "value area", "profile shape", "p-shape", "b-shape")):
            return KnowledgeCategory.VOLUME_PROFILE
        return KnowledgeCategory.FOOTPRINT

    def _fallback_text_extraction(self, text: str, name: str, category: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Local parsing fallback when offline or no API key."""
        clean_text = text.strip()
        summary = f"Document '{name}' ({len(clean_text)} characters) covering {category} methodologies."
        concepts = []
        if len(clean_text) > 100:
            concepts.append({
                "concept_name": f"{category} Principles - {Path(name).stem}",
                "explanation": f"Core principles extracted from {name}. Document contains guidelines on {category.lower()} strategies.",
                "trading_rules": ["Review source document for specific trigger criteria and confirmation rules."],
                "practical_examples": [f"Document text contains {len(clean_text.splitlines())} lines of trading documentation."],
                "relationships": [category],
                "source_page": 1,
                "confidence": 0.80,
            })
        return summary, concepts

    def _clean_json_response(self, text: str) -> str:
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
