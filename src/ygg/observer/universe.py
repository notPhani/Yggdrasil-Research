"""The instrument universe, frozen as of 2024-12-31 without looking at the event (decision 2.2).

Constituents are parsed from Wikipedia page revisions dated on or before 2024-12-31, identified by
revision id, so the list is reproducible and contains no hindsight:
  Nasdaq-100                  revid 1265020752 (2024-12-24, after the 23 Dec reconstitution)
  List of S&P 500 companies   revid 1265285344 (2024-12-26), GICS sector = Utilities
  PHLX Semiconductor Sector   revid 1246738930 (2024-09-20, the latest revision before 2024-12-31)
plus three Euronext semiconductor names and the benchmarks.
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

REVISIONS = {"nasdaq100": 1265020752, "sp500": 1265285344, "sox": 1246738930}
EUROPE = ["ASML.AS", "ASM.AS", "BESI.AS"]
BENCHMARKS = ["SPY", "QQQ", "SMH", "XLU", "XLK"]
ETFS = set(BENCHMARKS)
SECTOR_ETF = {"semis": "SMH", "utilities": "XLU", "tech": "XLK"}


def fetch_revision(revid: int, cache_dir: Path) -> str:
    path = Path(cache_dir) / f"rev_{revid}.wiki"
    if not path.exists():
        req = urllib.request.Request(f"https://en.wikipedia.org/w/index.php?oldid={revid}&action=raw",
                                     headers={"User-Agent": "yggdrasil-research/0.1"})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    return path.read_text()


def parse_nasdaq100(text: str) -> list[tuple[str, str]]:
    table = text[text.index('id="constituents"'):]
    table = table[: table.index("\n|}")]
    out = []
    for m in re.finditer(r"^\|\s*\[\[[^\]]*\]\][^|\n]*\|\|\s*([A-Z.]+)\s*\|\|\s*([^|\n]+?)\s*\|\|", table, re.M):
        out.append((m.group(1), m.group(2)))
    return out


def parse_sp500_utilities(text: str) -> list[str]:
    syms = re.findall(r"\{\{(?:NyseSymbol|NasdaqSymbol)\|([A-Z.]+)\}\}\s*\n\|[^\n]*?\|\|\s*Utilities\s*\|\|", text)
    return [s.replace(".", "-") for s in syms]


def parse_sox(text: str) -> list[str]:
    return re.findall(r"^\*\s.*,\s*([A-Z]{1,5})\s*$", text, re.M)


def build_universe(cache_dir: Path) -> dict:
    ndx = parse_nasdaq100(fetch_revision(REVISIONS["nasdaq100"], cache_dir))
    utils = parse_sp500_utilities(fetch_revision(REVISIONS["sp500"], cache_dir))
    sox = parse_sox(fetch_revision(REVISIONS["sox"], cache_dir))
    sector: dict[str, str] = {}
    for sym, gics in ndx:
        sector[sym] = "semis" if sym in sox else ("utilities" if gics == "Utilities" else "tech" if gics == "Information Technology" else "other")
    for s in sox:
        sector[s] = "semis"
    for s in utils:
        sector[s] = "utilities"
    for s in EUROPE:
        sector[s] = "semis"
    symbols = sorted(set(sector) | set(BENCHMARKS))
    return {"as_of": "2024-12-31", "revisions": REVISIONS, "counts": {"nasdaq100": len(ndx), "sp500_utilities": len(utils), "sox": len(sox)},
            "symbols": symbols, "sector": sector, "etfs": sorted(ETFS), "sector_etf": SECTOR_ETF}


def load_universe(data_dir: Path) -> dict:
    path = Path(data_dir) / "universe" / "universe.json"
    if not path.exists():
        u = build_universe(path.parent)
        path.write_text(json.dumps(u, indent=1, sort_keys=True))
    return json.loads(path.read_text())
