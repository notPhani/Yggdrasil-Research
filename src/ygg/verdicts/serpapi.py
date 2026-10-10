"""SerpApi as Engine 3's targeted evidence sensor, through contract C4 (decisions 0.5, 0.6, 6.2).

Per hypothesis, three queries built from its central subject: one confirming, two disconfirming (Heuer: look for
what would break it), at most 15 per case. Every response is archived on first call and replayed from the archive
afterwards (D5), so a case replays offline and spends no credits twice. Each result is matched to Engine 1 by
canonical URL:
  matched    first_seen is inherited from the earlier broad GDELT record (0.6): admissible before tau* if earlier
  unmatched  no Engine 1 sighting: the page is evidence for truth only (P_all), never for what moved the price
Results are origin = targeted. They never enter Engine 2 counts or fits (the one-way valve, 0.5), and they are not
witnesses that the trigger event occurred: they contribute claims only.

The key is read from SERPAPI_API_KEY. Without it every query is recorded as UNAVAILABLE and the verdict runs on
Engine 1 documents and Wayback pages alone; adding the key later and rerunning 'ygg verdict DAY' fills the gap
without any replay, because nothing here feeds back into Engine 2.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from ygg.observation.canon import registrable_domain, url_key
from ygg.store.blobs import BlobStore
from ygg.verdicts import claims as C
from ygg.verdicts.sources import owner, tier

API = "https://serpapi.com/search.json"
BUDGET_PER_CASE = 15
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'.-]+")
_STOP = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "as", "at", "by", "with", "from", "is", "are", "its", "after", "over"}


def core_terms(subject: str, label: str, n: int = 5) -> str:
    words = [w for w in _WORD.findall(label) if w.lower() not in _STOP][:n]
    subj = subject.replace("_", " ").strip()
    head = f'"{subj}" ' if subj and subj.lower() not in " ".join(words).lower() else ""
    return (head + " ".join(words)).strip()


def queries(subject: str, label: str) -> list[tuple[str, str, bool]]:
    """(kind, query, date-bounded to [tau* - 14 d, tau*]) for one hypothesis."""
    core = core_terms(subject, label)
    return [("confirm", core, True),
            ("disconfirm", f"{core} denied OR false OR misleading OR disputed", True),
            ("disconfirm", f"{core} excludes OR retracted OR correction OR overstated", False)]


class Sensor:
    def __init__(self, data_dir: Path, api_key: str | None = None, budget: int = BUDGET_PER_CASE):
        self.data_dir = Path(data_dir)
        self.key = api_key if api_key is not None else os.environ.get("SERPAPI_API_KEY")
        self.budget = budget
        self.cache = self.data_dir / "fetch" / "serpapi"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.blobs = BlobStore(self.data_dir / "blobs")

    def _params(self, q: str, tau: datetime, bounded: bool) -> dict:
        p = {"engine": "google", "q": q, "num": 10, "hl": "en", "gl": "us"}
        if bounded:
            lo = tau - timedelta(days=14)
            p["tbs"] = f"cdr:1,cd_min:{lo.month}/{lo.day}/{lo.year},cd_max:{tau.month}/{tau.day}/{tau.year}"
        return p

    def search(self, q: str, tau: datetime, bounded: bool) -> tuple[str, dict, str]:
        params = self._params(q, tau, bounded)
        ck = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
        path = self.cache / f"{ck}.json"
        if path.exists():
            return "CACHED", json.loads(path.read_text()), ck
        if not self.key:
            return "UNAVAILABLE", {}, ck
        url = API + "?" + urllib.parse.urlencode({**params, "api_key": self.key})
        req = urllib.request.Request(url, headers={"User-Agent": "yggdrasil-research/0.1"})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
        blob = self.blobs.put(raw, ".json")
        body = json.loads(raw)
        body.pop("search_metadata", None)                  # drop the request echo, which carries the key
        rec = {"params": params, "raw_blob": blob, "organic_results": body.get("organic_results", [])}
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(rec, indent=1))
        tmp.replace(path)
        return "DONE", rec, ck

    def run_case(self, hyps: list, tau: datetime, con, existing: dict[str, list[dict]], subject_of) -> tuple[list[dict], dict[str, list[dict]]]:
        """Queries for every hypothesis within the case budget; returns (search records, extra reports per hypothesis)."""
        ops, extra, spent = [], {h.hid: [] for h in hyps}, 0
        for h in hyps:
            have = {r.get("url_key") or url_key(r["url"]) for r in existing.get(h.hid, []) if r.get("url")}
            for i, (kind, q, bounded) in enumerate(queries(subject_of(h), h.entry_label)):
                if spent >= self.budget:
                    ops.append({"qid": f"q_{h.hid}_{i}", "hid": h.hid, "kind": kind, "query": q, "provider": "serpapi",
                                "status": "SKIPPED", "note": f"case budget of {self.budget} queries spent"})
                    continue
                try:
                    status, rec, ck = self.search(q, tau, bounded)
                except Exception as e:
                    ops.append({"qid": f"q_{h.hid}_{i}", "hid": h.hid, "kind": kind, "query": q, "provider": "serpapi",
                                "status": "ERROR", "note": str(e)[:120]})
                    continue
                spent += status == "DONE"
                matched = unmatched = 0
                for res in rec.get("organic_results", [])[:10]:
                    link = res.get("link") or ""
                    if not link:
                        continue
                    uk = url_key(link)
                    if uk in have:
                        continue
                    have.add(uk)
                    row = con.execute("SELECT min(first_seen), min(observation_id), min(copy_group) FROM obs_doc WHERE url_key = ?", [uk]).fetchone()
                    fs = row[0] if row and row[0] is not None else None
                    fs_iso = (fs if fs.tzinfo else fs.replace(tzinfo=tau.tzinfo)).isoformat() if fs is not None else None
                    matched += fs is not None
                    unmatched += fs is None
                    dom = registrable_domain(link)
                    rid = f"s_{uk[:12]}"
                    title = (res.get("title") or "").strip()
                    extra[h.hid].append({"id": rid, "source": dom, "tier": tier(dom), "owner": owner(dom),
                                         "group": (row[2] or uk)[:12] if fs is not None else uk[:12], "first_seen": fs_iso,
                                         "pre": bool(fs is not None and fs_iso < tau.isoformat()), "url": link, "url_key": uk,
                                         "title": title, "claims": C.from_title(rid, title, subject_of(h)), "copy": False,
                                         "origin": "targeted", "witness": False, "query": ck})
                ops.append({"qid": f"q_{ck[:10]}", "hid": h.hid, "kind": kind, "query": q, "provider": "serpapi", "status": status,
                            "bounded": bounded, "results": len(rec.get("organic_results", [])), "matched": matched, "unmatched": unmatched,
                            "note": "" if status != "UNAVAILABLE" else "no SERPAPI_API_KEY: recorded, not sent; rerun 'ygg verdict' after adding the key"})
        return ops, extra
