# Red-team verification scripts (2026-10-07)

These scripts settle three claims from the external audits. Results are recorded in the blueprint, §10.

| Script | Claim checked | Result |
|---|---|---|
| `e1_stable.py` | The locked clingo verdict template always has a stable model and stays tight | 0 of 3,000 random programs without a stable model; 0 non-tight. The controls are detected |
| `e2_dpbf.py` | Directed DPBF returns the optimal Steiner arborescence | 0 mismatches against brute force on 400 random directed graphs |
| `e3_qp_nb2.py` | Quasi-Poisson and NB2 estimates diverge | λ gap 0.15–0.26%, about 5× below sampling noise |

Requirements: Python 3.12 with `clingo`, `numpy`, `scipy`. Run `python e1_stable.py 3000`, `python e2_dpbf.py 400` and `python e3_qp_nb2.py`.
