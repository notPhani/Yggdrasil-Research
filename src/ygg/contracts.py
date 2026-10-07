"""The four contracts between units (Session 0), as frozen dataclasses with explicit Arrow schemas.

C1  ObservationRecord   Engine 1 -> Engine 2, Engine 3   (broad origin only, by construction: A1)
    TargetedPage        Engine 1 -> Engine 3 only        (pages fetched on Engine 3's request)
C2  SnapshotManifest    Engine 2 -> Engine 3             (immutable, content-addressed id)
C3  Case                stock observer -> Engine 3
C4  FetchRequest / FetchResponse   Engine 3 <-> Engine 1

A1: targeted pages are a separate type stored in a separate table. Engine 2's reader accepts only
ObservationRecord, which refuses origin='targeted', so a mislabelled record fails loudly instead
of leaking into attention.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import Literal

import pyarrow as pa

from ygg.determinism import stable_hash

SourceType = Literal["gdelt_gkg", "gdelt_event", "gdelt_mention", "serpapi", "page"]


@dataclass(frozen=True, slots=True)
class ObservationRecord:
    """C1. One object per copy group (Engine 1 hand-off, Session 1)."""
    observation_id: str                 # sha256, content-derived, so replay is idempotent
    source_type: SourceType
    source_name: str                    # outlet domain
    url: str
    url_key: str                        # sha256(canon(url)); derivable, recomputed on load
    native_id: str                      # e.g. GKGRECORDID
    observed_time: datetime             # batch time
    ingested_time: datetime             # D1: observed_time + lag in replay
    first_seen: datetime                # min ingested_time over exact-key duplicates
    window: int
    title: str = ""
    published_time: datetime | None = None   # PAGE_PRECISEPUBTIMESTAMP when present (about 59%)
    event_time: datetime | None = None
    authors: tuple[str, ...] = ()
    persons: tuple[str, ...] = ()
    orgs: tuple[str, ...] = ()
    all_names: tuple[str, ...] = ()
    countries: tuple[str, ...] = ()
    themes: tuple[str, ...] = ()
    tone: float | None = None
    word_count: int | None = None
    sharing_image: str = ""
    quotations: tuple[tuple[str, str], ...] = ()   # (verb, quote)
    amounts: tuple[tuple[float, str], ...] = ()    # (amount, object)
    copy_group: str = ""                # observation_id of the group root (earliest member)
    member_count: int = 1
    member_ids: tuple[str, ...] = ()
    merge_evidence: str = ""            # e.g. "L1:url", "L2:s1:image", "L2:A"
    content_hash: str = ""
    raw_ref: str = ""                   # blob sha256
    origin: Literal["broad"] = "broad"

    def __post_init__(self):
        if self.origin != "broad":
            raise ValueError("C1 records are broad by construction; targeted pages must be TargetedPage (A1)")


@dataclass(frozen=True, slots=True)
class TargetedPage:
    """A page fetched because Engine 3 asked. Evidence only, never attention (one-way valve, A1)."""
    page_id: str
    case_id: str
    query: str
    url: str
    url_key: str
    fetched_time: datetime
    first_seen: datetime                # inherited via canonical-URL match to a broad record (0.6), else fetched_time
    inherited_from: str = ""            # observation_id the first_seen came from, if any
    title: str = ""
    raw_ref: str = ""
    body_ref: str = ""
    admissible_pre: bool = False        # True only when first_seen came from an earlier broad record


@dataclass(frozen=True, slots=True)
class SnapshotManifest:
    """C2. Content-addressed manifest of the Engine 2 state at a window close."""
    t: int
    cfg_hash: str
    parent_snapshot_id: str
    inputs_hash: str
    tables: tuple[tuple[str, str], ...]  # (table name, sha256 of its Parquet bytes)
    snapshot_id: str = field(default="")

    def __post_init__(self):
        expected = snapshot_id(self.cfg_hash, self.t, self.parent_snapshot_id, self.inputs_hash)
        if self.snapshot_id and self.snapshot_id != expected:
            raise ValueError("snapshot_id does not match its contents")
        object.__setattr__(self, "snapshot_id", expected)


def snapshot_id(cfg_hash: str, t: int, parent: str, inputs_hash: str) -> str:
    return stable_hash(cfg_hash, str(t), parent, inputs_hash)


@dataclass(frozen=True, slots=True)
class InstrumentStat:
    ticker: str
    R: float
    gap: float
    AR: float
    SAR: float
    Mz: float
    Mv: float
    Mg: float
    fired: bool
    role: str                           # terminal member | etf member | secondary


@dataclass(frozen=True, slots=True)
class Case:
    """C3."""
    case_id: str
    day: str
    instruments: tuple[InstrumentStat, ...]
    clusters: tuple[tuple[str, ...], ...]
    tau_star: datetime
    cutoff_rule: str
    price_source: str


@dataclass(frozen=True, slots=True)
class FetchRequest:
    """C4 request."""
    case_id: str
    query: str
    engine: str
    date_min: str | None
    date_max: str | None
    budget_slot: int


@dataclass(frozen=True, slots=True)
class FetchResponse:
    """C4 response: results always re-enter through Engine 1's dedup and clocks."""
    request: FetchRequest
    page_ids: tuple[str, ...]
    archived_ref: str                   # D5: raw response archived under its sha256


_TS = pa.timestamp("us", tz="UTC")
_STRS = pa.list_(pa.string())

OBSERVATION_SCHEMA = pa.schema([
    ("observation_id", pa.string()), ("source_type", pa.string()), ("source_name", pa.string()),
    ("url", pa.string()), ("url_key", pa.string()), ("native_id", pa.string()),
    ("observed_time", _TS), ("ingested_time", _TS), ("first_seen", _TS), ("window", pa.int32()),
    ("title", pa.string()), ("published_time", _TS), ("event_time", _TS),
    ("authors", _STRS), ("persons", _STRS), ("orgs", _STRS), ("all_names", _STRS), ("countries", _STRS), ("themes", _STRS),
    ("tone", pa.float32()), ("word_count", pa.int32()), ("sharing_image", pa.string()),
    ("quotations", pa.list_(pa.struct([("verb", pa.string()), ("quote", pa.string())]))),
    ("amounts", pa.list_(pa.struct([("amount", pa.float64()), ("object", pa.string())]))),
    ("copy_group", pa.string()), ("member_count", pa.int32()), ("member_ids", _STRS), ("merge_evidence", pa.string()),
    ("content_hash", pa.string()), ("raw_ref", pa.string()), ("origin", pa.string()),
])

TARGETED_PAGE_SCHEMA = pa.schema([
    ("page_id", pa.string()), ("case_id", pa.string()), ("query", pa.string()), ("url", pa.string()), ("url_key", pa.string()),
    ("fetched_time", _TS), ("first_seen", _TS), ("inherited_from", pa.string()), ("title", pa.string()),
    ("raw_ref", pa.string()), ("body_ref", pa.string()), ("admissible_pre", pa.bool_()),
])


def schema_fields_match(cls, schema: pa.Schema) -> bool:
    return {f.name for f in fields(cls)} == set(schema.names)
