"""Map company names / tickers to NSE Yahoo symbols using NIFTY 100 list."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _candidate_paths() -> List[Path]:
    return [
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty_100_stocks.json",
        Path(__file__).resolve().parent.parent.parent / "data" / "nifty_100_stocks.json",
        Path.cwd() / "data" / "nifty_100_stocks.json",
        Path.cwd().parent / "data" / "nifty_100_stocks.json",
    ]


@lru_cache(maxsize=1)
def load_stock_universe() -> List[Dict[str, Any]]:
    """Load NIFTY 100 stock list from disk."""
    for path in _candidate_paths():
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            stocks = data.get("stocks", data) if isinstance(data, dict) else data
            return list(stocks) if isinstance(stocks, list) else []
    return []


def normalize_symbol(symbol: str) -> str:
    """Uppercase and append .NS when exchange suffix is omitted."""
    sym = symbol.strip().upper()
    if not sym:
        return sym
    if not sym.endswith(".NS") and not sym.endswith(".BO") and not sym.startswith("^"):
        return f"{sym}.NS"
    return sym


def _name_tokens(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def resolve_symbol(query: str) -> Optional[str]:
    """
    Resolve a free-text name or ticker to an NSE Yahoo symbol.

    Examples: "Reliance" -> RELIANCE.NS, "TCS" -> TCS.NS, "infy.ns" -> INFY.NS
    """
    if not query or not query.strip():
        return None

    raw = query.strip()
    stocks = load_stock_universe()

    # Direct symbol / ticker match
    candidate = normalize_symbol(raw)
    for s in stocks:
        sym = s.get("symbol") or s.get("ticker") or ""
        if sym.upper() == candidate or sym.upper() == raw.upper():
            return sym.upper() if sym.endswith((".NS", ".BO")) else normalize_symbol(sym)

    # Bare ticker without universe hit (still allow e.g. RELIANCE)
    if re.fullmatch(r"[A-Za-z0-9&.\-]+", raw) and len(raw) <= 20:
        # Prefer universe name match before blind .NS append
        bare = raw.upper().replace(".NS", "").replace(".BO", "")
        for s in stocks:
            sym = (s.get("symbol") or "").upper()
            if sym.replace(".NS", "").replace(".BO", "") == bare:
                return sym

    q = _name_tokens(raw)
    if not q:
        return normalize_symbol(raw) if re.fullmatch(r"[A-Za-z0-9&.\-]+", raw) else None

    # Exact / startswith name match
    best: Optional[Tuple[int, str]] = None
    for s in stocks:
        name = _name_tokens(s.get("name") or s.get("company") or "")
        sym = (s.get("symbol") or s.get("ticker") or "").upper()
        if not sym or not name:
            continue
        if q == name or name.startswith(q) or q in name.split():
            score = 100 if q == name else (80 if name.startswith(q) else 60)
            # Prefer shorter name ties (more specific)
            score -= min(len(name), 40)
            if best is None or score > best[0]:
                best = (score, sym)
        elif q in name:
            score = 40 - min(len(name), 30)
            if best is None or score > best[0]:
                best = (score, sym)

    if best:
        return best[1]

    # Fallback: treat as ticker
    if re.fullmatch(r"[A-Za-z0-9&.\-]+", raw):
        return normalize_symbol(raw)
    return None


def resolve_symbols(queries: List[str]) -> Dict[str, Optional[str]]:
    """Resolve multiple queries to symbols."""
    return {q: resolve_symbol(q) for q in queries}
