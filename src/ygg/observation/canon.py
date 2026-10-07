"""Canonical URLs and url_key (Session 1). The rules are deterministic and versioned with the config.

lowercase scheme and host · force https · IDNA-encode the host · strip leading www./m./amp. ·
drop default ports and fragments · collapse repeated slashes · strip a trailing '/' or '/amp' ·
drop tracker parameters · sort the remaining query keys · uppercase percent-encodings
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

CANON_VERSION = "canon-1"
TRACKER_PREFIXES = ("utm_",)
TRACKER_KEYS = frozenset({
    "fbclid", "gclid", "dclid", "msclkid", "yclid", "mc_cid", "mc_eid", "igshid", "ocid", "cmpid", "ncid",
    "_ga", "_gl", "ref", "ref_src", "smid", "smtyp", "taid", "guccounter", "guce_referrer", "guce_referrer_sig",
    "spm", "soc_src", "soc_trk",
})
HOST_PREFIXES = ("www.", "m.", "amp.", "mobile.")
_PCT = re.compile(r"%[0-9a-fA-F]{2}")
_SLASHES = re.compile(r"/{2,}")


def _host(netloc: str) -> str:
    host = netloc.rsplit("@", 1)[-1].lower()
    if host.endswith(":80") or host.endswith(":443"):
        host = host.rsplit(":", 1)[0]
    for p in HOST_PREFIXES:
        if host.startswith(p) and host.count(".") >= 2:
            host = host[len(p):]
            break
    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError:
        pass
    return host


def canon(url: str) -> str:
    url = url.strip()
    if "://" not in url:
        url = "https://" + url
    parts = urlsplit(url)
    host = _host(parts.netloc)
    path = _SLASHES.sub("/", parts.path or "/")
    path = quote(unquote(path), safe="/:@!$&'()*+,;=-._~")
    for suffix in ("/amp", "/amp/"):
        if path.endswith(suffix):
            path = path[: -len(suffix)] or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if k.lower() not in TRACKER_KEYS and not k.lower().startswith(TRACKER_PREFIXES)]
    q = urlencode(sorted(query), doseq=True)
    out = urlunsplit(("https", host, path, q, ""))
    return _PCT.sub(lambda m: m.group(0).upper(), out)


def url_key(url: str) -> str:
    return hashlib.sha256(canon(url).encode()).hexdigest()


def registrable_domain(host_or_url: str) -> str:
    """Cheap registrable-domain guess (last two labels, three for common second-level suffixes)."""
    host = _host(urlsplit(host_or_url).netloc) if "://" in host_or_url else _host(host_or_url)
    labels = host.split(".")
    if len(labels) >= 3 and labels[-2] in {"co", "com", "net", "org", "gov", "ac", "edu"} and len(labels[-1]) == 2:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])
