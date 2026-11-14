"""
Data models and schemas for Trading Intelligence Learning Engine.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class KnowledgeCategory:
    FOOTPRINT = "Footprint Analysis"
    GEX = "GEX Analysis"
    VOLUME_PROFILE = "Volume Profile"
    GENERAL = "General Methodology"

    DEFAULT_CATEGORIES = [
        "Footprint Analysis",
        "GEX Analysis",
        "Volume Profile",
        "Order Flow Microstructure",
        "Risk & Psychology",
    ]


class DocumentRecord(BaseModel):
    id: str
    filename: str
    original_name: str
    file_type: str
    file_path: str
    category: str
    size_bytes: int
    upload_date: str
    summary: str = ""
    page_count: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedConcept(BaseModel):
    id: str
    document_id: str
    category: str
    concept_name: str
    explanation: str
    trading_rules: List[str] = Field(default_factory=list)
    practical_examples: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)
    source_page: Optional[int] = None
    source_reference: str = ""
    confidence: float = 1.0
    created_at: str = ""


class LessonRecord(BaseModel):
    id: str
    title: str
    category: str
    user_explanation: str
    ai_understanding: str
    trading_rules: List[str] = Field(default_factory=list)
    practical_examples: List[str] = Field(default_factory=list)
    comparison_notes: str = ""
    clarifications_asked: List[str] = Field(default_factory=list)
    status: str = "pending"  # "pending", "approved", "rejected"
    version: int = 1
    source_document_id: Optional[str] = None
    chart_image_path: Optional[str] = None
    created_at: str
    updated_at: str
    approved_at: Optional[str] = None


class TradeLearningRecord(BaseModel):
    id: str
    timestamp: str
    symbol: str
    direction: str  # "BUY", "SELL"
    entry_price: float
    exit_price: Optional[float] = None
    outcome: str = "pending"  # "win", "loss", "breakeven", "open"
    why_entered: str = ""
    gex_levels_used: List[str] = Field(default_factory=list)
    footprint_signals: List[str] = Field(default_factory=list)
    volume_profile_levels: List[str] = Field(default_factory=list)
    checklist_satisfied: List[str] = Field(default_factory=list)
    pnl: Optional[float] = None
    lessons_learned: str = ""
    created_at: str


class AuditLogRecord(BaseModel):
    id: str
    entity_type: str  # "document", "lesson", "trade", "database"
    entity_id: str
    action: str  # "create", "update", "approve", "reject", "delete", "backup", "restore"
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str


class TeachAnalyzeRequest(BaseModel):
    explanation: str
    category: Optional[str] = KnowledgeCategory.FOOTPRINT
    chart_image_base64: Optional[str] = None
    chart_filename: Optional[str] = None


class TeachApproveRequest(BaseModel):
    title: str
    category: str
    user_explanation: str
    ai_understanding: str
    trading_rules: List[str] = Field(default_factory=list)
    practical_examples: List[str] = Field(default_factory=list)
    chart_image_path: Optional[str] = None


class QueryRequest(BaseModel):
    question: Optional[str] = None
    query: Optional[str] = None
    category: Optional[str] = None
    top_k: int = 5

    def get_query_text(self) -> str:
        return (self.question or self.query or "").strip()


class DocumentAskRequest(BaseModel):
    question: str
