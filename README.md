# JARVIS MARK 59 — Voice AI Assistant & Order Flow Trading System

JARVIS MARK 59 is an integrated trading intelligence and autonomous voice assistant platform combining **Mark-LVI** (Voice AI / LLM orchestration) with **OrderFlow-Analysis-Pro** (Institutional Order Flow Engine, MT5 Live Feed, and Real-Time Dashboard).

---

## Architecture Overview

```
MARK 59/
├── Analysis Pro/               # OrderFlow Trading Engine & Web Dashboard
│   ├── orderflow_system/       # Core analytics, microstructure, signals, pipelines
│   │   ├── analytics/          # Volume Profile, Delta, Footprint calculations
│   │   ├── dashboard/          # FastAPI web server, WebSocket manager, HTML5 UI
│   │   │   └── static/         # TradingView Lightweight Charts, Footprint, GEX overlay
│   │   ├── data/               # MT5 bridge, GexDash API client, models
│   │   ├── patterns/           # Absorption, initiative, divergence detectors
│   │   └── signals/            # Signal aggregation and trade execution logic
│   ├── run_orderflow.bat       # Launcher for orderflow dashboard (Port 8080)
│   └── pyproject.toml          # Engine dependencies and setup
│
├── Mark-LVI/                   # JARVIS Voice AI Assistant
│   ├── core/                   # Audio I/O, speech synthesis, hotword detection
│   ├── plugins/                # Trading Mode & OrderFlow integration plugins
│   ├── config/                 # Model configs, prompts, personalities
│   └── run_jarvis.bat          # Launcher for voice assistant
│
├── trading/                    # Execution routines and trading tools
├── START_JARVIS.bat            # Master launch script
└── .gitignore                  # Clean repository filters
```

---

## Key Features

### 1. Order Flow Analytics & MT5 Live Feed
- **Sub-100ms MT5 Polling**: Live broker ticks, bid/ask depth, tick aggression heuristics.
- **Volume Profile**: Dynamic POC (Point of Control), VAH (Value Area High), VAL (Value Area Low), and profile shapes (P-shape, b-shape, D-shape).
- **Order Flow Footprint**: Bid $\times$ Ask price level visualization with configurable imbalance detection (2x, 3x, 4x).
- **Institutional Signals**: Automated detection for absorption, initiative volume, liquidity sweeps, and exhaustion.

### 2. Live GEX Levels Integration (GexDash)
- **Direct API Stream**: Streams institutional dealer positioning (Call Wall, Put Wall, Gamma Flip, Expected Move 1D, Standard Deviation bands).
- **TradingView-Style Overlay**: Real-time price lines on Lightweight Charts with colored axis tags.
- **In-Dashboard API Manager**: Dedicated GEX API configuration section on port 8080 with instant verification and `.env` persistence.

### 3. Voice-Activated Trading Mode
- **Hands-Free Market Reports**: Ask JARVIS for structural analysis, POC/VAH/VAL status, buyer/seller control, and trade setups.
- **Strict Integrity Rules**: Clearly separates estimated CFD tick volume from exchange-cleared CME data.

---

## Quick Start

### Prerequisites
- Python 3.11+
- MetaTrader 5 (MT5) terminal logged into your broker account
- Active Internet connection for GEXDash levels and MT5 feeds

### Launching the System
1. **Start the OrderFlow Dashboard:**
   ```bat
   cd "Analysis Pro"
   run_orderflow.bat
   ```
   Open `http://localhost:8080` in your browser.

2. **Start the JARVIS Voice Assistant:**
   ```bat
   cd "Mark-LVI"
   run_jarvis.bat
   ```

---

## License
Proprietary — Developed for JARVIS MARK 59.
