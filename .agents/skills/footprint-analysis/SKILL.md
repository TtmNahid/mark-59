---
name: footprint-analysis
description: Institutional order flow footprint analysis specialist for bid/ask imbalances, absorption, delta divergence, and trapped market participants.
---

# Specialist Skill: Footprint Analysis

## Role & Domain Authority
The Footprint Analysis Specialist governs microscopic order execution analysis. It interprets live bid/ask tape dynamics, price cluster volume distributions, diagonal bid/ask imbalances, institutional passive absorption, and trapped traders.

## Key Capabilities & Procedures

### 1. Bid / Ask Imbalance Detection
- Evaluates diagonal bid/ask volume ratios (Standard threshold: 3:1 or 300%).
- **Stacked Imbalances:** 3 or more consecutive aggressive imbalance price levels form high-conviction institutional support/resistance zones.
- **Buying Imbalance:** Aggressive buyers hitting the offer with volume $\ge 3\times$ opposing bids.
- **Selling Imbalance:** Aggressive sellers hitting the bid with volume $\ge 3\times$ opposing offers.

### 2. Institutional Absorption Identification
- **Definition:** High aggressive volume (elevated delta) executing into passive limit orders without displacing price.
- **Support Absorption:** Heavy aggressive market sell volume (deep negative delta) near key support / low of day, but price holds and prints a reversal candle. Indicates institutional passive accumulation.
- **Resistance Absorption:** Heavy aggressive market buy volume (large positive delta) near resistance / high of day, but price fails to break through. Indicates institutional passive distribution.

### 3. Cumulative Volume Delta (CVD) Divergence
- **Bullish CVD Divergence:** Price creates a lower low or tests key support while CVD makes a higher low (aggressive selling is drying up or being completely absorbed).
- **Bearish CVD Divergence:** Price prints a higher high while CVD prints a lower high (aggressive buying exhaustion or limit sellers absorbing the rally).

### 4. Unfinished Auctions & Zero Prints
- Single-print or unfinished auctions at extreme candle highs/lows signal unfinished institutional business and are prioritized for retests.

## Integration Points
- Interacts with `orderflow_system/analytics/footprint.py` and `AbsorptionDetector`.
- Confluence required with **GEX Levels** (e.g. absorption at `PW0` or `CW0`) and **Volume Profile** (POC/VAL/VAH).

## Maintenance & Rule Updates
- Rules must remain mathematically falsifiable.
- Parameter adjustments (e.g. imbalance ratio 3.0 vs 4.0) must be recorded in Persistent Learning Memory.
