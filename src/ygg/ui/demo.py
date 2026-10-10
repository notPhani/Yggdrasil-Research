"""DEMO fixture: a case file with the exact schema 'ygg case' + 'ygg verdict' write, for building and testing the UI
before the replay lands. The market statistics are the measured Jan 27 2025 values; every search, tree, evidence and
verdict value is a fixture. The UI labels anything from here MODE: DEMO, and the module can be deleted without
touching the UI.
"""
from __future__ import annotations

from ygg.ui.domain import Investigation
from ygg.ui.recorded import load_investigation

_STATS = [  # measured 2026-10-05 on Yahoo daily bars (market-only model)
    ("SMH", -0.098, -4.9, -5.0, 4.5, -7.3, True), ("XLK", -0.049, -4.3, -4.5, 3.0, -6.8, True),
    ("NVDA", -0.170, -5.1, -6.3, 6.6, -8.6, True), ("AVGO", -0.174, -5.0, -8.0, 3.3, -10.3, True),
    ("TSM", -0.133, -5.0, -6.1, 4.7, -8.3, True), ("VST", -0.283, -7.8, -8.9, 4.1, -22.2, True),
    ("CEG", -0.208, -5.9, -9.0, 3.2, -19.6, True), ("NRG", -0.132, -5.5, -6.7, 2.3, -9.6, True),
    ("TLN", -0.216, -7.4, -9.5, 3.3, -16.3, True), ("MSFT", -0.021, -0.5, -0.6, 2.7, -9.1, False),
    ("ASML", -0.057, -1.1, -1.7, 3.7, -6.5, False), ("MU", -0.117, -3.0, -3.8, 3.0, -5.4, False),
    ("GOOGL", -0.042, -1.7, -2.0, 1.4, -5.4, False), ("XLU", -0.023, -2.1, -2.4, 2.1, -5.0, False),
]


def demo_case() -> dict:
    stats = [{"symbol": s, "R": r, "SAR": sar, "Mz": mz, "Mv": mv, "Mg": mg, "fired": f} for s, r, sar, mz, mv, mg, f in _STATS]
    n_r1, n_chip, n_pow, n_tar = "d3m0r1aa00000001", "d3m0c41p00000002", "d3m0p0w300000003", "d3m0t4r100000004"
    lab = {n_r1: "DeepSeek releases R1 reasoning model (DEMO)", n_chip: "AI chip demand and export curbs (DEMO)",
           n_pow: "Data-centre power deals (DEMO)", n_tar: "Tariff threats on chips (DEMO)"}
    L = lambda n: f"{n} :: {lab[n]}"
    tree = [{"from": "BOT", "to": L(n_r1), "p": 0.55, "cost_mnats": 900}, {"from": L(n_r1), "to": L(n_chip), "p": 0.45, "cost_mnats": 1100},
            {"from": L(n_r1), "to": L(n_pow), "p": 0.33, "cost_mnats": 1400}, {"from": L(n_chip), "to": "T0", "p": 0.45, "cost_mnats": 1100},
            {"from": L(n_pow), "to": "T1", "p": 0.41, "cost_mnats": 1200}]
    rival = [{"from": "BOT", "to": L(n_tar), "p": 0.12, "cost_mnats": 2420}, {"from": L(n_tar), "to": "T0", "p": 0.19, "cost_mnats": 1961},
             {"from": "BOT", "to": "T1", "p": 0.05, "cost_mnats": 3296}]
    best = sum(e["cost_mnats"] for e in tree)
    rcost = sum(e["cost_mnats"] for e in rival)
    rep = lambda i, src, tier, fs, pre, title, claims=(): {"id": f"r_demo{i:05d}", "source": src, "tier": tier, "owner": src, "group": f"g{i}",
                                                       "first_seen": fs, "pre": pre, "url": f"https://{src}/demo/{i}", "title": title,
                                                       "claims": list(claims), "copy": False}
    cl = lambda p, v, sc, span: {"subject": "deepseek_v3", "predicate": p, "value": v, "scope": sc, "polarity": 1, "report_id": "", "span": span,
                                 "extractor": "rule"}
    h1 = [rep(1, "arxiv.org", 1, "2024-12-27T03:00:00+00:00", True, "DeepSeek-V3 Technical Report (DEMO)",
              [cl("cost_of", "5.6M", "final_run_only", "excluding the costs associated with prior research and ablation experiments")]),
          rep(2, "reuters.com", 2, "2025-01-26T21:15:00+00:00", True, "DeepSeek's cheap model rattles AI investors (DEMO)"),
          rep(3, "example-wire.com", 2, "2025-01-26T23:00:00+00:00", True, "DeepSeek built frontier AI for $5.6M (DEMO)",
              [cl("cost_of", "5.6M", "all_in", "built for just $5.6 million")]),
          rep(4, "bloomberg.com", 2, "2025-01-27T14:02:00+00:00", False, "Nvidia sheds $590B in a day (DEMO)"),
          rep(5, "blog.example.net", 3, None, False, "Why the $5.6M figure misleads (DEMO)")]
    return {
        "cfg_hash": "demo", "notes": ["MODE: DEMO. Market statistics measured; every search, tree, evidence and verdict value is a fixture."],
        "case": {"day": "2025-01-27", "stats": stats, "fired": [s[0] for s in _STATS if s[6]],
                 "clusters": [["SMH", "XLK", "NVDA", "AVGO", "TSM"], ["VST", "CEG", "NRG", "TLN"]],
                 "terminal_clusters": [["SMH", "XLK", "NVDA", "AVGO", "TSM"], ["VST", "CEG", "NRG", "TLN"]],
                 "secondary": ["ASML", "GOOGL", "MSFT", "MU", "XLU"], "tau_star": "2025-01-27T08:00:00+00:00"},
        "search": {"t_snap": 3967, "groups": [{"terminals": ["T0", "T1"], "nodes": 304, "edges": 5120,
                   "best": {"cost_mnats": best, "tree": tree, "abstained_on": []},
                   "abstention_cost_mnats": 6592, "odds_best_vs_abstain": 2.718 ** ((6592 - best) / 1000),
                   "rivals": [{"entry": L(n_tar), "cost_mnats": rcost, "odds_vs_best": 2.718 ** ((rcost - best) / 1000), "tree": rival}],
                   "used_narratives": [n_r1, n_chip, n_pow]}]},
        "placebo": {"k": 20, "fer": 0.05, "p_emp": 1 / 21, "hubs": [["d3m0hub000000005 :: Trump administration (DEMO)", 0.70]],
                    "costs": [6100, 6400, 6592, 6592, 6592, 6592, 6300, 6592, 6592, 6000, 6592, 6592, 5900, 6592, 6592, 6592, 6200, 6592, 6592, 6592]},
        "verdicts": {
            "P_pre": {"verdicts": {"h1": "CONSISTENT-BUT-UNPROVEN", "h3": "CONTRADICTED"}, "bits": {"h1": [0, 0, 0, 0], "h3": [0, 0, 1, 1]},
                      "models": 1, "tight": True, "incoherent": False, "facts": 24, "diagnostic": {"h3": ["reported(r_demo00001, arxiv_org, x, b)."]}},
            "P_all": {"verdicts": {"h1": "SUPPORTED", "h3": "CONTRADICTED"}, "bits": {"h1": [1, 1, 0, 0], "h3": [0, 0, 1, 1]},
                      "models": 1, "tight": True, "incoherent": False, "facts": 31, "diagnostic": {}},
            "hypotheses": [{"hid": "h1", "label": lab[n_r1], "event": "", "signature_ok": True, "burst": True, "surprise_ok": True, "reports": h1[1:3] + h1[3:]},
                           {"hid": "h3", "label": "$5.6M was the full cost of V3 (DEMO)", "event": "", "signature_ok": True, "burst": True,
                            "surprise_ok": False, "reports": h1[:3]}],
            "searches": [{"qid": "q_demo1", "hid": "h3", "query": '"DeepSeek" V3 training cost', "provider": "serpapi", "status": "UNAVAILABLE",
                          "note": "no SERPAPI_API_KEY: evidence from Engine 1 documents and Wayback pages only"}]}}


def demo_investigation() -> Investigation:
    return load_investigation(demo_case(), source="DEMO")
