"""L2 semantic dedup (Session 1, four-step B with A as fallback; hackathon cut: step 1 + fallback A).

Every L1-unique document is assigned to a copy group in time order. The group root is its earliest
member. Engine 2 counts one object per root (y) and every member as reach (m) when it arrives, so
the tables stay append-only and causal.

Candidates (within the 72 h horizon): an earlier root with the same normalized title, or with the
same sharing image (site-wide logo images excluded).
  step 1  same normalized title, not a template title, and (same image | same author | names Jaccard >= j0)
  step A  different titles: title-embedding cosine >= theta_a and (names Jaccard >= j0 | an equal amount)
Template titles ("Gearing announcement" x14 from one site, different filings) never merge in
step 1. In the full design they go to step 2 (page heads); in the cut they stay separate.
Independent coverage (L3) never merges: every rule needs evidence of copying.
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np

_SUFFIX = re.compile(r"\s+(?:\||-|–|—|::)\s+([^|\-–—]{1,60})$")
_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_WS = re.compile(r"\s+")


def norm_title(title: str) -> str:
    """Casefold, drop a short trailing site-name segment ('... | The Herald'), strip punctuation."""
    t = unicodedata.normalize("NFKC", title or "").strip()
    m = _SUFFIX.search(t)
    if m and len(m.group(1).split()) <= 6 and len(t[: m.start()].split()) >= 4:
        t = t[: m.start()]
    t = _PUNCT.sub(" ", t.casefold())
    return _WS.sub(" ", t).strip()


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(slots=True)
class Root:
    oid: str
    time: datetime
    source: str
    url_key: str
    title_n: str
    image: str
    authors: frozenset
    names: frozenset
    amounts: frozenset
    vec: np.ndarray | None


@dataclass
class L2Config:
    horizon_h: float = 72.0
    j0: float = 0.5
    theta_a: float = 0.9
    logo_titles: int = 5          # an image shown under this many distinct titles from one source is a logo


@dataclass
class L2Dedup:
    cfg: L2Config = field(default_factory=L2Config)
    by_title: dict = field(default_factory=lambda: defaultdict(list))        # title_n -> [Root]
    by_image: dict = field(default_factory=lambda: defaultdict(list))        # image -> [Root]
    image_titles: dict = field(default_factory=lambda: defaultdict(dict))    # (image, source) -> {title_n: last time}
    title_sources: dict = field(default_factory=lambda: defaultdict(deque))  # title_n -> deque[(time, source, url_key, names)]
    roots: deque = field(default_factory=deque)                              # roots in time order
    seen: deque = field(default_factory=deque)                               # (time, title_n, image, source) for every doc

    def _expire(self, now: datetime) -> None:
        cutoff = now - timedelta(hours=self.cfg.horizon_h)
        while self.roots and self.roots[0].time < cutoff:
            r = self.roots.popleft()
            if r.title_n:
                lst = [x for x in self.by_title[r.title_n] if x is not r]
                if lst:
                    self.by_title[r.title_n] = lst
                else:
                    del self.by_title[r.title_n]
            if r.image:
                lst = [x for x in self.by_image[r.image] if x is not r]
                if lst:
                    self.by_image[r.image] = lst
                else:
                    del self.by_image[r.image]
        while self.seen and self.seen[0][0] < cutoff:
            _, title_n, image, source = self.seen.popleft()
            dq = self.title_sources.get(title_n)
            if dq is not None:
                while dq and dq[0][0] < cutoff:
                    dq.popleft()
                if not dq:
                    del self.title_sources[title_n]
            if image:
                titles = self.image_titles.get((image, source))
                if titles is not None:
                    for k in [k for k, v in titles.items() if v < cutoff]:
                        del titles[k]
                    if not titles:
                        del self.image_titles[(image, source)]

    def _is_template(self, title_n: str, source: str, url_key: str, names: frozenset) -> bool:
        """A title one source uses for different items: disjoint names under another URL, or >= 3 distinct URLs
        (generic page titles such as 'China Daily Website - Connecting China ...')."""
        urls = set()
        for _, s, uk, nm in self.title_sources.get(title_n, ()):
            if s == source and uk != url_key:
                if not (nm & names):
                    return True
                urls.add(uk)
        return len(urls) + 1 >= 3

    def _is_logo(self, image: str, source: str) -> bool:
        return len(self.image_titles.get((image, source), ())) >= self.cfg.logo_titles

    def assign(self, doc: dict, vec: np.ndarray | None) -> tuple[str, str]:
        """Return (copy_group root id, merge evidence) for one L1-unique document, then index it."""
        now = doc["observed_time"]
        self._expire(now)
        title_n = norm_title(doc["title"])
        names = frozenset(n.casefold() for n in doc["all_names"]) | frozenset(doc["persons"]) | frozenset(doc["orgs"])
        authors = frozenset(a.casefold() for a in doc["authors"])
        amounts = frozenset(round(a["amount"], 6) for a in doc["amounts"])
        image, source = doc["sharing_image"] or "", doc["source_name"]
        if image:
            self.image_titles[(image, source)][title_n] = now
        self.seen.append((now, title_n, image, source))
        use_image = bool(image) and not self._is_logo(image, source)
        template = bool(title_n) and self._is_template(title_n, source, doc["url_key"], names)
        root, evidence = None, ""
        short = len(title_n.split()) < 4
        if title_n and not template:
            for c in self.by_title.get(title_n, ()):
                image_ok = use_image and c.image == image and not self._is_logo(c.image, c.source)
                if c.source == source or short:
                    # same outlet or a short generic title: only a shared real image plus overlapping names counts
                    if image_ok and jaccard(names, c.names) >= self.cfg.j0:
                        root, evidence = c, "L2:s1:image+names"
                elif image_ok:
                    root, evidence = c, "L2:s1:image"
                elif authors and authors & c.authors:
                    root, evidence = c, "L2:s1:author"
                elif jaccard(names, c.names) >= self.cfg.j0:
                    root, evidence = c, "L2:s1:names"
                if root:
                    break
        if root is None and use_image and vec is not None:
            for c in self.by_image.get(image, ()):
                if c.title_n == title_n or c.vec is None or self._is_logo(c.image, c.source):
                    continue
                if float(vec @ c.vec) >= self.cfg.theta_a and (jaccard(names, c.names) >= self.cfg.j0 or (amounts & c.amounts)):
                    root, evidence = c, "L2:A:image+embedding"
                    break
        if title_n:
            self.title_sources[title_n].append((now, source, doc["url_key"], names))
        if root is not None:
            return root.oid, evidence
        r = Root(doc["observation_id"], now, source, doc["url_key"], title_n, image if use_image else "",
                 authors, names, amounts, vec)
        self.roots.append(r)
        if title_n:
            self.by_title[title_n].append(r)
        if r.image:
            self.by_image[r.image].append(r)
        return r.oid, "root"
