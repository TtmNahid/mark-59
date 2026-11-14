"""
FastAPI Router for Trading Intelligence Learning Engine.
Mounted into Analysis Pro dashboard app.
"""
from __future__ import annotations

import base64
import logging
import uuid
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse

from orderflow_system.intelligence.database import IntelligenceDatabase
from orderflow_system.intelligence.extractor import DocumentExtractor, _get_gemini_client
from orderflow_system.intelligence.teach_engine import TeachModeEngine
from orderflow_system.intelligence.retriever import KnowledgeRetriever
from orderflow_system.intelligence.models import (
    TeachAnalyzeRequest,
    TeachApproveRequest,
    QueryRequest,
    DocumentAskRequest,
    TradeLearningRecord,
    KnowledgeCategory,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["Trading Intelligence"])

db = IntelligenceDatabase()
extractor = DocumentExtractor()
teach_engine = TeachModeEngine(db)
retriever = KnowledgeRetriever(db)


# ── Categories ────────────────────────────────────────────────────────────────

@router.get("/categories")
async def get_categories():
    return {"categories": db.get_categories()}


@router.post("/categories")
async def add_category(payload: dict):
    name = payload.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Category name cannot be empty")
    ok = db.add_category(name)
    if not ok:
        raise HTTPException(status_code=409, detail="Category already exists or invalid")
    return {"ok": True, "category": name, "categories": db.get_categories()}


# ── Document Library & Uploads ────────────────────────────────────────────────

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(KnowledgeCategory.FOOTPRINT)
):
    try:
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Save file to disk
        saved_path = extractor.save_uploaded_file(file.filename or "uploaded_file", content_bytes)

        # Extract concepts, rules, summary
        doc_record, concepts = extractor.process_file(saved_path, file.filename or "uploaded_file", category)

        # Commit to persistent database
        db.insert_document(doc_record)
        if concepts:
            db.insert_concepts(concepts)

        return {
            "ok": True,
            "document": doc_record.model_dump(),
            "concepts_count": len(concepts),
            "concepts": [c.model_dump() for c in concepts]
        }
    except Exception as e:
        logger.error(f"Error processing uploaded document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.get("/documents")
async def list_documents(category: Optional[str] = None):
    docs = db.get_documents(category=category)
    return {"documents": [d.model_dump() for d in docs]}


@router.get("/document/{doc_id}")
async def get_document_details(doc_id: str):
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    concepts = db.get_concepts(document_id=doc_id)
    return {
        "document": doc.model_dump(),
        "concepts": [c.model_dump() for c in concepts]
    }


@router.delete("/document/{doc_id}")
async def delete_document(doc_id: str):
    ok = db.delete_document(doc_id)
    return {"ok": ok}


@router.post("/document/{doc_id}/ask")
async def ask_document_question(doc_id: str, payload: DocumentAskRequest):
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    concepts = db.get_concepts(document_id=doc_id)

    concept_text = "\n".join([
        f"- {c.concept_name}: {c.explanation} (Rules: {'; '.join(c.trading_rules)})"
        for c in concepts
    ])

    file_path = Path(doc.file_path)
    file_bytes = file_path.read_bytes() if file_path.exists() else None

    prompt = f"""
You are the AI Document Specialist for JARVIS MARK 59.
Answer the user's question STRICTLY based on this document: '{doc.original_name}' (Category: {doc.category}).

Document Summary:
{doc.summary}

Extracted Key Concepts:
{concept_text}

USER QUESTION:
{payload.question}

RULES:
1. Ground your answer exclusively in the document content.
2. If citing a page or concept, cite it clearly.
3. If the document does not contain the answer, state: "The document '{doc.original_name}' does not mention or contain information about [X]." Do NOT invent details.
"""
    client = _get_gemini_client()
    if client:
        try:
            contents = [prompt]
            if file_bytes and doc.file_type == "pdf" and len(file_bytes) <= 25 * 1024 * 1024:
                from google.genai import types
                contents.append(types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"))
            elif file_bytes and doc.file_type in ("png", "jpg", "jpeg"):
                from google.genai import types
                contents.append(types.Part.from_bytes(data=file_bytes, mime_type="image/jpeg"))

            resp = client.models.generate_content(model="gemini-3.1-flash-lite", contents=contents)
            return {"answer": resp.text.strip(), "document": doc.original_name}
        except Exception as e:
            logger.warning(f"Error querying document {doc_id}: {e}")

    # Fallback
    return {
        "answer": f"Document '{doc.original_name}' covers {doc.category}. Summary: {doc.summary}. (Neural model was temporarily unreachable).",
        "document": doc.original_name
    }


# ── Teach Mode ────────────────────────────────────────────────────────────────

@router.post("/teach/analyze")
async def teach_analyze(payload: TeachAnalyzeRequest):
    chart_path = None
    if payload.chart_image_base64:
        try:
            data = base64.b64decode(payload.chart_image_base64.split(",")[-1])
            fname = payload.chart_filename or f"chart_{uuid.uuid4().hex[:6]}.png"
            chart_path = extractor.save_uploaded_file(fname, data)
        except Exception as e:
            logger.warning(f"Could not save teach chart image: {e}")

    result = teach_engine.analyze_teaching(
        user_explanation=payload.explanation,
        category=payload.category or KnowledgeCategory.FOOTPRINT,
        chart_image_path=chart_path
    )
    return result


@router.post("/teach/approve")
async def teach_approve(payload: TeachApproveRequest):
    lesson = teach_engine.approve_lesson(
        title=payload.title,
        category=payload.category,
        user_explanation=payload.user_explanation,
        ai_understanding=payload.ai_understanding,
        trading_rules=payload.trading_rules,
        practical_examples=payload.practical_examples,
        chart_image_path=payload.chart_image_path
    )
    return {"ok": True, "lesson": lesson.model_dump()}


# ── Lessons & Approved Memory ─────────────────────────────────────────────────

@router.get("/lessons")
async def list_lessons(category: Optional[str] = None, status: Optional[str] = None):
    lessons = db.get_lessons(category=category, status=status)
    return {"lessons": [l.model_dump() for l in lessons]}


@router.get("/lesson/{lesson_id}")
async def get_lesson(lesson_id: str):
    lesson = db.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"lesson": lesson.model_dump()}


@router.post("/lesson/{lesson_id}/approve")
async def approve_existing_lesson(lesson_id: str):
    ok = db.approve_lesson(lesson_id)
    return {"ok": ok}


@router.post("/lesson/{lesson_id}/reject")
async def reject_existing_lesson(lesson_id: str):
    ok = db.reject_lesson(lesson_id)
    return {"ok": ok}


@router.delete("/lesson/{lesson_id}")
async def delete_lesson(lesson_id: str):
    ok = db.delete_lesson(lesson_id)
    return {"ok": ok}


# ── Knowledge Query (RAG Retrieval) ──────────────────────────────────────────

@router.post("/query")
async def query_knowledge(payload: QueryRequest):
    q = payload.get_query_text()
    result = retriever.query(
        question=q,
        category=payload.category,
        top_k=payload.top_k
    )
    return result


# ── Personal Trade Learning Journal (Module 5) ────────────────────────────────

@router.get("/trades")
async def list_trades(limit: int = 50):
    trades = db.get_trades(limit=limit)
    return {"trades": [t.model_dump() for t in trades]}


@router.post("/trades")
async def record_trade(payload: dict):
    now = datetime.utcnow().isoformat()
    record = TradeLearningRecord(
        id=str(uuid.uuid4()),
        timestamp=payload.get("timestamp") or now,
        symbol=payload.get("symbol", "XAUUSDT"),
        direction=payload.get("direction", "BUY").upper(),
        entry_price=float(payload.get("entry_price", 0.0)),
        exit_price=float(payload["exit_price"]) if payload.get("exit_price") is not None else None,
        outcome=payload.get("outcome", "pending"),
        why_entered=payload.get("why_entered", ""),
        gex_levels_used=payload.get("gex_levels_used", []),
        footprint_signals=payload.get("footprint_signals", []),
        volume_profile_levels=payload.get("volume_profile_levels", []),
        checklist_satisfied=payload.get("checklist_satisfied", []),
        pnl=float(payload["pnl"]) if payload.get("pnl") is not None else None,
        lessons_learned=payload.get("lessons_learned", ""),
        created_at=now,
    )
    db.insert_trade(record)
    return {"ok": True, "trade": record.model_dump()}


# ── History & Database Management ─────────────────────────────────────────────

@router.get("/history")
async def get_history(limit: int = 100):
    logs = db.get_audit_log(limit=limit)
    return {"audit_log": [log.model_dump() for log in logs]}


@router.get("/stats")
async def get_stats():
    return db.get_stats()


@router.get("/backup")
async def export_backup():
    data = db.export_database_dict()
    return JSONResponse(content=data)


@router.post("/restore")
async def import_restore(payload: dict):
    ok = db.import_database_dict(payload)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid backup schema or restore failed")
    return {"ok": True, "stats": db.get_stats()}
