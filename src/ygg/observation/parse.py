"""Pure parsers: raw GDELT zip bytes -> Arrow tables with the pruned column set (Session 1, frozen).

Kept from the GKG: record id, batch time, source, URL, themes, countries, persons, orgs, all names,
tone and word count, sharing image, quotations, amounts, and from the Extras XML PAGE_TITLE,
PAGE_PRECISEPUBTIMESTAMP and PAGE_AUTHORS. Dropped: GCAM (70% of bytes), the enhanced/offset
columns, counts, dates, related images and embeds. Rows whose column count is wrong go to quarantine.
"""
from __future__ import annotations

import html
import io
import re
import zipfile
from datetime import datetime, timezone

import pyarrow as pa

_TS = pa.timestamp("us", tz="UTC")
_STRS = pa.list_(pa.string())
GKG_PARSED_SCHEMA = pa.schema([
    ("record_id", pa.string()), ("batch_ts", _TS), ("source_collection", pa.int8()), ("source_name", pa.string()),
    ("url", pa.string()), ("title", pa.string()), ("published_time", _TS), ("authors", _STRS),
    ("themes", _STRS), ("countries", _STRS), ("persons", _STRS), ("orgs", _STRS), ("all_names", _STRS),
    ("tone", pa.float32()), ("word_count", pa.int32()), ("sharing_image", pa.string()),
    ("quotations", pa.list_(pa.struct([("verb", pa.string()), ("quote", pa.string())]))),
    ("amounts", pa.list_(pa.struct([("amount", pa.float64()), ("object", pa.string())]))),
])
EVENT_SCHEMA = pa.schema([
    ("event_id", pa.int64()), ("day", pa.string()), ("actor1", pa.string()), ("actor2", pa.string()), ("event_code", pa.string()),
    ("goldstein", pa.float32()), ("num_mentions", pa.int32()), ("num_sources", pa.int32()), ("num_articles", pa.int32()),
    ("avg_tone", pa.float32()), ("country", pa.string()), ("date_added", _TS), ("source_url", pa.string()),
])
MENTION_SCHEMA = pa.schema([
    ("event_id", pa.int64()), ("event_time", _TS), ("mention_time", _TS), ("mention_type", pa.int8()),
    ("source_name", pa.string()), ("url", pa.string()), ("confidence", pa.int16()),
])
QUARANTINE_SCHEMA = pa.schema([("kind", pa.string()), ("line_no", pa.int32()), ("n_fields", pa.int32()), ("raw_line", pa.string())])

_XML = {tag: re.compile(rf"<{tag}>(.*?)</{tag}>", re.S) for tag in ("PAGE_TITLE", "PAGE_PRECISEPUBTIMESTAMP", "PAGE_AUTHORS")}
_WS = re.compile(r"\s+")


def _ts(s: str) -> datetime | None:
    if len(s) == 14 and s.isdigit():
        try:
            return datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _split(s: str, sep: str = ";") -> list[str]:
    seen, out = set(), []
    for x in s.split(sep):
        x = x.strip()
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _f(s: str, cast=float):
    try:
        return cast(s)
    except (TypeError, ValueError):
        return None


def _unzip(blob: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        text = z.read(z.namelist()[0]).decode("utf-8", "replace")
    return text.split("\n")


def _xml(tag: str, s: str) -> str:
    m = _XML[tag].search(s)
    return _WS.sub(" ", html.unescape(m.group(1))).strip() if m else ""


def parse_gkg(blob: bytes) -> tuple[pa.Table, pa.Table]:
    rows, bad = [], []
    for i, line in enumerate(_unzip(blob)):
        if not line:
            continue
        c = line.split("\t")
        if len(c) != 27:
            bad.append({"kind": "gkg", "line_no": i, "n_fields": len(c), "raw_line": line[:2000]})
            continue
        tone = c[15].split(",")
        countries = _split(";".join(loc.split("#")[2] if loc.count("#") >= 2 else "" for loc in c[9].split(";")))
        names = _split(";".join(n.rsplit(",", 1)[0] for n in c[23].split(";") if n))
        quotes = []
        for q in c[22].split("#"):
            p = q.split("|", 3)
            if len(p) == 4 and p[3].strip():
                quotes.append({"verb": p[2].strip(), "quote": p[3].strip()})
        amounts = []
        for a in c[24].split(";"):
            if a.count(",") >= 2:
                head, _offset = a.rsplit(",", 1)
                amt, obj = head.split(",", 1)
                v = _f(amt)
                if v is not None:
                    amounts.append({"amount": v, "object": obj.strip()})
        authors = _xml("PAGE_AUTHORS", c[26])
        rows.append({
            "record_id": c[0], "batch_ts": _ts(c[1]), "source_collection": _f(c[2], int), "source_name": c[3].lower(),
            "url": c[4], "title": _xml("PAGE_TITLE", c[26]), "published_time": _ts(_xml("PAGE_PRECISEPUBTIMESTAMP", c[26])),
            "authors": _split(authors, ",") if authors else [], "themes": _split(c[7]), "countries": countries,
            "persons": _split(c[11]), "orgs": _split(c[13]), "all_names": names,
            "tone": _f(tone[0]) if tone and tone[0] else None,
            "word_count": _f(tone[6], int) if len(tone) > 6 else None,
            "sharing_image": c[18], "quotations": quotes, "amounts": amounts,
        })
    return pa.Table.from_pylist(rows, schema=GKG_PARSED_SCHEMA), pa.Table.from_pylist(bad, schema=QUARANTINE_SCHEMA)


def parse_events(blob: bytes) -> tuple[pa.Table, pa.Table]:
    rows, bad = [], []
    for i, line in enumerate(_unzip(blob)):
        if not line:
            continue
        c = line.split("\t")
        if len(c) != 61:
            bad.append({"kind": "export", "line_no": i, "n_fields": len(c), "raw_line": line[:2000]})
            continue
        rows.append({
            "event_id": _f(c[0], int), "day": c[1], "actor1": c[6], "actor2": c[16], "event_code": c[26],
            "goldstein": _f(c[30]), "num_mentions": _f(c[31], int), "num_sources": _f(c[32], int),
            "num_articles": _f(c[33], int), "avg_tone": _f(c[34]), "country": c[53], "date_added": _ts(c[59]), "source_url": c[60],
        })
    return pa.Table.from_pylist(rows, schema=EVENT_SCHEMA), pa.Table.from_pylist(bad, schema=QUARANTINE_SCHEMA)


def parse_mentions(blob: bytes) -> tuple[pa.Table, pa.Table]:
    rows, bad = [], []
    for i, line in enumerate(_unzip(blob)):
        if not line:
            continue
        c = line.split("\t")
        if len(c) != 16:
            bad.append({"kind": "mentions", "line_no": i, "n_fields": len(c), "raw_line": line[:2000]})
            continue
        rows.append({
            "event_id": _f(c[0], int), "event_time": _ts(c[1]), "mention_time": _ts(c[2]), "mention_type": _f(c[3], int),
            "source_name": c[4].lower(), "url": c[5], "confidence": _f(c[11], int),
        })
    return pa.Table.from_pylist(rows, schema=MENTION_SCHEMA), pa.Table.from_pylist(bad, schema=QUARANTINE_SCHEMA)


PARSERS = {"gkg": parse_gkg, "export": parse_events, "mentions": parse_mentions}
