# Demo footage: provenance and limits

Every frame in `media/yggdrasil-demo.mp4` and `media/parts/*.gif` comes from the running application, operating on the recorded investigations. No screen was mocked and no output was edited. The only processing is cropping, scaling, and burned-in subtitles.

## How the frames were captured

No screen recorder was available on the build machine, so frames come from the application's own renderers:

| Surface | Capture method |
|---|---|
| Terminal UI (`ygg ui`) | Textual's `save_screenshot` while the app is driven by its test pilot (key presses, row selection, replay), rasterized by headless Firefox |
| Graph window | Headless Firefox on the page served by the app's graph server, with the recorded case loaded. `?focus=<node>` and `?tree=<candidate>` are the page's own deep links |
| `ygg verify` | The command's Rich output, recorded with `Console(record=True)` |
| Animations | The repository's Manim renders (`blueprint/media/`), at 1.75x. Their numbers are illustrative unless marked |

Before rendering, all captured frames were scanned. They contain no SerpApi key, no `api_key` field, and no local filesystem path.

## The capture brief, checked against the implementation

| Brief item | What the real application shows | Used |
|---|---|---|
| Investigation overview | Case id, event cutoff τ* (labelled as a session start from daily bars), detection time, cluster price chart, ranked explanations, hypotheses, verdicts | yes |
| Market event | Cluster leads as % from the close before τ*, and the fired instruments and clusters in the dossier | yes |
| Explanation graph | The recorded graph: best tree, rivals within ln 20, the abstention path, p on edges, a node's incoming and outgoing edges with p, switching between candidates | yes |
| Cost comparison | Nats and odds for every candidate, including "we do not know" | yes |
| Query construction | The F6 trace shows each SerpApi query exactly as sent: `"<subject>" <label>` to confirm, and two disconfirming variants | yes |
| A SerpApi request "visibly sent" | **Not shown live.** Requests are sent by `ygg verdict`, which prints no per-query progress. The trace shows the recorded requests from 10 Oct 2026, each with its status (DONE, SKIPPED by the budget, or ERROR for a timeout) | recorded requests only |
| Search results | Result counts per query, canonical-URL matches and truth-only counts in the trace. In the evidence panels: source domain, first-seen time, title, and its band relative to τ* | yes, domains rather than full URLs |
| Evidence extraction | Rule-extracted claims under each report, grounded verbatim | yes |
| Supporting vs contradictory evidence | **Not implemented as a classification.** Queries are labelled confirm or disconfirm, but results are not classified as supporting or contradicting. A result can only refute through a contrary claim, and none did in the recorded cases. The video shows confirming and disconfirming queries side by side and says no result changed a verdict | queries only |
| Query optimization | **No planning screen exists.** What exists: three fixed templates, a date bound, a per-case budget (skips are shown), cache reuse, and URL dedup within a hypothesis | budget and statuses only |
| Temporal fence | The F3 evidence tab draws the τ* wall: pre-τ* admissible, pre-τ* sighting with post-τ* text (P_all only), post-τ*, and unmatched. On 13 Jan, lawsuits found by search sit after the wall | yes |
| Verdict | Hypothesis table, the brief's verdict section with the definition of SUPPORTED, and the logic tab with the four bits | yes |
| CONSISTENT-BUT-UNPROVEN | 5 of 6 hypotheses on 27 Jan, including both halves of the cheapest chain | yes |
| Why the Pulsar Helium path is cheap | The UI shows the p values (0.95 per link). The reason, an unbounded attention z-score in the link score, comes from reading the code and is not exposed in the UI. The video labels it as a likely cause | caption only |
| Replay | The UI replay re-reveals the recorded state on the case clock. `ygg verify` re-derives the observer, search, verdicts, placebo statistics and archive checks offline | yes |
| Hashes and checkpoints | The fixture's sha256 manifest is checked by `ygg verify`. The audit tab shows the snapshot window. Snapshot hashes are not displayed in the UI | manifest check |
