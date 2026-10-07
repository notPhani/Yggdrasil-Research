# Yggdrasil research

Research and design for **Yggdrasil**, a market event forensics system. Yggdrasil continuously builds a graph of news narratives and the attention each one receives, without regard to any particular stock. When a stock moves abnormally, it searches that graph for competing explanations, labels each one against the evidence (supported, contradicted, consistent but unproven, or unresolved), and certifies the verdicts in Lean 4. It never forecasts prices, and "we do not know" is always an allowed answer.

**Status: research and design only. Nothing is implemented yet.**

## Code (hackathon build, in progress)

The implementation lives in `src/ygg/`, a Python 3.12 package with a `ygg` command. Config: `config/default.toml`.

```
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/ygg fetch                  # GDELT 2.0 English stream, 2024-12-16 .. 2025-01-31: 13,533 files, 24.6 GB, md5-verified, resumable
.venv/bin/ygg ingest                 # Engine 1: parse, canonical URLs, exact + semantic dedup, clocks, missing-batch flag
.venv/bin/ygg replay                 # Engines 2a + 2b window by window; snapshots at every case and placebo cutoff
.venv/bin/ygg case 2025-01-27        # stock observer + Engine 3a: clusters, tau*, explanation trees, rivals, abstention
.venv/bin/ygg verdict 2025-01-27     # Engine 3b: hypotheses, evidence, claims, four-bit verdicts, dossier
.venv/bin/pytest -q                  # 60 tests: determinism D1-D7, contracts, red-team E1/E2/A4/A6, engines
```

Measured on the replay (2024-12-16 .. 2025-01-31):
- Engine 1: 5.80M GKG rows -> 5.77M unique objects (exact dedup) -> 4.01M stories after merging 1.76M syndicated copies (L2); 1 missing GDELT batch, flagged and masked
- Stock observer (universe frozen at 2024-12-31, 149 names): 27 Jan 2025 fires unaided on chips {NVDA, AVGO, TSM, MRVL, CDNS (+SMH, XLK)}, power {VST, CEG, NRG, PEG}, ASM.AS and COHR, with tau* = 08:00 UTC; other January cases are the LA wildfire utilities (EIX, PCG) and earnings reactions
- 2024 acceptance run: cases on 122 of 252 trading days (mostly earnings); search terminals k <= 8 on 251 of 252 days

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
