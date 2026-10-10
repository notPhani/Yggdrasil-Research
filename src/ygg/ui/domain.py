"""What the terminal shows, as plain frozen objects. The UI is a projection of Yggdrasil's recorded state: every
object carries the backend id (narratives, observations, hypotheses, snapshots), shortened only for display.

Temporal status of a piece of evidence (the UI never infers it, the adapters copy it from the record):
  PRE     first seen by Engine 1 before tau*, and its text is the version that existed then  -> P_pre and P_all
  LATE    first seen before tau*, but the text we hold was fetched after tau*                -> P_all only
  POST    first seen at or after tau*                                                          -> P_all only
  UNMATCHED  no Engine 1 sighting at all (e.g. a search result never seen by GDELT)            -> P_all only
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

PRE, LATE, POST, UNMATCHED = "PRE", "LATE", "POST", "UNMATCHED"
ADMISSIBLE = {PRE}


def short(kind: str, ident: str, n: int = 8) -> str:
    """Typed short id for display, e.g. N:4be1a9c0. The full id stays on the object."""
    return f"{kind}:{ident[:n]}" if ident else "—"


@dataclass(frozen=True)
class Instrument:
    symbol: str
    R: float | None = None
    SAR: float | None = None
    Mz: float | None = None
    Mv: float | None = None
    Mg: float | None = None
    gap: float | None = None
    fired: bool = False
    cluster: int | None = None          # index into Investigation.clusters
    secondary: bool = False


@dataclass(frozen=True)
class Edge:
    src: str                            # node id: "BOT", a narrative id, or a terminal name
    dst: str
    p: float
    cost_mnats: int
    src_label: str = ""
    dst_label: str = ""


@dataclass(frozen=True)
class Explanation:
    rank: int                           # 1 = best; rivals 2..; 0 = "we do not know"
    entry: str                          # entry narrative id ("BOT" for abstention)
    entry_label: str
    edges: tuple[Edge, ...]
    cost_mnats: int
    odds_vs_best: float                 # P(best) / P(this); 1.0 for the best
    abstained_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class Claim:
    predicate: str
    text: str


@dataclass(frozen=True)
class Evidence:
    rid: str
    source: str
    tier: int
    first_seen: datetime | None
    status: str                         # PRE / LATE / POST / UNMATCHED
    title: str
    url: str = ""
    claims: tuple[Claim, ...] = ()
    copy: bool = False
    diagnostic: bool = False            # removing it flips the verdict (P_pre or P_all)


@dataclass(frozen=True)
class Hypothesis:
    hid: str
    label: str
    entry: str
    signature_ok: bool
    burst: bool
    surprise_ok: bool
    verdict_pre: str
    verdict_all: str
    bits_pre: tuple[int, int, int, int] | None
    bits_all: tuple[int, int, int, int] | None
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True)
class SearchOp:
    qid: str
    hid: str
    query: str
    provider: str
    status: str                         # DONE / CACHED / UNAVAILABLE / SKIPPED
    results: int = 0
    matched: int = 0                    # canonical-URL matches to an Engine 1 record (first_seen inherited)
    unmatched: int = 0
    note: str = ""


@dataclass(frozen=True)
class Placebo:
    k: int
    fer: float
    p_emp: float
    hubs: tuple[tuple[str, float], ...]
    costs: tuple[int, ...] = ()


@dataclass(frozen=True)
class Investigation:
    case_id: str                        # the trading day
    tau_star: datetime | None
    detected: datetime | None           # when the trigger could fire: the daily close in the replay
    snapshot: str                       # window index of the frozen snapshot read by Engine 3
    instruments: tuple[Instrument, ...]
    clusters: tuple[tuple[str, ...], ...]
    explanations: tuple[Explanation, ...]
    hypotheses: tuple[Hypothesis, ...]
    searches: tuple[SearchOp, ...]
    placebo: Placebo | None
    phases: tuple[tuple[str, str], ...]  # (phase, DONE / PENDING / UNAVAILABLE / SKIPPED)
    graph_nodes: int = 0
    graph_edges: int = 0
    models_pre: int = 0
    models_all: int = 0
    cfg_hash: str = ""
    source: str = "RECORDED"            # RECORDED / DEMO
    notes: tuple[str, ...] = ()

    @property
    def best(self) -> Explanation | None:
        return next((e for e in self.explanations if e.rank == 1), None)

    @property
    def abstention(self) -> Explanation | None:
        return next((e for e in self.explanations if e.rank == 0), None)


@dataclass(frozen=True)
class FeedItem:
    t: datetime                         # first_seen (live: batch time)
    source: str
    title: str
    oid: str = ""
    narrative: str = ""


@dataclass(frozen=True)
class Candle:
    t: datetime
    o: float
    h: float
    l: float
    c: float
    v: float


@dataclass
class Stage:
    name: str
    status: str = "UNKNOWN"             # RUNNING / IDLE / DONE / COLD / UNKNOWN / UNAVAILABLE
    rate: str = ""
    watermark: str = ""
    detail: str = ""


@dataclass
class CaseRow:
    case_id: str
    state: str                          # ARCHIVED / ACTIVE
    phase: str
    terminals: str
    max_sar: float | None
    best: str
    odds: float | None
    p_emp: float | None
    source: str = "RECORDED"
    extra: dict = field(default_factory=dict)
