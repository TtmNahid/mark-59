---
name: trade-journal
description: Personal trade recording, confluence tagging, execution outcome tracking, and cognitive reflection specialist.
---

# Specialist Skill: Trade Journal

## Role & Domain Authority
The Trade Journal Specialist prepares and manages the institutional trade recording architecture. It captures the psychological rationale, quantitative confluences, multi-layer signals, and post-trade reflections for every trade executed by the trader or system.

## Data Model & Capture Requirements

### 1. Pre-Trade Confluence Checklist
Every trade record captures:
- **Identification:** Unique UUID, symbol (e.g. `XAUUSDT`), direction (`BUY` / `SELL`), and timestamp.
- **Entry & Execution:** Entry price, initial stop loss, take profit targets.
- **Causal Rationale (`why_entered`):** Detailed narrative of why the trade was initiated.

### 2. Multi-Layer Confluence Tagging
- **GEX Levels Used:** Specific gamma strikes active during entry (`PW0`, `CW0`, `FLIP`, `MP`, `EM+`, `EM-`).
- **Footprint Signals:** Specific microstructural patterns observed (e.g., `Absorption`, `Stacked Buying Imbalance`, `Exhaustion Print`, `Delta Divergence`).
- **Volume Profile Levels:** Structural profile locations (`POC`, `VAL`, `VAH`, `LVN rejection`).
- **Checklist Satisfied:** Array of verification criteria met prior to firing the order.

### 3. Post-Trade Reflection & Cognitive Feedback Loop
- **Trade Outcome:** Categorized as `win`, `loss`, `breakeven`, or `pending`.
- **Lessons Learned (`lessons_learned`):** Post-trade audit answering:
  - *Did execution match the written rules?*
  - *Was the trade invalidated properly according to plan?*
  - *What unexpected market reaction occurred?*

### 4. Trade Learning Integration
- In Phase 2, trade journal records feed back into **Teach Mode** and **Learning Memory** to calculate rule win-rates, detect recurrent cognitive biases, and propose rule adjustments.

## Independent Maintenance
- Managed via `orderflow_system/intelligence/models.py` (`TradeLearningRecord`) and `database.py`.
- REST endpoints: `GET /api/intelligence/trades`, `POST /api/intelligence/trades`, `GET /api/intelligence/trades/{trade_id}`.
