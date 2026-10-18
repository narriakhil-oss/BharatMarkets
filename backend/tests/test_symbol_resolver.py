"""Symbol resolver tests for chat name → NSE mapping."""

from app.utils.symbol_resolver import normalize_symbol, resolve_symbol


def test_normalize_appends_ns():
    assert normalize_symbol("reliance") == "RELIANCE.NS"
    assert normalize_symbol("TCS.NS") == "TCS.NS"
    assert normalize_symbol("^NSEI") == "^NSEI"


def test_resolve_common_names():
    assert resolve_symbol("Reliance") == "RELIANCE.NS"
    assert resolve_symbol("TCS") == "TCS.NS"
    assert resolve_symbol("Infosys") == "INFY.NS"
    assert resolve_symbol("HDFCBANK") == "HDFCBANK.NS"
