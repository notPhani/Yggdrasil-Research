# Claims audit, 12 October 2026

This file records what the repository can and cannot claim. Every entry was checked against the code, the tests, or the recorded case files in `data/cases/` (`fixtures/` holds a sanitized copy).

**Status legend.**
- **IMPLEMENTED:** the code does it.
- **TESTED:** a test in `tests/` establishes it.
- **RECORDED:** a historical replay produced it, and it is reproducible from the recorded artifacts.
- **HYPOTHESIS:** a design claim not yet tested.
- **NOT VALIDATED:** no evidence either way.

## Baseline

- **Git.** The working tree was clean. `build` was 2 commits ahead of `origin/build`, both README-only. `origin/main` equals `origin/build` at `c39df35`.
- **Tests.** `pytest -q` gave 86 passed in 28.8 s, run on 12 Oct 2026, before any changes in this pass.
- **CLI.** All commands in the README exist: fetch, fetch-status, ingest, embed, embed-export, embed-import, fit-narratives, replay, case, verdict, ui and tui.

## Discrepancies found

| # | Claim as written | What is true | Status | Action |
|---|---|---|---|---|
| 1 | τ* is "the first abnormal print" (README, UI header, video subtitles) | The observer gates on **daily** bars and derives τ* as the start of the earliest abnormal session: pre-market open for a gap shock, otherwise the regular open, and a fixed 08:00 UTC for Amsterdam. No intraday print is observed. The true move happens at or after τ*, so τ* is a conservative cutoff, not a print. | IMPLEMENTED | Renamed to "event cutoff (session start, daily bars)" |
| 2 | Amsterdam τ* | Hard-coded as 08:00 UTC, which is correct in winter only (09:00 CET) and an hour late in summer (09:00 CEST = 07:00 UTC). It does not affect the January cases. | IMPLEMENTED, bug | Fixed with zoneinfo; test added |
| 3 | SerpApi responses are archived with the key removed | `search()` wrote the **raw** response bytes to the blob store before removing `search_metadata`. It was only safe because SerpApi does not echo the key. A scan found the key in no file under `data/`, in no git object on any branch, and in no export. | IMPLEMENTED, unsafe order | Responses sanitized before writing; regression test with a fake key |
| 4 | "We do not know wins when the evidence is thin" | Abstention is a scored candidate, but it won in **none** of the 42 recorded searches: 2 real cases plus 40 placebo searches, with a false-explanation rate of 1.0 on both days. With p0 = 0.05 and λ = 0.3 it is too expensive to win against chains from a 700-node graph. | RECORDED | Claim removed; calibrating p0 listed as an open question |
| 5 | SerpApi evidence is central to the verdicts | SerpApi results enter the logic program as **claims only**, never as witnesses that the event occurred, so their only possible effect is to refute. In the recorded cases the verdicts are **identical before and after** the 30 searches. Of 158 results, 13 carried a claim extracted from the title. | RECORDED | Its role is described precisely (section 3 of the README) |
| 6 | Claims are extracted from search results | `claims.from_title` applies a small hand-written regex set to the result **title only**. The set covers released, ranks_top, restricts_exports, capability_parity, denies and alleges, and was written with the DeepSeek case in mind. No page text is fetched for search results. | IMPLEMENTED | Disclosed as a hindsight-shaped lexicon |
| 7 | SUPPORTED means the explanation is right | SUPPORTED means the entry narrative's main event in the 48 h before τ* was reported and corroborated, was first seen before τ*, had Yggdrasil's burst and spillover signature, and was not refuted. It says nothing about relevance to the move. On 27 Jan, "What the papers say", a PA newspaper review syndicated to 60 local sites, is SUPPORTED even though its link to the move is p = 0.029. | IMPLEMENTED | Semantics stated wherever verdicts appear |
| 8 | Corroboration needs independent sources | `sources.owner` maps most domains to themselves, so syndicated wire copies on sites with one corporate owner can count as independent. That happened on 27 Jan. | IMPLEMENTED, weakness | Documented as a known failure |
| 9 | Replay is bit-identical across hash seeds (README) | It was verified **manually** during development: day-level runs under PYTHONHASHSEED 1/2 and 11/22 gave identical state. The tests cover the determinism primitives (D1–D7), exact resume and digests, but no test varied the hash seed. | TESTED (primitives) | Seed-independence regression test added |
| 10 | Snapshots are "hash-chained" | Each manifest records `parent_snapshot_id` and an inputs hash. Nothing verifies the chain. | IMPLEMENTED | Wording changed to "record their parent" |
| 11 | Jan 27: "the hypotheses are CONSISTENT-BUT-UNPROVEN" | 5 of 6 are; "What the papers say" is SUPPORTED (see #7). | RECORDED | Corrected |
| 12 | Placebo p = 0.43 and 0.33, FER 1.0 | Recomputed from the recorded per-placebo costs: (1 + #{c ≤ real}) / (1 + K) gives 9/21 = 0.4286 and 7/21 = 0.3333. FER is 1.0 on both days. | RECORDED, reproduced | `ygg verify` recomputes these |
| 13 | The Steiner search finds "the" explanation | DPBF returns the **exact minimum** of a ranking objective, Σ(−ln p + λ), over the recorded graph for at most 8 terminals per group. That is the cheapest chain under the model's edge probabilities, not a causal finding. | IMPLEMENTED | Wording changed; `ygg verify` re-solves the recorded graph |
| 14 | Claims are checked by an NLI cross-encoder and GLiNER (disclosures, UI brief) | `verdicts/verifier.py` implements that stage, but nothing calls it: the recorded verdicts use rule-based claims only (GKG amounts and quotations, title patterns), grounded verbatim in a fetched page when one exists | IMPLEMENTED, unused | Disclosures and brief corrected |

## What the recorded experiments do and do not show

**What they show (RECORDED):**
- The full pipeline runs end to end on a 29-day GDELT replay.
- On 13 Jan it ranks a plausible story first: the Eaton Fire narrative for EIX and PCG.
- On 27 Jan its cheapest chain is not credible, and the verdict layer does not endorse it.
- Placebo statistics show the graph cost is not diagnostic on either day.

**What they do not show:**
- Accuracy over a population of events. There are two cases, chosen after the fact.
- That the method recovers known causes.
- That abstention behaves sensibly.
- That the verdict rules separate relevant from irrelevant events.

These are **NOT VALIDATED**.

## Open research questions

1. **Calibrate the abstention prior p0 and the node penalty λ** so that the false-explanation rate on quiet cutoffs approaches the 0.05 target, without looking at the two recorded cases.
2. **Bound the attention z-score in the link score.** This is failure 1 in the README. Evaluate it on events not yet inspected.
3. **Add relevance to `expl(H)`.** Make it require that the hypothesis's link to the moved cluster clears a threshold.
4. **Fix source independence.** Use real ownership groups and count wire copies once.
5. **Replace the title lexicon with a case-agnostic claim extractor**, evaluated on held-out events.
