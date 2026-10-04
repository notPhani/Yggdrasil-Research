# Yggdrasil turns attention flows into certified explanations

Yggdrasil can be built as one deterministic function that runs from a content-addressed news archive to Lean-certified verdicts. Every stage of that function rests on either a cited theorem or a proof written out in full here. The stages are:

- exact-key deduplication, with near-duplicates kept only as copy-group annotations;
- narrative identity carried by lineage rules, plus soft membership;
- a discrete-time softplus Hawkes drive under a divisive competition factor whose exponent `omega` is fitted from data rather than assumed;
- Hawkes attribution shares used as a proper transition policy;
- an exact Steiner-arborescence search that produces an optimality certificate for each instance;
- EC2 query allocation with corrected guarantees;
- four-bit stable-model verdicts.

The research overturns five parts of the working proposal: subtractive competition, Gaussian-prior MAP, MCTS/PUCT as the search core, the published EC2 bound, and classical entailment over conflicting sources. Each replacement below comes with its justification.

The deepest structural finding is that Yggdrasil's own measurement already conserves attention. Soft memberships sum to one, so in every window the tracked attention plus the null narrative equals the ingested volume exactly. "Semi-conservation" can therefore only mean how narratives share the predicted supply, and that is exactly what `omega` measures.

The smallest-explanation guarantee is real but conditional. Dynamic programming is exactly optimal on the subgraph it searches. A derived residual bound turns that into a global optimum whenever the optimum's cost falls below a computable threshold. Otherwise the claim is optimality within a probability-bounded class.

A single exogenous-source node does four jobs: it is the Hawkes immigrant source, the root of every explanation, the carrier of new information, and the "we do not know" answer. That is what lets abstention compete on equal terms with every story.

No Hawkes model has yet been fitted to real narrative data, and the notes contain no BTC fit either. Every claim about attention dynamics is therefore a falsification target, and five experiments are specified below to decide them.

## Every statement carries one of five provenance labels

Mathematical and design claims carry one of three labels:

- **[PROVEN]**: a published theorem, cited, with its conditions stated.
- **[DERIVED]**: a result proved in full in this report (some first sketched in the research notes and re-proved here). It is a real proof but has not been independently reviewed.
- **[CONJECTURE]**: a design hypothesis or modeling assumption that experiments must test.

Factual claims about data carry one of two labels, kept separate so that facts about Yggdrasil's own data never blur into literature claims:

- **[MEASURED]**: a number the research team produced from real data, by downloading and parsing all 96 GDELT 2.0 English batches for 2025-01-27 on 2026-10-03.
- **[EMPIRICAL]**: a measured result reported in the published literature.

All mathematics is written in plain-text, Python-style notation inside code blocks. Nothing in this report compares the design with graph neural network methods or claims to outperform them; the choices here are driven by the requirement for proofs and determinism, not by a benchmark comparison.

```
# Global notation
Delta = 15 * 60                      # seconds per window
t                                    # window index; window t = [t0 + t*Delta, t0 + (t+1)*Delta)
o                                    # one canonical observation (document record)
i, j, k in range(1, N + 1)           # tracked narratives at the active level of detail (LOD)
0                                    # null narrative: mass not assigned to any tracked narrative
BOT                                  # exogenous-source node of the explanation graph
m in range(M)                        # kernel timescales; tau[m] in hours; a[m] = exp(-Delta / tau[m])
y[i][t]                              # independence-weighted soft attention mass of narrative i in window t
V[t]                                 # total independence-weighted mass ingested in window t
F[t]                                 # the archive prefix up to the end of window t
softplus(x) = log(1 + exp(x)); sigmoid(x) = 1 / (1 + exp(-x)); pos(x) = max(x, 0)
rho(M)                               # spectral radius of a square matrix M
```

## 1. Five pieces of the working proposal do not survive the literature

| Working proposal | What the research shows | Replacement | Status |
|---|---|---|---|
| Subtractive competition `- kappa * T_recent` inside the linear predictor | Competition with empirical support is proportional. Subtraction distorts ratios between narratives, changes predicted totals when a narrative splits, linearizes pool depletion wrongly, and makes every narrative Granger-cause every other | Multiplicative factor `(B / (B + S_raw)) ** omega`, with `omega` fitted in [0, 1] and capacity `B` taken from predicted supply | Properties DERIVED (Props 6.2, 6.3). Empirical superiority CONJECTURE (experiment F2) |
| Gaussian priors with MAP | Equivalent to ridge: no sparsity, no sign structure, no oracle inequality, across `4 * N**2` coefficients. Unconstrained point-process GLM fits often explode | Convex sparse-group-lasso penalized quasi-likelihood, a tiny ridge for uniqueness, hierarchical centering for cold start, a positive-part stability constraint, and a Laplace approximation for uncertainty | Convexity and uniqueness DERIVED (Lemmas 6.7, 8.1). Oracle guarantees PROVEN for linear Hawkes only; transfer to this model is CONJECTURE |
| MCTS/PUCT as the search core | UCT theory is asymptotic, with a hyper-exponential worst case and an incomplete original proof. PUCT has no finite-sample theorem, fails at low budgets, and cannot see options with near-zero prior | Exact Dreyfus-Wagner/DPBF on a residual-certified local subgraph, plus branch-and-bound seeded by a Levin-tree-search incumbent | DP optimality PROVEN. Certificate DERIVED (Thm 12.6). Levin bound PROVEN |
| EC2 bound `2*ln(1/p_min) + 1` | Derived from a Golovin-Krause theorem whose proof was withdrawn in 2017 | `(2*ln(1/p_min) + 1)**2` via the corrected theorem, or the Esfandiari-Karbasi-Mirrokni bound; `1 - 1/e` for a fixed budget | DERIVED application of PROVEN theorems (Section 13) |
| Classical entailment from reports | Explodes once conflicting claims are accepted; derives nothing if reports are only reified | Tight normal logic program (flat ABA) with defeasible acceptance `ok(r)`; four-bit stable-model verdicts; grounded core; Lean reflection with LRAT | Partition theorem DERIVED (Thm 14.1). Complexity PROVEN |

### Subtractive competition contradicts every competition mechanism with empirical support

The working proposal subtracts a multiple of recent total attention inside the linear predictor. Every competition mechanism with empirical or theoretical support acts proportionally instead:

- **Agenda-setting.** Zhu's zero-sum agenda model is a mass-action exchange. A competing issue draws salience in proportion to the product of salience and coverage ([Zhu 1992](https://fbaum.unc.edu/teaching/PLSC541_Fall06/Zhu%20JQ%201992.pdf)).
- **Attention dynamics.** Lorenz-Spreen et al. model cross-topic competition with a Lotka-Volterra per-capita term ([Lorenz-Spreen et al. 2019](https://doi.org/10.1038/s41467-019-09311-w)).
- **Finite populations.** HawkesN multiplies the entire intensity by the remaining pool fraction ([Rizoiu et al. 2018](https://arxiv.org/abs/1711.01679)).
- **News cycles.** Leskovec's news-cycle model normalizes each source's choice of thread ([Leskovec et al. 2009](https://www.cs.cornell.edu/home/kleinber/kdd09-quotes.pdf)).
- **Markets.** **On high-news days the interdecile spread of earnings-announcement returns shrinks from 7.07% to 5.67%, a proportional dilution of about 20%** **[EMPIRICAL]** ([Hirshleifer, Lim & Teoh 2009](https://mpra.ub.uni-muenchen.de/3110/)).
- **Neuroscience.** Division is the canonical competition operator across sensory systems ([Carandini & Heeger 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3273486)).

Section 6 proves four defects of the subtractive form **[DERIVED]**:

- It distorts ratios between narratives.
- It changes predicted total attention when one narrative is split in two, so it is not closed under level-of-detail compression.
- It matches resource depletion only when the coefficient is proportional to each narrative's own drive, which is division in disguise.
- It routes every narrative's history into every other narrative's intensity, so every narrative Granger-causes every other by construction.

The replacement is a multiplicative factor with a fitted exponent. It nests "no competition" (`omega = 0`) and "hard capacity" (`omega = 1`), so semi-conservation becomes a measured quantity rather than an assumption.

### Gaussian-prior MAP gives neither sparsity nor guarantees

With N narratives and four timescales the cross-scale tensor has `4 * N**2` coefficients. Gaussian priors at the MAP are ridge regression: they shrink coefficients but never zero any of them, impose no sign structure, and come with no oracle inequality. The literature offers alternatives with stronger properties:

- **Oracle guarantees.** A weighted lasso with data-driven weights has a non-asymptotic oracle inequality for linear multivariate point processes **[PROVEN]** ([Hansen, Reynaud-Bouret & Rivoirard 2015](https://arxiv.org/abs/1208.0570)). l1 plus trace-norm penalties on a dictionary of unit-mass exponentials (Yggdrasil's exact kernel structure) have a sharp oracle inequality **[PROVEN]** ([Bacry et al. 2020](https://arxiv.org/abs/1501.00725)).
- **Network priors.** Spike-and-slab network priors with stability-aware hyperparameters are the Bayesian counterpart ([Linderman & Adams 2014](https://arxiv.org/abs/1402.0914)).
- **Stability.** **Data-fitted point-process GLMs with exponential links diverged in simulation in 35 of 99 cases even when they passed goodness-of-fit tests** **[EMPIRICAL]** ([Gerhard, Deger & Truccolo 2017](https://doi.org/10.1371/journal.pcbi.1005390)).

The replacement is a sparse-group lasso in the style of Xu, Farajtabar and Zha ([2016](https://arxiv.org/abs/1602.04511)). Each group is all timescales of one ordered narrative pair, so a zero group is exactly a Granger non-edge. On top of that:

- the penalty is centered on hierarchical prior means for cold start;
- a tiny ridge makes the minimizer unique;
- a positive-part stability constraint is enforced.

Section 6 proves that the objective is convex in the linear predictor. The oracle theorems above cover linear Hawkes with least-squares contrasts; that they carry over to a softplus quasi-Poisson model is **[CONJECTURE]**.

### MCTS/PUCT solves a different problem from explanation search

The theoretical record for tree-search methods of this family is weak:

- **UCT.** Its guarantee is that the root failure probability tends to zero at a polynomial rate as the number of episodes grows without bound **[PROVEN]** ([Kocsis & Szepesvári 2006](http://ggp.stanford.edu/readings/uct.pdf)). Its worst-case regret involves D-1 nested exponentials in the depth D ([Coquelin & Munos 2007](https://arxiv.org/abs/cs/0703062)). The original logarithmic-bonus argument is incomplete, and a polynomial bonus recovers only an `O(n**(-1/2))` value-error rate ([Shah, Xie & Xu 2020](https://arxiv.org/abs/1902.05213)).
- **PUCT.** The AlphaZero rule approximately tracks a regularized policy-optimization problem and can fail at low simulation budgets ([Grill et al. 2020](https://arxiv.org/abs/2007.12509)). AlphaZero can fail to improve its policy when it does not visit all root actions ([Danihelka et al. 2022](https://iclr.cc/virtual/2022/poster/6418)).
- **Prior blindness.** The prior multiplies the exploration bonus, so a wrong Hawkes prior near zero blinds the search to the true explanation.

Explanation search is a deterministic combinatorial optimization with a known additive objective, so exact dynamic programming and branch-and-bound apply directly. The prior-dependent guarantee the user wants comes from Levin tree search. Its expansions are bounded by the depth of the easiest goal divided by that goal's policy probability **[PROVEN]** ([Orseau et al. 2018](https://arxiv.org/abs/1811.10928)). With transition weights as the policy, search effort therefore grows as the exponential of the explanation's surprisal (Section 12).

### The published EC2 bound rests on a withdrawn proof

Golovin, Krause and Ray's `2*ln(1/p_min) + 1` guarantee for EC2 was obtained by applying the then-current Golovin-Krause min-cost-cover theorem ([Golovin, Krause & Ray 2010](https://arxiv.org/abs/1010.3091)). Version 5 of Golovin-Krause states that this proof was flawed, as pointed out by Nan and Saligrama in 2017. It proves squared logarithms instead and leaves the unsquared bound open ([Golovin & Krause v5](https://arxiv.org/abs/1003.3967)). Section 13 derives the bounds that can be cited today:

- `(2*ln(1/p_min) + 1)**2`;
- the Esfandiari-Karbasi-Mirrokni logarithmic bound ([Esfandiari, Karbasi & Mirrokni 2020](https://arxiv.org/abs/1911.03620));
- a `1 - 1/e` guarantee for a fixed query budget.

### Classical entailment over conflicting sources either explodes or derives nothing

Reifying reports, as in "source s reported phi", is classically consistent but inert: nothing about the world follows from it. Adding a classical bridge from reports to claims brings back explosion, since conflicting accepted claims entail everything ([SEP, Paraconsistent Logic](https://plato.stanford.edu/entries/logic-paraconsistent/)). In answer set programming the same failure shows up as having no answer set at all.

The replacement makes acceptance defeasible. It uses one assumption per report, attacked by contraries, undercutters and preferences, and reads verdicts from four brave and cautious queries over stable models. Flat ABA under stable semantics is NP-complete for credulous and coNP-complete for skeptical reasoning **[PROVEN]** ([Dimopoulos, Nebel & Toni 2002](https://doi.org/10.1016/S0004-3702(02)00245-X)). Incremental AGM revision is rejected for two reasons:

- iterated revision depends on the order in which news arrives;
- entailment from a revised base is Pi2P-complete for most operators **[PROVEN]** ([Eiter & Gottlob 1992](https://doi.org/10.1016/0004-3702(92)90018-S)).

### Six smaller corrections

1. **Keep the link; avoid the exponential.** The proposal's scaled softplus link is the right choice; it is used verbatim in neural Hawkes models ([Mei & Eisner 2017](https://arxiv.org/abs/1612.09328)). Exponential links should be avoided for excitation.
2. **The binning bias is smaller than the notes state, and correctable.** The notes say 22% of a 1-hour kernel's mass falls inside one 15-minute bin. That holds only for a parent event at the very start of its bin. For a parent placed uniformly within its bin, the same-bin fraction is 11.5%. The discrete trace also reproduces the shape at all lags of one bin or more exactly, so the bias is a known factor of 0.885 (Lemma 6.6) **[DERIVED]**.
3. **GDELT cannot support a continuous-time fit.** The notes suggest fitting continuous-time Hawkes processes on raw timestamps, but GKG's V2.1DATE is the batch timestamp, identical for every row of a file ([GKG Codebook V2.1](http://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf)). Only RSS carries sub-batch times, and those are self-reported.
4. **Hawkes coefficients measure offspring, not transfer.** A unit of attention on j that begets attention on i is not removed from j, and first moments identify only offspring plus transfer (Lemma 7.4) **[DERIVED]**.
5. **Z3 does not belong in the certified path.** For finite propositional verdicts, SAT with LRAT checking has the shortest trust chain.
6. **GDELT first-sighting counts are not attention measures.** NumMentions and NumSources are computed only in the 15-minute batch where an event is first seen ([Event Codebook V2.0](http://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf)). On the measured day, 97.1% of events had NumSources = 1 **[MEASURED]**.

## 2. What has actually been measured, and what has not

The only real-data measurements in the notes come from one day of GDELT 2.0 English data: all 96 batches of GKG, Events and Mentions for 2025-01-27, parsed with polars on a 4-core, 15 GB machine. Sources are the raw files themselves, for example [the 12:00 GKG batch](https://data.gdeltproject.org/gdeltv2/20250127120000.gkg.csv.zip), [its Translingual twin](https://data.gdeltproject.org/gdeltv2/20250127120000.translation.gkg.csv.zip), [the Events export](https://data.gdeltproject.org/gdeltv2/20250127120000.export.CSV.zip) and [the Mentions file](https://data.gdeltproject.org/gdeltv2/20250127120000.mentions.CSV.zip). Every number in the table is **[MEASURED]**.

| Quantity (2025-01-27 unless noted) | Value | Design implication |
|---|---|---|
| English GKG records | 130,852 (about 1,363 per batch); all IDs unique; 7,828 distinct source names | One row per document; GDELT does not deduplicate GKG |
| GKG English size | 533.9 MB zipped, 1,653.6 MB unzipped | Download once into a content-addressed archive |
| GKG Translingual | 908.6 MB zipped; the 12:00 batch had 3,735 translated vs 1,326 English records | English-only dropped about 74% of that batch's documents |
| Events and Mentions rows | 130,388 and 378,225 | Events are a derived annotation |
| Events with NumSources = 1 at first sighting | 97.1% (p99 = 2) | First-batch counts are useless as attention |
| Events sharing (Day, Actor1, Actor2, EventCode, FeatureID) with another event | 13.0% | GlobalEventID is not content identity |
| Mentions pointing to events first seen in an earlier batch | 63.1% (0.54% to events older than 24 h) | Use Mentions, not first-batch counts |
| Mention Confidence | median 40; 23.4% at 70 or above; 48.8% InRawText = 1 | Report a high-precision variant separately |
| Documents producing any coded event | 53,645, about 41% of GKG documents | Count documents, not CAMEO events |
| Extra URL merges from canonicalization | 447 (0.34%); raw duplicate URLs 0 | URL keys matter mostly across feeds |
| Metadata-identical documents | 19.0% of documents with non-trivial metadata (16.4% if tone must also match); 6,248 groups, 4,508 multi-source; one story on 271 and 233 iHeart subdomains | Syndication is large, but metadata also groups non-copies |
| MinHash and SimHash on GKG metadata | 44% of 20,000 documents flagged at J >= 0.8; 303,929 pairs within Hamming distance 3 | Metadata hashing over-merges and cannot define identity |
| Documents matching "deepseek" | 1,417 from 681 sources; peak 47 per batch | Low-count regime |
| Documents matching "nvidia" | 1,863 from 790 sources; peak 55 per batch | Low-count regime |
| Documents with theme ECON_STOCKMARKET | 6,183 | |
| Parse and benchmark time | 11.5 s per English GKG day (about 11,400 records/s); full one-day benchmark 21 s; peak RSS about 2.1 GB | A 3-week replay parses in about 4-5 minutes |
| Dedup throughput | URL canonicalization about 61,600/s; MinHash about 9,300 docs/s; SimHash about 26,900 docs/s with numpy | Pure Python suffices for fetched text |
| Columnar storage | 16.9 MB per day as 8-column Parquet | 3 weeks is about 0.36 GB |
| Live batch, 2026-10-03 19:00 UTC | 2.50 MB zipped vs a 5.56 MB per-batch mean on 2025-01-27 | One data point; coverage drift cannot be ruled out |

Several things were not measured:

- GDELT volumes for 2025-01-20 through 2025-01-26. This leaves the DeepSeek attention ramp before the NVIDIA drop unquantified, and it is the single most important data gap for the proof-of-concept.
- RSS volumes and SerpApi query budgets.
- Embedding and entity-linking throughput.
- Any intraday NVIDIA price statistic: SAR, Lee-Mykland, volume.

**The notes contain no BTC Hawkes fit results, and no Hawkes model of any kind has been fitted to real data in this research**, so no fitted parameter appears anywhere below. One consequence of the measured counts is physical rather than statistical. At about 50 documents per window for the day's top story, Poisson shot noise is about 1/sqrt(47), or 15% relative error **[DERIVED arithmetic]**. That is comparable to membership uncertainty, so the attention model must carry measurement variance explicitly.

## 3. The architecture is one deterministic function from archive to verdict

```
S0  adapters        GDELT 15-min batches (GKG, Events, Mentions) | RSS polled on the window grid | SerpApi on demand
                    raw blobs stored under sha256, GDELT zips verified against manifest md5
S1  dedup           exact-key cascade -> canonical observations; SimHash / MinHash -> copy groups; weights v[o]
S2  clocks          event / published / observed / ingested / first_seen; window(o); admissibility at a cutoff
S3  L1 events       single-pass LSH clustering, fixed seeds, fixed processing order
S4  L2 narratives   windowed deterministic clustering + MONIC lineage; soft membership p[o][n]; y[n][t]
S5  attention       traces z; drive eta; softplus; divisive competition with fitted omega; quasi-Poisson
S6  spawning        residual change detection -> exogenous bursts; emerge / split / merge -> cold-start priors
S7  update          per-window proximal step; periodic convex refit with stability constraint
S8  LOD             lumpability defect + closure test -> collapse / expand
S9  weights         attribution shares alpha -> horizon edge weights p_H(u -> v), including BOT
S10 trigger         SAR, robust z, Lee-Mykland, volume, cluster -> forensic case + cutoff tau_star
S11 explanation     graph G_tau; costs -log p; prizes; abstention edge BOT -> e_star
S12 search          push-PPR locality -> Levin incumbent -> DPBF with branch-and-bound -> certificate
S13 queries         EC2 over competing explanations; SerpApi; leakage-aware admissibility; stopping
S14 verdicts        ground tight programs P_pre and P_all; brave/cautious bits; grounded core
S15 certification   witnesses + LRAT + DP subsolution tables -> Lean 4 theorems; #print axioms audit
S16 report          competing explanations, verdicts, provenance, pre/post split, or "we do not know"
```

Determinism is a property of the whole chain, not of each stage in isolation. The theorem below states the conditions under which the chain is a pure function of its inputs.

```
# Theorem 3.1 (end-to-end replay determinism) [DERIVED]
# Let x[0], x[1], ... be the archived input records (raw blobs plus archived model outputs) sorted by the
# total order key(x) = (observed_time, source_rank, url_key, record_id). Let cfg be the frozen configuration:
# canonicalization rules, tracker list, shingle sizes, seeds, thresholds, model hashes, IDF and centroid
# snapshots, and solver versions. Suppose every stage is a state map st[n+1] = Phi(st[n], x[n], cfg) with
#   (D1) no wall-clock reads (replay sets ingested_time = observed_time + LAG),
#   (D2) every random draw taken from Philox(key = h(cfg, record ids), counter = draw index),
#   (D3) every floating-point reduction run in a fixed order, on a fixed binary, with pinned thread counts,
#   (D4) every tie (clustering, lineage, witness choice, core extraction) broken by a fixed key.
# Then every derived table and every verdict is a function of (x, cfg).
#
# Proof. Induction on n. st[0] = init(cfg) depends only on cfg. Suppose st[n] is a function of
# (x[:n], cfg). Then st[n+1] = Phi(st[n], x[n], cfg) is a function of (x[:n+1], cfg) as long as Phi depends
# only on its arguments:
#   (D1) removes dependence on the clock,
#   (D2) removes dependence on process RNG state,
#   (D3) removes dependence on reduction order,
#   (D4) removes dependence on the iteration order of unordered containers.
# Every output is a projection of a state. QED
#
# Remark. Rounding scores to a grid before threshold tests protects against last-bit differences across
# platforms, but it cannot help values that straddle a grid boundary. The guarantee comes from (D3), not
# from rounding.
```

Two consequences shape the rest of the design.

- **LLM output is archived input, not computation.** Any LLM-based claim extraction must be archived as an input record with its model hash. Replay reads the archived outputs and never re-runs the model.
- **Verdicts satisfy a stronger determinism.** They are defined by quantifying over all stable models of a ground program (Section 14), so any correct solver returns the same verdict. Operational determinism (which witness gets reported) is needed only for provenance.

## 4. Exact keys collapse observations; near-duplicates only annotate

### Ingestion turns every raw byte into an addressed, idempotent record

Three adapters feed one envelope:

- **GDELT.** The adapter polls the 15-minute manifests. They list each file as size, md5 and URL, and on 2026-10-03 the Translingual manifest ran one batch behind the English one ([GDELT lastupdate.txt](https://data.gdeltproject.org/gdeltv2/lastupdate.txt)).
- **RSS.** The adapter polls on the same window grid.
- **SerpApi.** It runs only when the query allocator in Section 13 asks for it.

GDELT IDs serve only as idempotency keys and are never treated as content identity. GKGRECORDID is a batch timestamp plus a serial ([GKG Codebook V2.1](http://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf)), and GlobalEventID "should NOT be used to sort events by date" ([Event Codebook V2.0](http://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf)).

Every identifier is a hash of content, so replays and re-downloads are no-ops:

```
raw_blob_id    = sha256(raw_bytes)                          # GDELT zip, RSS XML, SerpApi JSON
url_key        = sha256(canon(url))                         # canon defined below, rule set frozen in cfg
content_hash   = sha256(nfkc_lower_collapse_ws_strip_boilerplate(body)) if body else ""
observation_id = sha256(source_type + "|" + native_id + "|" + url_key + "|" + content_hash)

# exact-key cascade, first match wins; only these matches collapse records into one canonical observation
def canonical_of(o, index):
    for key in (("native", o.source_type, o.native_id), ("url", o.url_key), ("content", o.content_hash)):
        if key[-1] and key in index:
            return index[key]               # existing canonical observation (first seen in the total order)
    return o.observation_id                 # o becomes a new canonical observation
```

URL canonicalization does the following:

- lowercases scheme and host, forces https, and IDNA-encodes the host;
- strips leading "www.", "m." and "amp.", and default ports;
- collapses duplicate slashes, and strips trailing "/" and "/amp";
- drops the fragment and tracker keys (utm_*, fbclid, gclid and a frozen list of others);
- sorts the remaining query keys and uppercases percent-encoding.

This follows w3lib practice and RFC 3986 normalization ([RFC 3986 §6](https://www.rfc-editor.org/rfc/rfc3986#section-6)). On the measured day it merged 447 additional URLs (0.34%) among English GKG documents that had no raw duplicates **[MEASURED]**. Its real value is cross-feed: the same article seen through GDELT, RSS and SerpApi.

Neither NATS JetStream nor Kafka gives exactly-once processing into external state:

- JetStream deduplicates only on the message-ID header and only within a window that defaults to two minutes ([NATS docs](https://docs.nats.io/nats-concepts/jetstream/streams)).
- Kafka gives idempotent producers and transactions inside Kafka ([KIP-98](https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging)).

Consumers must therefore upsert by observation_id. With that rule, idempotence holds regardless of broker windows **[DERIVED]**: applying the same keyed upsert twice leaves the table unchanged.

### Near-duplicate detection is exact given its fingerprints

Near-exact copies are detected with 64-bit SimHash over word 3-shingles with term-frequency weights. Features are hashed with xxh64 at seed 0, never Python's per-process salted hash(). Random-hyperplane hashing collides per bit with probability 1 - theta/pi, where theta is the angle between feature vectors **[PROVEN]** ([Charikar 2002](https://www.cs.princeton.edu/courses/archive/spr04/cos598B/bib/CharikarEstim.pdf)). For 8 billion pages, 64-bit fingerprints with k = 3 gave precision and recall near 0.75 **[EMPIRICAL]** ([Manku, Jain & Das Sarma 2007](https://research.google.com/pubs/archive/33026.pdf)). A Hamming distance of 3 out of 64 bits corresponds to an angle of about 3*pi/64, a cosine of about 0.989, so this stage catches only near-verbatim reposts **[DERIVED arithmetic]**.

```
# Lemma 4.1 (pigeonhole index has exact recall at k = 3) [DERIVED]
# Split 64-bit fingerprints f1, f2 into 4 blocks of 16 bits. If hamming(f1, f2) <= 3, then f1 and f2 are
# identical on at least one block.
# Proof. The at most 3 differing bit positions fall in at most 3 of the 4 blocks, so at least one block holds
# no differing position and is identical in f1 and f2. QED
# Consequence: probing the 4 block tables returns every pair within distance 3. Acceptance is decided by
# exact Hamming computation, so the accepted pair set is a deterministic function of the fingerprints.
```

Edited syndication is detected with MinHash: 128 permutations at fixed seed 1, over 5-word shingles, the n-gram size used in news text-reuse work ([Nicholls 2019](https://ijoc.org/index.php/ijoc/article/view/9904)). Wire copy is mostly recombined rather than copied verbatim: in one 2026 study only 4.4% of aligned agency-to-outlet pairs were 1:1 **[EMPIRICAL]** ([Kuntur et al. 2026](https://arxiv.org/html/2603.29937v1)). Banded LSH proposes candidates with the S-curve below, which holds under ideal min-wise hashing **[PROVEN]** ([datasketch LSH](https://ekzhu.com/datasketch/lsh.html)).

```
P_candidate(s) = 1 - (1 - s**r)**b               # s = Jaccard similarity of shingle sets
# with b = 14, r = 9 (LSH threshold 0.7):  P(0.7) = 0.438, P(0.8) = 0.867, P(0.9) = 0.999   [DERIVED arithmetic]
accept_copy(A, B) = jaccard(S5(A), S5(B)) >= 0.8 or containment7(A, B) >= 0.5
containment7(A, B) = len(S7(A) & S7(B)) / len(S7(A))     # A derivative of B
```

LSH only affects recall. Exact Jaccard and containment on the candidates decide acceptance, so decisions are deterministic given the shingle definition, and recall itself is reproducible because the seeds are fixed.

Accepted pairs form copy groups by union-find, and each group's root is the member with the minimal total-order key. Near-duplicates are never deleted. They only annotate, so dedup decisions stay auditable and reversible.

GKG rows have no body text. For them, the measured over-merging rules out metadata hashing as identity (44% of documents flagged by MinHash at J >= 0.8, and 303,929 SimHash pairs within distance 3 among 20,000 documents, in both cases because GKG themes are a coarse controlled vocabulary **[MEASURED]**). GKG-only documents therefore get only exact keys plus a metadata-signature syndication flag.

### Independence weights count witnesses, not copies

Attention should count independent reports. Corporate syndicates can account for hundreds of URLs carrying one story, as with the 271 iHeart subdomains on the measured day **[MEASURED]**. Copying is also how errors spread: shared false values are evidence of dependence between sources ([Dong, Berti-Equille & Srivastava 2009](https://doi.org/10.14778/1687627.1687690)). The weight rule below is causal (it never looks ahead) and deterministic:

```
alpha_copy = 0.1                                       # disclosed in cfg
v[o] = 1.0         if no o2 with key(o2) < key(o) is an accepted near-duplicate of o (after owner-map collapse)
v[o] = alpha_copy  otherwise

# Lemma 4.2 (group mass) [DERIVED]
# If every member of a copy group after the first is an accepted near-duplicate of some earlier member, the
# group contributes 1 + alpha_copy * (n_g - 1) to any count that sums v.
# Proof. The first member in the total order has no earlier duplicate and gets weight 1. Every other member
# has an earlier duplicate and gets alpha_copy. Sum the weights. QED
```

A group formed by later merging two previously separate groups contributes two units of weight 1. That is the conservative choice under the causal rule. Both raw counts and weighted counts are reported to the attention layer.

### Four clocks and one admissibility rule

```
event_time[o]     # when the reported thing happened; GDELT Events.Day (daily), often None for GKG
published_time[o] # source-claimed time (RSS pubDate, page metadata); None for GDELT GKG
observed_time[o]  # GDELT batch timestamp (GKG DATE = DATEADDED = MentionTimeDate); RSS / SerpApi fetch time
ingested_time[o]  # replay: observed_time[o] + LAG, LAG = 15 min (disclosed); live: Yggdrasil clock
first_seen[o]     # min of ingested_time over all exact-key duplicates of o: the admissibility clock
window(o)         = floor((observed_time[o] - t0) / Delta)

admissible(o, tau) = first_seen[o] < tau            # evidence that can have moved a price at time tau
```

The codebooks fix what each clock can mean:

- GDELT 2.0 provides no per-article publication time. GKG V2.1DATE is the batch timestamp, the same for all rows of a file ([GKG Codebook V2.1](http://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf)).
- For Events, DATEADDED is "the field that should be used" at 15-minute resolution ([Event Codebook V2.0](http://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf)).

Admissibility uses Yggdrasil's own first-seen clock, never self-reported publication dates. In a 2026 audit of Google's date-restricted search, **71% of questions returned at least one page with substantial post-cutoff information, and 41% returned a page revealing the answer**. Stale or edited self-reported timestamps were among the causes **[EMPIRICAL]** ([El Lahib et al. 2026](https://arxiv.org/html/2602.00758v1)). The human-coded benchmark makes the same choice: it uses only articles published before the market reopens ([Baker, Bloom, Davis & Sammon, rev. 2025](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf)).

The rule is design, but its consequence is exact **[DERIVED]**: an observation that Yggdrasil first saw after the cutoff cannot enter the program that judges what moved the price (Section 14), however its page is dated.

## 5. Narratives keep their identity through lineage, not re-clustering

### Event clusters come from single-pass clustering with fixed seeds

Level L1 groups observations into event clusters. It uses the first-story-detection design: assign each document to its nearest neighbor's cluster unless the similarity falls below a novelty threshold, and make retrieval constant-time with random-hyperplane LSH ([Petrović, Osborne & Lavrenko 2010](https://aclanthology.org/N10-1021.pdf)). The feature mix follows the production-style news clusterer of Miranda et al.: TF-IDF over words and entities plus a Gaussian time kernel with sigma = 72 h ([Miranda et al. 2018](https://aclanthology.org/D18-1483.pdf)).

For GKG-only rows, which have no body, the text features are themes, persons, organizations and URL-slug tokens. IDF is frozen from a pre-window snapshot. Hyperplanes come from Philox with a fixed key, and documents are processed in total-order key order, so the clusters are reproducible bit for bit (Theorem 3.1).

```
sim(o, c) = (w_txt * cos(tfidf(o), centroid_txt[c]) + w_ent * jaccard(ents(o), ents[c])) \
            * exp(-(hours(o) - hours(c))**2 / (2 * 72**2))
assign(o) = argmax(sim(o, c) for c in lsh_candidates(o)) if max_sim >= tau_new else new_cluster(o)
# LSH sizing for cosine 0.8 with k = 13 bits per table and a 2.5% miss target          [DERIVED arithmetic]
P_coll = 1 - acos(0.8) / pi                    # = 0.7952
L = ceil(log(0.025) / log(1 - P_coll**13))     # = 71 tables
```

Neural cross-document event coreference is not used for identity. It reaches only about 80 CoNLL F1 on ECB+ even with gold mentions **[EMPIRICAL]** ([X-AMR 2024](https://arxiv.org/pdf/2404.08656)), so it serves at most as optional edge evidence between clusters.

### Narratives are windowed clusters whose IDs pass along lineage edges

Off-the-shelf methods do not give stable narrative identity in a stream:

- Dynamic topic models fix the number of topics ([Blei & Lafferty 2006](https://www.cs.columbia.edu/~blei/papers/BleiLafferty2006a.pdf)).
- BERTopic's topics-over-time keeps global topics fixed and only re-describes them per bin ([BERTopic docs](https://maartengr.github.io/BERTopic/getting_started/topicsovertime/topicsovertime.html)).
- DP-means is the small-variance limit of a Dirichlet-process mixture, and its objective (sum of squared distances plus lambda times the number of clusters) decreases monotonically. Unlike k-means, though, it depends on the order in which points are processed **[PROVEN]** ([Kulis & Jordan 2012](https://arxiv.org/pdf/1111.0352)).

Yggdrasil therefore clusters event clusters per window W (24 h, recomputed every 6 h). It uses DP-means with a fixed lambda and a fixed processing order, then matches windows by observation overlap with MONIC transitions ([Spiliopoulou et al. 2006](https://researchr.org/publication/SpiliopoulouNTS06/bibtex)) and many-to-many Jaccard matching ([Greene, Doyle & Cunningham 2010](https://research.google/pubs/tracking-the-evolution-of-communities-in-dynamic-social-networks/)).

```
J(C, N) = len(obs(C) & obs(N)) / len(obs(C) | obs(N))      # new candidate C vs alive narrative N
edges   = {(C, N) : J(C, N) >= J0}                         # J0 tuned once on the PoC window, then frozen
# fixed precedence: merges are resolved first, then splits; every tie is broken by min(key)
merge   : len(parents(C)) > 1   -> C takes the id of its oldest parent; the other parents get merged_into = C
split   : len(children(N)) > 1  -> the child with max overlap keeps id(N); the others get new ids with parent = N
survive : one-to-one            -> id(C) = id(N)
emerge  : parents(C) empty      -> id(C) = sha256(sorted(obs(C)) + str(window))   # content-derived new id
dormant : children(N) empty     -> state = dormant; state = disappeared after M_dorm windows
# every transition is stored as an immutable lineage edge
```

Under this precedence and tie-breaking, the ID map is a function of the two clusterings **[DERIVED]**: each rule's output depends only on overlap sets and fixed keys. Narrative maps (a linear program over about 100 articles) and RELATIO's agent-verb-patient triples are kept for offline description of a narrative's internal structure, not for streaming identity ([Keith Norambuena & Mitra 2020](https://faculty.washington.edu/tmitra/public/papers/cscw2020-narrativeMaps.pdf)).

### Soft membership includes an explicit null narrative

```
s[o][n] = cos(x[o], mu[n][w])          # mu frozen at the start of window w: membership never depends on arrival order
Z[o]    = exp(s0 / T) + sum(exp(s[o][k] / T) for k in top_m(o))        # m = 3 candidates
p[o][n] = exp(s[o][n] / T) / Z[o]      for n in top_m(o)
p[o][0] = exp(s0 / T) / Z[o]           # null narrative
# T and s0 are fitted once by negative log-likelihood on 200-500 labeled (observation, narrative) pairs, then frozen
```

Fitting one temperature on held-out data is the standard post-hoc calibration ([Guo et al. 2017](https://arxiv.org/abs/1706.04599)). Attention mass and its measurement variance follow from treating each observation's membership as a weighted Bernoulli draw. For independent Bernoulli(p) variables the sum has mean sum(p) and variance sum(p*(1-p)) **[PROVEN]** ([Poisson binomial](https://en.wikipedia.org/wiki/Poisson_binomial_distribution)). Scaling each draw by v gives the weighted version **[DERIVED]**: Var(v*X) = v**2 * p * (1-p), and independent variances add.

```
y[n][t]     = sum(p[o][n] * v[o] for o in window t)
Vmeas[n][t] = sum(p[o][n] * (1 - p[o][n]) * v[o]**2 for o in window t)   # lower bound if memberships co-move
V[t]        = sum(v[o] for o in window t)
```

The null option is not a technicality. It is where the conservation question lives.

```
# Lemma 5.1 (reservoir identity) [DERIVED]
# For every window t:  sum(y[n][t] for n in range(1, N + 1)) + y[0][t] == V[t].
# Proof. For each observation o, the probabilities p[o][n] over top_m(o) plus p[o][0] sum to 1 by
# construction of Z[o] (narratives outside top_m(o) get 0). Hence
#   sum over n of y[n][t] = sum over o of v[o] * (sum over n of p[o][n]) = sum over o of v[o] = V[t]. QED
```

Lemma 5.1 says that tracked attention plus the null narrative is conserved exactly in every window, and that this conservation is put there by the measurement. V[t] is set by ingestion: how many outlets GDELT crawls, diurnal publishing cycles, and coverage drift such as the 2.50 MB versus 5.56 MB batch sizes measured above. Any conservation found by summing y over all nodes is an identity, not a finding about attention.

The design response is to give the attention model a *predicted* supply as an exogenous capacity, and to define semi-conservation as a property of how tracked narratives share that supply (Section 6.7).

Physically, the tracked narratives are an open system exchanging attention with a reservoir: the null narrative plus everything GDELT never ingests. That is the grand-canonical picture, in which the system's particle number fluctuates while the system-plus-reservoir total is fixed from outside. It is also Hofbauer's construction: Lotka-Volterra dynamics on n species are equivalent to replicator dynamics on n+1 strategies, where the extra strategy plays the reservoir **[PROVEN, via secondary sources]** ([higher-order equivalence preprint, 2025](https://www.biorxiv.org/content/10.1101/2025.03.28.645916.full.pdf)).

### Splits and merges carry attention memory forward without creating or destroying it

```
# split: N -> children C_1..C_K, with overlap shares q[c] = len(obs(c) & obs(N)) / sum(len(obs(c2) & obs(N)) for c2)
z[c][m][t] = q[c] * z[N][m][t]
# merge: N_1..N_K -> C
z[C][m][t] = sum(z[N_l][m][t] for l in range(K))

# Lemma 5.2 (trace conservation under lineage operations) [DERIVED]
# For every timescale m, a split preserves the sum of z[.][m][t] over the lineage, and so does a merge.
# Proof. Split: sum over c of q[c] * z[N][m][t] = z[N][m][t], because the q[c] sum to 1. Merge: by definition. QED
```

Section 8 extends this to parameters (Lemma 8.3). With that extension, a split leaves every other narrative's drive unchanged at the moment of re-clustering, and the children's drives sum to the parent's.

## 6. The attention model is a softplus Hawkes drive under fitted divisive competition

### 6.1 The exact equations and parameters

The user chose a discrete-time nonlinear multivariate Hawkes process. The literature confirms that structure almost term for term:

- **Normalized multi-timescale basis.** A weight times a normalized lag profile is the discrete-time network Hawkes model ([Linderman & Adams 2015](https://arxiv.org/abs/1507.03228)) and the dictionary-of-exponentials parameterization ([Bacry et al. 2020](https://arxiv.org/abs/1501.00725)).
- **Softplus link.** The scaled softplus link is used verbatim in neural Hawkes models ([Mei & Eisner 2017](https://arxiv.org/abs/1612.09328)).
- **Gain modulation.** Circadian modulation of the excitation gain itself, not only the baseline, has precedent in Twitter cascades ([Kobayashi & Lambiotte 2016](https://arxiv.org/abs/1603.09449)).
- **Scheduled events.** Scheduled-event components in the baseline follow the macro-announcement jumps in [Omi, Hirata & Aihara (2017)](https://doi.org/10.1103/physreve.96.012303).

What changes is the competition term, the capacity, and how the parameters are regularized.

```
# One window step. Everything on the right-hand side of lam[.][t] is F[t-1]-measurable (predictable).
tau = [1.0, 6.0, 24.0, 168.0]                          # hours; experiment F3 also tests 2.5 and 720
a   = [exp(-0.25 / tk) for tk in tau]                  # = [0.7788, 0.9592, 0.98964, 0.998513]

z[j][m][t] = a[m] * z[j][m][t-1] + (1 - a[m]) * y[j][t-1]                 # unit-mass trace

base[i][t]   = b0[i] + c_how[i](how(t)) + sum(d[i][e] * D[e][t] for e in E_sched)
exc[i][j][t] = exp(g_how(how(t))) * sum(A[i][j][m] * z[j][m][t] for m in range(M))
eta[i][t]    = base[i][t] + sum(exc[i][j][t] for j in K(i))

lam_raw[i][t] = s * softplus(eta[i][t] / s)
S_raw[t]      = sum(lam_raw[i][t] for i in range(1, N + 1))

log_Vhat[t] = log(Vbar[how(t)]) + level[t-1]                              # predicted supply
level[t]    = (1 - kappa_L) * level[t-1] + kappa_L * (log(V[t]) - log(Vbar[how(t)]))
B[t]        = exp(beta_B + log_Vhat[t])                                    # capacity

lam[i][t] = lam_raw[i][t] * (B[t] / (B[t] + S_raw[t])) ** omega            # 0 <= omega <= 1

E[y[i][t] | F[t-1]]   = lam[i][t]
Var[y[i][t] | F[t-1]] = phi * lam[i][t] * (1 + lam[i][t] / r) + Vmeas[i][t]  # working variance

# Fourier hour-of-week profiles (168 hours), harmonics Q = [1, 2, 7, 14, 21] (weekly, daily, half-daily, 8-hourly)
c_how[i](h) = sum(ca[i][q] * cos(2*pi*q*h/168) + cb[i][q] * sin(2*pi*q*h/168) for q in Q)
g_how(h)    = sum(ga[q]    * cos(2*pi*q*h/168) + gb[q]    * sin(2*pi*q*h/168) for q in Q)
```

| Symbol | Shape | Meaning | Constraint or prior | Default |
|---|---|---|---|---|
| tau, a | M = 4 | kernel timescales and decay factors | fixed; set chosen by likelihood (F3) | 1 h, 6 h, 1 d, 1 w |
| b0 | N | baseline drive | hierarchical penalty toward the parent or neighbor mean | cold-start rule (Section 8) |
| ca, cb | N x 5 each | hour-of-week baseline | shrink toward population profile | 0 |
| d | N x len(E_sched) | scheduled-event effects (FOMC, CPI, earnings calendars, product events; dummies over [-1 h, +6 h]) | l1 | 0 |
| ga, gb | 5 each | global excitation-gain modulation | small ridge | 0 |
| A | N x N x M on support K(i) | cross-scale excitation, signed | sparse-group lasso; positive-part stability (Lemma 6.5) | 0 |
| K(i) | set | allowed sources for target i | 20 nearest centroids, plus i itself, plus pairs with high historical transport flow (Section 7.4) | built per narrative window |
| s | scalar | softplus scale | s > 0 | 1 attention unit, then fitted |
| omega | scalar | conservation exponent | [0, 1] | fitted (the semi-conservation measurement) |
| beta_B | scalar | capacity relative to predicted supply | real | fitted |
| kappa_L | scalar | supply-level smoothing rate | fixed | 1 - exp(-Delta / 1 week), about 0.00149 |
| phi | scalar | dispersion | Pearson moment estimate | fitted |
| r | scalar | NB2 size for intervals and PIT | moment estimate | fitted |

The traces have unit mass, so A has the reading the proposal intended **[DERIVED]**. Unrolling gives z[j][m][t] as the sum over k >= 1 of (1 - a[m]) * a[m]**(k-1) * y[j][t-k], plus a decaying initial term, and those weights sum to 1. In the linear regime (eta much larger than s, omega = 0), A[i][j][m] is therefore the expected number of extra attention units on i per unit on j, routed through timescale m.

### 6.2 Three facts about the softplus link carry every later proof

```
# Lemma 6.1 (softplus facts) [DERIVED]. Let f(x) = s * softplus(x / s) with s > 0.
# (F1) f(x) = pos(x) + e(x), where e(x) = s * log(1 + exp(-abs(x) / s)) and 0 < e(x) <= s * log(2).
# (F2) f is increasing, convex and 1-Lipschitz: f'(x) = sigmoid(x/s) in (0, 1);
#      f''(x) = sigmoid(x/s) * (1 - sigmoid(x/s)) / s > 0.
# (F3) f is log-concave.
# Proof.
# (F1) For x >= 0, log(1 + exp(u)) = u + log(1 + exp(-u)) with u = x/s. For x < 0, f(x) = s*log(1 + exp(-abs(x)/s)).
#      e is maximized at x = 0, where it equals s*log(2).
# (F2) Differentiate.
# (F3) Write f(x) = s*g(x/s) with g(u) = log(1 + exp(u)), so g' = sigmoid(u) and g'' = sigmoid(u)*(1 - sigmoid(u)).
#      Then (log f)'' = (g''*g - g'**2) / (s**2 * g**2), and g''*g <= g'**2 is equivalent to
#      (1 - sigmoid(u)) * g(u) <= sigmoid(u), i.e. g(u) <= exp(u), i.e. log(1 + exp(u)) <= exp(u),
#      which holds because log(1 + v) <= v for v > 0. QED
```

### 6.3 Divisive competition preserves ratios, caps totals and survives splitting; subtraction does none of these

```
# Proposition 6.2 (divisive competition) [DERIVED]. Fix t and write c = (B / (B + S_raw)) ** omega with B > 0 and
# 0 <= omega <= 1, so that lam[i] = c * lam_raw[i] and S = sum(lam) = c * S_raw.
# (a) Ratios:  lam[i] / lam[k] == lam_raw[i] / lam_raw[k].
# (b) Capacity: S <= S_raw and S <= B**omega * S_raw**(1 - omega). If omega == 1, S = B*S_raw/(B + S_raw) < B.
# (c) Monotonicity: S is strictly increasing in S_raw, so more drive never lowers total attention.
# (d) Merge consistency: if p is replaced by children a, b with lam_raw[a] + lam_raw[b] == lam_raw[p] and all other
#     lam_raw unchanged, then lam[a] + lam[b] == lam[p] and every other lam is unchanged, for every omega.
# (e) Softplus additivity: if eta[a], eta[b], eta[p] >= 0 and eta[a] + eta[b] == eta[p], then
#     abs(lam_raw[a] + lam_raw[b] - lam_raw[p]) <= 2 * s * log(2).
# Proof.
# (a) The common factor c cancels.
# (b) c <= 1 gives S <= S_raw. Write S = S_raw**(1 - omega) * B**omega * (S_raw/(B + S_raw))**omega and use
#     S_raw/(B + S_raw) < 1. For omega == 1, substitute.
# (c) dS/dS_raw = (B/(B + S_raw))**omega * (1 - omega*S_raw/(B + S_raw)) > 0, since omega*S_raw/(B + S_raw) < 1.
# (d) S_raw is unchanged, so c is unchanged, and lam[a] + lam[b] = c*(lam_raw[a] + lam_raw[b]) = c*lam_raw[p] = lam[p].
# (e) By (F1), lam_raw[x] = eta[x] + e(eta[x]) with 0 < e <= s*log(2) when eta[x] >= 0. The difference is
#     e(eta[a]) + e(eta[b]) - e(eta[p]), which lies in (-s*log(2), 2*s*log(2)]. QED

# Proposition 6.3 (subtractive competition) [DERIVED]. Let lam[i] = pos(D[i] - kappa*S) with kappa > 0 and S > 0.
# This is the s -> 0 limit of the working proposal; for s > 0 add the (F1) error of at most s*log(2) per narrative.
# Assume every narrative is active, D[i] > kappa*S.
# (a) Ratios: lam[i]/lam[k] = (D[i] - kappa*S)/(D[k] - kappa*S). If D[i] > D[k] this exceeds D[i]/D[k],
#     because D[k]*(D[i] - x) > D[i]*(D[k] - x) for 0 < x < D[k]. Shares tilt toward large narratives, and weak
#     narratives are zeroed first.
# (b) Granularity: splitting p into active children with D[a] + D[b] = D[p] gives lam[a] + lam[b] = lam[p] - kappa*S.
#     Predicted total attention, sum(D) - n_active*kappa*S, depends on how finely narratives are clustered.
# (c) Depletion: the finite-pool intensity (S_pool/N_pop) * D[i] = D[i] - (D[i]/N_pop) * A_held, with
#     A_held = N_pop - S_pool, has the subtractive form only if kappa_i = D[i]/N_pop. That coefficient is
#     proportional to the narrative's own drive, which is division.
# (d) Granger contamination: if S is built from all narratives' past mass, then
#     d lam[i] / d y[j][t-k] = -kappa * dS/dy[j][t-k] != 0 for every j.
# Proof. (a)-(c): algebra on the stated forms. (d): differentiate the active branch. QED
```

The finite-pool form in (c) is HawkesN, whose intensity multiplies the whole Hawkes drive by the remaining pool fraction and equals the SIR infection rate after recoveries are marginalized out ([Rizoiu et al. 2018](https://arxiv.org/abs/1711.01679)). Proposition 6.2(d) is the property level-of-detail compression needs, and Proposition 6.3(b) is the property that rules subtraction out of a multi-resolution system.

The multiplicative form is not ad hoc. Its omega = 1 case is the steady state of Grossberg's shunting on-center off-surround network, whose total activity saturates at a hard capacity ([Grossberg, Prelude to ART](https://webpages.uidaho.edu/rwells/techdocs/Biological%20Signal%20Processing/Chapter%2015%20Prelude%20to%20ART.pdf)).

```
# Lemma 6.4 (shunting steady state equals the omega = 1 normalization) [DERIVED]
# dx_i/dt = -Ah*x_i + (Bc - x_i)*I_i - x_i*sum(I_k for k != i), with Ah, Bc, I_k > 0, has the unique stable steady
# state x_i = Bc*I_i/(Ah + I_tot), where I_tot = sum(I_k).
# Proof. The right-hand side equals -Ah*x_i + Bc*I_i - x_i*I_tot. It is linear in x_i with slope -(Ah + I_tot) < 0,
# so it has a unique zero and that zero is stable. QED
# With I_i = lam_raw[i] and Ah = Bc = B this is lam[i] = lam_raw[i] * B/(B + S_raw), i.e. omega = 1.
```

The same algebra links several fields:

- **Optics.** It is a saturable gain, `g = g0 / (1 + I / I_sat)`: above threshold the intensity clamps instead of diverging. Lemma 6.5(b) below is the attention version of that clamping.
- **Economics.** With an exponential drive and sigma tending to 0, divisive normalization with exponent 1 is a softmax, which is the rational-inattention logit `P(i) proportional to P0[i] * exp(v[i] / lambda)` ([Matejka & McKay 2015](https://doi.org/10.1257/aer.20130047)).
- **Evolutionary dynamics.** That logit is one step of replicator dynamics.

Division therefore connects attention competition to neuroscience, economics and evolutionary dynamics at once. Subtraction connects only to inhibitory Hawkes kernels.

### 6.4 Stability: positive parts suffice for bounded means, and competition bounds them unconditionally

Continuous-time theory is mature:

- **Lipschitz links.** For nonlinear mutually exciting processes with an alpha-Lipschitz link, alpha times the kernel norm below 1 gives a stationary version **[PROVEN]** ([Brémaud & Massoulié 1996](https://doi.org/10.1214/aop/1065725193)).
- **Positive parts only.** If every link is non-decreasing and L-Lipschitz, a unique stationary version with finite mean exists when the spectral radius of the matrix L * ||h+[l][k]||_1 (positive parts of the kernels only) is below 1, or when every link is bounded **[PROVEN]** ([Sulem, Rivoirard & Rousseau, Lemma 2.1](https://arxiv.org/abs/2103.17164)). The positive-part condition comes from renewal arguments for signed kernels ([Costa et al. 2020](https://arxiv.org/abs/1801.04645)).
- **Discrete time.** Count network autoregressions with absolute-value contraction conditions are stationary and ergodic, with consistent Poisson QMLE **[PROVEN]** ([Armillotta & Fokianos](https://arxiv.org/abs/2104.06296); [nonlinear version](https://arxiv.org/abs/2202.03852)). Stability of discrete-time Hawkes processes with inhibition is only partly characterized even with memory length two ([J. Appl. Prob.](https://resolve.cambridge.org/core/journals/journal-of-applied-probability/article/almost-complete-characterization-of-the-stability-of-a-discretetime-hawkes-process-with-inhibition-and-memory-of-length-two/B720C3C6391FE38998644EB57AACA905)).

The notes flag the missing discrete-time positive-part theorem as a gap. The lemma below closes the first-moment half of it.

```
# Lemma 6.5 (first-moment non-explosion) [DERIVED]
# Assumptions:
#   - y[i][t] >= 0 with E[y[i][t] | F[t-1]] = lam[i][t];
#   - initial traces z[j][m][0] = z0[j] >= 0;
#   - base[i][t] <= beta_max[i] for all t;
#   - exp(g_how(h)) <= G_max for all h;
#   - B[t] <= B_max.
# Let Aplus[i][j][m] = pos(A[i][j][m]) and Pplus[i][j] = sum(Aplus[i][j][m] for m).
# (a) omega == 0: if rho(G_max * Pplus) < 1, then sup over t of E[y[i][t]] is finite for every i.
# (b) 0 < omega <= 1: for every real A (no spectral condition), sup over t of E[sum(y[i][t] for i)] is finite.
#     If omega == 1, sum(lam[i][t] for i) < B[t] <= B_max surely.
#
# Shared step. By (F1), lam_raw[i][t] <= s*log(2) + pos(eta[i][t]). Inhibitory terms only lower eta, and z >= 0, so
#   pos(eta[i][t]) <= pos(beta_max[i]) + G_max * sum(Aplus[i][j][m] * z[j][m][t] for j, m).
# Unrolling, z[j][m][t] = sum(w[m][k] * y[j][t-k] for k in 1..t) + a[m]**t * z0[j], with
# w[m][k] = (1 - a[m]) * a[m]**(k-1). The weights w[m][1..t] together with a[m]**t sum to 1, so
#   E[z[j][m][t]] <= U[j](t-1) := max(z0[j], max(E[y[j][r]] for r <= t-1)).
#
# Proof of (a). Let c[i] = s*log(2) + pos(beta_max[i]) and K = G_max * Pplus >= 0 with rho(K) < 1. By the tower
# property, E[y[i][t]] = E[lam[i][t]] <= c[i] + sum(K[i][j] * U[j](t-1) for j). Hence componentwise
#   U(t) <= max(U(t-1), c + K @ U(t-1)).
# Pick kap >= max(U(0)) and set w = inv(I - K) @ (c + kap*1). The Neumann series inv(I - K) = sum(K**n) converges
# and is >= I entrywise, so w >= c + kap*1 >= U(0), and c + K @ w = w - kap*1 <= w.
# Induction: U(t-1) <= w implies c + K @ U(t-1) <= c + K @ w <= w (because K >= 0), so U(t) <= w. QED (a)
#
# Proof of (b). Let S[t] = sum(lam[i][t] for i) and Ysum[t] = sum(y[i][t] for i). Prop 6.2(b) gives
# S[t] <= B_max**omega * S_raw[t]**(1 - omega). By the shared step,
#   S_raw[t] <= C0 + c1 * sum(z[j][m][t] for j, m), where
#   C0 = sum(s*log(2) + pos(beta_max[i]) for i) and c1 = G_max * max(sum(Aplus[i][j][m] for i) for j, m).
# For each m, sum(z[j][m][t] for j) is a convex combination of past Ysum plus the initial term, so its mean is at
# most W(t-1) := max(Z0, max(E[Ysum[r]] for r <= t-1)), where Z0 = sum(z0). x -> x**(1 - omega) is concave, so
# Jensen's inequality gives
#   E[Ysum[t]] = E[S[t]] <= h(W(t-1)),   h(u) = B_max**omega * (C0 + c1*M*u)**(1 - omega).
# h is nondecreasing and h(u)/u -> 0 as u -> infinity (since omega > 0), so u_star = sup({0} | {u : h(u) > u}) is
# finite. Let Wbar = max(W(0), u_star) + 1, so h(Wbar) <= Wbar.
# Induction: W(t-1) <= Wbar implies E[Ysum[t]] <= h(Wbar) <= Wbar, so W(t) <= Wbar.
# For omega == 1, Prop 6.2(b) gives S[t] < B[t] on every path. QED (b)
```

Part (a) is a discrete-time first-moment analogue of the positive-part condition: inhibitory coefficients never threaten boundedness, so negative entries of A, which carry real suppression between narratives, never need a stability penalty. Part (b) is the formal content of "semi-conservation prevents explosion": any omega > 0 turns excitation feedback sublinear.

The lemma bounds means only. It does not give stationarity, ergodicity or bounded variance.

**[CONJECTURE 6.A]** The omega > 0 model has a unique stationary, ergodic regime for bounded B. This is the discrete analogue of the bounded-link condition (C2) above. Until it is proved, the fitted model's simulated paths must be checked for persistent saturation. That check echoes the recommendation to use stability analysis as a goodness-of-fit diagnostic ([Gerhard et al. 2017](https://doi.org/10.1371/journal.pcbi.1005390)). When omega is near 0, the constraint rho(G_max * Pplus) <= 0.95 is enforced at each refit.

### 6.5 The 15-minute grid biases only the fastest kernel, and the bias is a known factor

Binned Hawkes counts converge weakly to the continuous process as the bin width shrinks, through INAR(infinity) **[PROVEN]** ([Kirchner 2016](https://arxiv.org/abs/1509.02007)). The binned approximation ignores triggering inside a bin ([Kirchner 2017](https://arxiv.org/abs/1509.02017)). Naive binned estimators can be severely biased **[EMPIRICAL]** ([Shlomovich et al. 2022](https://doi.org/10.1080/10618600.2022.2050247)). Whittle estimation remains consistent for linear stationary Hawkes processes even with large bins **[PROVEN]** ([Cheysson & Lang 2022](https://arxiv.org/abs/2003.04314)). For exponential kernels the bias has an exact form.

```
# Lemma 6.6 (binning an exponential kernel) [DERIVED]
# Assumptions: linear excitation with a unit-mass exponential kernel of timescale tau (offspring lag density
# exp(-l/tau)/tau); parent position uniform within its bin; bin width Delta. Let x = Delta/tau and a = exp(-x).
# The expected fraction of a parent's direct offspring landing k bins later is
#   frac[0] = 1 - (1 - a)/x
#   frac[k] = ((1 - a)**2 / (a*x)) * a**k          for k >= 1,     with sum(frac[k] for k >= 1) = (1 - a)/x.
# A discrete trace with weights (1 - a)*a**(k-1) and coefficient A_disc reproduces lag >= 1 transfer exactly iff
# A_disc = A_cont * (1 - a)/x. The fitted coefficient therefore estimates A_cont*(1 - a)/x, and the corrected
# estimate is A_cont_hat = A_disc_hat * x/(1 - a).
# Proof. A parent at u*Delta (u uniform on [0, 1)) lands an offspring in bin k >= 1 with probability
#   integral over l from (k - u)*Delta to (k + 1 - u)*Delta of exp(-l/tau)/tau dl = exp(-(k - u)*x) * (1 - a).
# Averaging over u: (1 - a)*a**k * (exp(x) - 1)/x = ((1 - a)**2/(a*x)) * a**k, using exp(x) - 1 = (1 - a)/a.
# Summing over k >= 1 gives (1 - a)/x, and frac[0] is the complement. Matching A_disc*(1 - a)*a**(k-1) with
# A_cont*frac[k] for all k >= 1 forces A_disc = A_cont*(1 - a)/x. QED
```

| tau | a | Same-bin fraction frac[0] (uniform parent) | Bound for a parent at bin start, 1 - a | Bias factor (1 - a)/x |
|---|---|---|---|---|
| 1 h | 0.7788 | 0.115 | 0.221 | 0.885 |
| 6 h | 0.9592 | 0.0205 | 0.041 | 0.979 |
| 1 d | 0.98964 | 0.0052 | 0.010 | 0.995 |
| 1 w | 0.998513 | 0.00074 | 0.0015 | 0.9993 |

The research notes reported the 0.221 column as "mass inside one bin". It is the worst case, not the typical case **[DERIVED]**. Uniform placement of parents within bins is itself an approximation, because bursts cluster within bins. Experiment F3 validates the correction by simulation.

The empirical decay timescales of news attention support a multi-scale basis **[EMPIRICAL]**:

- a novelty half-life of 69 minutes on digg, with stretched-exponential decay ([Wu & Huberman 2007](https://arxiv.org/abs/0704.1158));
- a 2.5-hour news-to-blog lag ([Leskovec et al. 2009](https://www.cs.cornell.edu/home/kleinber/kdd09-quotes.pdf));
- time in the hourly top 50 falling from 17.5 hours in 2013 to 11.9 hours in 2016 ([Lorenz-Spreen et al. 2019](https://doi.org/10.1038/s41467-019-09311-w));
- most news access gone within 36 hours, with a power-law tail ([Dezsö et al. 2006](https://doi.org/10.1103/physreve.73.066132));
- power-law relaxation with theta about 0.4 for herding YouTube videos ([Crane & Sornette 2008](https://arxiv.org/abs/0803.2189)).

In finance, power-law kernels are often expressed as sums of about 15 exponentials ([Bacry, Mastromatteo & Muzy 2015](https://arxiv.org/abs/1502.04592)). Four log-spaced exponentials cover 1 hour to 1 week. Experiment F3 tests a 2.5-hour and a 30-day component by held-out likelihood, and re-estimates the weights periodically, because timescales drift over the years.

### 6.6 Quasi-Poisson fitting is convex in the linear predictor

```
# Point-estimation objective (quasi-Poisson; phi does not change the minimizer)
Q(theta) = sum(lam[i][t] - y[i][t] * log(lam[i][t]) for i in range(1, N + 1) for t in train) / phi
```

The Poisson quasi-likelihood is consistent for the conditional-mean parameters of INAR and INGARCH models even when the true conditional law is not Poisson **[PROVEN]** ([Ahmad & Francq 2016](https://doi.org/10.1111/jtsa.12167)). Consistency for this softplus model with competition is **[CONJECTURE]**. Quasi-likelihood needs only the mean and a variance function, so fractional soft-membership masses are admissible.

```
# Lemma 6.7 (convexity in the linear predictor) [DERIVED]
# For y >= 0 and any constant c > 0, l(x) = c*f(x) - y*log(c*f(x)) with f(x) = s*softplus(x/s) is strictly convex in x.
# Hence if eta[i][.] is affine in the parameters theta_i of row i (gain g_how and competition factors held fixed),
# each row's objective is convex in theta_i, and strictly convex if the row design has full column rank.
# Proof. c*f is strictly convex by (F2). -y*log(f) is convex because f is log-concave (F3) and y >= 0.
# -y*log(c) is constant. Composition with an affine map preserves convexity. QED
#
# Gradient used by every solver (derived from l):
dl_deta[i][t] = (sigmoid(eta[i][t] / s) / lam_raw[i][t]) * (lam[i][t] - y[i][t]) / phi
# because d/dx [c*f - y*log(c*f)] = c*f' - y*f'/f = (f'/f) * (c*f - y)
```

The NB2 log-likelihood is not convex in the same parameterization. It is used only for intervals and probability integral transforms, which follows the notes' recommendation to keep quasi-Poisson point estimates.

Model checking runs on three tools:

- the nonrandomized PIT for count predictions ([Czado, Gneiting & Held 2009](https://doi.org/10.1111/j.1541-0420.2009.01191.x));
- the discrete-time correction to time-rescaling tests, because plain exponential references reject correct models on binned data ([Haslinger, Pipa & Brown 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2932849));
- a variance-versus-mean plot of Pearson residuals, which decides between quasi-Poisson and NB2 working variances.

### 6.7 Semi-conservation becomes three measurable claims

Lemma 5.1 settles what semi-conservation cannot mean in Yggdrasil: the sum over all nodes, null included, is an identity. The literature on reader attention supports partial zero-sum behavior **[EMPIRICAL]**:

- **Flat capacity.** Public-agenda carrying capacity showed no significant linear increase over 40 years ([McCombs & Zhu 1995](https://doi.org/10.1086/269491)).
- **Transient totals.** Wikipedia pageviews rose after mobility restrictions, correlating with time at home (r = 0.63), but the rise was transient in 11 of 12 languages ([Ribeiro et al. 2021](https://arxiv.org/abs/2005.08505)).
- **Crowding out.** Disasters that coincide with unrelated newsworthy events receive less coverage and less relief ([Eisensee & Strömberg 2007](https://doi.org/10.1162/qjec.122.2.693)).
- **Excitation coexists with competition.** A new event drives more secondary attention to related past events than primary attention to itself ([Garcia-Gavilanes et al. 2017](https://doi.org/10.1126/sciadv.1602368)).

GDELT, however, measures publication supply, not reader time. So the hypothesis must be restated in terms Yggdrasil can falsify:

```
# Conjecture 6.B (semi-conservation, operational) [CONJECTURE]
# (SC1) Competition for predicted supply: omega > 0, with a confidence interval excluding 0 on held-out data,
#       where B[t] uses predicted supply Vhat[t] (never concurrent V[t], which would be mechanical by Lemma 5.1).
# (SC2) Bounded capacity: the supply level, level[t] = log(V[t]/Vbar[how(t)]) smoothed daily, is mean-reverting
#       rather than a random walk once ingestion-source counts are controlled.
# (SC3) Proportional crowd-out: an exogenous shock to unrelated narratives lowers each tracked narrative's
#       attention by the same proportion (Prop 6.2(a)), not by the same absolute amount (Prop 6.3(a)).
# Semi-conservation is accepted only if all three hold (decision rules in experiment F1).
```

Two failure modes contaminate any test of conservation, and both push fitted branching ratios toward 1:

- **Competition-induced criticality.** When memes compete for a fixed screen capacity, births and deaths balance exactly and the system sits at a critical branching ratio ([Gleeson et al. 2014, PRL](https://arxiv.org/abs/1305.4328)). A Hawkes fit that omits the budget will push its own spectral radius toward 1 to explain the conserved total. In physics terms, the conserved quantity behaves like a marginal hydrodynamic mode.
- **Rigid baselines.** Fitting Hawkes models to regime-switching Poisson data produces apparent criticality where the true branching ratio is 0, and intraday seasonality biases the ratio strongly **[EMPIRICAL]** ([Filimonov & Sornette 2015](https://arxiv.org/abs/1308.6756)). Flexible baselines bring estimates down to 0.41 ([Omi et al. 2017](https://doi.org/10.1103/physreve.96.012303)) or reject criticality outright ([Wheatley, Wehrli & Sornette 2019](https://ideas.repec.org/a/taf/quantf/v19y2019i7p1165-1178.html)).

Yggdrasil therefore reports rho(G_max * Pplus) only from fits that include the flexible baseline, scheduled events and the competition term.

### 6.8 New attention enters as exogenous surprise; new narratives enter through lineage

**Exogenous attention.** New attention is attention the fitted drive did not predict. Yggdrasil detects it on residuals, not raw counts. Burst detectors run on raw counts also flag endogenous cascades that the Hawkes model already explains, which is exactly the separation forensics needs.

```
u[i][t] = Phi_inv(mid_PIT(y[i][t]; lam[i][t], phi, r, Vmeas[i][t]))   # approximately N(0, 1) under a correct model
# Bayesian online change-point recursion (constant hazard H = 1/L_cp), run per narrative on u[i][.]:
post[r_t = 0]     proportional to sum(post_prev[r] * pred(u[i][t] | r) * H for r)
post[r_t = r + 1] proportional to post_prev[r] * pred(u[i][t] | r) * (1 - H)
burst(i, t) = post[r_t <= 2] > 0.5 and mean(u[i][run]) > 0      # positive regime shift
# after a confirmed burst, add a decaying baseline dummy D_burst[i][t'] = exp(-(t' - t)*Delta / 1 day)
```

The run-length recursion is exact under its model assumptions **[PROVEN]** ([Adams & MacKay 2007](https://arxiv.org/abs/0710.3742)). Pairing it with nonlinear Hawkes residuals is a design choice **[CONJECTURE]**. The decaying dummy assigns a persistent exogenous level to the baseline rather than to spurious excitation. That is the discrete form of letting the background flex ([Wheatley, Wehrli & Sornette 2019](https://ideas.repec.org/a/taf/quantf/v19y2019i7p1165-1178.html)).

Kleinberg's batched burst automaton is run on shares (relevant mass y[i][t] out of the total) as a model-free cross-check ([Kleinberg 2002](https://www.cs.cornell.edu/home/kleinber/bhs.pdf)). Section 7.1 sends unexplained positive residual mass to BOT. That makes an exogenous burst a candidate root of explanations automatically, which matches the idea that root causes are interventions on a node's own mechanism: a shifted conditional distribution given the parents ([CIRCA, Li et al. 2022](https://arxiv.org/abs/2206.05871)).

**New narratives.** New narratives are born by the emerge rule of Section 5. The DP-means novelty threshold plays the role of the Dirichlet-process concentration. Its generative reading is the Dirichlet-Hawkes process, in which a new document opens a cluster with probability proportional to a base rate and joins an existing cluster with probability proportional to that cluster's current Hawkes intensity ([Du et al. 2015](https://doi.org/10.1145/2783258.2783411)). A newborn narrative starts with zero traces, or with inherited traces for splits (Lemma 5.2), and with parameters from the cold-start rule (Section 8).

## 7. Transition weights are Hawkes attribution shares, made into a proper policy

### 7.1 Window-level attribution sends unexplained mass to the exogenous source

The search prior needs one thing above all: for each narrative, a probability distribution over "where its attention came from", with an explicit exogenous option. Hawkes attribution provides exactly that.

```
# Attribution for target i in window t
den = pos(base[i][t]) + sum(pos(exc[i][j][t]) for j in K(i))
alpha_model[i][t][j]   = pos(exc[i][j][t]) / den       if den > 0 else 0.0     # parent narrative j
alpha_model[i][t][BOT] = pos(base[i][t]) / den         if den > 0 else 1.0     # exogenous source

explained          = min(y[i][t], lam[i][t])
mass[i][t][j]      = explained * alpha_model[i][t][j]
mass[i][t][BOT]    = explained * alpha_model[i][t][BOT] + pos(y[i][t] - lam[i][t])   # surprise goes to BOT
alpha[i][t][x]     = mass[i][t][x] / y[i][t]           for x in K(i) + [BOT], when y[i][t] > 0
suppressors[i][t]  = sorted(j for j in K(i) if exc[i][j][t] < 0)                     # provenance only

# Lemma 7.1 (properness) [DERIVED]
# For y[i][t] > 0, sum(alpha[i][t][x] for x in K(i) + [BOT]) == 1 and every alpha >= 0.
# Proof. sum(alpha_model) == 1 by construction, so the total mass is explained + pos(y - lam)
#        = min(y, lam) + pos(y - lam) = y. Every term is nonnegative. QED

# Lemma 7.2 (exactness and neutrality)
# (a) [PROVEN] For linear Hawkes processes (identity link, nonnegative components, omega = 0), conditional on the
#     event history each event's parent is drawn independently, with probability (component)/(intensity) per
#     component and (background)/(intensity) for "immigrant".
# (b) [DERIVED] The competition factor multiplies every component of lam[i][t] by the same c[i][t] > 0, so
#     alpha_model is independent of omega: divisive competition is attribution-neutral.
# (c) [DERIVED] Under subtractive competition the term -kappa*S is a negative component of the intensity. It has
#     no parent interpretation, and including it would break the probability simplex of (a).
# Proof of (b): numerator and denominator of alpha_model are computed before c is applied, and c cancels from the
# expected-mass split c*lam_raw*alpha_model. Proof of (c): a probability vector needs nonnegative components. QED
```

Part (a) is the basis of stochastic declustering, where background and triggering probabilities are mu/lambda and g/lambda ([Zhuang, Ogata & Vere-Jones 2002](https://doi.org/10.1198/016214502760046925)), and of the parent-variable Gibbs samplers made conjugate by Poisson superposition ([Linderman & Adams 2014](https://arxiv.org/abs/1402.0914)).

With a nonlinear link the exact immigrant-offspring cluster representation is lost, which is why signed-kernel theory uses renewal arguments instead ([Costa et al. 2020](https://arxiv.org/abs/1801.04645)). Outside the linear regime, the positive-part shares are therefore an approximation **[CONJECTURE: adequate when most mass sits in windows with eta well above s]**. The surprise rule makes a model's failure visible: mass the model did not predict is attributed to new information, never to an invented parent.

Composing attributions across windows gives a genealogy. In the linear regime, part (a) makes the ancestral line of a uniformly chosen attention unit a backward Markov chain absorbed at BOT **[DERIVED]**. The parent of a unit depends only on the intensity components at its own window, and parent draws are independent given the history, so the parent's parent is drawn afresh from the components at the parent's window.

### 7.2 Horizon edge weights form a proper policy over parents

```
H_win(tau) = [tau - H, tau)                       # H = 14 days by default (open decision)
mass_i     = sum(y[i][t] for t in H_win(tau))
p_H(j -> i)   = sum(y[i][t] * alpha[i][t][j]   for t in H_win(tau)) / mass_i
p_H(BOT -> i) = sum(y[i][t] * alpha[i][t][BOT] for t in H_win(tau)) / mass_i

# Lemma 7.3 [DERIVED]: for every narrative i with mass_i > 0, sum(p_H(j -> i) for j) + p_H(BOT -> i) == 1.
# Proof. p_H(. -> i) is a convex combination, with weights y[i][t]/mass_i, of the per-window probability vectors
# alpha[i][t][.] (Lemma 7.1). A convex combination of probability vectors is a probability vector. QED
#
# Lag-resolved variant (for time-expanded graphs): the share of exc[i][j][t] coming from window t - k is
#   exp(g_how(how(t))) * sum(A[i][j][m] * (1 - a[m]) * a[m]**(k-1) for m) * y[j][t-k] / exc[i][j][t]
# This is exact by unrolling the trace.
```

These weights are excitation (offspring) weights. They answer "whose attention begot this narrative's attention". For publication-supply data, where articles beget articles, that is the causal reading an explanation needs.

### 7.3 Transport flows answer a different question and serve as a cross-check

The research recommends a second, conserving notion of transition: attention mass that moves from one narrative to another. The notes rank prior-regularized aggregate-Markov estimators first for that job. These estimators pool, across windows, unbalanced optimal-transport couplings with a semantic cost. Entropic unbalanced transport relaxes the marginal constraints with KL penalties and is solved by a generalized Sinkhorn diagonal scaling ([Chizat et al. 2018](https://arxiv.org/abs/1607.05816); [Liero, Mielke & Savaré 2018](https://ar5iv.arxiv.org/html/1508.07941)).

```
# Unbalanced entropic OT between consecutive windows (a = y[:, t], b = y[:, t+1], C[i][j] = semantic distance)
min over pi >= 0:  sum(C*pi) + eps*KL(pi | outer(a, b)) + lam1*KL(pi.sum(1) | a) + lam2*KL(pi.sum(0) | b)
K = exp(-C / eps)
repeat:  u = (a / (K @ v)) ** (lam1 / (lam1 + eps));  v = (b / (K.T @ u)) ** (lam2 / (lam2 + eps))
pi = diag(u) @ K @ diag(v)      # destroyed mass a - pi.sum(1) = decay; created mass b - pi.sum(0) = new information
# exponent forms reproduced in the notes from memory: verify against Chizat et al. before implementing
```

Waddington-OT is the closest analogue of this problem. It recovers temporal couplings from destructive snapshots of 315,000 cells at 40 time points ([Schiebinger et al. 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6615720)). Its theory states both the promise and the trap.

The promise: if the true law is a diffusion with gradient drift, dX = -grad(Psi) dt + sigma dB, it is the unique minimizer of relative entropy to Brownian motion among all path laws with the same temporal marginals **[PROVEN]** ([Lavenant et al. 2024, Theorem 1.1](https://arxiv.org/abs/2102.09204)).

The trap: in the same paper, failure to model branching creates spurious transport, and periodic drift is invisible from marginals. Two lemmas make the trap precise for Yggdrasil.

```
# Lemma 7.4 (offspring and transfer are confounded in means, separated in Fano factors) [DERIVED]
# Unit-level model: each of the y[i][t] (integer) units on i independently (a) moves to j with probability P[i][j],
# where sum over j of P[i][j] <= 1 and the remainder decays, and (b) begets Poisson(H[i][j]) new units on j,
# independently of (a). In addition, Poisson(Lam[j]) immigrants arrive. Then
#   E[y[j][t+1] | y[:, t]]   = sum(y[i][t] * (P[i][j] + H[i][j]) for i) + Lam[j]
#   Var[y[j][t+1] | y[:, t]] = sum(y[i][t] * (P[i][j]*(1 - P[i][j]) + H[i][j]) for i) + Lam[j]
#   Var - E                  = -sum(y[i][t] * P[i][j]**2 for i)
# Proof. Arrivals at j are a sum of independent pieces: for each source i, a Binomial(y_i, P_ij) count of movers
# (mean y*P, variance y*P*(1 - P)), a Poisson(y_i*H_ij) count of offspring, and Poisson(Lam_j) immigrants. Means and
# variances of independent summands add; subtract. QED
# Consequence: first moments identify only G = P + H, the transport-versus-branching confound. Transfer leaves a
# sub-Poissonian signature (the binomial partition noise of a beam splitter acting on a fixed photon number).
```

Whether that signature survives Yggdrasil's fractional, independence-weighted masses, plus overdispersion from common shocks, is **[CONJECTURE]**. Lemma 7.4 uses integer units, and soft membership adds positive measurement variance. Experiment F1 treats a negative Fano deficit as informative and its absence as uninformative.

```
# Lemma 7.5 (identifiability from means) [DERIVED]
# Stack X = [y_1 .. y_{T-1}]^T and Y = [y_2 .. y_T]^T, so E[Y | X] = Xt @ Theta with Xt = [X, ones] and
# Theta = [P_eff; Lam^T]. Theta is identified from E[Y | X] iff Xt has full column rank N + 1.
# Proof. If rank(Xt) = N + 1, then pinv(Xt) @ Xt = I and Theta = pinv(Xt) @ E[Y | X] is unique. Otherwise some v != 0
# has Xt @ v = 0, and Theta + outer(v, w) gives the same E[Y | X] for every w. QED
# Near stationarity, y_t is roughly constant, so the rank is about 1: N equations for about N**2 unknowns.

# Lemma 7.6 (fluctuations identify the relaxation operator) [DERIVED]
# If y[t+1] - ybar = P^T @ (y[t] - ybar) + e[t+1], with e[t+1] uncorrelated with y[t] and y stationary, then
# Gamma1 = P^T @ Gamma0, where Gamma0 = Cov(y[t], y[t]) and Gamma1 = Cov(y[t+1], y[t]). So P^T = Gamma1 @ inv(Gamma0)
# whenever Gamma0 is invertible.
# Proof. Cov(y[t+1], y[t]) = P^T @ Cov(y[t], y[t]) + Cov(e[t+1], y[t]) = P^T @ Gamma0. QED
# Physics reading: Onsager's regression hypothesis. Spontaneous fluctuations relax by the same operator as
# macroscopic perturbations, so lagged covariances reveal P even when means are flat.

# Lemma 7.7 (circulations are invisible to snapshot pairs) [DERIVED]
# With node-edge incidence B (N x m), flows f satisfy the balance B @ f = rhs, rhs = s_in - d_out - (y[t+1] - y[t]).
# (i) Solutions form f0 + ker(B), and dim ker(B) = m - N + c, where c is the number of connected components.
# (ii) The minimum-norm solution is f_star = B^T @ phi with L @ phi = rhs, where L = B @ B^T is the graph Laplacian.
# Proof. (i) An incidence matrix has rank N - c, so dim ker(B) = m - (N - c). (ii) Write f = f_r + f_k with
# f_r in im(B^T) and f_k in ker(B), which are orthogonal complements. Then ||f||**2 = ||f_r||**2 + ||f_k||**2 is
# minimized at f_k = 0, so f_star = B^T @ phi and B @ B^T @ phi = rhs. QED (Thomson's principle for electrical networks.)
```

Graph Hodge theory gives the gradient-curl-harmonic decomposition behind (i) ([Lim 2020](https://arxiv.org/abs/1507.05379v3)). From exact aggregate counts, conditional least squares is consistent. With noisy aggregates, a lagged-covariance moment estimator is consistent instead, and it is the first learning method with guarantees for a subclass of collective graphical models **[PROVEN]** ([Bernstein & Sheldon 2016](https://ar5iv.labs.arxiv.org/html/1604.04182)). Exact inference in collective graphical models is NP-hard even on trees **[PROVEN]** ([Sheldon et al. 2013](https://proceedings.mlr.press/v28/sheldon13.html)).

**Design decision.** Transport flows are computed per window pair as an ancestry diagnostic and as a support prior: pairs with persistent flow join K(i). They are not the search policy. Excitation weights have exact meaning in the linear regime (Lemma 7.2a) and need no conservation assumption that the data have yet to earn. Transfer weights are not identified from means (Lemmas 7.4 and 7.5), and their gradient-flow identifiability theorem excludes the rotations (risk-on and risk-off cycles) that markets exhibit.

### 7.4 Structural edges, not Granger tests on intensities, carry forensic influence

```
# Lemma 7.8 (Granger semantics) [DERIVED]
# (a) omega = 0: lam[i] depends on the history of y[j] iff A[i][j][m] != 0 for some m.
# (b) omega > 0: if some narrative k has A[k][j][.] != 0, lam[i] depends on y[j]'s history through S_raw even when
#     A[i][j][.] == 0.
# Proof. (a) The coefficient of y[j][t-k] in eta[i][t] is C[k] = exp(g_how) * sum(A[i][j][m]*(1 - a[m])*a[m]**(k-1) for m).
#     If C[k] = 0 for all k >= 1, then sum(beta[m] * a[m]**(k-1) for m) = 0 for k = 1..M, with
#     beta[m] = A[i][j][m]*(1 - a[m]). The a[m] are distinct, so this Vandermonde system is nonsingular and
#     beta = 0; a[m] < 1 then gives A[i][j][.] = 0. Conversely, any nonzero C[k] changes eta[i], and f is strictly
#     increasing (F2). (b) c[i][t] is a strictly monotone function of S_raw, which contains lam_raw[k]. QED
```

Part (a) extends the linear result to the softplus link. In the linear case, Granger non-causality is equivalent to a zero kernel **[PROVEN]** ([Eichler, Dahlhaus & Dueck 2017, Prop. 3.2](https://arxiv.org/abs/1605.06759)). Part (b) is the divisive analogue of Proposition 6.3(d). The difference is that divisive competition is attribution-neutral (Lemma 7.2b), so influence claims read off A stay clean, while mean-field competition is reported as one separate number, omega.

Latent drivers that GDELT does not see, such as wire services and social media, can create spurious edges unless identifiability conditions hold ([Jin & Huang 2026](https://arxiv.org/abs/2508.11727)). Bounded-degree dependency graphs are recoverable after polylogarithmic observation time even with time-varying baselines **[PROVEN]** ([Mossel & Sridhar 2026](https://arxiv.org/abs/2601.11717)). Experiment F4 tests edges against both risks.

## 8. Bayesian cold start and a 15-minute update cycle with a unique answer

### 8.1 A convex penalized quasi-likelihood replaces Gaussian-prior MAP

```
# theta = (b0, ca, cb, d, A); ga, gb, omega, beta_B, s, phi, r are handled in the outer loop
Pen(theta) = sum(lam_grp * wgt[i][j] * norm2(A[i][j][:] - A0[i][j][:]) for i for j in K(i))   # pairwise groups
           + lam_l1 * sum(abs(A[i][j][m] - A0[i][j][m]) for i for j in K(i) for m in range(M))
           + lam_d  * sum(abs(d[i][e]) for i for e in E_sched)
           + sum((b0[i] - b0_prior[i])**2 / (2 * sd_b[i]**2) for i)
           + sum(norm2(ca[i] - ca_pop)**2 + norm2(cb[i] - cb_pop)**2 for i) / (2 * sd_c**2)
           + eps_ridge * norm2(theta)**2                    # eps_ridge = 1e-6: uniqueness, not shrinkage
wgt[i][j] = 1 / (1 + kappa_sim * cos(e[i], e[j]))         # semantically close pairs are penalized less
feasible: max(sum(G_max * pos(A[i][j][m]) for j for m) for i) <= 0.95      # imposed only while omega_hat < 0.05

# Lemma 8.1 (unique block minimizer) [DERIVED]
# With ga, gb, omega, beta_B, s fixed and the competition factors c[i][t] > 0 frozen, Q + Pen has exactly one
# minimizer over the feasible set.
# Proof. eta is affine in theta, so Q is convex (Lemma 6.7). Each penalty term is a norm, an absolute value or a
# convex quadratic, hence convex, and eps_ridge*norm2**2 is strictly convex. The feasible set is convex: pos is
# convex, and sums and maxima of convex functions are convex. Q is bounded below, because lam - y*log(lam) >=
# y - y*log(y) for y > 0 and >= 0 for y = 0. The ridge term makes the objective coercive. A strictly convex, coercive,
# lower-semicontinuous function on a closed convex set has a unique minimizer. QED
# Since rho(K) <= max row sum of K for K >= 0, the feasible set enforces rho(G_max*Pplus) <= 0.95, the Lemma 6.5(a) condition.
```

Uniqueness gives semantic determinism for the fit. Any convergent solver returns the same parameters to within tolerance, so the answer is defined by the objective rather than by the solver's path.

The penalty design follows the literature:

- **Pairwise groups.** Grouping all timescales of a pair follows sparse-group-lasso Hawkes estimation ([Xu, Farajtabar & Zha 2016](https://arxiv.org/abs/1602.04511)). A zero group is exactly a Granger non-edge (Lemma 7.8a).
- **Similarity scaling.** Scaling penalties by similarity is a convex stand-in for latent-space and stochastic-block-model network priors ([Linderman & Adams 2014](https://arxiv.org/abs/1402.0914)) and for infectivity parameterized by node features ([Zhou, Zha & Song, AAAI 2014](https://doi.org/10.1609/aaai.v28i1.8733)).
- **Uncertainty.** Uncertainty comes from a Laplace approximation on the active set: an inverse Fisher-plus-prior Hessian with Fisher weight c*f'(eta)**2/(phi*f(eta)). This is an approximation, not a theorem. The scalable option with proven posterior concentration is variational Bayes for nonlinear Hawkes ([Sulem et al., JMLR 2025](https://arxiv.org/abs/2212.00293)).

### 8.2 The outer loop handles competition without losing monotonicity

```
for it in range(n_outer):                                   # fixed count: deterministic
    c = (B / (B + S_raw(theta))) ** omega                   # freeze competition factors
    cand = argmin(Q_c(theta2) + Pen(theta2) for theta2 in feasible)     # unique by Lemma 8.1
    step = 1.0
    while J(theta + step * (cand - theta)) > J(theta) and step > 2**-20:
        step /= 2                                           # J = true objective with c recomputed
    theta = theta + step * (cand - theta) if J(theta + step*(cand - theta)) <= J(theta) else theta
    omega, beta_B = argmin of J over the grid omega in [0, 0.05, ..., 1] x beta_B grid   # ties: smallest omega
    ga, gb = few gradient steps on J                        # gain modulation

# Lemma 8.2 (monotone outer loop) [DERIVED]: J(theta_it) is nonincreasing in it and converges.
# Proof. Each accepted update satisfies J_new <= J_old by the acceptance test, and grid minimization over
# (omega, beta_B) cannot increase J because the current values are on the grid. J is bounded below (Lemma 8.1),
# so the sequence converges. QED (Convergence of values, not global optimality: the joint problem is nonconvex.)
```

### 8.3 Every 15 minutes the system updates in a fixed order

```
def on_window_close(t):
    obs = ingest_and_dedup(batch[t])                          # Section 4, deterministic
    memberships(obs, centroids_frozen[window_of(t)])          # Section 5
    y[:, t], Vmeas[:, t], V[t] = aggregate(obs)
    pit[:, t] = mid_pit(y[:, t], lam[:, t], phi, r, Vmeas[:, t])   # lam[:, t] was computed at t-1 (predictable)
    bursts = bocpd_update(Phi_inv(pit[:, t]))                 # Section 6.8
    theta = prox_step(theta, grad_window(t), step0 / sqrt(n_t))    # online proximal step; gradient from Lemma 6.7
    z[:, :, t+1] = a * z[:, :, t] + (1 - a) * y[:, t]
    level, Vhat[t+1] = update_supply(level, V[t])
    alpha[:, t, :] = attribution(theta, z[:, :, t], y[:, t], lam[:, t])   # Section 7.1
    lam[:, t+1] = predict(theta, z[:, :, t+1], Vhat[t+1])
    if t % W_narr == 0:  lineage_update()     # Section 5: emerge, split, merge -> traces (Lemma 5.2), priors (8.4)
    if t % K_refit == 0: outer_refit()        # Section 8.2, warm start, stability constraint
    if t % K_lod == 0:   lod_check()          # Section 9
    check_market_triggers(t)                  # Section 10
```

The online step is mirror descent on a time-discretized loss. It has a tracking-regret guarantee of order sqrt(T) times (1 plus the comparator's total deviation from the assumed dynamics), for convex losses and contractive dynamics **[PROVEN]** ([Hall & Willett 2016](https://arxiv.org/abs/1409.0031)). Lemma 6.7 makes the per-window loss convex when omega = 0 and the gain is fixed, so the guarantee applies in that case **[DERIVED]**. With omega > 0 it is **[CONJECTURE]**, and the daily outer refit restores the exact objective.

### 8.4 Cold start borrows strength through lineage and similarity

```
# Emerge (no parent): K5 = 5 nearest alive narratives by centroid cosine, weights wk proportional to cos(e[new], e[k])
b0_prior[new] = median(b0[k] for k in K5)
A0[new][j][:] = sum(wk * A[k][j][:] for k in K5);  A0[j][new][:] = sum(wk * A[j][k][:] for k in K5)
z[new][:][t] = 0
# Prior strength decays with evidence:
lam_prior(new, t) = lam0 / (1 + n_eff(new, t) / n0),  n_eff = cumulative mass since birth

# Split N -> children c with shares q[c] (sum q == 1), traces split by Lemma 5.2:
b0[c], ca[c], cb[c], d[c] = q[c]*b0[N], q[c]*ca[N], q[c]*cb[N], q[c]*d[N]
A[c][j][m]  = q[c] * A[N][j][m]        for j outside the lineage          # rows split (targets add)
A[j][c][m]  = A[j][N][m]               for j outside the lineage          # columns copy (per-unit influence kept)
A[c][c2][m] = q[c] * A[N][N][m]        for siblings c, c2 (c2 == c included)

# Lemma 8.3 (split consistency) [DERIVED]
# At the split instant, (i) every outside narrative's eta is unchanged and (ii) sum(eta[c] for c) == eta[N].
# Proof. (i) For outside j: sum over c of A[j][c][m]*z[c][m] = A[j][N][m] * sum(q[c])*z[N][m] = A[j][N][m]*z[N][m].
# (ii) The base terms sum to base[N], because they are linear in (b0, ca, cb, d) and sum(q) == 1. The outside
# excitation sums to sum over j of A[N][j]*z[j]. The internal excitation is
# sum over c, c2 of q[c]*A[N][N]*q[c2]*z[N] = A[N][N]*z[N]. The common gain factor multiplies both sides. QED
# With Prop 6.2(d,e), predicted intensities are preserved to within len(children)*s*log(2) when all drives are >= 0.

# Merge N_1..N_K -> C with trace weights w_l = z[N_l]/sum(z[N_l2] for l2) (exact at the merge instant, same bookkeeping):
b0[C] = sum(b0[N_l]);  A[C][j] = sum(A[N_l][j]);  A[j][C] = sum(w_l * A[j][N_l]);  A[C][C] = sum over l, l2 of A[N_l][N_l2]*w_l2
```

The notes found no theory for adding nodes to a Hawkes network online, beyond the generative Dirichlet-Hawkes mechanism and feature-parameterized infectivity. The emerge rule is therefore **[CONJECTURE]**. The split and merge rules are exact bookkeeping, and their later drift is exactly the lumpability defect measured in Section 9.

## 9. Level of detail compresses only where the coarse node is closed

Exact and ordinary lumpability define the aggregations of a Markov chain whose aggregated chain reproduces stationary and transient quantities exactly, with bounds for near-lumpability **[PROVEN]** ([Buchholz 1994](https://resolve.cambridge.org/core/journals/journal-of-applied-probability/article/abs/exact-and-ordinary-lumpability-in-finite-markov-chains/2DC748F09D80BEEB03CCF18036E149D7)). Informational closure, where the macro level is best predicted by the macro level alone, is equivalent to causal closure and is tied to strong lumpability ([Rosas et al. 2024](https://arxiv.org/html/2402.09090v2)). The lemmas below turn this into a checkable rule for Yggdrasil's nonlinear model.

```
# Lemma 9.1 (lumpability of linear mean dynamics) [DERIVED]
# Let E[y[t+1] | F_t] = A_lin @ y[t] + mu, and let V be the N x n_blocks 0/1 matrix with exactly one 1 per row.
# The block totals Y = V^T @ y have mean dynamics that depend on y only through Y iff V^T @ A_lin = Ahat @ V^T
# for some Ahat. Equivalently, for every target block I and source block J, sum(A_lin[i][j] for i in I) is the
# same for all j in J.
# Proof. (if) V^T @ (A_lin @ y + mu) = Ahat @ V^T @ y + V^T @ mu. (only if) If V^T @ A_lin @ y depends on y only
# through V^T @ y, then V^T @ A_lin annihilates ker(V^T), so its rows lie in the row space of V^T, i.e.
# V^T @ A_lin = Ahat @ V^T. Applying both sides to the basis vector e_j gives (V^T @ A_lin)[I][j] = Ahat[I][J(j)],
# constant over j in J. QED

# Lemma 9.2 (traces aggregate exactly) [DERIVED]
# The trace of a block total equals the sum of member traces: Z[J][m][t] = sum(z[j][m][t] for j in J).
# Proof. The trace recursion is linear with the same coefficients for every narrative, and the initial values add. QED

# Lemma 9.3 (closure bound for the softplus model) [DERIVED]
# Collapse block I into a macro node with eta_I = base_I + gain * sum(Ahat[I][J][m] * Z[J][m] for J, m), where
# base_I = sum(base[i] for i in I). Define
#   delta[I][J][m] = max(abs(sum(A[i][j][m] for i in I) - Ahat[I][J][m]) for j in J).
# Then abs(sum(eta[i] for i in I) - eta_I) <= gain * sum(delta[I][J][m] * Z[J][m] for J, m), and if every eta[i] >= 0
# and eta_I >= 0,
#   abs(sum(lam_raw[i] for i in I) - s*softplus(eta_I/s)) <= gain * sum(delta*Z) + len(I) * s * log(2).
# Proof. sum(eta[i]) - eta_I = gain * sum over J, m, j in J of (sum(A[i][j][m] for i in I) - Ahat[I][J][m]) * z[j][m].
# Bound each bracket by delta and use Lemma 9.2. For the softplus step, (F1) gives lam_raw[i] = eta[i] + e_i with
# 0 < e_i <= s*log(2), and the macro value equals eta_I + e_I. The e-terms differ by less than len(I)*s*log(2). QED
# When raw sums are preserved, the competition layer is exact under collapse (Prop 6.2(d)).
```

The collapse rule combines the structural defect with a predictive closure test, with hysteresis so that the tree does not oscillate:

```
collapse(I) iff  max over J, m of delta[I][J][m] * Zscale[J][m] <= tol_lump
            and  closure_gain(I) <= tol_close                 # held-out log-lik(parent | parent + children histories)
                                                              #   minus log-lik(parent | parent history)
            and  all(eta[i] >= 0 for i in I) over the last day
expand(I)   iff  either test fails on 3 consecutive checks    # shocks break within-node homogeneity
```

Three results support the rule:

- **Lumpability failure costs memory.** By Mori-Zwanzig, coarse-graining without time-scale separation introduces memory kernels ([Mori-Zwanzig review](https://pmc.ncbi.nlm.nih.gov/articles/PMC4644152)). Coarse nodes need their own, typically longer-tailed, kernels. This is a principled reason to refit A per LOD level rather than summing child coefficients.
- **Candidate partitions have principled sources.** They can come from KL-optimal spectral aggregation of the estimated dynamics ([Deng, Mehta & Meyn 2011](https://experts.illinois.edu/en/publications/optimal-kullback-leibler-aggregation-via-spectral-theory-of-marko/)) or from the Laplacian renormalization group on the similarity graph ([Villegas et al. 2023](https://www.arxiv.org/abs/2203.07230)).
- **Markets already coarse-grain.** Capacity-constrained investors process market- and sector-level information before firm-level information ([Peng & Xiong 2006](https://ideas.repec.org/a/eee/jfinec/v80y2006i3p563-602.html)). That is an economic microfoundation for a category-then-member tree, and divisive normalization with exponent 1 is exactly merge-consistent on such a tree (Prop 6.2(d)).

Storage tiers follow the LOD tree:

- **Hot:** the last 24-72 hours of observations, open clusters, narratives touched in the last week, indices and centroids.
- **Warm:** 7-90 days in Parquet, with all aggregates.
- **Cold:** the immutable, content-addressed archive.

Each parent stores additive aggregates of its children (counts, weighted mass, the mean and variance of attention), so coarsening loses nothing the attention layer sums.

## 10. The abnormal-event trigger opens a case and fixes the information cutoff

Yggdrasil never forecasts. Market data enter only to decide that something abnormal happened and when it first became visible. The triggers combine three standard ingredients: daily event-study abnormal returns ([MacKinlay 1997](https://ideas.repec.org/a/aea/jeclit/v35y1997i1p13-39.html); formulas as documented by [EventStudyTools](https://www.eventstudytools.com/methodology/test-statistics)), a robust z-score ([NIST/SEMATECH](https://itl.nist.gov/div898/handbook/eda/section3/eda35h.htm)), and the Lee-Mykland intraday jump test ([Lee & Mykland 2008](https://www.scheller.gatech.edu/directory/research/finance/lee/pdf/leemykland08.pdf)).

```
# T1 daily abnormal return: market + sector model, estimated on trading days [t-260, t-11]
AR[t]   = R[t] - (alpha_i + beta_i * Rm[t] + gamma_i * Rsec[t])
S2_AR0  = S2_AR * (1 + 1/Mest + (Rm[0] - mean(Rm_est))**2 / sum((Rm[k] - mean(Rm_est))**2 for k in est))
SAR0    = AR[0] / sqrt(S2_AR0)
Mz[t]   = 0.6745 * (AR[t] - median(AR_est)) / MAD(AR_est)
fire_T1 = abs(SAR0) >= 4 or abs(Mz[t]) >= 5                  # 3.5 in sensitive mode
# T2 raw-move fallback for short histories
fire_T2 = abs(R[t]) >= max(0.025, 4 * 1.4826 * MAD(R[t-60:t]))
# T3 Lee-Mykland on 5-minute returns, K = 270, level 1%
L[i]          = log(S[i] / S[i-1]) / sigma_hat[i]
sigma_hat[i]**2 = sum(abs(log(S[j]/S[j-1])) * abs(log(S[j-1]/S[j-2])) for j in range(i-K+2, i)) / (K - 2)
cc  = sqrt(2 / pi)
C_n = sqrt(2*log(n)) / cc - (log(pi) + log(log(n))) / (2 * cc * sqrt(2*log(n)))
S_n = 1 / (cc * sqrt(2*log(n)))
jump[i] = (abs(L[i]) - C_n) / S_n > -log(-log(1 - 0.01))      # threshold = 4.6001
# T4 jump share of daily variance
RV = sum(r[j]**2 for j);  BV = (pi/2) * sum(abs(r[j]) * abs(r[j-1]) for j >= 1);  RJ = (RV - BV) / RV
# T5 abnormal volume (design construction, no primary source in the notes)
Mv = 0.6745 * (log(vol[t]) - median(log(vol[t-60:t]))) / MAD(log(vol[t-60:t]));   fire_T5 = Mv >= 3.5
# T6 clustered events: Kolari-Pynnonen adjustment of cross-sectional statistics
z_adj = z * sqrt((1 - rbar) / (1 + (Nfirms - 1) * rbar))
# gating rule
open_case = (fire_T1 or (short_history and fire_T2)) and (any(jump) or fire_T5)
```

Three cautions come with these statistics:

- **Variance shifts.** Even small event-induced variance increases make common tests over-reject **[EMPIRICAL]** ([Boehmer, Musumeci & Poulsen 1991](https://ink.library.smu.edu.sg/lkcsb_research/4666)).
- **Clustered events.** Under event-date clustering, low cross-correlation is already serious enough to require the adjustment in T6 ([Kolari & Pynnönen 2010](https://papers.ssrn.com/abstract=1830364)).
- **Interpreting T4.** A high jump share with one Lee-Mykland timestamp points to a discrete trigger. A large abnormal return with a low jump share points to diffuse repricing, which is harder to explain. High-clarity jumps are more concentrated intraday **[EMPIRICAL]** ([Baker et al., rev. 2025](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf)).

When several names fire on one day, as they did on 2025-01-27, Yggdrasil opens one cluster case with per-instrument sub-events and searches for a shared driver before idiosyncratic ones.

```
# Information cutoff [CONJECTURE: design rule]
tau_star(case) = min(first_abnormal_time(x) for x in instruments(case))
first_abnormal_time(x) = earliest Lee-Mykland jump time of x on the event day, or, if the abnormal return sits in a
                         closed-market gap, the time of the first print after the gap (pre-market, or the open of
                         the earliest-trading linked market) that already shows the move
```

The gap rule matters for overnight and weekend moves. A strict cutoff at the previous close would exclude news published while the market could not trade, even though that news can only show up in the first post-gap print. Taking the minimum over the cluster makes the cutoff conservative. If European semiconductor names moved before the US open, their first abnormal print bounds the cutoff for NVIDIA too.

## 11. An explanation is a minimum-cost arborescence rooted at the exogenous source

### 11.1 The explanation graph and its costs

```
# Explanation graph at cutoff tau = tau_star; only admissible evidence (first_seen < tau) enters
V_tau = [BOT] + narratives alive in H_win(tau) at the active LOD + terminals T
T     = [e_star] + sub-events of the other instruments in the cluster          # k = len(T)
edges and costs (lam_node >= 0 is added to every edge entering a non-BOT node):
  (j -> i)   narratives with p_H(j -> i) >= p_floor     c = -log(p_H(j -> i)) + lam_node
  (BOT -> i) every narrative i                          c = -log(p_H(BOT -> i)) + lam_node
  (u -> x)   narrative u in Cand(x), terminal x          c = -log(p_link(u -> x)) + lam_node
  (BOT -> x) every terminal x ("x is unexplained")       c = -log(p0[x]) + lam_node
p_link(u -> x) = (1 - p0[x]) * exp(score[u][x]) / sum(exp(score[k][x]) for k in Cand(x))
score[u][x]    = log(rel[u][x] + eps_rel) + zatt[u]
rel[u][x]      = share of u's horizon mass in documents linked to x's entity, peer set or sector
zatt[u]        = robust z-score of u's mass in [tau - 24 h, tau) against its trailing 30 days
# for every terminal x: sum(p_link(u -> x) for u in Cand(x)) + p0[x] == 1     [DERIVED: softmax plus complement]

feasible S : an arborescence rooted at BOT that contains every terminal and whose leaves are all terminals
cost(S)    = sum(c(e) for e in S)
S_star     = argmin over feasible S of cost(S)          # the smallest (most parsimonious) explanation
we_do_not_know  iff  (BOT -> e_star) in S_star
```

Terminals are sinks in G_tau, because price events cannot cause pre-cutoff narratives, so they are always leaves.

The construction makes BOT do four jobs at once:

- It is the Hawkes immigrant source: every narrative's BOT edge carries its exogenous share, surprise included (Lemma 7.1).
- It is the root of every explanation.
- It is where new information enters: an exogenous burst on the DeepSeek-R1 narrative is the edge BOT -> N_R1.
- Its direct edge to e_star is abstention, priced at -log(p0). "We do not know" therefore wins exactly when no narrative chain to the event is more probable than the prior probability of an unexplained move.

The calibration of p0 depends on the unit of analysis **[EMPIRICAL]**:

- **US index jumps.** 17% since 1900 had no identifiable reason in next-day newspapers, falling from about 35% to about 10% over 90 years ([Baker et al., rev. 2025](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf)).
- **Single stocks.** In a small sample, intraday jumps were almost always associated with news ([Lee & Mykland 2008](https://www.scheller.gatech.edu/directory/research/finance/lee/pdf/leemykland08.pdf)).

p0 is therefore an open decision for each instrument class.

The roles also line up with the reservoir of Section 5. At the tracked level, exogenous attention is attention arriving from untracked sources, so BOT is the reservoir as seen by the causal layer **[CONJECTURE: interpretive identification]**.

```
# Conjecture 11.A (independent-edge semantics) [CONJECTURE]
# Each edge e is "active" independently with probability p(e); each included non-BOT node carries a prior factor
# exp(-lam_node); an explanation asserts that all of its edges are active.
# Lemma 11.1 (Steiner optimum = MAP explanation) [DERIVED]
# Under 11.A, P(S) is proportional to exp(-cost(S)). So S_star is the MAP explanation, and the posterior odds of S1
# over S2 are exp(cost(S2) - cost(S1)).
# Proof. -log(prod(p(e) for e in S) * exp(-lam_node * n_nodes(S))) = cost(S), and exp(-x) is decreasing. QED
```

In physics terms, cost is energy, S_star is the ground state, competing explanations are low-lying excitations, and their odds are Boltzmann factors at unit temperature. Counting shared edges once is what makes the optimum parsimonious, in the two-part minimum-description-length sense where shared structure is described once. That sense of parsimony is analogous to MDL graph summarization ([VoG, Koutra et al. 2014](https://arxiv.org/abs/1406.3411)); Yggdrasil's model does not formally derive it.

The definition matches actual causality in two places. Temporal precedence and actuality (AC1) are built into admissibility, and subset-minimality (AC3) is implied by cost-minimality when costs are positive **[DERIVED]**: deleting a redundant branch strictly lowers the cost. Full Halpern-Pearl causality is out of reach. Deciding it is DP-complete for the modified definition and Sigma2P-complete for the original in general models **[PROVEN]** ([Aleksandrowicz et al. 2017](https://arxiv.org/abs/1412.3076)), and market structural causal models are rarely available.

### 11.2 Competing explanations are the best explanation through each entry point

```
entry(S) = children of BOT in S other than terminals
for each candidate entry r (narrative in G_X with p_H(BOT -> r) > 0):
    S_r = best feasible explanation containing (BOT -> r)                 # Lemma 11.2
report every S_r with cost(S_r) <= cost(S_star) + log(R_odds)             # R_odds = 20: odds of at least 1:20
always report the abstention solution S_0 (edge BOT -> e_star) and its cost

# Lemma 11.2 (best explanation through a given entry) [DERIVED]
# Let OPT_r be the minimum cost over feasible S containing (BOT -> r). Then
#   OPT_r = c(BOT -> r) + min over nonempty X subset of T of [T_full(r, X) + T_minus_r(BOT, T - X)],
# where T_full(v, X) is the DP value on G (minimum cost of an arborescence rooted at v containing X), T_minus_r
# is the DP value on G with node r deleted, and T_minus_r(BOT, empty set) = 0.
# Proof. (>=) In an optimal S containing (BOT -> r), the subtree below r is an arborescence rooted at r containing some
# nonempty X (its leaves are terminals). The rest of S is an arborescence rooted at BOT that avoids r and contains
# T - X. The two parts cost at least T_full(r, X) and T_minus_r(BOT, T - X).
# (<=) Take minimizers of both parts for the best X and add (BOT -> r). For every node w that appears in both parts,
# delete the edge entering w in the BOT part. Each node then has exactly one parent. Ancestor chains of nodes in
# r's part stay in r's part, so no cycle forms. Prune non-terminal leaves. All terminals remain, the cost does not
# increase (costs are >= 0), and (BOT -> r) is present. QED
```

This is the arborescence form of distinct-root keyword search, where each answer has a different root ([BLINKS, He et al. 2007](https://research.ibm.com/publications/blinks-ranked-keyword-searches-on-graphs)). Here each answer has a different exogenous entry, computed exactly.

The output structure mirrors the best human-coded protocol, which assigns each jump a primary and a secondary reason, keeps an explicit "Unknown & No Explanation" category, and records disagreement among coders ([Baker et al., rev. 2025](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf)).

Contradicting evidence acts after the search. When Section 14 labels a claim CONTRADICTED, the edges that depend on it are deleted and the search reruns. Deleting edges only changes the graph, so the DP stays exact. In consistency-based diagnosis, the parsimonious consistent explanations are the minimal hitting sets of the conflict sets **[PROVEN]** ([Reiter 1987, via Jannach et al.](https://web-ainf.aau.at/pub/jannach/files/Conference_IJCAI_2015.pdf)). Conflicts that span branches and cannot be expressed as edge deletions would need a branch-and-bound outer loop, which this design does not yet specify.

## 12. Search returns a smallest explanation, with a certificate for each instance

### 12.1 Hardness rules out approximation and leaves exactness on small terminal sets

Smallest connecting subgraphs are NP-hard, and the variants Yggdrasil needs (directed, group) approximate badly **[PROVEN]**:

- **Undirected.** Approximation within 96/95 is NP-hard, and the best ratio known is ln 4 + eps < 1.39 ([Steiner tree problem summary](https://en.wikipedia.org/wiki/Steiner_tree_problem)).
- **Directed.** Directed Steiner tree admits `O(log(k)**2 / log(log(k)))` in quasi-polynomial time, and a matching lower bound holds under the Projection Game Conjecture ([Grandoni, Laekhanukit & Li 2019](https://arxiv.org/abs/1811.03020)).
- **Group.** Group Steiner tree admits no `log(k)**(2 - eps)` approximation unless NP has quasi-polynomial Las Vegas algorithms ([Halperin & Krauthgamer 2003](https://www.wisdom.weizmann.ac.il/~robi/papers/HK-GroupSteiner2-STOC03.pdf)). Time-respecting DAGs do not escape this, because the standard layered reduction produces DAG instances **[DERIVED, from the notes' argument]**.

Exact dynamic programming is exponential only in the number of terminals: `O*(3**k * n + 2**k * n**2 + n*m)` for Dreyfus-Wagner, and `2**k` with small integer weights **[PROVEN]** ([Björklund et al. 2007](https://arxiv.org/abs/cs/0611101)). The DPBF variant runs in `O(3**k * n + 2**k * ((k + log(n)) * n + m))` **[PROVEN]** ([Ding et al. 2007](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/icde07steiner.pdf)). For the NVIDIA cluster k is about 6, so `3**k = 729` and a local graph of 10,000 nodes costs about 7 million basic steps **[DERIVED arithmetic]**. The design therefore restricts the search to a certified local subgraph and solves it exactly.

### 12.2 The dynamic program and its optimality proof

```
# Directed DPBF over states (v, X), X a nonempty subset of T, on the local graph G_X; costs c >= 0 include lam_node
Tval = {}; heap = []; done = set()
for x in T:
    push(heap, (0.0, x, frozenset([x])))
while heap:
    val, v, X = pop_min(heap)                      # ties broken by (val, node_id, sorted(X))
    if (v, X) in done: continue
    done.add((v, X)); Tval[(v, X)] = val
    if v == BOT and X == frozenset(T): return val, backtrack(v, X)
    for u in parents(v):                           # grow: put edge u -> v above the arborescence at v
        push(heap, (val + c(u, v), u, X))
    for Y in finished_sets_at(v):                  # merge with finished, disjoint terminal sets at v
        if not (X & Y): push(heap, (val + Tval[(v, Y)], v, X | Y))

# Lemma 12.2 (node-cost folding) [DERIVED] Every non-root node of an arborescence has exactly one entering edge, so
# adding lam_node to every edge cost charges each non-BOT node exactly once.

# Theorem 12.1 (DP optimality) [PROVEN for undirected Steiner trees (Dreyfus-Wagner, DPBF); directed version DERIVED]
# With nonnegative costs, the first pop of (v, X) has val == Topt(v, X), the minimum cost of an arborescence rooted
# at v containing X. In particular, the first pop of (BOT, T) returns the optimum, and backtracking yields a witness.
# Proof. Achievability: each pushed value is the cost of a structure built by grow and merge steps. A merge may share
# nodes between its two parts; removing the duplicate entering edges as in Lemma 11.2 yields an arborescence of no
# larger cost. Hence val >= Topt(v, X).
# Optimality: suppose (v, X) is the first state popped with val > Topt(v, X). Take an optimal arborescence for
# (v, X) and its grow/merge decomposition down to base states (x, {x}), which are pushed with their exact value 0.
# Some state (w, Y) of the decomposition is not yet finalized while all of its decomposition children are finalized
# with exact values. When its last child was finalized, (w, Y) was pushed with a value at most the cost of the
# optimal sub-arborescence at w, which is at most Topt(v, X) < val because costs are >= 0. A min-heap would have
# popped that entry before (v, X), a contradiction (if (w, Y) == (v, X), its own smaller entry is popped first). QED
```

Admissible lower bounds can prune further without losing optimality, as in progressive A*-style group Steiner search ([PrunedDP++, Li et al. 2016](https://opus.cloud1.lib.uts.edu.au/handle/10453/121805)). Yggdrasil uses the simplest safe rule:

```
# Lemma 12.3 (branch-and-bound safety) [DERIVED]
# Let UB be the cost of any feasible explanation and d_bot(v) the shortest-path distance from BOT to v. Discarding
# every finalized state with Tval[(v, X)] + d_bot(v) >= UB loses no explanation of cost < UB.
# Proof. Let S be an explanation with cost(S) < UB whose sub-arborescence at v contains exactly the terminals X.
# The path from BOT to v and the subtree at v share no edge, so
#   cost(S) >= Topt(v, X) + d_bot(v) = Tval[(v, X)] + d_bot(v),
# using Theorem 12.1 for the finalized value. Discarding the state would therefore require cost(S) >= UB,
# contradicting cost(S) < UB. States reached by other routes are unaffected. QED
```

### 12.3 Residual mass certifies that the local subgraph contains the answer

Push-style local algorithms compute personalized PageRank with work independent of graph size, and they leave an explicit residual. Approximate PageRank runs in O(1/(eps*alpha)) and never overestimates the true vector, because the residual is nonnegative **[PROVEN, undirected]** ([Andersen, Chung & Lang 2006](https://www.math.ucsd.edu/~fan/wp/localpartition.pdf)). The heat-kernel analogue does at most `2 * N * exp(t) / eps` work ([Kloster & Gleich 2014](https://arxiv.org/abs/1403.3148)). Yggdrasil runs a directed variant on the reversed explanation graph, with transition probabilities equal to the edge weights.

```
# Push from terminal x on the reversed graph: Qrev[v][u] = p(u -> v) for parents u of v, with BOT absorbing
p = defaultdict(float); r = defaultdict(float); r[x] = 1.0; queue = deque([x])
while queue:
    v = queue.popleft()
    if r[v] < eps: continue
    mass, r[v] = r[v], 0.0
    p[v] += alpha * mass
    for u in sorted(parents_with_bot(v)):          # BOT has no parents and only absorbs
        r[u] += (1 - alpha) * mass * p_edge(u, v)
        if r[u] >= eps and u not in queue: queue.append(u)
R_x = sum(r.values());  X_x = {v for v in p if p[v] > 0}

# Lemma 12.4 (invariant and work) [DERIVED]
# Let PPR(s) = alpha * sum((1 - alpha)**n * s @ Qrev**n for n >= 0) for a row vector s >= 0.
# (i) p + PPR(r) == PPR(chi_x) after every push.
# (ii) With threshold eps, there are at most 1/(alpha*eps) pushes.
# (iii) If every node holding residual at the start of a sweep is pushed once during the sweep, sum(r) shrinks by a
#       factor of at least (1 - alpha) over the sweep.
# Proof. (i) PPR(chi_v) = alpha*chi_v + (1 - alpha)*PPR(chi_v @ Qrev) by linearity, so moving alpha*r[v] into p and
# (1 - alpha)*r[v]*Qrev[v] into r preserves p + PPR(r). (ii) Each push adds at least alpha*eps to sum(p), and
# sum(p) <= sum(PPR(chi_x)) <= 1. (iii) Every unit of residual present at the start is pushed at least once; a push
# returns at most (1 - alpha) of its mass (rows of Qrev sum to at most 1); returned mass that lands on unpushed
# nodes is pushed again and shrinks further. QED

# Lemma 12.5 (residual certificate and path bound) [DERIVED]
# (a) For every node u: 0 <= PPR(chi_x)[u] - p[u] <= R_x.
# (b) If the reversed graph has a path of L' edges from x to u with probability product pi, then
#     PPR(chi_x)[u] >= alpha * (1 - alpha)**L' * pi.
# (c) Hence p[u] > 0 whenever alpha * (1 - alpha)**L' * pi > R_x.
# Proof. (a) PPR(chi_x) - p = PPR(r) = sum over v of r[v] * PPR(chi_v), and each entry of PPR(chi_v) lies in [0, 1].
# (b) PPR(chi_x)[u] is a sum of nonnegative walk terms alpha*(1 - alpha)**len(W)*prob(W); keep the given path.
# (c) Combine (a) and (b). QED
```

```
# Theorem 12.6 (certified smallest explanation) [DERIVED]
# Run push from every terminal x in T. Let X = {BOT} | set(T) | union of X_x, let G_X be the induced subgraph, and
# fix L >= 1. Define rho_x = R_x / (alpha * (1 - alpha)**L) and
#   Gamma = min over x in T of min(-log(rho_x) + lam_node, (L + 1) * lam_node).
# Let C_X be the DP optimum on G_X (Theorem 12.1). If C_X <= Gamma, then C_X is the optimum over all of G_tau, and
# the DP's arborescence is a smallest explanation.
# Proof. Restricted solutions are feasible, so OPT <= C_X. Take any feasible S not contained in G_X. WLOG S is pruned
# (pruning non-terminal leaves never raises cost), and since G_X is induced, S has a node u outside X. In a pruned
# arborescence u lies on the path from BOT to some terminal x. Let that sub-path run from u to x with L' >= 1 edges
# and probability product pi; reversed, it is a path from x to u. Because u is not in X, Lemma 12.5(c) and
# (1 - alpha)**L' >= (1 - alpha)**L for L' <= L give: either L' > L, or pi <= rho_x.
#   If pi <= rho_x: the sub-path's costs sum to -log(pi) + L' * lam_node >= -log(rho_x) + lam_node.
#   If L' > L: the sub-path enters at least L + 1 non-BOT nodes, costing at least (L + 1) * lam_node.
# All costs are >= 0, so cost(S) >= Gamma >= C_X. No explanation outside G_X beats C_X, so OPT = C_X. QED
# If C_X > Gamma, the certificate fails. Lower eps, raise L or lam_node, or report the weaker DERIVED statement:
# C_X is optimal among explanations whose nodes reach their terminals by sub-paths with L' <= L and pi > rho_x.
```

This is the precise sense in which only a small neighborhood needs to be explored. The guarantee follows the semantics of parsimony: it certifies everything probable enough to compete, not every improbable chain. It is also a per-instance certificate rather than a worst-case theorem. Whether it succeeds on real cases is exactly the locality hypothesis tested in experiment F5.

### 12.4 Levin tree search turns transition weights into a provable effort bound

```
# Incumbent search on G_X. A search node is a partial explanation: assigned (child -> parent) pairs plus an ordered
# frontier, initially T in fixed order. Canonical rule: expand the first frontier node f. Actions: parents u of f in
# G_X plus BOT, minus any u that would close a cycle. Child probability pi(child) = pi(node) * pr(u -> f), where pr is
# p(u -> f) renormalized over the allowed actions. A new non-BOT parent joins the end of the frontier. Goal: empty
# frontier. LevinTS expands nodes in increasing d0(n)/pi(n); the mixing of Lemma 12.10 is applied to pr.

# Theorem 12.7 (Levin tree search) [PROVEN]
# For a search tree with pi(root) = 1 and pi(n) equal to the sum of its children's pi, LevinTS expands at most
# min over goal nodes n of d0(n)/pi(n) nodes before expanding its first goal.

# Lemma 12.8 (canonical bijection) [DERIVED]
# Goal leaves correspond one-to-one to pruned arborescences of G_X rooted at BOT that contain T.
# Proof. A goal leaf maps to its set of (child -> parent) pairs. Every added node is the parent of an existing node,
# so all leaves are terminals; cycles are excluded; every non-BOT node has exactly one parent. Conversely, the frontier
# node at each step is a function of the partial tree, so the arborescence forces each action to be that node's
# parent. By induction on steps, distinct leaves give distinct arborescences, and every arborescence is reached. QED

# Corollary 12.9 (effort grows as the exponential of surprisal) [DERIVED]
# Renormalization only raises probabilities, so pi(S) >= prod(p(e) for e in S), and
#   N_expansions <= min over feasible S of d0(S) * exp(sum(-log(p(e)) for e in S)).
# Proof. Theorem 12.7 with Lemma 12.8. QED

# Lemma 12.10 (robustness to a wrong prior) [DERIVED]
# Mix pr'(a) = (1 - beta) * pr(a) + beta / n_actions with n_actions <= Bmax. For every goal S at depth d:
#   N_expansions <= d0(S) * min((1 - beta)**(-d) / pi(S), (Bmax / beta)**d).
# Proof. pr'(a) >= max((1 - beta) * pr(a), beta / Bmax) at every step, and a product of maxima is at least the
# maximum of the products. Apply Theorem 12.7. QED
```

Theorem 12.7 is Theorem 3 of [Orseau et al. (2018)](https://arxiv.org/abs/1811.10928), which also shows that expanding by decreasing probability alone may never reach a goal. Corollary 12.9 is a Levin-complexity statement: description length plus log-time. Effort is linear in the explanation's size and exponential in its surprisal, so the Hawkes prior's quality translates directly into compute.

Policy-guided heuristic search tightens the bound with an admissible heuristic. It also proves a near-matching lower bound: for every proper policy and every algorithm that expands only children of expanded nodes, some trees force a loss of at least g(par(par(n*)))/pi(n*) **[PROVEN]** ([Orseau & Lelis 2021](https://arxiv.org/abs/2103.11505)). Rerooting at verified evidence nodes can cut T to `O(q * T**(1/q))` in the best case with q good rerooting points **[PROVEN]** ([Orseau, Hutter & Lelis 2024](https://arxiv.org/abs/2412.05196)). Mixing (Lemma 12.10) guarantees what PUCT cannot: a finite bound for every goal, even when the prior puts near-zero mass on the truth.

Levin search returns the minimizer of d0/pi, not of cost, so the full search runs in a fixed order:

1. Push-PPR from each terminal gives X and the residuals R_x.
2. LevinTS on G_X gives an incumbent with cost UB.
3. DPBF with the Lemma 12.3 pruning gives C_X.
4. Theorem 12.6 checks the certificate.
5. Lemma 11.2 computes the competing explanations.

### 12.5 The minimality proof itself can be checked in Lean

```
# Lemma 12.11 (subsolution certificate) [DERIVED]
# Suppose a table Tc over states (v, X) satisfies
#   (i)   Tc[(x, {x})] <= 0 for every terminal x,
#   (ii)  Tc[(u, X)] <= c(u, v) + Tc[(v, X)] for every edge u -> v and every X,
#   (iii) Tc[(v, X1 | X2)] <= Tc[(v, X1)] + Tc[(v, X2)] for all disjoint nonempty X1, X2.
# Then Tc[(v, X)] <= Topt(v, X) for all states. If, in addition, a witness arborescence has cost Tc[(BOT, T)], it is
# optimal.
# Proof. Induction on (number of edges + len(X)) of a pruned optimal arborescence Tr for (v, X), with all leaves in X.
# - No edges: X == {v}, and (i) applies.
# - v not in X with exactly one child w: cost = c(v, w) + cost(subtree) >= c(v, w) + Tc[(w, X)] >= Tc[(v, X)],
#   by the induction hypothesis and (ii).
# - Otherwise (v has at least two children, or v is in X and has a child): split X into nonempty X1, X2 carried by
#   edge-disjoint sub-arborescences at v (X1 = {v} when v is in X). Each part has fewer edges or a smaller X, so
#   cost >= Tc[(v, X1)] + Tc[(v, X2)] >= Tc[(v, X)] by (iii). QED
# Checking (i)-(iii) takes O(3^k n + 2^k m) comparisons, the same order as the DP.

# Lemma 12.12 (quantization for exact arithmetic) [DERIVED]
# Let ct(e) = ceil(c(e)/delta) * delta. If St is optimal for ct and S_star for c, then
# cost_c(St) <= cost_c(S_star) + delta * n_edges(S_star).
# Proof. c <= ct < c + delta edgewise, so cost_c(St) <= cost_ct(St) <= cost_ct(S_star) < cost_c(S_star) + delta*n_edges. QED
```

The per-incident minimality certificate has four parts:

- the push log, replayable with exact rationals, whose invariant (Lemma 12.4(i)) is proved once;
- the subsolution table;
- the witness tree;
- the inequality C_X <= Gamma.

Every component has a checker whose soundness is proved once. Running them inside Lean by reflection, in the same way as the verdict certificates of Section 14, is feasible in principle. Its cost at k = 6 and n = 10,000 is unmeasured **[CONJECTURE]**.

When k exceeds about 10, exact search stops being practical. The fallback is the primal-dual prize-collecting method with ratio 2 - 1/(n-1) ([Goemans & Williamson 1995](https://math.mit.edu/~goemans/PAPERS/GoemansWilliamson-1995-AGeneralApproximationTechniqueForConstrainedForestProblems.pdf)), whose dual value can give an instance-specific optimality gap. The best known prize-collecting ratio is now 1.7994 ([Ahmadi et al. 2024](https://arxiv.org/abs/2405.03792)). That GW implementations expose a usable dual bound was not verified **[CONJECTURE]**.

## 13. The SerpApi budget goes to the queries that best separate competing explanations

### 13.1 EC2 over explanations, with guarantees that can be cited today

SerpApi is a targeted sensor. It runs only after a case is open, and only to discriminate among the competing explanations of Section 11.2. Hypotheses are pairs h = (explanation, theta): the explanation is one of the reported S_r or the abstention S_0, and theta is a noise state that records which queries happen to retrieve relevant pages. The prior over explanations is proportional to exp(-cost(S_r)) across the reported set. That prior is the posterior of Lemma 11.1 under Conjecture 11.A, and whether it is calibrated is a **[CONJECTURE]**. Queries are templated from the claim atoms of each explanation. Each query's outcome (supports, contradicts or silent) must be a deterministic function of h.

```
# Equivalence-class determination: hypotheses h = (explanation, theta); classes = "which explanation is true"
w({h, h2})  = P(h) * P(h2)                                          # for h, h2 in different classes
E_q(h)      = {{h1, h2} : x_q(h1) != x_q(h) or x_q(h2) != x_q(h)}    # edges that query q cuts if h is true
f_EC(A, h)  = w(union(E_q(h) for q in A))
q_next      = argmax over unused q of Delta_EC(q | outcomes so far) / cost(q)     # ties: smallest query id
Q_EC        = 1 - sum(P(class_i)**2 for i)        # <= 1;  eta_EC = min edge weight >= p_min**2

# Theorem 13.0 (cited) [PROVEN]
# (GK5)  If f is adaptive monotone and adaptive submodular, then the greedy policy run for l steps satisfies
#        f_avg(greedy[l]) > (1 - exp(-l/k)) * f_avg(OPT[k]); with l = k this is 1 - 1/e.
# (GK13) If f is strongly adaptive monotone and strongly adaptive submodular and the instance is self-certifying,
#        then c_avg(greedy) <= c_avg(OPT) * (ln(Q/eta) + 1)**2.
# (GK14) Under adaptive monotonicity and adaptive submodularity only: c_wc(greedy) <= c_wc(OPT) * (ln(Q/(delta*eta)) + 1).
# (EKM2) Under adaptive monotonicity and adaptive submodularity: c_avg(greedy) <= (c_avg(OPT) + 1) * ln(n*Q/eta) + 1,
#        where n is the number of items.

# Lemma 13.1 (EC2 is strongly adaptive submodular) [DERIVED]
# For each fixed h, f_EC(., h) is a weighted coverage function of the query set, hence submodular (pointwise
# submodular). f_EC is adaptive submodular and strongly adaptive monotone (Golovin, Krause & Ray), and adaptive
# submodularity plus pointwise submodularity implies strong adaptive submodularity (Golovin & Krause).
# Proof. Coverage: adding q to A gains the weight of E_q(h) not already covered, which can only shrink as A grows.
# The remaining two facts are cited. QED

# Corollary 13.2 (EC2 bounds without the withdrawn theorem) [DERIVED]
# (a) Query until resolved, unit costs: c(EC2) <= (2*ln(1/p_min) + 1)**2 * c(OPT).
# (b) c(EC2) <= (c(OPT) + 1) * ln(Nq / p_min**2) + 1, where Nq is the number of candidate queries.
# (c) Fixed budget B with unit costs: the expected cut weight of EC2 after B queries exceeds (1 - 1/e) times that of
#     the best B-query adaptive policy.
# Proof. EC2 instances are self-certifying, with Q_EC <= 1 and eta_EC >= p_min**2, so ln(Q/eta) <= 2*ln(1/p_min).
# Substitute into GK13 via Lemma 13.1 for (a), into EKM2 for (b), and apply GK5 for (c). QED
```

The cited results come from four papers:

- GK5, GK13 and GK14 are Theorems 5, 13 and 14 of the corrected Golovin-Krause paper ([Golovin & Krause v5](https://arxiv.org/abs/1003.3967)).
- EKM2 is Theorem 2 of [Esfandiari, Karbasi & Mirrokni (2020)](https://arxiv.org/abs/1911.03620). The same paper gives a semi-adaptive scheme that reaches 1 - 1/e - eps with O(log n log k) rounds, which is useful when SerpApi calls are issued in parallel batches.
- The EC2 construction and the reasons generalized binary search and information gain fail on equivalence classes are from [Golovin, Krause & Ray (2010)](https://arxiv.org/abs/1010.3091).

These guarantees have conditions that bind in practice:

- **Noise inflates the bound.** With noise states, p_min becomes the smallest positive probability among (h, theta) pairs, which can be tiny and makes the bounds loose.
- **The guarantees are relative to the model.** They compare EC2 with the optimal policy under the assumed outcome model, so model misspecification is not covered.
- **Unequal costs are not covered.** The cost-sensitive budgeted version was not read, so non-uniform SerpApi engine pricing falls under **[CONJECTURE]**.
- **The value of information is out of reach.** Optimizing it exactly is NP^PP-hard even on polytrees ([Krause & Guestrin 2009](https://doi.org/10.1613/jair.2737)). This is the deeper reason to use a submodular surrogate.

### 13.2 Retrieved pages enter the pre-move evidence only through the archive

```
for each SerpApi result g (raw JSON archived; observation source_type = "serpapi"; first_seen = fetch time):
    o = archived_observation_with(url_key(g))
    if o is not None and first_seen[o] < tau_star:
        add g's claims to P_pre with o's first_seen and provenance      # the archive proves existence before the cutoff
    else:
        add g's claims to P_all only                                    # truth of claims, never "what moved the price"
```

Search-engine date filters leak post-event content in most questions, as Section 4 documented. Document date metadata is often inaccurate as well, so future data leaks into time-restricted retrieval ([Paleka et al. 2025](https://arxiv.org/html/2506.00723v1)).

The rule above has an exact consequence **[DERIVED]**: in a replay, no SerpApi page can enter the pre-move program unless the GDELT or RSS archive already held its URL before the cutoff. Replays reuse archived SerpApi payloads, so query outcomes stay deterministic under Theorem 3.1 even though live search results change over time.

### 13.3 Stopping is error-controlled and verdict-aware

```
LLR = log P(outcomes | leader) - log P(outcomes | runner_up)
stop if LLR >= log((1 - beta_err) / alpha_err) or LLR <= log(beta_err / (1 - alpha_err))
     or budget exhausted
     or no unused query has an outcome that would flip any verdict bit of Section 14     # diagnosticity stop
```

The two-threshold rule is Wald's SPRT. Its approximate error control carries over, but its optimality is proved only for i.i.d. observations under two simple hypotheses ([SPRT](https://en.wikipedia.org/wiki/Sequential_probability_ratio_test)). For actively chosen experiments, the right optimality citation is Chernoff's sequential design of experiments and its modern form. That theory is asymptotically optimal as the penalty for a wrong declaration grows, and it requires known outcome distributions ([Naghshvar & Javidi 2013](https://arxiv.org/abs/1203.4626)).

The diagnosticity stop is deterministic and links allocation to Heuer's sensitivity analysis: a query is worth paying for only if one of its outcomes could change a verdict. The EC2 posterior allocates queries. It never decides verdicts.

## 14. Verdicts are four bits over stable models, certified in Lean 4

### 14.1 Evidence becomes a tight normal program with defeasible acceptance

Three formalisms converge on the same structure for conflicting sources:

- skeptical and credulous inference over maximal consistent subsets ([Rescher & Manor 1970](https://doi.org/10.1007/BF00154005));
- belief as what holds in every maximally consistent evidence family ([van Benthem & Pacuit 2011](https://eprints.illc.uva.nl/423/));
- skeptical and credulous acceptance over extensions of an argumentation framework ([Dung 1995](https://doi.org/10.1016/0004-3702(94)00041-X)).

The argumentation version wins because it adds preferences, undercutters and mature solvers. Flat ABA coincides with normal logic programs under stable semantics ([Bondarenko et al. 1997](https://doi.org/10.1016/S0004-3702(97)00015-5)), and ASPIC+ supplies the attack types: undermining, rebutting and undercutting ([Modgil & Prakken 2013](https://doi.org/10.1016/j.artint.2012.10.008)).

Schum's credibility attributes (veracity, objectivity, observational sensitivity) become attackable undercutters rather than fudge factors ([Anderson, Schum & Twining 2005](https://doi.org/10.1017/CBO9780511610585)). Copy detection collapses syndicated reports to their origin before arguments are built, following the principle that copied errors otherwise get amplified ([Dong, Berti-Equille & Srivastava 2009](https://doi.org/10.14778/1687627.1687690)).

```
% clingo encoding. Facts come from the unverified preprocessing layer and are logged as premises.
reported(r17, src_a, occurred(ev_r1), b20250120).     % report, source, literal, time bucket
contrary(occurred(ev_x), not_occurred(ev_x)).         % declared contraries (both directions)
tier(src_a, 1).   independent(r17, r42).   copy_of(r52, r17).   retracted(r60).
before(ev_r1, move).   trigger(h1, ev_r1).   signature_ok(h1).   schema_refuter(h3, excludes_prior_research(v3)).

ok(R)       :- reported(R, _, _, _), not defeated(R).                  % defeasible acceptance (ABA assumption)
holds(L)    :- reported(R, _, L, _), ok(R).                           % bridge from reports to claims
defeated(R) :- reported(R, S, L, _), contrary(L, L2), reported(R2, S2, L2, _), ok(R2),
               independent(R, R2), tier(S, K), tier(S2, K2), K2 <= K.  % equal tiers defeat each other
defeated(R) :- retracted(R).
defeated(R) :- copy_of(R, _).                                         % copies add no independent support
refuted(H)  :- trigger(H, E), holds(after_cutoff(E)).                 % strict temporal refuter
refuted(H)  :- schema_refuter(H, L), holds(L).
expl(H)     :- trigger(H, E), holds(occurred(E)), before(E, move), signature_ok(H), not refuted(H).
```

The template is tight **[DERIVED]**. Its positive dependency graph has edges holds -> ok, defeated -> ok, refuted -> holds and expl -> holds, and ok depends on defeated only negatively. So the graph has no cycle.

The equal-tier rule gives a small worked case **[DERIVED]**. For two independent reports with contrary literals and equal tiers, the restriction to that pair has exactly two stable models: one accepts the first report, and the other accepts the second. If both were accepted, each would be defeated. If neither were, no defeat rule could fire, so both would be accepted.

Numeric side conditions are pre-evaluated into ground atoms such as before/2 and after_cutoff/1, which keeps real arithmetic out of the certified path. Two programs are built for every case:

- **P_pre** contains only admissible evidence, with first_seen < tau_star. It decides whether a claim can explain the move.
- **P_all** contains all evidence up to report time. It decides whether a claim is true.

Post-move evidence can therefore change a truth verdict but never the account of what moved the price.

### 14.2 The verdict map is total, exclusive and deterministic

```
SM(P) = set of stable models of P;   precondition: SM(P) nonempty (otherwise see Section 14.3)
bIN  = exists M in SM(P) with expl(H) in M          # brave
cIN  = forall M in SM(P): expl(H) in M              # cautious
bOUT = exists M in SM(P) with refuted(H) in M
cOUT = forall M in SM(P): refuted(H) in M

SUPPORTED               iff cIN
CONTRADICTED            iff cOUT
UNRESOLVED              iff bOUT and not cOUT
CONSISTENT_BUT_UNPROVEN iff not bOUT and not cIN

# Lemma 14.2 (exclusivity) [DERIVED]
# If every rule with head expl(H) contains "not refuted(H)", then no stable model contains both expl(H) and refuted(H).
# Proof. Every stable model of a normal program is a model of its Clark completion, so expl(H) in M implies that
# some rule body for expl(H) is true in M, and in particular refuted(H) is not in M. QED

# Theorem 14.1 (verdict partition) [DERIVED]
# If SM(P) is nonempty and Lemma 14.2's condition holds, exactly one of the four verdicts holds for each H.
# Proof. Exhaustive: if bOUT, the verdict is CONTRADICTED when cOUT and UNRESOLVED otherwise; if not bOUT, it is
# SUPPORTED when cIN and CONSISTENT_BUT_UNPROVEN otherwise. Exclusive:
#   cIN: every model contains expl(H), so by Lemma 14.2 none contains refuted(H). Then not bOUT, which rules out
#        UNRESOLVED; not cOUT, which rules out CONTRADICTED; and CONSISTENT_BUT_UNPROVEN requires not cIN.
#   cOUT: SM nonempty gives bOUT, which rules out CONSISTENT_BUT_UNPROVEN; UNRESOLVED requires not cOUT; and every
#        model contains refuted(H), so none contains expl(H), giving not cIN.
#   UNRESOLVED: bOUT gives a model containing refuted(H), hence not expl(H) (Lemma 14.2), so not cIN.
#   CONSISTENT_BUT_UNPROVEN: not cIN, and not bOUT implies not cOUT (because SM is nonempty). QED
```

The completion fact holds for every normal program, and for tight programs the converse also holds (Fages' theorem) **[PROVEN]** ([Erdem & Lifschitz 2003](https://doi.org/10.1017/S1471068403001765)).

The asymmetries are deliberate:

- A hypothesis refuted under some coherent reading lands in UNRESOLVED rather than CONSISTENT-BUT-UNPROVEN. This follows Heuer's rule of ranking hypotheses by the evidence inconsistent with them ([Heuer 1999](https://www.cia.gov/resources/csi/books-monographs/psychology-of-intelligence-analysis-2/)).
- Support established in only some readings stays unproven.

ACH's structure is kept but its scoring step is replaced, because controlled studies found that ACH did not improve accuracy and may increase inconsistency **[EMPIRICAL]** ([Dhami, Belton & Mandel 2019](https://strathprints.strath.ac.uk/69049/); [Mandel, Karvetski & Dhami 2018](https://www.cambridge.org/core/journals/judgment-and-decision-making/article/boosting-intelligence-analysts-judgment-accuracy-what-works-what-fails/1530E9DAE8F42B2E8FC2B5FE374DB50F)).

The raw profile, meaning the set of statuses over all models, is stored with every verdict. A diagnosticity list (the evidence items whose removal flips the verdict, computed with n+1 solver runs) is the mechanized form of ACH's sensitivity analysis.

### 14.3 A polynomial grounded core backs every verdict, and incoherent evidence is certified as such

The grounded extension is the least fixpoint of the defense operator. It is unique and contained in every complete extension, and grounded reasoning is P-complete **[PROVEN]** ([Dung 1995](https://doi.org/10.1016/0004-3702(94)00041-X); [Baroni, Caminada & Giacomin 2011](https://doi.org/10.1017/S0269888911000166)). Grounded semantics corresponds to the well-founded model of the logic program ([Wu, Caminada & Gabbay 2009](https://doi.org/10.1007/s11225-009-9210-5)), which is computable in polynomial time ([Van Gelder, Ross & Schlipf 1991](https://doi.org/10.1145/116825.116838)).

```
# Lemma 14.3 (linear-time grounded certificate) [DERIVED]
# Let (Args, Att) be an argumentation framework and Lab a labelling with natural-number ranks such that
#   (G1) every IN argument a has all of its attackers OUT, each with rank < rank(a);
#   (G2) every OUT argument b has some IN attacker c with rank(c) < rank(b);
#   (G3) Lab is a complete labelling.
# Then IN(Lab) equals the grounded extension G.
# Proof. Strong induction on rank shows IN is a subset of G and every OUT argument is attacked by G.
# - An IN argument of rank q: every attacker b is OUT with rank < q and has an IN attacker c with rank < rank(b) < q.
#   By induction c is in G, so G defends the argument, and since G = F(G) the argument is in G.
# - An OUT argument of rank q has an IN attacker of rank < q, which is in G by induction.
# (A rank-0 IN argument has no attackers, so it is in G; no OUT argument has rank 0.)
# By (G3), Lab is complete, and the grounded extension is the least complete extension, so G is a subset of IN.
# Checking (G1)-(G3) is linear in len(Att). QED
```

Core-SUPPORTED and core-CONTRADICTED flags mark hypotheses settled already in this unique, polynomial core, whichever rival reading one prefers. The core is maximally skeptical, so it loses "floating conclusions" that are reached by different routes in every rival reading. Whether those should be accepted is itself contested ([Horty 2002](https://doi.org/10.1016/S0004-3702(01)00160-6)). Reporting both the core and the stable profile exposes the difference instead of hiding it.

Contradicting sources mostly produce symmetric rebuttals. Asymmetric preferences and undercutters can create odd attack cycles, and odd cycles can leave no stable model at all. This is the argumentation analogue of geometric frustration: an antiferromagnetic triangle has no ground state that satisfies every bond. When SM(P) is empty, Yggdrasil emits INCOHERENT-EVIDENCE with a certified UNSAT proof that no stable model exists, and falls back to the grounded labelling:

- a true core atom yields SUPPORTED or CONTRADICTED;
- an undefined atom with arguments on both sides yields UNRESOLVED;
- anything else yields CONSISTENT-BUT-UNPROVEN.

How often real evidence programs lack stable models is unknown, and Section 16 measures it.

### 14.4 Complexity stays inside NP and coNP by design

For normal ground programs, stable-model existence and brave reasoning are NP-complete and cautious reasoning is coNP-complete. Disjunctive rules would raise these to Sigma2P and Pi2P **[PROVEN]** ([Dantsin et al. 2001](https://doi.org/10.1145/502807.502810)), which is why the rule language forbids them. The verdict is a fixed Boolean combination of four such queries plus one existence check, so it is decided with at most five SAT calls and lies in Theta2P **[DERIVED]**: a constant number of NP-oracle calls is in P^NP[O(log n)].

Skeptical preferred acceptance is Pi2P-complete, so preferred and semi-stable semantics are kept out of the certified path **[PROVEN]** ([Dunne & Bench-Capon 2002](https://doi.org/10.1016/S0004-3702(02)00261-8)). Logic-based abduction is Sigma2P-complete in general and NP-complete for Horn theories ([Eiter & Gottlob 1995](https://doi.org/10.1145/200836.200838)). Yggdrasil avoids it by judging a fixed, enumerated set of explanations supplied by the search, never an open abduction space.

### 14.5 Lean certifies the verdict, and the audit shows exactly what was trusted

The pipeline uses proof by reflection: write a Boolean checker, prove it sound once, and run it on certificates produced for each incident.

- **Positive answers** (NP side) come with witness models, which are checked in linear time.
- **Negative answers** (coNP side) come from CaDiCaL's LRAT refutation of the Tseitin CNF of the program's completion conjoined with the query literal. LRAT adds hints that make checking linear-time ([Cruz-Filipe et al. 2017](https://arxiv.org/abs/1612.02353)).

```lean
-- proved once (new work: no Lean library for Dung, ABA or ASP semantics was found)
theorem checkStable_sound (P : GroundProgram) (M : Finset Atom) :
    checkStable P M = true → IsStableModel P M := ...
theorem fages (P : GroundProgram) (hT : Tight P) (M : Finset Atom) :
    IsStableModel P M ↔ M ⊨ completion P := ...
theorem verdict_of_certificates (P : GroundProgram) (H : Expl) (c : Certs) :
    checkCerts P H c = true → verdict P H = c.claimed := ...

-- generated per incident
theorem incident_20250127_nvda_h3 : verdict P_pre_20250127 h3 = Verdict.contradicted :=
  verdict_of_certificates P_pre_20250127 h3 certs_h3 (by native_decide)
#print axioms incident_20250127_nvda_h3   -- shows Lean.ofReduceBool whenever native code was trusted
```

The trust policy is explicit:

- **The fast path trusts the compiler.** native_decide "adds the entire Lean compiler to the trusted part" and leaves the axiom Lean.ofReduceBool visible in #print axioms ([Lean tactic docs](https://www.cs.rochester.edu/~yzhu104/lean-gccjit/Lean/Parser/Tactic.html)). bv_decide has the same caveat: it refutes goals with the bundled CaDiCaL and checks the LRAT proof with verified algorithms ([Lean 4.12 release](https://lean-lang.org/blog/2024-10-3-lean-4120)).
- **The kernel-only path avoids native trust.** Mathlib's lrat_proof uses the Lean kernel itself as the LRAT checker ([Mathlib FromLRAT](https://florisvandoorn.com/LeanCourse25/docs/Mathlib/Tactic/Sat/FromLRAT.html)).
- **Native checking scales.** Streaming LRAT certificates into Lean while the solver is still running imported 174 TB of certificates for the empty-hexagon problem; a garbled stream can only fail the check, never yield a false theorem ([Szeider 2026](https://arxiv.org/abs/2607.00815)).
- **Precedents are thin.** The closest Lean precedent is a four-valued conflict model ([Kato 2026](https://arxiv.org/abs/2609.11174)). Abstract argumentation frameworks have been formalized in Isabelle/HOL ([Steen & Fuenmayor 2021](https://arxiv.org/abs/2110.09174)).

Kernel-only throughput at 10,000-100,000 clauses has never been benchmarked, and that is the number that decides the trust policy. The recommended fallback is kernel-only checking for the grounded core (linear-size certificates), native checking for the LRAT parts, and recorded axioms for every verdict.

Lean proves the statement "given ground program P (with this hash), the verdict for H is V". Several things are outside the proof: claim extraction from text, copy detection, source tiers, the choice of explanation schemas, and the attention model that proposed the explanations. Every published verdict states that boundary.

## 15. Replaying NVIDIA on 2025-01-27 exercises every stage

### 15.1 The dated record separates information arrival from attention arrival

| Date | Fact | Source | Relation to the move |
|---|---|---|---|
| 2024-12-27 | DeepSeek-V3 report: 2.788M H800 GPU-hours, $5.576M at $2 per hour, "excluding the costs associated with prior research and ablation experiments"; 2,048-GPU cluster | [arXiv 2412.19437v1](https://arxiv.org/html/2412.19437v1) | before |
| 2025-01-20 | R1 release: o1-parity claim, MIT license, API prices $0.55 per million input tokens (cache miss) and $2.19 per million output tokens | [DeepSeek API docs](https://api-docs.deepseek.com/news/news250120) | before |
| 2025-01-21 | Stargate, up to $500B of AI infrastructure (aggregator) | [Wikipedia](https://en.wikipedia.org/wiki/Stargate_LLC) | before |
| 2025-01-22 | R1 paper | [arXiv 2501.12948v1](https://arxiv.org/abs/2501.12948v1) | before |
| 2025-01-23 | Scale AI CEO claims DeepSeek has 50,000 H100s (unverified; aggregator of CNBC) | [OfficeChai](https://officechai.com/ai/scale-ai-ceo-says-deepseek-had-50000-nvidia-h100-gpus-elon-musk-agrees/) | before |
| 2025-01-24 | Meta guides 2025 capex to $60-65B | [Yahoo Finance/AP](https://finance.yahoo.com/news/meta-invest-65-billion-capital-141439561.html) | before |
| 2025-01-24 or 25 | "The Short Case for Nvidia Stock" (dates differ across sources) | [original post](https://youtubetranscriptoptimizer.com/blog/05_the_short_case_for_nvda); [diginomica](https://diginomica.com/node/28410) | before |
| 2025-01-24 to 27 | App downloads rise from about 1M to 2.6M; No. 1 on the US App Store on Sunday 2025-01-26 | [TechCrunch](https://techcrunch.com/2025/01/27/deepseek-displaces-chatgpt-as-the-app-stores-top-app) | before the Monday open |
| 2025-01-26 | "DeepSeek-R1 is AI's Sputnik moment" | [Fortune](https://fortune.com/2025/01/27/marc-andreessen-deepseek-sputnik-ai-markets) | before |
| 2025-01-27 | NVDA closes at $118.42, down 16.9%; a $589B loss (Bloomberg) or $593B (Reuters, Fortune) | [AP via Investment Executive](https://investmentexecutive.com/writer/matt-obrien-the-associated-press); [Bloomberg](https://www.bloomberg.com/news/articles/2025-01-27/asml-sinks-as-china-ai-startup-triggers-panic-in-tech-stocks); [Fortune](https://fortune.com/2025/01/28/deepseek-nvidia-tech-buy-dip) | the move |
| 2025-01-27 | Broadcom -17.4%, Vistra -28.27%, Constellation -20.85%, Nasdaq -3.1% (aggregator of Reuters) | [Rappler/Reuters](https://www.rappler.com/?p=2907009) | cluster |
| 2025-01-27 | Nadella: "Jevons paradox strikes again!" Nvidia calls DeepSeek "an excellent AI advancement" | [Fortune](https://fortune.com/2025/01/27/microsoft-ceo-satya-nadella-deepseek-optimism-jevons-paradox); [IG](https://www.ig.com/au/news-and-trade-ideas/why-nvidia-s-share-price-dropped-17--after-deepseek-news-250128) | timing relative to the cutoff unverified |
| 2025-01-28 | NVDA rebounds about 8.9% to $128.99 | [Motley Fool](https://www.fool.com/investing/2025/01/28/why-nvidia-stock-skyrocketed-today) | after |
| 2025-01-28/29 | Distillation allegations; Microsoft and OpenAI investigating | [BNN Bloomberg](https://bnnbloomberg.ca/business/technology/2025/01/29/microsoft-probing-if-deepseek-linked-group-improperly-obtained-openai-data) | after |
| about 2025-01-31 | SemiAnalysis estimate of about 50,000 Hopper GPUs and about $1.6B hardware capex | [Tom's Hardware](https://tomshardware.com/tech-industry/artificial-intelligence/deepseek-might-not-be-as-disruptive-as-claimed-firm-reportedly-has-50-000-nvidia-gpus-and-spent-usd1-6-billion-on-buildouts) | after |
| about 2025-01-31 to 02-01 | Commerce probe reported; Singapore cites Nvidia: "no reason to believe" | [Fox Business](https://www.foxbusiness.com/technology/us-reportedly-investigating-whether-chinas-deepseek-used-restricted-ai-chips); [Malay Mail](https://www.malaymail.com/news/singapore/2025/02/01/singapore-reaffirms-compliance-with-us-export-laws-amid-deepseek-nvidia-chip-diversion-concerns/165187) | after |
| 2025-09-17 | Nature paper: R1 training cost $294,000 on top of the V3 base model | [Daily Star/Reuters](https://d11.thedailystar.net/tech-startup/news/deepseek-spent-294000-train-its-popular-ai-model-3989806) | after |

The single measured day shows the scale **[MEASURED]**. On 2025-01-27, 1,417 English GKG documents from 681 sources matched "deepseek", peaking at 47 per batch, and 1,863 from 790 sources matched "nvidia", peaking at 55. The ramp from 2025-01-20 to 2025-01-26 has not been measured.

### 15.2 What Yggdrasil should output, stated as predictions to falsify

All items below are **[CONJECTURE]**: predictions of the specified system, not computed results.

**Case setup.** The case opens on a cluster trigger, with terminals for NVDA, Broadcom, Vistra and Constellation, plus European semiconductor names if they are in the instrument universe. The Bloomberg URL slug "asml-sinks-as-china-ai-startup-triggers-panic-in-tech-stocks" suggests that European semiconductor names moved before the US open. If so, the cluster cutoff falls early Monday, Europe time, and every weekend item (the App Store ranking, the viral thesis, the Sputnik post) is admissible under the gap rule of Section 10.

**Admissibility.** The distillation allegations, the SemiAnalysis estimates, the export-control probe and the Nature cost disclosure have first_seen after the cutoff. By the admissibility rule they cannot enter G_tau or P_pre at all **[DERIVED from Section 4]**. They inform only the truth verdicts in P_all.

**Competing explanations.** The search should return explanations through distinct entries, each a candidate root of the cascade:

- the R1-release narrative (efficiency shock, H1);
- the app-surge or viral-thesis narratives (attention cascade, H6);
- the Stargate-and-Meta-capex narrative (capex return on investment, H7);
- the chip-count claim (export controls, H4);
- the abstention solution.

**The decisive attention test.** The decisive test is whether Hawkes attribution assigns the weekend attention surge to BOT, meaning an exogenous attention event, or to the R1-release narrative as offspring. Information was public by 2025-01-20, but attention peaked on 2025-01-25/26. Separating those two arrivals is exactly what Yggdrasil's attention layer is for, and either answer is informative. A Vistra and Constellation branch through a data-center-power narrative would show that one explanation covers the cluster rather than NVDA alone, the shared-driver pattern the attention-spillover literature predicts ([Guo et al. 2018](https://arxiv.org/pdf/1703.02715)).

**Expected verdicts.**

- **The $5.6M framing (H3).** The strong "frontier AI for $5.6M all-in" claim should come out CONTRADICTED in P_pre. The pre-move primary source contains its own refuter: the V3 report's exclusion of prior research and ablations. The narrow claim of 2.788M GPU-hours for the final run should be CONSISTENT-BUT-UNPROVEN. H3 is a claim inside H1's chain, so its contradiction prunes the strong framing, not the efficiency-shock explanation itself.
- **Forecast-type explanations (H1, H7, H2).** H1 and H7 should be CONSISTENT-BUT-UNPROVEN and flagged as forecasts about future demand, which Yggdrasil does not adjudicate. The same holds for the Jevons counter-hypothesis (H2) if it is admissible at all.
- **The export-control claim (H4).** H4 should be UNRESOLVED in P_all: an allegation against an equal-tier denial is exactly the two-model case of Section 14.1.
- **The attention cascade (H6).** H6 should be SUPPORTED as a timing explanation if, and only if, Yggdrasil's own attention series shows the weekend burst before the cutoff and no comparable earlier price reaction. Both facts require the unmeasured days.

## 16. Evaluation and five falsification experiments decide the open hypotheses

### 16.1 Evaluation measures what Yggdrasil claims, against human ceilings

The best human benchmark is the jump-coding dataset of Baker, Bloom, Davis and Sammon. It holds 3,715 codings of 377 US jumps for 1980-2023 and 6,684 codings of 802 jumps for 1900-1979, and the codings are public ([Baker et al., rev. 2025](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf)). Pairwise agreement on the primary reason sets the ceiling and floor **[EMPIRICAL]**:

| Comparison (1980-2023) | Granular categories | Policy vs non-policy |
|---|---|---|
| Within WSJ | 78.0% | 92.6% |
| All coders and all papers | 58.2% | 81.0% |
| Random assignment | 18.6% | 58.1% |

Yggdrasil's evaluation has six parts:

- **(a) Category agreement.** The category of Yggdrasil's top explanation is compared with the human primary reason, between that floor and ceiling.
- **(b) Abstention calibration.** On jumps humans coded "Unknown & No Explanation", Yggdrasil should return S_0 or UNRESOLVED at a comparable rate. False-confident explanations are the key failure metric.
- **(c) Temporal integrity.** This measures the share of cited evidence with first_seen < tau_star. An LLM leakage judge, if used, must be validated against humans; the published template reached 76.1% agreement and quadratic weighted kappa 0.85 ([El Lahib et al. 2026](https://arxiv.org/html/2602.00758v1)).
- **(d) Provenance precision and recall.** These are scored against the generative-search baseline, where only 51.5% of sentences were fully supported by their citations and 74.5% of citations supported their statement **[EMPIRICAL]** ([Liu, Zhang & Liang 2023](https://arxiv.org/abs/2304.09848)).
- **(e) Contradiction coverage.** This is a new metric: the recall of expert-listed contradicting evidence, such as the V3 cost caveat.
- **(f) Post-hoc consistency.** This checks verdicts against facts resolved later, and it is retrospective only. Drift after news and reversal after no-news extreme moves can serve as a weak validation signal, never as a forecast ([Chan 2003](https://academicnewsletter.sufe.edu.cn/info/357702)).

Two further checks guard against memorization in LLM-assisted extraction:

- **Contamination probe.** LLMs reproduce pre-cutoff headlines and returns exactly, and neither instructions nor masking prevent it ([Lopez-Lira, Tang & Zhu 2025](https://arxiv.org/html/2504.14765v2)). Each case therefore runs a probe: the model is asked for the outcome with no evidence, and a correct answer flags the case as memorization-exposed.
- **Chronological cross-check.** A chronologically consistent model labels the same evidence as a cross-check ([He et al. 2025](https://arxiv.org/html/2502.21206v3)).

The engineering checks are:

- the certificate success rate of Theorem 12.6;
- LevinTS expansions against Corollary 12.9;
- how often evidence programs have no stable model;
- kernel-only Lean checking time at 10,000-100,000 clauses.

### 16.2 The experiments that decide the hypotheses

Each experiment uses rolling-origin held-out windows with one-day block bootstrap intervals, so that serial dependence does not inflate significance.

```
# F1  Semi-conservation (Conjecture 6.B)
# F1a artifact control: regress log V[t] on log(active_sources[t]) + hour-of-week. If R**2 is near 1, supply is
#     ingestion-driven and any conservation in the full sum is measurement (Lemma 5.1).
# F1b SC1: profile quasi-likelihood for omega, with B from predicted supply.   SC1 holds iff the 95% interval excludes 0.
# F1c SC2: daily supply level lev[d] = log(V/Vbar); fit lev[d] = phiL * lev[d-1] + e after controlling active sources.
#     SC2 holds iff the interval for phiL lies below 1.
# F1d SC3 and form: around exogenous high-news shocks unrelated to narrative i, fit
#       dlog_y[i] = b0 + b1 * shock + b2 * shock / size[i] + noise
#     divisive predicts b1 < 0 and b2 = 0 (equal proportional drop, Prop 6.2(a));
#     subtractive predicts b2 < 0 (equal absolute drop, Prop 6.3(a)); no competition predicts b1 = b2 = 0.
# F1e variance ratio: VR = Var(sum(e[i])) / sum(Var(e[i])) on Pearson residuals of the omega = 0 model with predicted
#     supply, excluding scheduled common-shock windows. VR < 1 supports competition; VR > 1 indicates common shocks.
# F1f transfer signature: regress (y[j][t+1] - lam[j][t+1])**2 - lam[j][t+1] - Vmeas[j][t+1] on y[:, t]. Negative
#     coefficients are the Lemma 7.4 signature; nonnegative ones are uninformative (overdispersion masks transfer).
# Decision: accept semi-conservation iff SC1, SC2 and SC3 all hold. Reject it if omega's interval contains 0 and b1
# is not significant.

# F2  Competition form
# models: M0 (omega = 0); M_sub (eta -= kappa * T_recent); M_div (omega free); M_log (eta -= omega*log(1 + S_raw/B));
#         M_share (total by NB regression, shares by Dirichlet-multinomial softmax)
# score: held-out quasi-deviance and NB2 log score
# granularity test: fit at LOD levels l and l+1 and compare predicted tracked totals on held-out windows.
#     Prop 6.2(d,e) predicts agreement within len(children)*s*log(2) per split for M_div; Prop 6.3(b) predicts a
#     discrepancy of about kappa*S per split for M_sub.
# Decision: M_sub is falsified if it loses on held-out score and shows the granularity discrepancy.

# F3  Kernel timescales and binning
# simulation: continuous-time linear Hawkes with known 1 h and 6 h exponential kernels, binned at 15 min and refit.
#     Prediction (Lemma 6.6): A_disc / A_cont = 0.885 for 1 h and 0.979 for 6 h, up to sampling error.
# real data: compare tau sets {1, 6, 24, 168} h, the same plus 2.5 h, plus 720 h, and a 12-15 exponential
#     power-law proxy; test g_how = 0 against free; track timescale weights in rolling 30-day refits.
# Decision: add a component only if held-out deviance improves beyond its bootstrap interval.

# F4  Cross-narrative excitation
# stability: the share of bootstrap refits in which group A[i][j][:] is nonzero; keep pairs above 0.8.
# placebo: shift y[j] by +/- 7 days (preserving hour-of-week); real edges lose their likelihood gain.
# confounding: add a shared latent common-shock factor to every baseline; edges that vanish were confounded.
# semantics: correlation between fitted sum(A[i][j][:]) and cos(e[i], e[j]) on held-out pairs.
# Decision: an edge is reported as influence only if it passes stability, placebo and confounding tests.

# F5  Locality of explanations (Theorem 12.6)
# corpus: coded US jumps for 1985-2023 plus curated single-stock events.
# per case: certificate success (C_X <= Gamma) at the operating (alpha, eps, L, lam_node); whether the human-coded
#     cause lies in X; the surprisal and size of S_star; LevinTS expansions against Corollary 12.9.
# Decision: locality holds for a case class if the certificate succeeds, and human causes lie in X, in at least an
# agreed share of cases (proposed 90%). Otherwise widen the push radius or drop exactness for that class.
```

The semantic check in F4 tests a published regularity: related events excite each other's attention ([Garcia-Gavilanes et al. 2017](https://doi.org/10.1126/sciadv.1602368)), while unrelated news distracts proportionally ([Hirshleifer, Lim & Teoh 2009](https://mpra.ub.uni-muenchen.de/3110/)). In this model, the first is specific excitation in A and the second is mean-field competition in omega.

The proof-of-concept adds one more experiment. Download GDELT for 2025-01-20 through 2025-01-26, which takes about 5 minutes per day of English GKG at the measured bandwidth. Then fit the model and check the predictions of Section 15.2, above all whether the weekend surge is attributed to BOT or to the R1 narrative.

## 17. Decisions still open for the user

| Decision | Options | Recommendation | Settled by |
|---|---|---|---|
| Language scope | English only; English plus Translingual | English for the PoC, disclosing the 74% document drop measured in one batch; Translingual as a robustness run | F1a and F4 sensitivity |
| Copy weight alpha_copy | 0 to 1 | 0.1, disclosed | Verdict sensitivity |
| Narrative window and lineage threshold J0 | W = 6-24 h; J0 = 0.2-0.4 | 24 h recomputed every 6 h; J0 tuned once and frozen | ID churn and purity on the PoC |
| Membership calibration | size of the labeled slice | 200-500 pairs; fit T and s0 once | Calibration curves |
| Timescale set | 4; plus 2.5 h; plus 30 d; power-law proxy | Start with 4 | F3 |
| Capacity B | predicted supply; exogenous constant; concurrent V | Predicted supply (concurrent V is mechanical by Lemma 5.1) | F1b |
| omega | free; fixed at 0 or 1 | Free | F1, F2 |
| Inference | penalized QL plus Laplace; variational Bayes; Gibbs | Penalized QL plus Laplace for the PoC | Interval coverage in simulation |
| Search-graph granularity | narrative level; time-expanded 6 h epochs | Narrative level, with lag-resolved attribution kept for later | F5 |
| Edge semantics | Hawkes attribution; transport flows | Attribution as the policy, transport as support prior and diagnostic | F1f, F4 |
| Horizon H | 3-30 days | 14 days | Verdict sensitivity |
| Abstention prior p0 | per instrument class | Calibrated on historical jump coding by class | Evaluation (b) |
| lam_node, L, alpha, eps | | Choose so the certificate succeeds on most training cases | F5 |
| Competitor odds R_odds | 10-100 | 20 | Analyst review |
| Source tiers and preference policy | historical accuracy; curated | Historical-accuracy tiers, logged as premises | Rate of incoherent evidence |
| Lean trust policy | kernel-only; native; mixed | Kernel-only grounded core, native LRAT, axioms recorded | Kernel benchmark at 10,000-100,000 clauses |
| LLM role | extraction only; none | Extraction only, archived, contamination-probed, chronologically cross-checked | Leakage audit |
| Cutoff rule for gaps and clusters | previous close; first post-gap print; cluster minimum | First post-gap print, cluster minimum | Replay sensitivity |
| SerpApi budget and costs | unit cost; engine-specific | Unit cost until the cost-sensitive theorem is checked | Literature check |
| Stopping errors | alpha_err, beta_err | 0.05 and 0.05, plus the diagnosticity stop | Evaluation (b), (e) |

## Conclusion

The research changes the question Yggdrasil asks of its attention data. "Is attention conserved?" is already answered by Yggdrasil's own measurement, trivially and uninformatively, because membership is normalized. The scientific question is how strongly narratives compete for the supply the newswires are expected to deliver. That question has a single dial, omega, which the fitted model reports alongside everything else. If the data return omega near zero, that is a finding, not a failure: publication supply would then behave like excitation without a budget, and the competition reported in the reader-attention literature would belong to readers rather than newsrooms.

The same economy of structure runs through the search. One exogenous node carries new information, roots every explanation and prices ignorance, so "we do not know" is never a fallback bolted on afterward. It is simply the cheapest explanation whenever the narrative graph cannot do better. Corollary 12.9 then ties model quality directly to proof cost. Search effort scales with the exponential of the true explanation's surprisal under the Hawkes prior, so the attention model's real job is not to predict anything. Its job is to make true explanations unsurprising, which is what makes them cheap to find and certify.

## Appendix: ledger of cited theorems and their conditions

| Result | Exact conditions | Source | Used in |
|---|---|---|---|
| Stationary nonlinear Hawkes with finite mean | Non-decreasing L-Lipschitz links; spectral radius of `L * norm1(h_plus)` below 1, or bounded links; continuous time | [Sulem et al., Lemma 2.1](https://arxiv.org/abs/2103.17164) | 6.4 |
| Stationarity of nonlinear mutually exciting processes | alpha-Lipschitz link with `alpha * integral(abs(h)) < 1` (multivariate: spectral radius) | [Brémaud & Massoulié 1996](https://doi.org/10.1214/aop/1065725193) | 6.4 |
| Count network autoregression stationarity, ergodicity and QMLE | Componentwise contraction with rho(G) < 1, G = mu1*W + mu2*I | [Armillotta & Fokianos](https://arxiv.org/abs/2202.03852) | 6.4 |
| INAR(infinity) existence; binned counts converge to Hawkes | Reproduction mean below 1; bin width tending to 0 | [Kirchner 2016](https://arxiv.org/abs/1509.02007) | 6.5 |
| Whittle estimation from bin counts is consistent | Linear stationary Hawkes; moment condition on the kernel | [Cheysson & Lang 2022](https://arxiv.org/abs/2003.04314) | 6.5 |
| Poisson QMLE consistency | INAR/INGARCH regularity conditions | [Ahmad & Francq 2016](https://doi.org/10.1111/jtsa.12167) | 6.6 |
| Lasso oracle inequality | G >= c*I and \|b - bbar\| <= d; linear multivariate point processes; least-squares contrast | [Hansen, Reynaud-Bouret & Rivoirard 2015](https://arxiv.org/abs/1208.0570) | 1, 8.1 |
| Sharp oracle inequality, l1 plus trace norm | Linear Hawkes, dictionary of unit-mass exponentials | [Bacry et al. 2020](https://arxiv.org/abs/1501.00725) | 1 |
| Granger non-causality iff zero kernel | Linear multivariate Hawkes | [Eichler, Dahlhaus & Dueck 2017](https://arxiv.org/abs/1605.06759) | 7.4 |
| Tracking regret of dynamic mirror descent | Convex losses; contractive dynamics; step proportional to 1/sqrt(t) | [Hall & Willett 2016](https://arxiv.org/abs/1409.0031) | 8.3 |
| Parent posterior factorizes | Linear Hawkes, conditional on the history | [Zhuang, Ogata & Vere-Jones 2002](https://doi.org/10.1198/016214502760046925); [Linderman & Adams 2014](https://arxiv.org/abs/1402.0914) | 7.1 |
| Exact run-length recursion | Model assumptions of BOCPD | [Adams & MacKay 2007](https://arxiv.org/abs/0710.3742) | 6.8 |
| DP-means: small-variance limit, monotone objective, order dependence | DP mixture, small-variance limit | [Kulis & Jordan 2012](https://arxiv.org/pdf/1111.0352) | 5 |
| Hyperplane collision probability 1 - theta/pi | Random hyperplanes | [Charikar 2002](https://www.cs.princeton.edu/courses/archive/spr04/cos598B/bib/CharikarEstim.pdf) | 4 |
| LV on n species equivalent to replicator on n+1 strategies | Positive orthant and interior of the simplex | [preprint citing Hofbauer 1981](https://www.biorxiv.org/content/10.1101/2025.03.28.645916.full.pdf) | 5 |
| Minimal relative entropy recovers the true path law | Gradient-drift SDE; finite initial entropy | [Lavenant et al. 2024](https://arxiv.org/abs/2102.09204) | 7.3 |
| CLS consistent from exact counts; MoM consistent under noise | Time-homogeneous chain; stated noise conditions | [Bernstein & Sheldon 2016](https://ar5iv.labs.arxiv.org/html/1604.04182) | 7.3 |
| Exact CGM inference NP-hard | Even tree-structured models | [Sheldon et al. 2013](https://proceedings.mlr.press/v28/sheldon13.html) | 7.3 |
| Exact and ordinary lumpability exactness | Finite Markov chains | [Buchholz 1994](https://resolve.cambridge.org/core/journals/journal-of-applied-probability/article/abs/exact-and-ordinary-lumpability-in-finite-markov-chains/2DC748F09D80BEEB03CCF18036E149D7) | 9 |
| Exact Steiner tree DP | Nonnegative weights; `O*(3**k * n + 2**k * n**2 + n*m)`; `2**k` with small integer weights | [Björklund et al. 2007](https://arxiv.org/abs/cs/0611101); [Ding et al. 2007](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/icde07steiner.pdf) | 12.2 |
| Steiner hardness: 96/95 inapproximable; directed `log(k)**2 / log(log(k))` tight; group no `log(k)**(2 - eps)` | Standard complexity assumptions as stated | [summary](https://en.wikipedia.org/wiki/Steiner_tree_problem); [GLL 2019](https://arxiv.org/abs/1811.03020); [HK 2003](https://www.wisdom.weizmann.ac.il/~robi/papers/HK-GroupSteiner2-STOC03.pdf) | 12.1 |
| Levin tree search bound N <= min d0/pi | Tree search; pi(root) = 1; pi additive over children | [Orseau et al. 2018](https://arxiv.org/abs/1811.10928) | 12.4 |
| PHS lower bound g(par(par(n*)))/pi(n*) | Proper policy; algorithms that expand children of expanded nodes | [Orseau & Lelis 2021](https://arxiv.org/abs/2103.11505) | 12.4 |
| Approximate PageRank in O(1/(eps*alpha)) with residual | Undirected graphs | [Andersen, Chung & Lang 2006](https://www.math.ucsd.edu/~fan/wp/localpartition.pdf) | 12.3 |
| UCT root failure probability tends to zero polynomially | Finite-horizon MDP, rewards in [0, 1], bias terms scaled by depth | [Kocsis & Szepesvári 2006](http://ggp.stanford.edu/readings/uct.pdf) | 1 |
| Adaptive greedy: 1 - 1/e; squared-log average cost; log worst case | Adaptive monotone and adaptive submodular (strong versions and self-certification for the squared-log bound) | [Golovin & Krause v5](https://arxiv.org/abs/1003.3967) | 13 |
| Adaptive greedy cost (c* + 1)*ln(nQ/eta) + 1 | Adaptive monotone and adaptive submodular | [Esfandiari, Karbasi & Mirrokni](https://arxiv.org/abs/1911.03620) | 13 |
| EC2 adaptive submodular and strongly adaptive monotone; self-certifying | Deterministic outcomes given (h, theta); known prior | [Golovin, Krause & Ray 2010](https://arxiv.org/abs/1010.3091) | 13 |
| Active sequential testing is asymptotically optimal | Known outcome distributions; wrong-declaration penalty growing | [Naghshvar & Javidi 2013](https://arxiv.org/abs/1203.4626) | 13.3 |
| Grounded extension unique, least complete; labellings correspond to extensions | Finite argumentation frameworks | [Dung 1995](https://doi.org/10.1016/0004-3702(94)00041-X); [Caminada 2006](https://doi.org/10.1007/11853886_11) | 14.3 |
| Flat ABA stable semantics: credulous NP-complete, skeptical coNP-complete | Flat frameworks | [Dimopoulos, Nebel & Toni 2002](https://doi.org/10.1016/S0004-3702(02)00245-X) | 14.4 |
| Normal programs: brave NP-complete, cautious coNP-complete; disjunctive Sigma2P/Pi2P | Ground programs | [Dantsin et al. 2001](https://doi.org/10.1145/502807.502810) | 14.4 |
| Stable models are completion models, with equality for tight programs | Normal programs; tightness for the converse | [Erdem & Lifschitz 2003](https://doi.org/10.1017/S1471068403001765) | 14.2 |
| Well-founded semantics polynomial; grounded = well-founded | Normal programs, flat frameworks | [Van Gelder et al. 1991](https://doi.org/10.1145/116825.116838); [Wu et al. 2009](https://doi.org/10.1007/s11225-009-9210-5) | 14.3 |
| Diagnoses are the minimal hitting sets of conflict sets | Consistency-based diagnosis | [Reiter 1987, via Jannach et al.](https://web-ainf.aau.at/pub/jannach/files/Conference_IJCAI_2015.pdf) | 11.2 |
| Halpern-Pearl causality: DP-complete (modified), Sigma2P-complete (original, general models) | Finite structural models | [Aleksandrowicz et al. 2017](https://arxiv.org/abs/1412.3076) | 11.1 |
| LRAT checking in linear time | LRAT proof format | [Cruz-Filipe et al. 2017](https://arxiv.org/abs/1612.02353) | 14.5 |
| Lee-Mykland statistic and its asymptotic rejection rule | Local bipower variance; K matched to sampling frequency | [Lee & Mykland 2008](https://www.scheller.gatech.edu/directory/research/finance/lee/pdf/leemykland08.pdf) | 10 |
| Shannon-cost rational inattention yields a prior-weighted logit | Discrete choice with Shannon information cost | [Matejka & McKay 2015](https://doi.org/10.1257/aer.20130047) | 6.3 |
| Propositional belief revision Pi2P-complete for most operators | Propositional knowledge bases | [Eiter & Gottlob 1992](https://doi.org/10.1016/0004-3702(92)90018-S) | 1 |
| Value-of-information optimization NP^PP-hard on polytrees | Graphical models | [Krause & Guestrin 2009](https://doi.org/10.1613/jair.2737) | 13.1 |
