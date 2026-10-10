# Yggdrasil research

Research and design for **Yggdrasil**, a market event forensics system. Yggdrasil continuously builds a graph of news narratives and the attention each one receives, without regard to any particular stock. When a stock moves abnormally, it searches that graph for competing explanations, labels each one against the evidence (supported, contradicted, consistent but unproven, or unresolved), and certifies the verdicts in Lean 4. It never forecasts prices, and "we do not know" is always an allowed answer.

**Status: hackathon build (SerpApi India Hackathon 2026, Open Innovation). All engines run end to end on a replay of the DeepSeek-R1 / NVIDIA event (27 January 2025), with a live control panel.**

## Code

The implementation lives in `src/ygg/`, a Python 3.12 package with a `ygg` command. Config: `config/default.toml`.

```
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/ygg fetch                  # GDELT 2.0 English stream, 2024-12-16 .. 2025-01-31: 13,533 files, 24.6 GB, md5-verified, resumable
.venv/bin/ygg ingest                 # Engine 1: parse, canonical URLs, exact + semantic dedup, clocks, missing-batch flag
.venv/bin/ygg embed-import DIR --release embeddings-minilm-v1   # MiniLM title vectors computed on a GPU (sha256, id order, CPU parity checked)
.venv/bin/ygg replay                 # Engines 2a + 2b window by window (checkpoint every 3 days; --resume after a crash)
.venv/bin/ygg case 2025-01-27        # stock observer + Engine 3a: clusters, tau*, explanation trees, rivals, abstention, 20 placebos
.venv/bin/ygg verdict 2025-01-27     # Engine 3b: hypotheses, SerpApi evidence (C4), claims, four-bit verdicts, dossier
.venv/bin/ygg ui [--demo]            # terminal: live control panel + investigations; graph window at http://127.0.0.1:8765/
.venv/bin/pytest -q                  # 85 tests: determinism, contracts, red-team cases, engines, SerpApi sensor, adaptive emergence
```

- **SerpApi key.** Engine 3b reads `SERPAPI_API_KEY`. Without it every query is recorded as UNAVAILABLE and the verdict uses Engine 1 documents and Wayback pages only. Adding the key later and rerunning `ygg verdict DAY` fills in the evidence without a replay: targeted results never feed back into Engine 2 (the one-way valve).
- **Replay window.** The clock origin is 2024-12-16; processing runs 2024-12-30 .. 2025-01-28 (a 3-week blind cold start before R1 on 20 January), chosen for the deadline. Threads are pinned (`OMP_NUM_THREADS=2`) and `PYTHONHASHSEED` is irrelevant to the result (verified across seeds).
- **Graph window.** `ygg ui` serves the investigation's recorded explanation graph on 127.0.0.1:8765. On a remote machine forward the port: `ssh -L 8765:localhost:8765 host`.
- **Narratives (2a-L).** κ_s = 250 (the prequential score rises monotonically to 250; data-implied κ 280-310); log α = -15 and T = 2 are defaults, not fitted; splits and merges need 3 consecutive winning checks; at 300 alive narratives the system is full (splits pause, a birth sends the least-recently-active narrative dormant).

Measured on the replay (2024-12-16 .. 2025-01-31):
- Engine 1: 5.80M GKG rows -> 5.77M unique objects (exact dedup) -> 4.01M stories after merging 1.76M syndicated copies (L2); 1 missing GDELT batch, flagged and masked
- Stock observer (universe frozen at 2024-12-31, 149 names): 27 Jan 2025 fires unaided on chips {NVDA, AVGO, TSM, MRVL, CDNS (+SMH, XLK)}, power {VST, CEG, NRG, PEG}, ASM.AS and COHR, with tau* = 08:00 UTC; other January cases are the LA wildfire utilities (EIX, PCG) and earnings reactions
- 2024 acceptance run: cases on 122 of 252 trading days (mostly earnings); search terminals k <= 8 on 251 of 252 days

## Terminal

`ygg ui` opens the control panel; `ygg ui --demo` adds a fixture investigation labelled DEMO.

- **Control panel.** Command line (`NVDA GP`, `CASE 2025-01-13`, `5D`, `C`), watchlist, one central 1-minute price chart (braille line with previous close, VWAP and volume; `C` candles, `D` 1D/5D), quote, the recorded world model (alive/dormant narratives, bursts, edges, BOT share, top narratives), the GDELT feed (latest served batch; the live lag was 45-75 minutes on 10 Oct 2026), investigations, and an F-key bar with the engine status.
- **Investigation.** Verdict first, then the cluster leads as % from the close before τ*, the ranked explanations (click one for its **brief**: claim, why this path edge by edge, what it was tested against, the verdict and the evidence it hinges on, what would change it, limits), the hypotheses and the evidence of the selected one with the τ* wall. F1-F7: overview, story, evidence, logic, placebo, trace, audit. `R` replays the recorded investigation: panels fill only as the replay clock passes the moment each became knowable.
- **Graph window.** http://127.0.0.1:8765/ shows the explanation graph exactly as `ygg case` recorded it, in three views: explanations (BOT, the best tree, rivals, abstention and the candidate stories that reach the cluster, with p on each step), neighborhood (a node with its strongest sources and targets) and full graph (every narrative that can reach the cluster, in rows by hops). `G` in the terminal focuses a node there; clicking a node there selects its hypothesis here.
- The UI never recomputes a result and never moves τ*. The brief is assembled from the recorded case only; no language model writes it.

## Results of the replay (option C, recorded 10 Oct 2026)

- **2025-01-13, Edison International and PG&E.** Best chain: "Eaton Fire death toll rises" into the EIX+PCG cluster, 4.2 : 1 against "we do not know", seven rivals within 20 : 1. P_pre and P_all are SUPPORTED. The verdict hinges on a yahoo.com item ("Investigators probe Eaton Canyon electrical tower area...") first seen 14.5 hours before τ*. Placebos: 20 quiet cutoffs, empirical p = 0.43, false-explanation rate 1.0, so the graph cost alone is not diagnostic here and the dated evidence carries the verdict.
- **2025-01-27, DeepSeek-R1.** 13 instruments fired in four clusters (chips, power producers, ASM International, Coherent); τ* = 08:00 UTC, the Amsterdam open. The cheapest chain is not credible: a dormant "Pulsar Helium" narrative links to three clusters at p = 0.95 and a "Zebrafish protein" narrative to ASM. The safeguards hold: placebo empirical p = 0.33 (false-explanation rate 1.0) and both hypotheses are CONSISTENT-BUT-UNPROVEN. A DeepSeek narrative existed from 20 Jan (hours after the R1 release) with 70 DeepSeek-titled articles before τ*, but it did not win the cluster links.
- **Known failure, not fixed before submission.** The link score adds a robust z of a narrative's last-day attention to log-lift with no bound; for a narrative whose earlier daily attention was near zero the MAD is tiny, so a revived dormant narrative can take almost all link mass for every cluster. This is the likely cause on 27 Jan, from reading the code, not yet measured. A bounded z (MAD floor or clip) is the fix; it was not applied tonight because it would be tuned on the test case.
- One Jan 27 hypothesis, "What the papers say – December 30", is SUPPORTED with a positive signature. It has not been examined yet.

## Disclosures

- **AI tools.** Claude (Anthropic) was used for design, code and documentation.
- **Open models.** sentence-transformers/all-MiniLM-L6-v2 (narrative embeddings, computed on a local GPU and verified against CPU), minishlab/potion-base-8M (near-duplicate step), an NLI cross-encoder and GLiNER in the evidence verifier.
- **Data.** GDELT 2.0 (public), Yahoo chart API (unofficial endpoint, responses archived), Wayback Machine snapshots for evidence pages, SerpApi for targeted evidence (optional key).
- **Not fitted, disclosed.** log α = -15 and the entity temperature T = 2 are defaults; κ_s = 250 is supported by the prequential score and the data-implied κ; the adaptive-emergence terms are calibrated on two warmup days; the 300-narrative ceiling enforces the locked capacity.
- **Scope cut.** Lean certification (stretch) and the live intraday trigger are not implemented; without a SerpApi key, evidence comes from GDELT documents and Wayback pages only.
- **Prior work.** The design and research in this repository's `blueprint/`, `brief/` and `reports/`.

## Contents

| Path | What it is |
|---|---|
| `blueprint/index.html` | **Yggdrasil Blueprint, the final architecture document** (design locked through Session 7 plus 4.2′): every engine's formulas and intermediate terms, parameter sensitivity, stability proofs, extreme cases, terminal mockups, build plan, measured facts and sources |
| `blueprint/media/` | Ten Manim animations (MP4, H.264) with poster frames; the page streams them from the jsDelivr CDN, pinned to commit b30c91e |
| `blueprint/src/` | Page parts, `build.py` (assembles `index.html`), `final_scenes.py` (Manim sources for the five new animations), `verdict_check.py` (the clingo verdict check) |
| `brief/index.html` | Visual brief: key findings, the architecture, the math, and Manim animations, including a 13-chapter film of the whole pipeline |
| `brief/media/` | Rendered animations (MP4, H.264) and poster frames |
| `brief/manim_pipeline.py`, `brief/manim_scenes.py` | Manim sources for the film and the five topic animations |
| `reports/Yggdrasil attention model and search.md` | Full report: architecture from ingestion to search, written as mathematics, with proofs and a ledger of every cited theorem |
| `research_notes/Yggdrasil attention model and search/` | The six research tracks behind the report |

## How claims are labeled

- **PROVEN**: a published theorem, cited, with its conditions stated.
- **DERIVED**: proved in full in the report; not yet independently reviewed.
- **CONJECTURE**: a design hypothesis that the falsification experiments (F1 to F5) must test.
- **MEASURED**: produced from real data (GDELT 2.0, 27 January 2025).
- **EMPIRICAL**: a measured result from the published literature.

## Main results

- **Attention model:** a discrete-time, multivariate softplus Hawkes process on 15-minute windows, with memory traces at 1 h, 6 h, 1 day and 1 week, and a divisive competition factor `(B / (B + S_raw)) ** omega` with `omega` fitted in [0, 1].
- **Conservation is built into the measurement:** soft memberships sum to one, so tracked attention plus a null narrative equals ingested volume exactly. "Semi-conservation" therefore reduces to how strongly narratives compete for predicted supply, which `omega` measures.
- **Transition weights:** Hawkes attribution shares, with unexplained mass routed to an exogenous source node (BOT) that is also the root of every explanation and the "we do not know" answer.
- **Search:** exact dynamic programming (Dreyfus-Wagner / DPBF) on a local subgraph certified by push-style personalized PageRank. When the optimum costs at most a computable threshold, it is the smallest explanation in the whole graph. Levin tree search bounds the effort by depth times exp(surprisal).
- **Verdicts:** evidence as a tight normal logic program with defeasible acceptance of each report; four brave and cautious stable-model queries give the verdict; Lean 4 checks witness models and LRAT refutation proofs.
- **What the research overturned** from earlier plans: subtractive competition, Gaussian-prior MAP, MCTS/PUCT as the search core, the original EC2 bound, and classical entailment over conflicting sources.

## Viewing the documents

- Blueprint (final): https://notphani.github.io/Yggdrasil-Research/blueprint/ (the site root redirects here)
- Earlier research brief: https://notphani.github.io/Yggdrasil-Research/brief/

Both are served by GitHub Pages from the `main` branch root. Locally, open `blueprint/index.html` or `brief/index.html` in a browser; they load fonts and MathJax from public CDNs.

## Re-rendering the animations

The animations use Manim Community 0.20.1 with Pango text only, so no LaTeX installation is needed.

```bash
micromamba create -y -p ./env -c conda-forge python=3.11 manim
./env/bin/manim -qm brief/manim_pipeline.py P00_Overview     # one chapter; P00 to P12
./env/bin/manim -qm brief/manim_scenes.py HawkesBumps        # topic animations
```

The published film concatenates chapters P00 to P12 and pads each frame so captions sit above a browser's video controls:

```bash
ffmpeg -f concat -safe 0 -i list.txt \
  -vf "scale=1138:640:flags=lanczos,pad=1280:720:71:12:color=0x10151b" \
  -c:v libx264 -pix_fmt yuv420p -crf 24 -preset slow -movflags +faststart -an PipelineFilm.mp4
```

## Data and sources

Measurements come from public GDELT 2.0 files for 27 January 2025. All literature is cited inline in the report and notes. Numbers in the animations are illustrative except where marked as measured.

## License

MIT. See `LICENSE`.
