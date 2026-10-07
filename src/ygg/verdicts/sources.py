"""Source tiers and ownership (decision 6.5), frozen as of 2024-12-31 and disclosed.

tier 0  Yggdrasil's own measurements
tier 1  primary: the actor itself, filings, papers, governments
tier 2  wire services and national outlets
tier 3  everything else (local outlets, aggregators, blogs, unknown domains)
Ownership: a few known syndication families map to one owner; otherwise the registrable domain.
Reports are independent only across different owners and different copy groups (Engine 1).
"""
from __future__ import annotations

from ygg.observation.canon import registrable_domain

PRIMARY = {"arxiv.org", "github.com", "sec.gov", "huggingface.co", "deepseek.com", "nvidia.com", "microsoft.com",
           "openai.com", "meta.com", "google.com", "blog.google", "apple.com", "amazon.com", "tsmc.com", "broadcom.com",
           "vistracorp.com", "constellationenergy.com", "nrg.com", "federalreserve.gov", "bls.gov", "whitehouse.gov",
           "commerce.gov", "bis.doc.gov", "ec.europa.eu", "gov.cn"}
WIRES_NATIONAL = {"reuters.com", "apnews.com", "bloomberg.com", "afp.com", "wsj.com", "ft.com", "nytimes.com",
                  "washingtonpost.com", "cnbc.com", "bbc.co.uk", "bbc.com", "theguardian.com", "economist.com", "cnn.com",
                  "nbcnews.com", "abcnews.go.com", "cbsnews.com", "npr.org", "marketwatch.com", "barrons.com", "forbes.com",
                  "fortune.com", "businessinsider.com", "axios.com", "politico.com", "scmp.com", "nikkei.com",
                  "theverge.com", "techcrunch.com", "wired.com", "arstechnica.com", "latimes.com", "usatoday.com",
                  "foxbusiness.com", "foxnews.com", "aljazeera.com", "dw.com", "france24.com", "japantimes.co.jp",
                  "straitstimes.com", "theaustralian.com.au", "abc.net.au", "cbc.ca", "globeandmail.com", "independent.co.uk",
                  "telegraph.co.uk", "thetimes.co.uk", "time.com", "newsweek.com", "yahoo.com", "investing.com"}
OWNER_FAMILIES = {"iheart.com": "iheartmedia", "patch.com": "patch", "newsquest.co.uk": "newsquest",
                  "gannett.com": "gannett", "msn.com": "microsoft-msn", "yahoo.com": "yahoo"}


def tier(domain: str) -> int:
    d = registrable_domain(domain)
    if d.endswith(".gov") or ".gov." in d or d in PRIMARY:
        return 1
    if d in WIRES_NATIONAL:
        return 2
    return 3


def owner(domain: str) -> str:
    d = registrable_domain(domain)
    return OWNER_FAMILIES.get(d, d)
