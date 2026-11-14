---
name: knowledge-library
description: Ingestion, parsing, multimodal extraction, and cataloging specialist for trading PDFs, books, spreadsheets, and chart screenshots.
---

# Specialist Skill: Knowledge Library

## Role & Domain Authority
The Knowledge Library Specialist manages the ingestion, indexing, and persistent cataloging of trading research documents, books, strategy guides, spreadsheets, and chart screenshots.

## Document Ingestion & Extraction Protocols

### 1. Supported File Formats & Extractors
- **PDF Documents:** Processed through `pypdf` + Gemini multimodal parsing for multi-page concept extraction, preserving page numbers, trading rules, and practical examples.
- **DOCX & TXT:** Text extraction for trading notes, methodology write-ups, and rule cheat sheets.
- **CSV Spreadsheets:** Tabular data extraction for backtesting results, historical trade logs, and level databases.
- **Chart Screenshots (PNG, JPG, WEBP):** Computer vision parsing of candle structures, footprint heatmaps, indicators, and price markings.

### 2. Information Extraction Structure
Every ingested document is parsed into discrete records:
- **Original Metadata:** Unique UUID, filename, file type, file size, page count, and MD5 hash (to prevent duplicate ingestion).
- **Executive Summary:** Concise 2-3 paragraph breakdown of the document's core thesis.
- **Discrete Concepts (`ExtractedConcept`):**
  - Concept name & category.
  - Granular explanation.
  - Formal trading rules.
  - Practical trade setups & examples.
  - Source reference (document title and specific page range, e.g., `Page 14-16`).

### 3. Strict Truthfulness & Citation Rule
- The Knowledge Library **never invents or extrapolates** unstated assertions.
- Extracted concepts must clearly distinguish between:
  1. *What the author/document explicitly states.*
  2. *Practical operational applications.*
- When responding to document questions, the AI must cite page numbers or document sections directly.

## Independent Maintenance
- Implemented in `orderflow_system/intelligence/extractor.py` and `database.py`.
- Category taxonomy can be expanded dynamically without schema migrations.
