---
name: volume-profile
description: Volume Profile and Market Profile specialist governing auction market theory, value area framing, POC migration, and volume distribution shapes.
---

# Specialist Skill: Volume Profile

## Role & Domain Authority
The Volume Profile Specialist analyzes horizontal volume distributions, fair value discovery, auction market theory, and multi-day value migration to determine high-timeframe directional bias and key inflection levels.

## Key Concepts & Distribution Geometry

### 1. Core Profile Architecture
- **POC (Point of Control):** The single price level where the highest volume was transacted during the session. Acts as market equilibrium and high-liquidity magnet.
- **VAH (Value Area High):** Upper boundary containing the top 70% of transacted volume. Serves as resistance if price opens below, or support if price breaks out above.
- **VAL (Value Area Low):** Lower boundary containing the bottom of the 70% value area. Serves as support if price opens above, or resistance if rejected below.
- **LVN (Low Volume Nodes):** Prices where minimal auctioning took place. Act as rejection zones or fast-travel slippage corridors.
- **HVN (High Volume Nodes):** Dense consolidation nodes where buyers and sellers agree on price.

### 2. Profile Shapes & Directional Biases
- **D-Shape (Balanced / Neutral):**
  - Symmetrical Gaussian bell curve with POC centered.
  - Signal: Equilibrium between buyers and sellers. Trade the edges (Fade VAH short, fade VAL long).
- **P-Shape (Short Covering / Bullish Initiative):**
  - Thin volume stalk at the bottom, heavy volume cluster at the top with POC high.
  - Signal: Initiative aggressive buying or short covering. Bias is Bullish/Long on retests of POC/VAL.
- **b-Shape (Long Liquidation / Bearish Initiative):**
  - Heavy volume consolidation at the bottom, thin single-print stalk at the top with POC low.
  - Signal: Long liquidation or initiative selling. Bias is Bearish/Short on rallies to POC/VAH.
- **Double Distribution (Transition / Breakout):**
  - Two distinct bell curves separated by an LVN vacuum corridor.
  - Signal: Trend day transitioning between two balance areas. Respect the breakout direction.

### 3. Execution Rules & Confluence
- **Value Area Rule (80% Rule):** If price opens outside the previous day's Value Area and then accepts inside the Value Area for two consecutive 30-minute bars, there is an 80% statistical probability of filling the entire Value Area to the opposite extreme.
- Combine with **Footprint Absorption** at VAH/VAL to confirm entry timing.

## Independent Maintenance
- Implemented in `orderflow_system/analytics/volume_profile.py` and `ProfileFramingEngine`.
- Profile aggregation spans (1-day, 3-day, 5-day merged) are configurable and verified independently.
