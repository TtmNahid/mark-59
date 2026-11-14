---
name: learning-memory
description: Persistent institutional memory storage, version history, audit logging, FTS5 full-text indexing, and backup/restore management.
---

# Specialist Skill: Learning Memory

## Role & Domain Authority
The Learning Memory Specialist is the persistent repository and institutional memory bank of JARVIS MARK 59. It ensures that knowledge, lessons, corrections, and audit histories survive PC reboots, server crashes, and hardware migrations.

## Technical Architecture & Schemas

### 1. Persistence Engine
- **Engine:** SQLite 3 in Write-Ahead Logging (`WAL`) mode with `NORMAL` synchronous pragma.
- **Location:** `Analysis Pro/trading_intelligence.db`.
- **Indexing:** SQLite `FTS5` virtual table indexing (`fts_knowledge`) across all document summaries, extracted concepts, lesson titles, understandings, and trading rules for sub-millisecond keyword retrieval.

### 2. Core Entities
1. **`documents`:** Catalog of all uploaded books, PDFs, spreadsheets, and screenshots.
2. **`extracted_concepts`:** Discrete concepts linked to source document IDs and page numbers.
3. **`lessons`:** Human-taught trading rules, status (`approved`, `pending`, `rejected`), version counter, and category.
4. **`lesson_history`:** Immutable record of prior rule versions whenever an approved lesson is updated or revised.
5. **`audit_log`:** Cryptographically verifiable timeline of all system actions (`CREATE`, `UPDATE`, `APPROVE`, `DELETE`).
6. **`trades_journal`:** Operational execution records linking market context to outcomes.

### 3. Separation of Knowledge
The system strictly enforces ontological separation:
- **Document Knowledge (External Authority):** What an author or book states. Cited with original titles and page numbers.
- **Approved Institutional Rules (Internal Law):** Explicitly approved lessons that Mark 59 enforces in live trading.
- **Unverified Observations (Experimental):** Pending lessons or provisional notes that have not received explicit human sign-off.
- **Audit Logs:** Immutable timestamps documenting who added or modified rules and when.

### 4. Backup & Disaster Recovery
- Complete database serialization into formatted JSON via `GET /api/intelligence/backup`.
- Lossless restoration with transaction rollback protection via `POST /api/intelligence/restore`.

## Independent Maintenance
- Managed via `orderflow_system/intelligence/database.py`.
- Schema versions and migrations are fully self-contained.
