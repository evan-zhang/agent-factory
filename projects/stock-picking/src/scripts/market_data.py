#!/usr/bin/env python3
"""Read-only market data providers for stock-picking discovery."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - dependency guard
    yaml = None


DEFAULT_LONGBRIDGE_ENV = Path("/Users/evan/.openclaw/gateways/life/domains/quant/.env")
DEFAULT_UNIVERSE_FILE = Path("src/config/universe.yaml")
DEFAULT_UNIVERSES = {
    "CN": ["600519.SH", "000001.SZ"],
    "HK": ["9988.HK", "3690.HK"],
    "US": ["AAPL.US", "MSFT.US"],
}
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


class MarketDataError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class QuoteSnapshot:
    symbol: str
    last: Decimal
    change_percentage: Decimal | None
    turnover: Decimal | None
    volume: int | None
    status: str
    raw: dict[str, Any]


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def parse_json_prefix(output: str) -> Any:
    """Parse the first JSON value and ignore CLI notices printed afterwards."""
    text = output.lstrip()
    try:
        value, _ = json.JSONDecoder().raw_decode(text)
    except json.JSONDecodeError as exc:
        raise MarketDataError("invalid_quote_json", str(exc)) from exc
    return value


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_quotes(value: Any) -> list[QuoteSnapshot]:
    if isinstance(value, dict):
        records = [value]
    elif isinstance(value, list):
        records = value
    else:
        raise MarketDataError("invalid_quote_shape", "quote response must be an object or list")

    quotes: list[QuoteSnapshot] = []
    for record in records:
        if not isinstance(record, dict):
            raise MarketDataError("invalid_quote_item", "quote item must be an object")
        symbol = str(record.get("symbol") or "")
        last = _decimal(record.get("last"))
        if not symbol or last is None:
            raise MarketDataError("invalid_quote_item", "quote item missing symbol or last")
        quotes.append(
            QuoteSnapshot(
                symbol=symbol,
                last=last,
                change_percentage=_decimal(record.get("change_percentage")),
                turnover=_decimal(record.get("turnover")),
                volume=_int(record.get("volume")),
                status=str(record.get("status") or "unknown"),
                raw=record,
            )
        )
    return quotes


def default_symbols(market: str) -> list[str]:
    try:
        return list(DEFAULT_UNIVERSES[market])
    except KeyError as exc:
        raise MarketDataError("unsupported_market", f"unsupported market {market}") from exc


def load_universe_symbols(path: Path, market: str, universe_ref: str) -> list[str]:
    if yaml is None:
        raise MarketDataError("yaml_unavailable", "PyYAML is required for universe config")
    if not path.exists():
        return default_symbols(market)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise MarketDataError("universe_unreadable", str(exc)) from exc
    universes = data.get("universes")
    if not isinstance(universes, dict):
        raise MarketDataError("invalid_universe_config", "universes must be an object")
    market_config = universes.get(market)
    if not isinstance(market_config, dict):
        raise MarketDataError("unknown_universe_market", f"market not configured: {market}")
    selected = market_config.get(universe_ref)
    if selected is None and universe_ref.endswith("_default"):
        selected = market_config.get("default")
    if not isinstance(selected, list) or not selected:
        raise MarketDataError("unknown_universe_ref", f"universe not configured: {market}/{universe_ref}")
    symbols: list[str] = []
    for index, item in enumerate(selected):
        if isinstance(item, str):
            symbol = item
        elif isinstance(item, dict) and isinstance(item.get("symbol"), str):
            symbol = item["symbol"]
        else:
            raise MarketDataError("invalid_universe_symbol", f"invalid symbol row at {market}/{universe_ref}/{index}")
        symbols.append(symbol)
    return symbols


def run_longbridge_quote(symbols: list[str], env_file: Path = DEFAULT_LONGBRIDGE_ENV, timeout_seconds: int = 30) -> list[QuoteSnapshot]:
    if not symbols:
        raise MarketDataError("empty_universe", "at least one symbol is required")
    if not env_file.exists():
        raise MarketDataError("longbridge_env_missing", f"env file not found: {env_file}")
    quoted_symbols = " ".join(_shell_quote(symbol) for symbol in symbols)
    cmd = f"set -a; source {_shell_quote(str(env_file))}; set +a; longbridge quote {quoted_symbols} --format json"
    completed = subprocess.run(
        ["zsh", "-lc", cmd],
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
    )
    output = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0 or (stderr.startswith("Error:") and not output):
        message = stderr or output or "longbridge quote failed"
        raise MarketDataError("longbridge_quote_failed", message)
    return normalize_quotes(parse_json_prefix(output))


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def quote_to_evidence(quote: QuoteSnapshot, request: dict[str, Any], created_at: str | None = None) -> dict[str, Any]:
    created = created_at or now_utc()
    raw_text = json.dumps(quote.raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    return {
        "schema": "evidence_ref.v1",
        "evidence_id": evidence_id_from_hash(digest),
        "created_at": created,
        "created_by": "node_3_taroc",
        "source_url": "",
        "source_id": quote.symbol,
        "source_type": "broker_data",
        "source_subtype": "other",
        "title": f"Longbridge quote {quote.symbol}",
        "excerpt": quote_excerpt(quote),
        "publisher": "Longbridge",
        "fetched_at": created,
        "observed_at": created,
        "language": "en",
        "snapshot_ref": f"longbridge:{quote.symbol}:{request['signal_date']}",
        "claim_hash": digest,
        "publisher_authority": 0.85,
        "ai_classified_quality": 0.75,
        "classification_method": "publisher_table",
        "source_quality": "high",
        "status": "active",
        "content_hash": "sha256:" + digest,
        "raw_snapshot_path": None,
    }


def quote_excerpt(quote: QuoteSnapshot) -> str:
    change = "n/a" if quote.change_percentage is None else f"{quote.change_percentage}%"
    turnover = "n/a" if quote.turnover is None else str(quote.turnover)
    volume = "n/a" if quote.volume is None else str(quote.volume)
    return f"last={quote.last}; change={change}; turnover={turnover}; volume={volume}; status={quote.status}"


def evidence_id_from_hash(hex_digest: str) -> str:
    number = int(hex_digest[:32], 16)
    chars: list[str] = []
    for _ in range(26):
        number, remainder = divmod(number, 32)
        chars.append(CROCKFORD[remainder])
    return "ev_" + "".join(reversed(chars))


def score_quotes(quotes: list[QuoteSnapshot], limit: int = 3) -> list[QuoteSnapshot]:
    return sorted(quotes, key=lambda quote: quote.turnover or Decimal("0"), reverse=True)[:limit]
