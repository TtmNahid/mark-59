"""
OrderFlow Analysis Pro Client for Mark LVI
Connects to the local OrderFlow backend (default: http://127.0.0.1:8080).
"""
from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Tuple

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://127.0.0.1:8080"

# Common alias mapping to internal OrderFlow symbols
SYMBOL_ALIASES = {
    "GOLD": "XAUUSDT",
    "XAU": "XAUUSDT",
    "XAUUSD": "XAUUSDT",
    "XAUUSDT": "XAUUSDT",
    "SILVER": "XAGUSD",
    "XAG": "XAGUSD",
    "XAGUSD": "XAGUSD",
    "NASDAQ": "NAS100USDT",
    "NAS100": "NAS100USDT",
    "US100": "NAS100USDT",
    "NQ": "NAS100USDT",
    "NAS100USDT": "NAS100USDT",
    "SP500": "SP500",
    "ES": "SP500",
    "US500": "SP500",
    "DOW": "DJ30",
    "DJ30": "DJ30",
    "US30": "DJ30",
    "YM": "DJ30",
    "DAX": "DAX40",
    "DAX40": "DAX40",
    "DE30": "DAX40",
    "FTSE": "UK100",
    "UK100": "UK100",
    "BTC": "BTCUSDT",
    "BITCOIN": "BTCUSDT",
    "BTCUSD": "BTCUSDT",
    "BTCUSDT": "BTCUSDT",
    "ETH": "ETHUSDT",
    "ETHEREUM": "ETHUSDT",
    "ETHUSD": "ETHUSDT",
    "ETHUSDT": "ETHUSDT",
    "SOL": "SOLUSDT",
    "SOLUSDT": "SOLUSDT",
    "OIL": "USOIL",
    "USOIL": "USOIL",
    "WTI": "USOIL",
    "BRENT": "UKOIL",
    "UKOIL": "UKOIL",
    "EURUSD": "EURUSD",
    "GBPUSD": "GBPUSD",
    "USDJPY": "USDJPY",
    "AUDUSD": "AUDUSD",
    "USDCAD": "USDCAD",
    "USDCHF": "USDCHF",
    "NZDUSD": "NZDUSD",
    "EURGBP": "EURGBP",
    "EURJPY": "EURJPY",
    "GBPJPY": "GBPJPY",
    "APPLE": "AAPL",
    "AAPL": "AAPL",
    "TESLA": "TSLA",
    "TSLA": "TSLA",
    "AMAZON": "AMZN",
    "AMZN": "AMZN",
    "MICROSOFT": "MSFT",
    "MSFT": "MSFT",
    "NVIDIA": "NVDA",
    "NVDA": "NVDA",
    "META": "META",
    "GOOGLE": "GOOGL",
    "GOOGL": "GOOGL",
}

def normalize_symbol(raw_symbol: str) -> str:
    """Normalize user input or ticker into the OrderFlow system symbol."""
    if not raw_symbol:
        return "XAUUSDT"
    clean = raw_symbol.upper().strip().replace("/", "").replace("-", "").replace(" ", "")
    return SYMBOL_ALIASES.get(clean, clean)


def get_configured_url() -> str:
    """Read configured API URL from Mark LVI's memory config if present."""
    try:
        from memory.config_manager import get_plugin_setting
        url = get_plugin_setting("orderflow", "api_url", DEFAULT_BASE_URL)
        return str(url).strip() or DEFAULT_BASE_URL
    except Exception:
        return DEFAULT_BASE_URL


class OrderFlowClient:
    def __init__(self, base_url: str | None = None, timeout: float = 3.5):
        self.base_url = (base_url or get_configured_url()).rstrip("/")
        self.timeout = timeout

    def _get(self, path: str):
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, headers={"User-Agent": "Jarvis-MarkLVI/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            return {"error": f"Cannot connect to OrderFlow engine at {self.base_url}: {e.reason}"}
        except Exception as e:
            return {"error": f"OrderFlow request error: {e}"}

    def is_online(self) -> bool:
        res = self._get("/api/stats")
        return isinstance(res, dict) and "error" not in res

    def test_connection(self) -> Tuple[bool, str]:
        res = self._get("/api/stats")
        if isinstance(res, dict) and "error" not in res:
            src = res.get("data_source", "unknown")
            clients = res.get("ws_clients", 0)
            return True, f"Connected to OrderFlow Engine (Source: {src.upper()}, WS Clients: {clients})."
        err = res.get("error", "Unknown connection failure") if isinstance(res, dict) else "No response"
        return False, f"Failed to connect to {self.base_url}: {err}"

    def get_instruments(self):
        return self._get("/api/instruments")

    def get_scanner(self):
        return self._get("/api/scanner")

    def get_strategy_status(self, symbol: str):
        sym = normalize_symbol(symbol)
        return self._get(f"/api/strategy-status/{sym}")

    def get_bias(self, symbol: str):
        sym = normalize_symbol(symbol)
        return self._get(f"/api/bias/{sym}")

    def get_volume_profile(self, symbol: str, days: int = 5):
        sym = normalize_symbol(symbol)
        return self._get(f"/api/volume-profile/{sym}?days={days}")

    def get_orderbook(self, symbol: str, levels: int = 10):
        sym = normalize_symbol(symbol)
        return self._get(f"/api/orderbook/{sym}?levels={levels}")

    def get_delta(self, symbol: str, count: int = 60):
        sym = normalize_symbol(symbol)
        return self._get(f"/api/delta/{sym}?count={count}")

    def get_footprint(self, symbol: str):
        sym = normalize_symbol(symbol)
        return self._get(f"/api/footprint/{sym}")

    def get_signals(self, symbol: str, limit: int = 5):
        sym = normalize_symbol(symbol)
        return self._get(f"/api/signals/{sym}?limit={limit}")

    def get_microstructure(self, symbol: str):
        sym = normalize_symbol(symbol)
        return self._get(f"/api/microstructure/{sym}")

    def get_trade(self, symbol: str):
        sym = normalize_symbol(symbol)
        return self._get(f"/api/trade/{sym}")

    def get_candles(self, symbol: str, count: int = 100, tf: int = 60):
        sym = normalize_symbol(symbol)
        return self._get(f"/api/candles/{sym}?count={count}&tf={tf}")

    def get_gex(self, symbol: str, refresh: bool = False):
        sym = normalize_symbol(symbol)
        return self._get(f"/api/gex/{sym}{'?refresh=true' if refresh else ''}")
