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
│   ├── requirements.txt        # Python package dependencies
│   ├── pyproject.toml          # Package configuration
│   ├── .env.example            # Environment configuration template
│   └── run_orderflow.bat       # Auto-setup and launcher for orderflow dashboard (Port 8080)
│
├── Mark-LVI/                   # JARVIS Voice AI Assistant
│   ├── core/                   # Audio I/O, speech synthesis, hotword detection
│   ├── plugins/                # Trading Mode & OrderFlow integration plugins
│   ├── config/                 # Model configs, prompts, personalities
│   │   └── api_keys.json.example # API key template (Gemini, etc.)
│   ├── requirements.txt        # Mark-LVI package dependencies
│   ├── setup.py                # Automated environment setup script
│   └── run_jarvis.bat          # Auto-setup and launcher for voice assistant
│
├── SETUP_ALL.bat               # One-click master installer for both environments
├── START_JARVIS.bat            # Interactive master launch menu
└── .gitignore                  # Clean repository filters (ignores secrets, db, venvs)
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

## Installation & Setup on a Fresh Machine

### Prerequisites
1. **Operating System**: Windows 10 or 11 (64-bit).
2. **Python**: Python 3.10, 3.11, or 3.12 installed from [python.org](https://www.python.org/downloads/).
   > **CRITICAL**: Make sure to check **"Add python.exe to PATH"** during Python installation!
3. **MetaTrader 5 (MT5)**: Installed and logged into your broker account.
4. **Git**: Installed from [git-scm.com](https://git-scm.com/).

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/TtmNahid/mark-59.git
cd mark-59
```

---

### Step 2: One-Click Environment Setup
Double-click `SETUP_ALL.bat` in the root folder, or run:
```bat
SETUP_ALL.bat
```
This script will automatically:
1. Create virtual environments (`.venv`) for both **Analysis Pro** and **Mark-LVI**.
2. Install all required dependencies for both systems.
3. Generate template configuration files (`.env` and `config/api_keys.json`).

*Alternatively, simply double-clicking `START_JARVIS.bat`, `run_orderflow.bat`, or `run_jarvis.bat` will also detect if `.venv` is missing and automatically configure the environment!*

---

### Step 3: Configure API Keys (Optional)

1. **GEXDash API Key (For Institutional GEX Levels)**:
   - Either paste your API key directly in the web dashboard at `http://localhost:8080` (under the GEX API Configuration panel), OR
   - Edit `Analysis Pro/.env`:
     ```env
     GEXDASH_API_KEY=your_key_here
     ```

2. **Gemini API Key (For JARVIS Voice AI)**:
   - Edit `Mark-LVI/config/api_keys.json`:
     ```json
     {
       "gemini": "your_gemini_api_key_here"
     }
     ```

---

## Running the System

You can run everything via the Master Launcher:

Double-click `START_JARVIS.bat`:
```
======================================================================
                      JARVIS MARK 59 - MASTER LAUNCHER
======================================================================

  [1] Start OrderFlow Analysis Pro Dashboard (Port 8080)
  [2] Start JARVIS Mark-LVI Voice AI Assistant
  [3] Start BOTH (OrderFlow Dashboard + JARVIS Assistant)
  [4] One-Click Setup / Reinstall Dependencies (SETUP_ALL.bat)
  [5] Exit
```

Or run individual components:
- **OrderFlow Dashboard**: Double-click `Analysis Pro\run_orderflow.bat` and open `http://localhost:8080`.
- **JARVIS Voice Assistant**: Double-click `Mark-LVI\run_jarvis.bat`.

---

## License
Proprietary — Developed for JARVIS MARK 59.
