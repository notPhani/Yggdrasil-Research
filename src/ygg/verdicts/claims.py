"""Claim extraction cascade (decisions 6.3, 6.12, A5), deterministic stages.

A claim is a typed tuple (subject, predicate, value, scope, polarity, report_id, span). Closed vocabulary:
released, occurred, cost_of, trained_with, capability_parity, ranks_top, denies, alleges, invests, guides_capex,
restricts_exports, retracts.
  stage 1 (gdelt): GKG amounts and quotations with their verbs
  stage 2 (rule):  title/lede patterns plus NegEx-style scope cues ("excluding", "only", "final run", ...)
  stage 3 (verifier, separate module): spaCy -> GLiNER -> NLI cross-encoder (+ GLiREL)
A5: every tuple carries a span and survives only if that span occurs verbatim in the text it is checked
against (the fetched page when available). Contradictions are computed by rules, never by a model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

PREDICATES = ("released", "occurred", "cost_of", "trained_with", "capability_parity", "ranks_top", "denies",
              "alleges", "invests", "guides_capex", "restricts_exports", "retracts")
SCOPE_CUES = {
    "final_run_only": re.compile(r"\b(excluding|excludes|exclude|not includ\w*|only the final|final (training )?run|"
                                 r"official training|does not include|doesn'?t include)\b", re.I),
    "all_in": re.compile(r"\b(total cost|all[- ]in|entire|in total|everything|from scratch)\b", re.I),
}
NEGATION = re.compile(r"\b(no|not|never|denied|denies|deny|false|untrue|refuted|rejects?)\b", re.I)
DENY_VERBS = re.compile(r"\b(denied|denies|deny|refuted|rejects?|dismiss\w*|disput\w*)\b", re.I)
ALLEGE_VERBS = re.compile(r"\b(alleg\w*|accus\w*|claims?|suspect\w*|reportedly)\b", re.I)
RELEASE = re.compile(r"\b(releases?|released|launch(es|ed)?|unveil(s|ed)?|rolls? out|debuts?|introduc(es|ed))\b", re.I)
TOPS = re.compile(r"\b(tops|topped|hits? (no\.?|number) ?1|no\.? ?1|surpass(es|ed)|overtak(es|en)|dethron\w*)\b", re.I)
COST_OBJ = re.compile(r"\b(dollar|usd|cost|train|spent|spend|budget)\w*", re.I)
CAPEX_OBJ = re.compile(r"\b(capex|capital expenditure|invest\w*|data cent\w*|infrastructure)\b", re.I)
EXPORT = re.compile(r"\b(export (controls?|curbs?|restrictions?|ban)|chip (ban|curbs?|restrictions?))\b", re.I)
PARITY = re.compile(r"\b(rivals?|on par|matches|as good as|outperforms?|beats?|comparable to)\b", re.I)


@dataclass(frozen=True)
class Claim:
    subject: str
    predicate: str
    value: str
    scope: str
    polarity: int
    report_id: str
    span: str
    extractor: str


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def from_title(report_id: str, title: str, subject: str) -> list[Claim]:
    out = []
    if RELEASE.search(title):
        out.append(Claim(subject, "released", "model", "unspecified", 1, report_id, title, "rule"))
    if TOPS.search(title):
        out.append(Claim(subject, "ranks_top", "chart", "unspecified", 1, report_id, title, "rule"))
    if EXPORT.search(title):
        out.append(Claim(subject, "restricts_exports", "chips", "unspecified", -1 if NEGATION.search(title) else 1, report_id, title, "rule"))
    if PARITY.search(title):
        out.append(Claim(subject, "capability_parity", "frontier", "unspecified", 1, report_id, title, "rule"))
    if DENY_VERBS.search(title):
        out.append(Claim(subject, "denies", _obj(title), "unspecified", 1, report_id, title, "rule"))
    elif ALLEGE_VERBS.search(title):
        out.append(Claim(subject, "alleges", _obj(title), "unspecified", 1, report_id, title, "rule"))
    return out


def _obj(text: str) -> str:
    t = text.lower()
    for k in ("smuggl", "export", "distill", "copied", "stole", "chips", "cost", "training"):
        if k in t:
            return k
    return "claim"


def scope_of(sentence: str) -> str:
    for scope, rx in SCOPE_CUES.items():
        if rx.search(sentence):
            return scope
    return "unspecified"


def from_amounts(report_id: str, amounts: list[dict], text: str, subject: str) -> list[Claim]:
    """GKG amounts -> cost_of / invests / guides_capex; the scope comes from the sentence holding the amount."""
    out = []
    sents = sentences(text)
    for a in amounts:
        obj = a.get("object", "")
        if COST_OBJ.search(obj):
            pred = "cost_of"
        elif CAPEX_OBJ.search(obj):
            pred = "guides_capex" if "capex" in obj.lower() or "capital" in obj.lower() else "invests"
        else:
            continue
        val = f"{a['amount']:.6g}"
        sent = next((s for s in sents if obj.strip() and obj.strip().lower() in s.lower()), "")
        out.append(Claim(subject, pred, val, scope_of(sent) if sent else "unspecified", 1, report_id,
                         sent or obj, "gdelt"))
    return out


def from_quotes(report_id: str, quotes: list[dict], subject: str) -> list[Claim]:
    out = []
    for q in quotes:
        verb, quote = q.get("verb", ""), q.get("quote", "")
        if DENY_VERBS.search(verb) or (NEGATION.search(quote) and DENY_VERBS.search(quote)):
            out.append(Claim(subject, "denies", _obj(quote), "unspecified", 1, report_id, quote, "gdelt"))
        elif ALLEGE_VERBS.search(verb):
            out.append(Claim(subject, "alleges", _obj(quote), "unspecified", 1, report_id, quote, "gdelt"))
    return out


def grounded(claim: Claim, page_text: str) -> bool:
    """A5: keep a tuple only if its span occurs verbatim (whitespace-normalized) in the checked text."""
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    return bool(claim.span) and norm(claim.span) in norm(page_text)


def contrary(a: Claim, b: Claim) -> bool:
    """Same subject and predicate with incompatible scope or polarity; alleges vs denies on the same object."""
    if a.subject == b.subject and a.predicate == b.predicate:
        if a.polarity != b.polarity:
            return True
        if a.predicate == "cost_of" and {a.scope, b.scope} == {"all_in", "final_run_only"}:
            return True
    if a.subject == b.subject and {a.predicate, b.predicate} == {"alleges", "denies"} and a.value == b.value:
        return True
    return False
