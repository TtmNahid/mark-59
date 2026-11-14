---
name: gex-analysis
description: Institutional Gamma Exposure (GEX) analysis specialist for dealer positioning, options gamma regimes, volatility boundaries, and price wall reactions.
---

# Specialist Skill: GEX Analysis

## Role & Domain Authority
The GEX Analysis Specialist governs options-implied structural dealer positioning. It models options market maker hedging flows, volatility regimes, expected moves, and major gamma strike levels.

## Key Concepts & Structural Levels

### 1. Volatility Regimes (+GEX vs -GEX)
- **Positive Gamma Regime ($Spot \ge Flip$):**
  - Dealers are long gamma. They hedge by buying dips and selling rips.
  - Market behavior: Mean-reverting, low realized volatility, sticky price action.
  - Playbook: Fade extreme moves toward central gravity strikes (MP / CW0).
- **Negative Gamma Regime ($Spot < Flip$):**
  - Dealers are short gamma. They hedge by selling declines and buying rallies.
  - Market behavior: High volatility, cascade risk, violent trending momentum, wide slippage.
  - Playbook: Trend continuation, breakout expansion, respect directional momentum.

### 2. Major Gamma Strikes & Roles
- **CW (Call Wall):** Absolute overhead resistance where dealer short call delta hedging peaks.
- **CW0 (Primary Call Resistance):** Nearest overhead call wall acting as intraday target or resistance ceiling.
- **PW (Put Wall):** Absolute structural floor where dealer put delta hedging terminates downside cascades.
- **PW0 (Primary Put Support):** Nearest downside put strike acting as strong mean-reversion defense or sweep liquidity pool.
- **FLIP (Gamma Flip / Zero Gamma):** The boundary price separating positive gamma regime from negative gamma regime.
- **MP (Max Pain):** Theoretical options expiration magnet where option sellers minimize payout liability.
- **EM+ / EM- (Expected Move Boundaries):** $\pm 1\sigma$ and $\pm 50\%$ statistical ranges for the daily options expiration cycle.

## Execution Rules & Confluence
1. Never short into `PW0` or `PW` without a confirmed breakdown and negative gamma cascade.
2. Absorption at `PW0` with bullish footprint delta triggers high-probability scalp back to `CW0` or `FLIP`.
3. In -GEX regime, support levels break more easily; avoid counter-trend knife-catching without stacked footprint absorption.

## Independent Maintenance
- API connections with GexDash are managed in `orderflow_system/data/gex_client.py`.
- Level updates, custom strike formulas, and strike shift interpretations are auditable via the Knowledge Library.
