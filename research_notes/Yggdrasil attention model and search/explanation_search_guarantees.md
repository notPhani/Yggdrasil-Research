# Provable Guarantees for Parsimonious Explanatory Subgraphs and Budgeted Adaptive Evidence Search (for Yggdrasil)

Notation used throughout (plain text, no LaTeX): n = |V|, m = |E|, k = number of terminals/groups/keywords, O*(.) hides polynomial factors, ln = natural log, log2 = base-2 log, "s.t." = subject to. "[VERIFIED]" means the statement was read in the primary source (PDF text) during this session. "[NOT RE-VERIFIED]" means it is standard or from prior knowledge and was not re-read this session; treat it as a pointer that needs checking before use in a proof.

---

## 1. Steiner tree family as "smallest connecting subgraph": exact DP, approximation ratios, hardness

### Takeaway
"Smallest connecting subgraph" has exact algorithms whose cost is exponential only in the number of terminals k (Dreyfus-Wagner 3^k, and 2^k for small integer weights). The approximation picture depends heavily on the variant. Undirected edge-weighted: ln 4 + eps < 1.39, and 96/95 is NP-hard to beat. Node-weighted: Theta(ln k). Prize-collecting: 1.7994 as of STOC 2024. Group: O(log^2) on trees, and log^{2-eps} k is hard. Directed: O(log^2 k / log log k) in quasi-polynomial time, and that is tight. Yggdrasil's influence graph is directed and time-ordered, so the directed and group variants are the ones to plan around. Their approximation is weak, which is the main reason to prefer exact DP over a small, locality-certified subgraph.

### Cited Findings
**Problem definition and exact DP**
- Steiner tree in graphs: given undirected G = (V, E), weights w(e) > 0, terminal set K ⊆ V, find a minimum-weight subgraph connecting K. It is necessarily a tree with leaves in K. The problem is NP-hard [VERIFIED]. — [Björklund, Husfeldt, Kaski, Koivisto, "Fourier meets Möbius" (arXiv cs/0611101; STOC 2007)](https://arxiv.org/abs/cs/0611101)
- Dreyfus-Wagner (1971) runs in O*(3^k n + 2^k n^2 + n m) time. Björklund et al. give the first O*(2^k n^2 + n m) algorithm "provided that the edge weights are small integers", i.e. pseudo-polynomial in the max weight M, via fast subset convolution over the min-sum semiring [VERIFIED]. — [Björklund et al. 2007](https://arxiv.org/abs/cs/0611101)
- Mölle, Richter and Rossmanith, and then Fuchs, Kern, Mölle, Richter, Rossmanith and Wang (2007), give O*((2+eps)^k p(n)) for any fixed eps > 0. The degree of p(n) grows like 12 sqrt(eps^-1 ln eps^-1), with examples O*(2.5^k n^14.2) and O*(2.1^k n^57.6), so it is impractical for small eps [VERIFIED as quoted by Björklund et al.]. — [Björklund et al. 2007](https://arxiv.org/abs/cs/0611101)
- Steiner tree is FPT in |S| via Dreyfus-Wagner in 3^|S| poly(n). Faster variants run in c^|S| poly(n) for any c > 2, or 2^|S| poly(n) W for small weights (W = max edge weight). Polynomial-space algorithms run in 2^|S| poly(n) W (Lokshtanov & Nederlof 2010) and 7.97^|S| poly(n) log W (Fomin, Kaski, Lokshtanov, Panolan et al. 2015) [VERIFIED, Wikipedia summary]. — [Wikipedia: Steiner tree problem](https://en.wikipedia.org/wiki/Steiner_tree_problem)
- Parameterized lower bounds. There is no 2^{eps t} poly(n) algorithm for any eps < 1 (t = number of edges of the optimal tree) unless Set Cover has a 2^{eps n} poly(m) algorithm (Cygan et al. 2016). There is no polynomial kernel unless coNP ⊆ NP/poly, even with unit weights and parameter t (Dom, Lokshtanov, Saurabh 2014) [VERIFIED, Wikipedia summary]. — [Wikipedia: Steiner tree problem](https://en.wikipedia.org/wiki/Steiner_tree_problem)
- Erickson, Monma & Veinott (1987), "Send-and-split method for minimum-concave-cost network flows" (Math. of OR 12(4):634-664). This is the Dreyfus-Wagner-type DP. For uncapacitated networks with n nodes, a arcs and d+1 demand nodes, the search snippet reports an operation count of the form (n/2)*3^d + s*2^d with s = n log2 n + 3a. I reconstructed that from a garbled snippet, but it matches the commonly cited O(3^k n + 2^k (n log n + m)) for Dreyfus-Wagner with Fibonacci-heap shortest paths. — [INFORMS (EMV 1987)](https://pubsonline.informs.org/doi/fpi/10.1287/moor.12.4.634)

**Approximation and hardness (undirected, edge-weighted)**
- Approximation ratios: the MST heuristic gives 2 - 2/t, Robins-Zelikovsky (2000) give 1.55, and Byrka, Grandoni, Rothvoß & Sanità (STOC 2010; JACM 2013) give **ln(4) + eps <= 1.39** via an LP relaxation with iterative randomized rounding. Approximating within **96/95 ≈ 1.0105 is NP-hard** (Chlebík & Chlebíková 2008) [VERIFIED, Wikipedia summary]. — [Wikipedia: Steiner tree problem](https://en.wikipedia.org/wiki/Steiner_tree_problem)

**Node-weighted Steiner tree (NWST)**
- Klein & Ravi: a greedy "spider decomposition" algorithm with ratio **2 ln k**. Guha & Khuller (Information and Computation 1999): 1.5 ln k with "branch-spiders", generalized to **(1.35 + eps) ln k**, plus a practical greedy with ratio 1.6103 ln k [VERIFIED, abstract-level]. — [Guha & Khuller, UMD tech report CS-TR-3849](https://drum.lib.umd.edu/handle/1903/924)

**Prize-collecting Steiner tree (PCST)**
- PCST: each vertex has a penalty that can be paid instead of connecting it. Minimize (tree edge cost) + (penalties of vertices not in the tree) [VERIFIED]. — [Ahmadi, Gholami, Hajiaghayi, Jabbarzade, Mahdavi, "PCST: A 1.79 Approximation" (STOC 2024)](https://arxiv.org/abs/2405.03792)
- Goemans & Williamson (SICOMP 24(2):296-317, 1995): primal-dual, purely combinatorial (no LP solve). The PCST guarantee in the paper is **(2 - 1/(n-1))** times the LP optimum [VERIFIED, inequality "Ys <= (2 - 1/(n-1)) ..." in the PCST section; PDF OCR is noisy]. The abstract states O(n log n)-type running times and factor 2 for most constrained forest problems. The PCST implementation is usually quoted as O(n^2 log n); the PDF OCR drops superscripts, so check this. — [Goemans & Williamson 1995 PDF](https://math.mit.edu/~goemans/PAPERS/GoemansWilliamson-1995-AGeneralApproximationTechniqueForConstrainedForestProblems.pdf)
- Archer, Bateni, Hajiaghayi & Karloff (FOCS 2009) improved 2 to **1.9672**. Ahmadi et al. (STOC 2024) improved it to **1.7994** with an iterative approach that uses GW as the baseline and a weighted average of three solutions with beta = 1.252 [VERIFIED]. — [Ahmadi et al. 2024](https://arxiv.org/abs/2405.03792)

**Group Steiner tree (GST)**
- Garg, Konjevod & Ravi (SODA 1998; J. Algorithms 2000) give a randomized polylog approximation. On trees, the later covering-Steiner paper gives O(log N log(mK)) and notes "for the group Steiner problem with K = 1, this approximation ratio matches the best-known ratio", i.e. GKR on trees is **O(log N log m)** (N = max group size, m = number of groups) [VERIFIED]. — [Konjevod, Ravi, Srinivasan, covering Steiner (CMU PDF)](https://www.contrib.andrew.cmu.edu/~ravi/cst.pdf)
- General graphs lose a probabilistic tree-embedding factor. A search summary reports GKR's general-graph bound as **O(log^3 n log k)**, and O(log^2 n log k) for graphs excluding small minors [search summary of the GKR record; not read in full]. — [GKR record, IAS repository](https://repository.ias.ac.in/101268/)
- Halperin & Krauthgamer (STOC 2003): for every fixed eps > 0, GST admits no efficient **log^{2-eps} k** approximation unless NP has quasi-polynomial Las Vegas algorithms. This holds even on hierarchically well-separated trees, and is nearly tight with the known log-squared ratio on trees [VERIFIED, abstract-level]. — [Halperin & Krauthgamer STOC 2003 PDF](https://www.wisdom.weizmann.ac.il/~robi/papers/HK-GroupSteiner2-STOC03.pdf)
- Exact GST with k groups (keywords): DPBF runs in **O(3^k n + 2^k ((k + log n) n + m))** (see Section 2). — [Ding et al., ICDE 2007](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/icde07steiner.pdf)

**Directed Steiner tree (DST)**
- DST: given a directed weighted graph, root r and k terminals, find a minimum-cost arborescence with an r-to-t path for every terminal. Grandoni, Laekhanukit & Li (STOC 2019) give an **O(log^2 k / log log k)** approximation in quasi-polynomial time n^{polylog k}. Under the Projection Game Conjecture and NP not ⊆ ∩_{0<delta<1} ZPTIME(2^{n^delta}), they prove a **matching Omega(log^2 k / log log k)** lower bound for quasi-polynomial algorithms. They note the classical Charikar et al. quasi-polynomial algorithm is actually **O(log^3 k)**: Charikar et al. claimed O(log^2 k) "due to a mistake in prior work". Charikar et al. also give the polynomial-time O(k^eps) regime [VERIFIED]. — [Grandoni, Laekhanukit, Li 2019](https://arxiv.org/abs/1811.03020)

### Inferences
- **Dreyfus-Wagner/DPBF recurrence** (standard form, reproduced from memory; matches DPBF's tree-grow/tree-merge description). Let T(v, X) be the minimum cost of a tree rooted at v that covers terminal subset X. Then:
  T(v, X) = min( min over edges (v,u) of [w(v,u) + T(u, X)] (grow), min over disjoint X1, X2 with X1 ∪ X2 = X of [T(v, X1) + T(v, X2)] (merge) ),
  with T(v, {t}) = 0 if v satisfies terminal t. Process states in increasing cost order (Dijkstra over (v, X)). The first time a state (v, K) is popped, it is optimal. This "first pop is optimal" property is exactly what makes DPBF return the minimum tree, and it is what Yggdrasil can cite to prove minimality.
- The same DP runs on directed graphs: grow along reversed edges to get an arborescence rooted at the market event. It also handles node weights by charging the node weight on the edge that enters the node. The 3^k bound is unchanged [NOT RE-VERIFIED as a citation; standard].
- If edges must respect time (an upstream narrative must precede downstream nodes), the graph is a DAG. That does not make DST easy: the standard layered reduction from GST produces DAG instances, so the Halperin-Krauthgamer hardness carries over [my inference].
- Rough feasibility of exact DP (arithmetic on 3^k n, constants ignored): k = 8 and n = 1e5 is about 6.6e8 basic steps. k = 10 and n = 1e5 is about 5.9e9. k = 12 and n = 1e4 is about 5.3e9. Exact search is realistic for k <= ~10 on a locally restricted subgraph of ~1e4 to 1e5 nodes (see Section 5 for how to certify the restriction).

### Gaps
- I did not read Byrka et al. or Chlebík & Chlebíková directly; the ratios come from the Wikipedia summary.
- I did not verify the node-weighted hardness statement. It is standard that NWST generalizes Set Cover, so there is no (1 - eps) ln k approximation unless NP ⊆ DTIME(n^{O(log log n)}), but I found no primary source this session.
- I did not verify the exact form of Charikar et al.'s polynomial-time tradeoff (often quoted as i^2 (i-1) k^{1/i} in time O(n^i k^{2i})).
- Nederlof's ICALP 2009 polynomial-space result was not checked separately. Wikipedia attributes the poly-space 2^k poly(n) W bound to Lokshtanov & Nederlof 2010.
- The exact running time of the GW PCST implementation is not pinned down: OCR ambiguity between O(n log n) and O(n^2 log n).

---

## 2. Keyword search over graphs returning minimal trees: BANKS, DPBF, BLINKS and their optimality guarantees

### Takeaway
Of the classic graph keyword-search systems, only the DP family (DPBF 2007, and PrunedDP/PrunedDP++ 2016) returns the provably optimal group Steiner tree (top-1). They do it in time exponential only in the number of keywords. BLINKS changes the objective ("distinct-root" semantics: sum of root-to-keyword distances), which makes optimality tractable, and it proves an instance-optimality-style bound on its backward expansion. BANKS-style backward expansion is heuristic.

### Cited Findings
- **DPBF** (Ding, Yu, Wang, Qin, Zhang, Lin, ICDE 2007) studies GST-k: find the top-k minimum-cost connected trees that contain at least one node from every keyword group. For k = 1 this is the minimum-cost group Steiner tree (NP-complete). DPBF is a parameterized solution with time **O(3^l n + 2^l ((l + log n) n + m))**, l = number of keywords [VERIFIED via abstract/summary]. — [Ding et al., ICDE 2007 (MSR PDF)](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/icde07steiner.pdf)
- **BLINKS** (He, Wang, Yang, Yu, SIGMOD 2007): top-k keyword search on graphs with a bi-level index (graph partitioned into blocks, with block-level summaries plus intra-block shortest-path information). Its "cost-balanced expansion" backward search has cost **within a factor of m (the number of query keywords) of an optimal "oracle" backward search strategy** that visits the minimum number of nodes needed to produce the top-k answers. The index allows forward jumps from a node to a keyword, which makes the search effectively bidirectional [VERIFIED, abstract-level]. — [BLINKS (IBM Research record)](https://research.ibm.com/publications/blinks-ranked-keyword-searches-on-graphs); [Duke Scholars record](https://scholars.duke.edu/publication/807130)
- **PrunedDP / PrunedDP++** (Li, Qin, Yu, Mao, SIGMOD 2016): an "efficient and progressive" GST algorithm based on optimal-tree decomposition and conditional tree merging. It adds a progressive A*-search with carefully designed lower bounds, finds the optimal solution, and reports at least two orders of magnitude speedup over the prior state of the art [VERIFIED, abstract-level]. — [UTS record](https://opus.cloud1.lib.uts.edu.au/handle/10453/121805)
- Follow-ups exist on GPU-accelerated optimal GST search and on GST with both vertex and edge weights (titles only; not read). — [dbscholar listing](https://rmarcus.info/dbscholar/papers/12303)

### Inferences
- DPBF is Dreyfus-Wagner with a virtual source per keyword group, run as best-first search over (node, keyword-subset) states. Its optimality argument is the "first pop is optimal" Dijkstra argument. PrunedDP++ keeps that and adds admissible lower bounds (A*), so the A* optimality theorem in Section 4 gives the same optimality guarantee with fewer expansions.
- BLINKS' distinct-root semantics (score = sum over keywords of dist(root, nearest keyword node)) is a shortest-path-tree relaxation of Steiner cost. It overcounts shared edges, so it is not parsimonious in the Steiner sense. It is a natural way to enumerate *competing* explanations, though, because each answer has a different root (for Yggdrasil, a different upstream narrative).
- For Yggdrasil, "competing explanations" maps onto DPBF's progressive top-k, or onto root-distinct top-k (one optimal tree per candidate upstream narrative root, each computed exactly).

### Gaps
- I could not download the BANKS (Bhalotia et al., ICDE 2002) or BANKS-II (Kacholia et al., VLDB 2005) papers. My belief is that both use backward or bidirectional expanding search heuristics, emit answers in approximately ranked order, and have no optimality guarantee. That is not verified this session.
- I could not access DPBF's exact space bound (I believe O(2^l n)) or the precise progressive top-k guarantee.
- PrunedDP++'s exact "progressive approximation ratio" statement was not read.
- Kimelfeld & Sagiv (PODS 2006) and Golenberg, Kimelfeld & Sagiv (SIGMOD 2008) cover approximate top-k enumeration with polynomial delay. I did not research them.

---

## 3. Abduction and diagnosis: parsimonious covering, minimal hitting sets, complexity of abduction, MPE/MAP, MDL

### Takeaway
There are three formal notions of "parsimonious explanation":
1. Set-cover parsimony: a minimal or minimum cover of the observed manifestations (Peng-Reggia).
2. Consistency-based parsimony: a minimal hitting set of conflicts (Reiter).
3. Probabilistic parsimony: MPE/MAP, or MDL.

The complexity ladder is steep. Finding *some* explanation is often polynomial. Finding a *best* (minimum or most plausible) one is NP-hard (Bylander et al.). Logic-based abduction is Sigma2P-complete in general (Eiter-Gottlob). MPE is NP-complete, and MAP is NP^PP-complete, staying NP-complete even on polytrees (Park-Darwiche).

### Cited Findings
- **Parsimonious covering theory** (Peng & Reggia 1990). A diagnostic problem is a 4-tuple P = <D, M, C, M+>: D = disorders, M = manifestations, C = causal relation, M+ = observed manifestations. The solution Sol(P) is defined as the set of all *irredundant covers* of M+ (covers with no proper subset that is also a cover). This set can be very large, which motivated the probabilistic extension that ranks hypotheses by likelihood [VERIFIED, secondary summaries]. — [UMIACS summary of parsimonious covering theory](https://www.umiacs.umd.edu/publications/modeling-diagnostic-reasoning-summary-parsimonious-covering-theory); [CEUR-WS Vol-1648 paper2](https://www.ceur-ws.org/Vol-1648/paper2.pdf)
- **Reiter 1987**, "A theory of diagnosis from first principles" (AIJ 32:57-95). A conflict set is a set of components that cannot all be functioning normally given SD and OBS. A hitting set intersects every set in a collection. **Central theorem: a diagnosis is a minimal hitting set of the collection of (minimal) conflict sets.** Reiter computes diagnoses with a breadth-first HS-tree that uses pruning and conflict reuse [VERIFIED via secondary sources]. — [Jannach et al. IJCAI 2015 (summarizing Reiter)](https://web-ainf.aau.at/pub/jannach/files/Conference_IJCAI_2015.pdf)
- Greiner, Smith & Wilkerson (1989) published a correction to Reiter's HS-tree algorithm (the HS-DAG variant fixes a pruning flaw). — [Greiner et al. correction PDF](https://www.cse.sc.edu/~mgv/csce580sp14/greinerCorrectionReiter.pdf)
- **Bylander, Allemang, Tanner & Josephson 1991**, "The computational complexity of abduction" (AIJ 49(1-3):25-60). For abduction defined as finding the most plausible combination of hypotheses that explains all the data, the problem is **NP-hard in general**. Three factors drive intractability: choosing between *incompatible* hypotheses, reasoning about *cancellation* effects, and satisfying the *maximum plausibility* requirement. The paper also identifies a tractable restricted class [VERIFIED, abstract-level]. — [Cambridge chapter summary](https://www.cambridge.org/core/books/abductive-inference/computational-complexity-of-abduction/EA4BCC2B10F4A39683E346643CAB9E24); [datalearner record](https://www.datalearner.com/academic/journal-papers/0004-3702/volumes-and-issues/129/paper-detail/457)
- **Eiter & Gottlob 1995**, "The complexity of logic-based abduction" (JACM 42(1):3-42). Deciding whether a propositional abduction problem has a solution is **Sigma2P-complete**, even if the abducibles and query variables are all the variables and the KB is in CNF. It is **NP-complete when the KB is Horn**, even acyclic Horn. Relevance (is hypothesis h in some subset-minimal explanation?) is Sigma2P-complete. Known polynomial classes include a definite Horn CNF KB with a query that is a conjunction of positive literals (Selman & Levesque) [VERIFIED via Gottlob-Pichler-Wei's summary and search summaries]. — [Zanuttini, "New polynomial classes for logic-based abduction" (JAIR; arXiv 1106.5263)](https://arxiv.org/abs/1106.5263); [JACM 1995 index](https://projects.csail.mit.edu/jacm/jacm95.html)
- **MPE/MAP in Bayesian networks** (Park & Darwiche, JAIR 2004). D-MPE is **NP-complete (Shimony 1994)**. D-MAP is **NP^PP-complete** (Theorem 1). It stays NP^PP-complete under strong restrictions, e.g. network depth 2 (Theorem 2). NP^PP contains the whole polynomial hierarchy (Toda). MAP is **NP-complete even on polytrees**, cannot be effectively approximated there, and stays hard even when MPE and Pr are easy [VERIFIED]. — [Park & Darwiche 2004](https://arxiv.org/abs/1107.0024)
- **VoG** (Koutra, Kang, Vreeken, Faloutsos; SDM 2014, SADM 2015). VoG builds a vocabulary of subgraph types that occur often in real graphs (stars, cliques, chains, etc.) and looks for the most succinct description of the graph in that vocabulary under **MDL**. A subgraph enters the summary if it lowers total description length. Contributions are an encoding scheme, the VoG algorithm for minimizing description cost, and experiments on multi-million-edge graphs [VERIFIED, abstract-level]. — [VoG (arXiv 1406.3411)](https://arxiv.org/abs/1406.3411); [VoG project page](https://vreeken.groups.cispa.de/prj/vog/)

### Inferences
- Minimum-cardinality covers and minimum hitting sets are Set Cover in disguise. So "smallest explanation" is NP-hard to find and ln-approximable by greedy, while irredundant (subset-minimal) explanations can be found greedily in polynomial time by deleting redundant elements. That is exactly the "find one vs. find best" gap Bylander et al. describe.
- MDL two-part code length L(S) + L(data | S) equals -log P(S) - log P(data | S) up to coding constants. Minimizing it is MAP over explanation structures. PCST can be read as a special two-part code: "model cost" = edge/node costs of the tree, "data cost" = penalties for evidence left unexplained. This is an analogy that has to be made precise by picking codes; it is not a theorem from these sources.
- Contradicting evidence fits Reiter's consistency framing. A set of edges or claims that cannot all hold together given a contradicting observation is a conflict. Candidate explanations that survive must hit every conflict, and the minimal hitting sets are the parsimonious survivors.

### Gaps
- Not verified this session:
  - Peng & Reggia's exact probabilistic causal model likelihood. From memory: L(D_I, M+) = L1 L2 L3, with L1 = prod over m_j in M+ of (1 - prod over d_i in D_I of (1 - c_ij)), L2 = prod over d_i in D_I, m_l in effects(d_i) \ M+ of (1 - c_il), L3 = prod over d_i in D_I of p_i/(1 - p_i).
  - Their theorems on when the most probable explanation is irredundant.
  - de Kleer & Williams 1987 (GDE, AIJ 32:97-130). From memory: ATMS-based minimal conflicts, candidates as minimal hitting sets, and probe selection by one-step minimum expected entropy. No source was fetched.
- Eiter-Gottlob's full table was not re-read: necessity Pi2P-complete, and the Delta-level classes for cardinality or priority minimality.
- Treewidth-exponential exact MPE (variable elimination, O(n exp(w))) and MPE inapproximability (Abdelbar & Hedetniemi 1998) are standard but not re-verified.
- VoG's specific heuristics (PLAIN / TOP-K / GREEDY'NFORGET) and the absence of an optimality guarantee are from memory. Finding the MDL-optimal model is generally intractable.
- Rissanen (1978, Automatica, "Modeling by shortest data description") was not fetched.

---

## 4. Search algorithms with guarantees: A*, branch and bound, MCTS/UCT, PUCT, Levin tree search, PHS

### Takeaway
- A* with an admissible heuristic returns an optimal solution. With a consistent heuristic it is optimally efficient among admissible A*-like algorithms.
- UCT has only asymptotic guarantees: polynomial-rate failure convergence. The log-bonus proof was later shown to be incomplete, and the worst case is hyper-exponential in depth. AlphaZero-style PUCT has no matching theorem and fails at low simulation budgets.
- The policy-guided family has finite, prior-dependent bounds that are exactly what a "transition weights as prior" design needs. Levin tree search (expansions <= min over goals of d0(n)/pi(n)), PHS (loss <= g(n*)/pi(n*) times a heuristic factor, with a near-matching lower bound) and rerooted sqrt-LTS (2024) all give such bounds.

### Cited Findings
**A* and optimal efficiency**
- A* with an admissible heuristic is admissible, i.e. it returns an optimal solution. A heuristic is consistent (monotone) if h(x) <= d(x, y) + h(y) for every edge (x, y). Dechter & Pearl (JACM 1985) proved that A* with a consistent heuristic is **optimally efficient with respect to all admissible A*-like algorithms** (on the *set* of nodes expanded, not the number of expansions). With an admissible but inconsistent heuristic, A* can expand a node exponentially many times in the worst case (Martelli). Relaxing admissibility (weighted A*) trades optimality for speed with bounded suboptimality [VERIFIED, Wikipedia summary]. — [Wikipedia: A* search algorithm](https://en.wikipedia.org/wiki/A*_search_algorithm)

**UCT / MCTS**
- Kocsis & Szepesvári (ECML 2006) run UCB1 at each node with bias c_{t,s} = 2 C_p sqrt(ln t / s). **Theorem 6**: consider a finite-horizon MDP with rewards in [0,1], horizon D and K actions per state, and UCT with UCB1 bias terms multiplied by D. Then the bias of the estimated expected payoff X̄_n is **O(log(n)/n)**, and the **failure probability at the root converges to zero at a polynomial rate** as the number of episodes grows to infinity [VERIFIED]. — [Kocsis & Szepesvári 2006 PDF](http://ggp.stanford.edu/readings/uct.pdf)
- Coquelin & Munos (UAI 2007, INRIA RR): UCT can be overly optimistic, with regret **Omega(exp(exp(...exp(1)...)))** (D-1 nested exponentials, D = depth) in the worst case. They propose modified variants with depth-exponential but not hyper-exponential regret [VERIFIED for the lower bound wording]. — [Coquelin & Munos, "Bandit algorithms for tree search"](https://arxiv.org/abs/cs/0703062)
- Shah, Xie & Xu (SIGMETRICS 2020 extended abstract; arXiv v4 2020): the claimed proof that UCT approximates the value function "is incomplete", because the logarithmic bonus assumes regret of the recursively dependent non-stationary bandits concentrates exponentially, which is unlikely to hold. They prove polynomial concentration and propose a **polynomial bonus B_{t,s} ~ t^{1/4}/s^{1/2}** (with eta = 1/2). **Theorem 1**: for an MDP satisfying their Assumption 1, with appropriate constants, |E[V̂_n(s)] - V*(s)| <= gamma^H eps0 + O(n^{eta-1}) for 1/2 <= eta < 1, giving a best-case rate of **O(n^{-1/2})**. Here eps0 = ||V̂ - V*||_inf is the leaf-value error. They note AlphaGo Zero's bonus scales as t^{1/2}/s, "qualitatively similar" to theirs [VERIFIED]. — [Shah, Xie, Xu](https://arxiv.org/abs/1902.05213)

**PUCT (AlphaZero) and its failure modes**
- AlphaZero's selection rule is argmax_a [ Q(x,a) + c * pi_theta(a|x) * sqrt(sum_b n(x,b)) / (1 + n(x,a)) ]. Grill et al. (ICML 2020) show the empirical visit distribution approximately tracks the solution of a **regularized policy optimization** problem, and note the original algorithm can fail, "e.g., when per-search simulation budgets are low" [VERIFIED]. — [Grill et al. 2020](https://arxiv.org/abs/2007.12509)
- Danihelka, Guez, Schrittwieser & Silver (ICLR 2022): AlphaZero "can fail to improve its policy network if not visiting all actions at the root of a search tree". Gumbel AlphaZero/MuZero samples actions without replacement and replaces AlphaZero's heuristic mechanisms with a policy-improvement-guaranteeing procedure, which significantly improves planning with few simulations [VERIFIED, abstract-level]. — [Danihelka et al. ICLR 2022](https://iclr.cc/virtual/2022/poster/6418)

**Levin tree search (LevinTS)**: Orseau, Lelis, Lattimore & Weber, NeurIPS 2018
- *Setting*: a policy pi over action sequences (nodes) with pi(n0) = 1 and pi(n) = sum over children n' of pi(n'). d0(n) is the length of the action sequence, and the usual depth is d(n) = d0(n) - 1. N(TS, N^g) is the number of expansions before the first node of target set N^g is expanded [VERIFIED].
- *Theorem 1*: expanding nodes in decreasing order of pi(n) alone "may never expand any node of the target set N^g, even if for all n in N^g, pi(n) > 0" [VERIFIED].
- *Theorem 2*: LevinTS (best-first in increasing d0(n)/pi(n), with state cuts under a Markovian policy) expands states in best-first order and at their lowest cost first [VERIFIED].
- **Theorem 3**: for any target set N^g, **N(LevinTS, N^g) <= min over n in N^g of d0(n)/pi(n)**. The proof uses the facts that every leaf of the current search tree has d0/pi <= c and that the leaves' probabilities sum to <= 1. The bound extends Levin search's theorem (Solomonoff 1984) to trees and is tight within a small factor on some trees [VERIFIED].
- *Theorem 4 (multiTS, known max depth d_max)*: E[N] <= d_max / pi+_{d_max}, where pi+_{d_max} = sum of pi(n) over target nodes with d0(n) <= d_max [VERIFIED].
- **Theorem 6 (LubyTS(inf,1), unknown depth)**: E[N(LubyTS, N^g)] <= min over d >= 1 of [ d + (d / pi+_d) * ( log2(d / pi+_d) + 6.1 ) ], with pi+_d the cumulative probability of target nodes of depth <= d. Adapting to an unknown depth costs an extra log(d/pi+_d) factor. LubyTS is good when many solutions exist, e.g. O(d log d) when target nodes at depth d have cumulative probability 1/2, where LevinTS needs about 2^d [VERIFIED]. — [Orseau et al. 2018](https://arxiv.org/abs/1811.10928)

**Policy-guided heuristic search (PHS)**: Orseau & Lelis, AAAI 2021
- *Setting*: a non-negative loss l(n) per expanded node and g(n) = sum of l(n') over n' in anc*(n) (with l = 1, g(n) = d0(n)). Heuristic factor eta(n) >= 1. PHS = best-first with **phi(n) = eta(n) * g(n) / pi(n)** (phi = inf if pi(n) = 0). The analysis uses the monotone phi+(n) = max over ancestors of phi, and eta+(n) = phi+(n) pi(n) / g(n) >= eta(n). L_phi(n) = leaves of {n' : phi+(n') <= phi+(n)} [VERIFIED].
- **Theorem 1 (PHS upper bound)**: for any non-negative loss, any solution set N_G, any policy pi and any eta >= 1, PHS returns n* in argmin over N_G of phi+(n*), and the **search loss L(PHS, n*) <= (g(n*)/pi(n*)) * eta+(n*) * sum over n in L_phi(n*) of pi(n)/eta+(n)** [VERIFIED].
- **Corollary 2**: if eta = 1 everywhere, **L(PHS, n*) <= g(n*)/pi(n*)**. This equals the LevinTS bound when l = 1 [VERIFIED].
- **Theorem 4 (lower bound)**: for every proper policy (children's conditional probabilities sum to 1), every non-negative loss with l(n0) = 0, and every search algorithm S that expands only children of already expanded nodes, there exist trees and solution sets with **min over n* of L(S, n*) >= g(n̂*)/pi(n*), where n̂* = par(par(n*))**. So Corollary 2 is near-tight for *any* algorithm [VERIFIED].
- *PHS-admissible eta*: for all n and all solution descendants n*, phi(n) <= phi(n*) and eta(n*) = 1. **Corollary 5**: then L(PHS, n*) <= (g(n*)/pi(n*)) * sum over n in L_phi(n*) of pi(n)/eta+(n), a strict improvement because the sum is <= 1. **Theorem 6**: if h is admissible for A*, then eta_h(n) = (g(n) + h(n))/g(n) is PHS-admissible (phi_h = (g + h)/pi). **Corollary 7**: L <= (g(n*)/pi(n*)) * sum over leaves of pi(n)/(1 + h+(n)/g(n)) [VERIFIED].
- *PHS\**: etâ_h(n) = (1 + h(n)/g(n)) / pi(n)^{h(n)/g(n)}, giving phî_h(n) = (g(n) + h(n)) / pi(n)^{1 + h(n)/g(n)}, an estimate of g(n*)/pi(n*). It may not be PHS-admissible, so Theorem 1 holds but Corollary 5 may not. *Theorem 10*: the Theorem 1 bound survives safe state pruning under stated assumptions [VERIFIED]. — [Orseau & Lelis 2021](https://arxiv.org/abs/2103.11505)

**Recent LTS work (2023-2026)**
- Orseau, Hutter & Lelis (IJCAI 2023; arXiv v3 Nov 2024): the LTS bound used as a training loss ("LTS loss") is **convex** for parameterized context models (LTS+CM), which enables convex optimization with convergence guarantees. With NN policies it is non-convex [VERIFIED, abstract-level]. — [LTS with Context Models](https://arxiv.org/abs/2305.16945)
- Orseau, Hutter & Lelis, "Exponential speedups by rerooting Levin tree search" (arXiv Dec 2024).
  - *Slenderness cost*: pi^lambda(n) = sum over ancestors n' ⪯ n of 1/pi(n'). It is self-counting, |{n : pi^lambda(n) <= theta}| <= theta, and satisfies pi^lambda(n) <= 1 + d(n)/pi(n). So it is a tighter LTS cost than d/pi.
  - **Corollary 12 (sqrt-LTS guarantee)**: for every subtask decomposition n_{T1} ≺ ... ≺ n_{Tm} = n_T, T <= max over 1 <= i < m of (w_{<T} / w_{Ti}) * pi^lambda(n_{T(i+1)}; n_{Ti}).
  - *Corollary 17 (robust)*: with arbitrary input weights w̃, T <= (1 + ln(w̃_{<T}/w̃_1)) * max over i of (w̃_{<=Ti}/w̃_{Ti}) * pi^lambda(n_{T(i+1)}; n_{Ti}).
  - Headline: if LTS takes time T, sqrt-LTS with q good rerooting points takes **O(q T^{1/q})** in the best case. The paper also gives an example within a factor 4 of a lower bound [VERIFIED].
  — [Rerooting LTS](https://arxiv.org/abs/2412.05196)
- A 2026 follow-up, "Structure-Induced Information for Rerooting Levin Tree Search", is listed as an ICML 2026 poster (learned rerooter). I did not read its content. — [ICML 2026 poster page](https://icml.cc/virtual/2026/poster/66710)

### Inferences
- **Key algebraic link for Yggdrasil**: if the policy is a product of per-step transition probabilities, pi(n) = prod p_i, and edge cost is c = -log p, then d0(n)/pi(n) = d0(n) * exp(c(n)). LevinTS order is therefore uniform-cost search on surprisal with a log-depth correction (log(d0/pi) = log d0 + c(n)). The Theorem 3 bound reads: **expansions <= d0(n*) * exp(surprisal of the cheapest goal)**. Search effort is exponential in the explanation's surprisal. This is a Levin-complexity (Kt = description length + log time) statement in disguise, i.e. Solomonoff/Levin universal search.
- PHS returns argmin of phi+, which for eta = 1 is argmin of g/pi. That is **not** the minimum-cost (g) solution. To get both a provable effort bound and a minimality proof, either:
  - (a) run PHS/LevinTS for an incumbent and then A*/branch-and-bound with an admissible bound to certify optimality, or
  - (b) define the goal test as "explanation with cost <= theta" and iterate theta.
- Branch and bound (Land & Doig 1960) is optimal whenever the bound is a valid lower bound (for minimization). This is standard and was not re-verified here.
- Known PUCT failure modes relevant to Yggdrasil:
  - (i) No finite-sample theorem exists for the rule as deployed.
  - (ii) The prior multiplies the exploration bonus. An action with pi_theta(a|x) ≈ 0 is almost never tried, so a wrong Hawkes prior can blind the search (this follows from the formula). AlphaZero's Dirichlet root noise is a patch; that detail is from memory.
  - (iii) Low simulation budgets break policy improvement (Grill et al.; Danihelka et al.).

### Gaps
- Not verified this session:
  - Rosin's PUCB (2011) bandit-with-prior regret bound.
  - The exact regularizer in Grill et al. (I believe pi̅ = argmax over y of [Q^T y - lambda_N KL(pi_theta, y)] with lambda_N = c sqrt(sum_b n_b)/(|A| + sum_b n_b)).
  - Coquelin-Munos' improved-variant regret expression (garbled in extraction).
- No finite-sample regret bound for AlphaZero-style PUCT was found. That is consistent with the literature above, but I cannot claim exhaustive coverage.

---

## 5. Local graph algorithms with locality guarantees: approximate PPR push, heat kernel PageRank, random walk with restart

### Takeaway
Push-style local algorithms compute PPR or heat-kernel vectors with work bounds independent of graph size: O(1/(eps alpha)) for PPR, and 2N e^t / eps for the heat kernel. They return explicit residuals, which certify how much probability mass was left unexplored. That certificate is what lets Yggdrasil prove that restricting the explanation search to a small neighborhood loses nothing above a threshold.

### Cited Findings
- **Andersen, Chung & Lang (FOCS 2006), Theorem 1**: ApproximatePageRank(v, alpha, eps) runs in time **O(1/(eps alpha))** and computes p = apr(alpha, chi_v, r) whose residual satisfies **max over u of r(u)/d(u) < eps**, with **vol(Supp(p)) <= 1/(eps alpha)**. The running time is independent of graph size. Because the residual is non-negative, **apr(alpha, s, r) <= pr(alpha, s) always**. The approximation obeys p + pr(alpha, r) = pr(alpha, s) (linearity) [VERIFIED; theorem text partially garbled in extraction, consistent with the stated runtime].
- *ACL Theorem 8 (local partitioning)*: suppose a set C has conductance Phi(C) <= phi^2/(22500 log^2(100 m)) and vol(C) <= (1/2) vol(G), and v is in C_alpha for alpha = phi^2/(225 ln(100 sqrt(m))). Then some b in [1, ceil(log2 m)] makes PageRank-Nibble(v, phi, b) return a set S, and any returned S has Phi(S) < phi, 2^{b-1} < vol(S) < (2/3) vol(G), and vol(S ∩ C) > 2^{b-2}. *Theorem 7*: PageRank-Nibble runs in time O(2^b polylog(m)/phi^2); the log exponent was garbled in extraction [VERIFIED except that exponent]. — [Andersen, Chung, Lang 2006 PDF](https://www.math.ucsd.edu/~fan/wp/localpartition.pdf)
- **Heat kernel diffusion**: weights alpha_k replaced by t^k/k!, i.e. h = e^{-t} sum over k of (t^k/k!) P^k s (Chung's heat kernel PageRank). It weights short walks more heavily than PPR. **Kloster & Gleich (KDD 2014), hk-relax, Theorem 1**: a deterministic coordinate-relaxation (push) algorithm outputs x with ||D^{-1} exp{tP} s - D^{-1} x||_inf < eps, doing work bounded by **2N psi_1(t)/eps <= 2N e^t / eps** edges, where N is the Taylor degree, which "grows slowly" with eps. This is "a provably constant runtime in a degree-weighted" sense [VERIFIED]. — [Kloster & Gleich 2014](https://arxiv.org/abs/1403.3148)
- **Random walk with restart as used for news influence**: Shahaf & Guestrin define Pi_i(v) = eps * 1(v = d_i) + (1 - eps) * sum over (u,v) in E of Pi_i(u) P(v|u), the stationary distribution of a restart walk from document d_i on a document-word bipartite graph [VERIFIED]. — [Shahaf & Guestrin, IJCAI 2011](https://www.ijcai.org/Proceedings/11/Papers/455.pdf)
- Directed and target-side PPR estimators exist (FAST-PPR, KDD 2014; "PPR to a target node"). Not read this session. — [FAST-PPR](https://arxiv.org/abs/1404.3181)

### Inferences
- **Locality certificate, directed-graph version** (derived here from the linearity identity; simple proof, not from a paper). For any push variant that maintains p + PPR(r) = PPR(chi_s) with r >= 0, we have PPR_s(u) - p(u) = sum over v of r(v) PPR_v(u) <= ||r||_1 for every u, because PPR_v(u) <= 1. So **every node with PPR_s(u) > R := ||r||_1 lies in Supp(p)**, and R is known exactly at termination. Each push from v with r(v) >= eps moves alpha * r(v) >= alpha * eps mass into p, and p's total mass is <= 1, so there are at most 1/(alpha eps) pushes.
- **Path-to-PPR lemma** (derived; elementary). PPR_s(u) = sum over walks W from s to u of alpha (1 - alpha)^{|W|} P(W). So for any single path P of length L and transition probability product rho, PPR_s(u) >= alpha (1 - alpha)^L rho. Combining the two results: **if every edge of an admissible explanation has path probability >= rho from the event and depth <= L, and alpha (1 - alpha)^L rho > R, then every node of that explanation is inside the explored set.** This is the formal "only a small neighborhood needs exploring" guarantee to feed into the exact Steiner DP of Section 1.
- On undirected graphs ACL gives a sharper per-node statement: 0 <= pr(u) - p(u) <= eps * d(u), because the degree vector is a fixed point of the lazy-walk PageRank operator. This is standard and was not re-derived from the paper text.

### Gaps
- Not verified: Chung & Simpson's randomized heat-kernel PageRank bound, Tong-Faloutsos-Pan RWR (ICDM 2006), or the bidirectional PPR estimators (Lofgren et al.).
- The exact log exponent in ACL Theorem 7 is unresolved (garbled extraction).

---

## 6. Adaptive, budgeted evidence gathering: adaptive submodularity, EC2, GBS, budgeted max coverage, value of information

### Takeaway
Adaptive greedy is provably near-optimal for adaptive monotone submodular objectives: (1 - 1/e) for budgeted maximization. For coverage it is logarithmic in the worst case, and squared-log in the average case under the corrected 2017 proof, restored to logarithmic (with an additive +1) by Esfandiari-Karbasi-Mirrokni. EC2 converts noisy hypothesis discrimination into an adaptive submodular edge-cutting objective.

Big caveat for anyone writing proofs: EC2's published (2 ln(1/p_min) + 1) bound and the "ln" GBS bound were derived from the Golovin-Krause min-cost-cover theorem whose proof was later found flawed.

### Cited Findings
**Adaptive submodularity** (Golovin & Krause, JAIR 2011; arXiv v5, Dec 2017)
- *Definitions*: Delta(e | psi) = E[ f(dom(psi) ∪ {e}, Phi) - f(dom(psi), Phi) | Phi ~ psi ].
  - Adaptive monotone: Delta(e | psi) >= 0 for all psi with P[Phi ~ psi] > 0.
  - Adaptive submodular: Delta(e | psi) >= Delta(e | psi') whenever psi ⊆ psi' and e not in dom(psi').
  - Strong adaptive monotonicity: E[f(dom(psi), Phi) | psi] <= E[f(dom(psi) ∪ {e}, Phi) | psi, Phi(e) = o] for every possible outcome o.
  - Pointwise submodularity is **not** sufficient for adaptive submodularity (counterexample in the paper). Adaptive submodular plus pointwise submodular implies strongly adaptive submodular.
  [VERIFIED]
- **Theorem 5 (budgeted maximization)**: if f is adaptive monotone and adaptive submodular and pi is an alpha-approximate greedy policy, then for all policies pi* and positive integers l, k: **f_avg(pi[l]) > (1 - e^{-l/(alpha k)}) f_avg(pi*[k])**. With l = k this gives **1 - e^{-1/alpha}**, i.e. 1 - 1/e for exact greedy [VERIFIED].
- **Theorem 13 (average-case min-cost cover, corrected v5)**: if f is *strongly* adaptive submodular and *strongly* adaptive monotone, f(E, phi) = Q for all phi, eta is the granularity (f(S, phi) > Q - eta implies f(S, phi) = Q), and delta = min over phi of p(phi), then **c_avg(pi) <= alpha c_avg(pi*_avg) (ln(Q/(delta eta)) + 1)^2** in general, and **(ln(Q/eta) + 1)^2 for self-certifying instances**. *Historical note in v5*: an earlier version claimed the un-squared logarithmic factors, but "the proof was flawed as pointed out by Nan and Saligrama (2017)". Whether the log bound holds was left open [VERIFIED].
- **Theorem 14 (worst-case cost)**: here adaptive monotone and adaptive submodular suffice. **c_wc(pi) <= alpha c_wc(pi*_wc) (ln(Q/(delta eta)) + 1)**, with Q := E[f(E, Phi)] [VERIFIED].
- *Hardness*: no polynomial (1 - eps) ln(Q/eta) approximation for self-certifying adaptive stochastic min cost cover unless NP ⊆ DTIME(n^{O(log log n)}) (from Feige). *Theorem 26*: without adaptive submodularity, even pointwise-modular adaptive stochastic maximization has no O(|E|^{1-eps}/beta) approximation unless PH = Sigma2P. *Theorem 25*: the adaptivity gap of adaptive stochastic min-sum cover is Omega(n/log n) [VERIFIED]. — [Golovin & Krause (arXiv 1003.3967 v5)](https://arxiv.org/abs/1003.3967)
- **Esfandiari, Karbasi & Mirrokni** ("Adaptivity in Adaptive Submodularity", arXiv v2 Jul 2020). Assuming only adaptive submodularity and adaptive monotonicity (no "strong" conditions), **Theorem 2: c_avg(pi_greedy) <= (c_avg(pi*) + 1) * ln(n Q / eta) + 1**, with n = |E|. They describe this as proving the Golovin-Krause conjecture "asymptotically". They also give a semi-adaptive policy with **O(log n * log k) adaptive rounds achieving 1 - 1/e - eps** against a fully sequential k-step optimum, and show no constant factor is possible with o(log n) rounds. Truncation does not preserve adaptive submodularity [VERIFIED]. — [Esfandiari, Karbasi, Mirrokni](https://arxiv.org/abs/1911.03620)

**Generalized binary search (GBS)**
- Dasgupta (NeurIPS 2004): **Q(GBS) <= 4 Q* ln(1/min over h of pi(h))** [VERIFIED via search summary of Theorem 3]. — [Dasgupta 2004](https://proceedings.neurips.cc/paper/2004/hash/c61fbef63df5ff317aecdc3670094472-Abstract.html)
- Golovin-Krause v5 **Theorem 21**: GBS uses OPT * (ln(1/min p_H(h)) + 1)^2 expected queries, improving to O((ln |H|)^2) with a modified prior p'(h) ∝ max(p_H(h), 1/|H|^2) [VERIFIED]. — [Golovin & Krause v5](https://arxiv.org/abs/1003.3967)

**EC2 for noisy hypothesis discrimination** (Golovin, Krause & Ray, NeurIPS 2010)
- *Equivalence Class Determination (ECD)*: hypotheses H are partitioned into classes H_1..H_m, and the policy must end with the version space inside one class.
  - Edges E = all pairs {h, h'} in different classes, with weight w({h, h'}) = P(h) P(h').
  - Test t under true h cuts E_t(h) = {{h', h''} : h'(t) != h(t) or h''(t) != h(t)}.
  - Objective f_EC(A, h) = w(union over t in A of E_t(h)).
  - EC2 greedily picks t* in argmax over t of Delta_EC(t | x_A)/c(t).
  - Instances are self-certifying, with Q = w(E) = 1 - sum_i P(h in H_i)^2 <= 1 and eta = min edge weight >= p_min^2.
  [VERIFIED]
- **Theorem 3**: if P(h) is rational for all h, **c(pi_EC) <= (2 ln(1/p_min) + 1) c(pi*)**, p_min = min over h of P(h). With unit costs, Kosaraju et al.'s modified-prior trick gives O(log n) [VERIFIED].
- *Noise*: with outcomes x_T(h, Theta), a deterministic function of the hypothesis and a noise variable, reduce to ECD over pairs (h, theta) with classes H_i = {x_T(h_i, theta)}. **Theorem 4**: **c(pi_EC) <= (2 ln(1/p'_min) + 1) c(pi*)** with p'_min = min {P(h, theta) : P(h, theta) > 0}. The same holds for decision-making, where classes are "same optimal decision" [VERIFIED].
- *Why not GBS or information gain*: with a uniform prior over n hypotheses and two classes, GBS can need about n/2 tests in expectation where very few suffice. Class-entropy information gain fails because of test complementarities [VERIFIED].
- *Cost*: naive EC2 costs O(N n^2 l) per round (N tests); the paper gives faster implementations [VERIFIED].
- *Provenance caveat*: Theorem 3 is derived by applying "Theorem 10 of [9]", the then-current Golovin-Krause min-cost-cover theorem with a ln(Q/eta) + 1 factor. That is the theorem whose proof v5 retracted [VERIFIED by reading both papers].
— [Golovin, Krause, Ray 2010](https://arxiv.org/abs/1010.3091)

**Budgeted maximum coverage and value of information**
- Khuller, Moss & Naor (IPL 1999): a **(1 - 1/e)** approximation for budgeted maximum coverage, which is best possible, using cost-effectiveness greedy plus a standard enumeration of small subsets [VERIFIED, secondary]. — [as summarized in arXiv 1808.03085](https://arxiv.org/abs/1808.03085)
- Krause & Guestrin (JAIR 2009), "Optimal value of information in graphical models": efficient *optimal* nonmyopic observation selection for chains (HMMs). Optimizing value of information is **NP^PP-hard even for polytrees**, and computing decision-theoretic VOI objectives is **#P-complete even for naive Bayes** [VERIFIED, abstract-level]. — [Krause & Guestrin 2009](https://doi.org/10.1613/jair.2737)
- Best-arm identification with a fixed budget (Audibert, Bubeck & Munos, COLT 2010): successive rejects (SR) and UCB-E are essentially optimal. Their misidentification probability decays exponentially at a rate optimal up to log factors [VERIFIED, abstract-level]. — [Audibert, Bubeck, Munos 2010](https://www.learningtheory.org/colt2010/papers/59Audibert.pdf)

### Inferences
- **What can safely be cited for EC2 today** (my derivation from the verified statements):
  - (a) f_EC is a weighted coverage function of the test set for each fixed hypothesis, hence pointwise submodular. Since GKR prove it adaptive submodular and strongly adaptive monotone, it is strongly adaptive submodular. Golovin-Krause v5 Theorem 13 (self-certifying) then gives **c(pi_EC) <= (ln(Q/eta) + 1)^2 c(pi*) <= (2 ln(1/p_min) + 1)^2 c(pi*)**.
  - (b) Esfandiari-Karbasi-Mirrokni Theorem 2 gives **c(pi_EC) <= (c(pi*) + 1) ln(N/p_min^2) + 1** with N tests and unit costs.
  - The originally published un-squared (2 ln(1/p_min) + 1) should be cited with the provenance caveat.
- For a **fixed query budget B** (not coverage), Golovin-Krause Theorem 5 applies to f_EC with unit costs: greedy EC2 achieves >= (1 - 1/e) of the expected cut weight of the best B-query adaptive policy. Non-uniform query costs need the cost-sensitive variant (see Gaps).
- If queries must be sent in parallel batches (API latency), the Esfandiari-Karbasi-Mirrokni semi-adaptive scheme gives 1 - 1/e - eps with O(log n log k) rounds.

### Gaps
- I did not read the cost-sensitive version of the Golovin-Krause maximization theorem (the paper says a later theorem "generalizes Theorem 5 to nonuniform item costs").
- Not read: Javdani et al. 2014 (HEC), Chen et al. 2015 (DRD, "submodular surrogates for VOI"), Chen, Hassani & Krause 2017 (ECED for noisy correlated tests).
- I confirmed Khuller-Moss-Naor's "enumerate triples" detail and the (1/2)(1 - 1/e) simple modified greedy only from secondary snippets.
- Exact SR bound, from memory (not re-verified): error <= (K(K-1)/2) exp(-(n - K)/(loḡ(K) H2)), with loḡ(K) = 1/2 + sum from i=2 to K of 1/i and H2 = max over i of i * Delta_(i)^{-2}.
- The Esfandiari-Karbasi-Mirrokni publication venue (I believe COLT 2021) was not verified.

---

## 7. Coherent story chains in news: Connecting the Dots and Metro Maps

### Takeaway
Shahaf-Guestrin coherence is a weakest-link (max-min) objective over word-influence. Influence is a random-walk-with-restart quantity, structurally the same as a Hawkes/PPR transition prior. Chains are found by LP plus rounding, or by best-first search with an admissible bound, which is optimal but worst-case exponential. Approximation-ratio approaches were explicitly abandoned because concatenation only guarantees a factor-2 loss and greedy gets only 1/K. Metro maps put submodular coverage on top of a "coherence graph" and get 1 - 1/e^{1/alpha} via submodular orienteering.

### Cited Findings
- **Coherence objective** (Shahaf & Guestrin, KDD 2010; IJCAI 2011 summary): Coherence(d_1..d_n) = max over activations of min over i = 1..n-1 of sum over w of Influence(d_i, d_{i+1} | w) * 1(w active in d_i, d_{i+1}). Constraints: limit the total number of active words and the words active per transition, and activate each word at most once (one contiguous stretch, against "jitteriness"). Activations are relaxed to [0,1], which turns it into an LP. "A chain is only as strong as its weakest link" [VERIFIED]. — [Shahaf & Guestrin, IJCAI 2011](https://www.ijcai.org/Proceedings/11/Papers/455.pdf)
- **Influence**: Influence(d_i, d_j | w) = Pi_i(d_j) - Pi_i^w(d_j), where Pi_i is the restart-walk stationary distribution from d_i on the doc-word bipartite graph and Pi_i^w is the same with word w turned into a sink. w need not appear in either document [VERIFIED]. — [Shahaf & Guestrin, IJCAI 2011](https://www.ijcai.org/Proceedings/11/Papers/455.pdf)
- **Chain finding**: KDD 2010 formulated chain search as "another LP" with "a rounding technique with proved guarantees", which was slow and approximate. A later best-first search with an admissible evaluation function "is guaranteed to find the optimum, although it can take exponential time in the worst case" (Theorem 2.2.3 in Shahaf's thesis: findOptimalChain always terminates with an optimal solution, or with ∅ if none exists) [VERIFIED]. — [IJCAI 2011](https://www.ijcai.org/Proceedings/11/Papers/455.pdf); [Shahaf PhD thesis CMU-CS-12-140](https://www.csd.cmu.edu/sites/default/files/phd-thesis/CMU-CS-12-140.pdf)
- **Why they abandoned approximation ratios**: the LP objective implies Coherence(d_1..d_{2k-1}) >= (1/2) min{Coherence(d_1..d_k), Coherence(d_k..d_{2k-1})}, so concatenation loses at most a factor 2. But a greedy algorithm over single edges gives only a **1/K** approximation ratio, "for this reason, we abandon high approximation ratios" [VERIFIED]. — [Shahaf thesis](https://www.csd.cmu.edu/sites/default/files/phd-thesis/CMU-CS-12-140.pdf)
- **Metro maps** (Shahaf, Guestrin & Horvitz, WWW 2012 "Trains of thought"; also KDD 2012 "Metro maps of science"). *Problem 3.2*: find a map M maximizing Conn(M) s.t. m-Coherence(M) >= tau and Cover(M) >= (1 - eps) kappa. *Observation 3.3*: two m-coherent chains overlapping in m-1 articles conjoin into an m-coherent chain. The "coherence graph" has m-chains as vertices and conjoinable pairs as edges, so its paths are exactly the m-coherent chains. Short chains are found by best-first search with an admissible function (optimal). *Problem 3.4*: choose K paths with |docs(p_i)| <= l maximizing Cover, which is NP-hard. Cover is submodular, so greedy gives 1 - 1/e if all paths can be enumerated. Otherwise they use submodular orienteering (Chekuri & Pál 2005, quasi-polynomial, alpha = O(log OPT)), and **greedy plus orienteering achieves a 1 - 1/e^{1/alpha} approximation**, solving O(|D|^2) orienteering problems [VERIFIED]. — [Trains of thought PDF](https://www.erichorvitz.com/trains_of_thought.pdf)

### Inferences
- Yggdrasil's narrative-to-narrative Hawkes transition weights can play the role of Influence(d_i, d_{i+1}). An explanation *path* from an upstream narrative to the event can then be scored by weakest-link coherence (bottleneck path) rather than by sum of costs. Bottleneck paths are polynomial (max-min path), but the activation-pattern constraints make the true objective LP-based.
- The coherence-graph trick (m-chains as vertices) is a clean way to impose "context" (m-th order Markov) coherence while keeping path search on a graph. That is useful if Hawkes influence is too myopic (m = 2 is exactly the out-of-context associative chain they warn about).

### Gaps
- I did not obtain the exact KDD 2010 rounding guarantee (approximation factor and probability statement).
- KDD 2012 "Metro maps of science" connectivity objective details and the CACM 2015 "Information cartography" summary were not read.

---

## 8. Root-cause analysis in other domains (AIOps/microservices, industrial diagnosis): which guarantees exist

### Takeaway
Random-walk RCA (MicroRCA, CloudRanger and relatives) is heuristic, and I found no formal correctness guarantees. Causal RCA gives *identifiability/soundness* guarantees only under strong assumptions: perfect CI oracle, causal sufficiency, (extended) faithfulness, known or learned CBN. CIRCA gives a necessary-and-sufficient "intervention recognition criterion". RCD gives soundness of its localized causal discovery.

### Cited Findings
- **CIRCA** (Li et al., KDD 2022), "Causal inference-based root cause analysis ... with intervention recognition".
  - *Theorem 3.1*: knowledge needed for intervention recognition is equivalent to Pearl's Layer 2 (interventional) under faithfulness.
  - *Corollaries 3.2/3.3*: Layer-2 knowledge is needed, and Layer-3 (counterfactual) is not.
  - **Theorem 3.4 (Intervention Recognition Criterion)**: let G be a causal Bayesian network. Under faithfulness, **V_i is intervened iff P_m(V_i | pa(V_i)) != P(V_i | pa(V_i))**, i.e. its conditional distribution given its parents changed. The authors argue this is necessary and sufficient, and use it as the criterion for root-cause indicators.
  CIRCA builds a structural graph from system architecture plus regression-based hypothesis testing [VERIFIED]. — [CIRCA (arXiv 2206.05871)](https://arxiv.org/abs/2206.05871)
- **RCD** (Ikram, Chakraborty, Mitra, Saini, Bagchi, Kocaoglu, NeurIPS 2022) treats the failure as an intervention on the root cause and adds an F-node (0 = normal, 1 = anomalous). It learns only the part of the causal graph near the root cause using a localized, hierarchical Psi-PC. **Theorem 1**: "Given access to a perfect conditional independence oracle, and under the causal sufficiency, and the extended faithfulness assumptions Algorithm 1 returns the true root cause variables" (soundness). In their synthetic experiments, CIRCA's accuracy degrades as the node count grows [VERIFIED]. — [RCD (NSF PAR PDF)](https://par.nsf.gov/servlets/purl/10495798); [NeurIPS 2022 abstract](https://proceedings.neurips.cc/paper_files/paper/2022/hash/c9fcd02e6445c7dfbad6986abee53d0d-Abstract.html)
- **CloudRanger and ServiceRank** apply second-order random walks to identify culprit services in cloud incidents [VERIFIED, secondary mention]. — [Second-order random walk systems paper (arXiv 2203.16123)](https://arxiv.org/abs/2203.16123)
- Surveys of microservice RCA exist (2021 and 2024). I found no claims of formal guarantees for random-walk methods in the abstracts. — [Soldani & Brogi survey](https://arxiv.org/abs/2105.12378); [2024 RCA survey](https://arxiv.org/abs/2408.00803)
- Industrial and model-based diagnosis analog: Reiter's minimal-hitting-set theorem (Section 3) is the formal guarantee in consistency-based diagnosis.

### Inferences
- The transferable guarantee for Yggdrasil is CIRCA's criterion. If the narrative/market graph is treated as a CBN with Hawkes parents, a node is a root-cause candidate iff its conditional intensity given parents shifted (an anomalous immigrant/background rate rather than an explained excitation). This maps to Hawkes "immigrant vs. offspring" attribution, but the faithfulness and sufficiency assumptions are unlikely to hold for news. Treat it as a heuristic with a conditional theorem.
- Random-walk RCA (personalized PageRank from the anomaly) is basically Section 5's PPR. Its value is locality, not correctness.

### Gaps
- MicroRCA (Wu, Tordsson, Elmroth, Kao, NOMS 2020) and CloudRanger (Wang et al., CCGrid 2018) primary papers were not retrieved; their methods are described from memory and secondary mentions.
- Not researched: Budhathoki et al. (ICML 2022, Shapley-based outlier RCA), 2024-2025 outlier-RCA identifiability papers, BARO, and RCAEval.
- No industrial fault-diagnosis guarantees (e.g., diagnosability in discrete-event systems, Sampath et al. 1995) were researched.

---

## 9. Stopping rules: information foraging, marginal value theorem, secretary/odds, SPRT, active hypothesis testing

### Takeaway
There are four relevant stopping theories:
- MVT gives the patch-leaving rule (leave when the marginal gain rate drops to the habitat average) under deterministic, diminishing-returns assumptions.
- Secretary and odds rules give 1/e-optimal one-shot selection.
- SPRT is the exactly optimal stopping rule for two simple hypotheses with i.i.d. data (Wald-Wolfowitz).
- For *actively chosen* queries among many hypotheses, the correct theory is Chernoff's sequential design of experiments and Naghshvar-Javidi's active sequential hypothesis testing, which is asymptotically optimal as the error penalty grows.

### Cited Findings
- **Marginal value theorem** (Charnov 1976): "The predator should leave the patch it is presently in when the marginal capture rate in the patch drops to the average capture rate for the habitat." The optimal residence time is given by the tangent to the gain curve from the expected transit time. Assumptions include that the forager controls departure to maximize intake/time and that patch qualities are randomly distributed [VERIFIED, Wikipedia]. — [Wikipedia: Marginal value theorem](https://en.wikipedia.org/wiki/Marginal_value_theorem)
- **Information foraging** (Pirolli & Card; PARC, 1990s): users' information-seeking parallels animal foraging. "Information scent" is the cue users use to estimate the value of a path or patch [VERIFIED, Wikipedia]. — [Wikipedia: Information foraging](https://en.wikipedia.org/wiki/Information_foraging)
- **Secretary problem**: the optimal policy rejects the first r - 1 applicants and then accepts the first best-so-far. The optimal cutoff tends to n/e, and the success probability tends to 1/e. The odds algorithm gives the shortest rigorous proof and shows the optimal win probability is always >= 1/e [VERIFIED]. — [Wikipedia: Secretary problem](https://en.wikipedia.org/wiki/Secretary_problem)
- **Odds theorem** (Bruss): the odds strategy is optimal, i.e. it maximizes the probability of stopping on the last success [VERIFIED]. — [Wikipedia: Odds algorithm](https://en.wikipedia.org/wiki/Odds_algorithm)
- **SPRT** (Wald): accumulate S_i = S_{i-1} + log Lambda_i, and continue while a < S_i < b, with **a ≈ log(beta/(1 - alpha))** and **b ≈ log((1 - beta)/alpha)**. The thresholds are approximate because of overshoot. Wald and Wolfowitz (Ann. Math. Stat. 19(3):326-339, 1948) proved SPRT optimal [VERIFIED]. — [Wikipedia: SPRT](https://en.wikipedia.org/wiki/Sequential_probability_ratio_test)
- **Active sequential hypothesis testing**: Chernoff (1959) posed the binary active testing problem (the decision maker chooses which experiment to run) and gave a randomized strategy that is asymptotically optimal as the error probability tends to 0. Naghshvar & Javidi (Ann. Statist. 41(6):2703-2738, 2013) give DP-based lower bounds on the optimal total cost. Their first heuristic achieves Chernoff asymptotic optimality: the relative gap to optimal total cost tends to 0 as the wrong-declaration penalty grows. Their second achieves a nonzero information acquisition rate, which is optimal for noisy dynamic search with size-independent noise [VERIFIED]. — [Naghshvar & Javidi 2013](https://arxiv.org/abs/1203.4626)

### Inferences
- Wald-Wolfowitz optimality is for i.i.d. observations under two simple hypotheses, minimizing expected sample size under both. Search-engine results for actively chosen queries are neither i.i.d. nor passively sampled. So the SPRT thresholds can be used as *error-controlled* stopping thresholds (Wald's inequalities on alpha and beta are robust), but the optimality claim does not transfer. Chernoff/Naghshvar-Javidi is the right citation for optimality.
- Adaptive submodularity is the policy-level version of the MVT's diminishing-returns assumption. Under it, "stop querying explanation i when its expected marginal edge-cut per unit cost falls below the best alternative's" is the greedy rule that the Golovin-Krause guarantees cover. That is a real structural link, but MVT's own optimality proof does not apply to stochastic adaptive settings.

### Gaps
- Not verified: Wald's approximation for expected sample size (E_1[N] ≈ [(1 - beta) b + beta a]/KL(f1 || f0)), MSPRT for many hypotheses (Baum & Veeravalli 1994; Dragalin, Tartakovsky & Veeravalli 1999), or Pirolli & Card's 1999 Psych. Review rate-of-gain formulas.

---

## 10. Synthesis: how to combine these results for Yggdrasil (definitions, exact/approximate computation, prior-guided search bound, budgeted querying)

### Takeaway
1. Define the "smallest explanatory subgraph" as an optimum of a directed, node- and edge-weighted, prize-collecting group Steiner arborescence rooted at the market event. Costs are surprisal (-log of Hawkes attribution probabilities) plus a parsimony penalty per node.
2. Compute it exactly with Dreyfus-Wagner/DPBF over a PPR-certified local subgraph when k <= ~10. Otherwise approximate with primal-dual (GW-style) and report a per-instance dual certificate.
3. Find candidates quickly with Levin/PHS search, using Hawkes attribution as the policy. That gives a theorem-backed bound: expansions (or query spend) <= d0(n*) * exp(surprisal(n*)), or g(n*)/pi(n*).
4. Spend the SerpApi budget with EC2 greedy over the competing explanations: (1 - 1/e) for a fixed budget, and log or log^2 factors for "query until resolved". Stop with SPRT-style error-controlled thresholds.

Each step is tagged below as PROVEN THEOREM (with conditions), DERIVED LEMMA (short proof given here, not peer reviewed), or DESIGN CONJECTURE (needs proof or empirical validation).

### Cited Findings
Theorems this design relies on, restated from Sections 1-9:
- Dreyfus-Wagner and DPBF give exact (group) Steiner trees in O(3^k n + 2^k((k + log n) n + m)). — [Ding et al. 2007](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/icde07steiner.pdf); [Björklund et al.](https://arxiv.org/abs/cs/0611101)
- PCST: GW 2 - 1/(n-1), and 1.7994 (STOC 2024). — [GW 1995](https://math.mit.edu/~goemans/PAPERS/GoemansWilliamson-1995-AGeneralApproximationTechniqueForConstrainedForestProblems.pdf); [Ahmadi et al. 2024](https://arxiv.org/abs/2405.03792)
- DST: O(log^2 k / log log k) in quasi-polynomial time, and this is tight. GST: no log^{2-eps} k. — [GLL 2019](https://arxiv.org/abs/1811.03020); [HK 2003](https://www.wisdom.weizmann.ac.il/~robi/papers/HK-GroupSteiner2-STOC03.pdf)
- LevinTS: N <= min d0(n)/pi(n). PHS: L <= g(n*)/pi(n*), with a matching-order lower bound for any algorithm. sqrt-LTS: O(q T^{1/q}) best case. — [Orseau et al. 2018](https://arxiv.org/abs/1811.10928); [Orseau & Lelis 2021](https://arxiv.org/abs/2103.11505); [Orseau, Hutter, Lelis 2024](https://arxiv.org/abs/2412.05196)
- A* with admissible h is optimal; with consistent h it is optimally efficient. — [Wikipedia: A*](https://en.wikipedia.org/wiki/A*_search_algorithm)
- ACL push: O(1/(eps alpha)) work, residual-certified. hk-relax: 2N e^t / eps work. — [ACL 2006](https://www.math.ucsd.edu/~fan/wp/localpartition.pdf); [Kloster & Gleich 2014](https://arxiv.org/abs/1403.3148)
- Adaptive greedy: 1 - 1/e for budgeted maximization (Theorem 5). For cover: log^2 average-case (v5 Theorem 13), log worst-case (Theorem 14), and (c* + 1) ln(nQ/eta) + 1 (EKM). EC2: (2 ln(1/p_min) + 1) as published, with the caveat. — [Golovin & Krause v5](https://arxiv.org/abs/1003.3967); [EKM](https://arxiv.org/abs/1911.03620); [GKR 2010](https://arxiv.org/abs/1010.3091)
- Reiter: diagnoses are exactly the minimal hitting sets of conflicts. — [Jannach et al. summary](https://web-ainf.aau.at/pub/jannach/files/Conference_IJCAI_2015.pdf)
- Chernoff / Naghshvar-Javidi: active sequential testing is asymptotically optimal. SPRT gives error-controlled thresholds. — [Naghshvar & Javidi](https://arxiv.org/abs/1203.4626); [SPRT](https://en.wikipedia.org/wiki/Sequential_probability_ratio_test)

### Inferences

**(1) A precise definition of "smallest explanatory subgraph"**
- *Graph.* G = (V, E) is directed and time-stamped. V = narratives ∪ events ∪ entities ∪ observations, and an edge u -> v means "u can influence or support v", with timestamp(u) <= timestamp(v). The market event is e*.
- *Edge costs (DESIGN CONJECTURE: modeling choice).* For each edge (u -> v), c(u, v) = -log p(u -> v), where p(u -> v) is the Hawkes branching attribution for v's excitation: p(parent = u | v) = phi_{uv}(t_v - t_u)/lambda_v(t_v), with the background term mu_v(t_v)/lambda_v(t_v) as the "no parent" option. This is the standard Hawkes cluster/branching representation, not re-verified this session. Node cost lambda_node >= 0 is a parsimony (MDL model-length) penalty. Evidence terminal t has prize pi(t) = cost of leaving it unexplained.
- *Feasible explanations.* F(e*) is the set of arborescences S (edges pointing toward e*) that:
  - (i) contain e*,
  - (ii) contain at least one node of the root group R (upstream narratives with attention above a threshold), making this a group-Steiner constraint,
  - (iii) have their remaining terminals either included or paying their prize (prize-collecting).
- *Objective.* cost(S) = sum over e in S of c(e) + sum over v in S of lambda_node + sum over t not in S of pi(t).
- *Definition.* A smallest (most parsimonious) explanation is any S* in argmin over S in F(e*) of cost(S). Competing explanations are the root-distinct optima: for each r in R, S*_r = argmin over S in F(e*) containing r of cost(S) (BLINKS-style distinct roots), or the top-K of DPBF's progressive enumeration.
- *Interpretation (DERIVED, conditional).* If attributions along distinct edges are treated as independent and prizes are -log likelihoods of unexplained evidence, cost(S) = -log [P(structure S) * P(unexplained evidence)] up to constants. So S* is the MAP explanation structure in that model, which ties Steiner parsimony to MPE and two-part MDL (Section 3). The independence assumption is a modeling conjecture, not a theorem.
- *Contradicting evidence (PROVEN framework, Reiter).* If contradicting observations make certain edge sets jointly inconsistent (conflicts), the surviving explanations must hit every conflict: the parsimonious survivors are the minimal hitting sets (Reiter's theorem). Implement as hard constraints or penalties in the DP.

**(2) Compute it exactly for small k, approximately otherwise, and certify the locality restriction**
- *Exact (PROVEN THEOREM, conditions: non-negative costs, k terminals/groups).* Run Dreyfus-Wagner/DPBF on reversed edges rooted at e*, in O(3^k n + 2^k((k + log n) n + m)). The first time state (e*, all terminals) is popped from the priority queue, its cost is optimal. That is the minimality proof the user wants. Add PrunedDP++-style admissible lower bounds (A*) for speed without losing optimality: A* optimality needs an admissible bound, and expanding each state only once needs a consistent one.
- *Prize-collecting exactly (DERIVED, standard).* PCST reduces to a rooted Steiner instance in which each optional terminal t can connect through a direct edge of cost pi(t) to a virtual root. So the same DP applies with k = number of prize terminals [standard reduction, not re-verified].
- *Small integer weights (PROVEN, Björklund et al.).* If surprisal costs are quantized to integers <= M, use the 2^k-time subset-convolution DP. Quantization adds at most (number of tree edges) * (quantization step) additive error [DERIVED].
- *Locality restriction (DERIVED LEMMA, Section 5).*
  - Run push-PPR from e* on the reversed graph, with restart alpha and transition probabilities = Hawkes attributions. At termination R = ||r||_1 is known.
  - Lemma: every node u with PPR(u) > R is in the explored set.
  - Path lemma: any node reachable from e* by an attribution path of length <= L and probability >= rho has PPR >= alpha (1 - alpha)^L rho.
  - Choosing eps so that R < alpha (1 - alpha)^L rho **guarantees** that every explanation whose edges all lie on paths with probability >= rho and depth <= L is contained in the local subgraph. The restricted DP's optimum is then the global optimum over that class.
  - Work is <= 1/(alpha eps) pushes, independent of total graph size.
  - Caveat: this certifies containment of the high-probability explanation class, not of arbitrary low-probability explanations. That is the right semantics for "most parsimonious".
- *Approximate regime (PROVEN, with caveats).*
  - Undirected relaxations: 1.39 (Byrka et al.).
  - Node-weighted: (1.35 + eps) ln k.
  - Prize-collecting: GW primal-dual, factor 2 - 1/(n-1). Its dual solution gives a **per-instance lower bound**, so the system can report "returned explanation is within factor (cost / dual) of optimal" on every query. That is a certified gap rather than a worst-case ratio. The certificate idea is standard LP duality; I did not verify that GW's implementation exposes it.
  - Directed/group: only polylog ratios are possible (GLL; Halperin-Krauthgamer). Prefer exact DP on the certified local subgraph, with k pruned by clustering terminals.

**(3) Hawkes transition weights as a search prior, with a provable effort bound**
- *Search space.* A node of the search tree is a partial explanation built by a canonical expansion order (e.g., always expand the open frontier node with the latest timestamp first, and choose its parent or background). Canonical ordering makes each explanation correspond to exactly one search-tree node, so LevinTS's tree assumptions hold without duplicates.
- *Policy.* pi(child | parent) = Hawkes attribution probabilities at the chosen frontier node, including the background/stop option, so probabilities sum to 1 and the policy is proper.
- *Bound (PROVEN THEOREM, LevinTS Theorem 3 / PHS Corollary 2, conditions: tree-structured search space, proper policy, goal test well defined).* The number of expansions before the first goal (a feasible explanation) satisfies N <= min over goal nodes of d0(n)/pi(n). If each expansion costs l(n) (compute or API spend), the total loss is <= g(n*)/pi(n*).
- *Algebraic reading (DERIVED).* With pi(n) = exp(-c(n)), the bound is **N <= d0(n*) * exp(c(n*))**: search effort is exponential in the surprisal of the easiest explanation and linear in its size. PHS Theorem 4 shows no algorithm that uses these expansions can do fundamentally better in the worst case: there are trees where it needs >= g(par(par(n*)))/pi(n*).
- *Adding a heuristic (PROVEN, PHS Theorem 6 / Corollary 7).* Use an admissible lower bound h on remaining cost, e.g. the sum over unsatisfied terminals of the shortest surprisal distance to the partial tree, divided by a constant to keep it admissible for Steiner, or a DP bound on a relaxed problem. Then eta_h = (g + h)/g is PHS-admissible, and the bound tightens by the factor sum of pi(n)/(1 + h+(n)/g(n)) <= 1.
- *Optimality plus bounded effort (DESIGN, built from proven pieces).* PHS returns argmin of g/pi, not argmin of g. Pipeline:
  - (a) PHS/LevinTS finds the first incumbent, with a bounded effort guarantee.
  - (b) A*/DPBF with an admissible bound and the incumbent as upper bound proves minimality.
  - Step (b) is not covered by a pi-dependent bound; its worst case is the DP bound in (2).
- *Robustness to a misspecified prior (DERIVED).* Mix pi' = (1 - beta) pi + beta * uniform(branching B). For any goal at depth d, pi'(n*) >= max((1 - beta)^d pi(n*), (beta/B)^d), so N <= d0 * min((1 - beta)^{-d}/pi(n*), (B/beta)^d). This hedges against PUCT-style prior blindness.
- *Rerooting (PROVEN for sqrt-LTS, Corollaries 12 and 17).* Verified evidence nodes ("clue nodes" in Orseau-Hutter-Lelis terms) can serve as rerooting points. With q good clue nodes, the best case is O(q T^{1/q}) instead of T.
- *Why not MCTS/PUCT (from the theorems in Section 4).* UCT gives only asymptotic, polynomial-rate failure decay, with hyper-exponential worst-case regret. The original log-bonus proof is incomplete. PUCT has no finite theorem and fails at low budgets. If a value-based MCTS is still wanted, use a polynomial bonus (Shah-Xie-Xu, O(n^{-1/2}) value error) or a Gumbel-style root (policy improvement guarantee). Neither gives a prior-probability-to-expansions bound like LevinTS/PHS.

**(4) Allocating the SerpApi query budget across competing explanations**
- *Hypotheses.* H = {competing explanations S*_r} × {noise states theta} (e.g., whether a query returns a relevant article given that S*_r is true). Each query q has an outcome x_q(h, theta) (supports / contradicts / silent) and cost c(q). Equivalence classes = "which explanation (or which decision) is correct".
- *Algorithm.* EC2: choose q in argmax of Delta_EC(q | observations)/c(q), with edge weights P(h, theta) P(h', theta') between different classes.
- *Guarantees (PROVEN, with conditions and caveats).*
  - Coverage, i.e. query until resolved, unit costs: (2 ln(1/p_min) + 1) OPT as published by GKR 2010, but derived from the later-retracted Golovin-Krause theorem. Citable today: (2 ln(1/p_min) + 1)^2 OPT via v5 Theorem 13, using pointwise submodularity of f_EC (DERIVED step), or (OPT + 1) ln(N/p_min^2) + 1 via EKM Theorem 2.
  - Worst-case cost: ln(Q/(delta eta)) + 1 via Theorem 14.
  - Fixed budget B with unit costs: >= (1 - 1/e) of the optimal B-query adaptive policy's expected cut weight (Theorem 5 applied to f_EC, a DERIVED application).
  - Batched queries: 1 - 1/e - eps with O(log n log k) adaptive rounds (EKM).
  - Conditions: outcomes must be a *deterministic* function of (h, theta) with known prior P(h, theta). Hypotheses must be enumerated (K competing explanations times noise states). The guarantees are relative to the optimal policy *under that model*, so model misspecification is not covered.
- *Non-uniform query costs (DESIGN CONJECTURE).* Use cost-normalized greedy. A cost-sensitive version of Theorem 5 exists in Golovin-Krause per their text but was not read. Khuller-Moss-Naor's (1 - 1/e) with partial enumeration is non-adaptive only.
- *Stopping (DESIGN, with proven ingredients).* Stop when the posterior log-odds of the leading explanation against the runner-up cross Wald's threshold log((1 - beta)/alpha). Wald's error inequalities give approximate error control. Optimality of the stopping time is only proven for i.i.d., two-hypothesis, passive sampling. For actively chosen queries, cite Chernoff / Naghshvar-Javidi asymptotic optimality, which needs known per-query outcome distributions. Alternatively, an MVT-style rule (stop when expected marginal cut weight per query < average achievable rate) is justified *heuristically* by adaptive submodularity's diminishing returns.
- *Fallback when outcomes are noisy scores, not discrete (PROVEN in its own model).* Treat each explanation as an arm whose mean is its support score. Successive rejects achieves exponentially small misidentification probability with a fixed budget, optimal up to log factors (Audibert-Bubeck-Munos). This needs i.i.d. noisy rewards per arm, which is a strong assumption for web search.

**Summary of proof status**
- PROVEN, given the conditions stated above:
  - exact optimality of the DP output;
  - A* optimality with an admissible bound;
  - LevinTS/PHS expansion and loss bounds, and the PHS lower bound;
  - sqrt-LTS bounds;
  - push-PPR work bounds;
  - Golovin-Krause Theorems 5, 13 (log^2) and 14;
  - the EKM log bound;
  - Reiter's hitting-set characterization;
  - Steiner, PCST, GST and DST approximation and hardness numbers.
- DERIVED HERE (short proofs, need review):
  - the residual-mass locality certificate and the path-to-PPR lemma;
  - the surprisal form of the LevinTS bound;
  - the prior-mixing robustness bound;
  - f_EC strong adaptive submodularity via pointwise submodularity;
  - quantization error for the 2^k DP.
- DESIGN CONJECTURES:
  - Hawkes attribution as edge probabilities with independence across edges (so Steiner = MAP);
  - deterministic (h, theta) outcome models for SerpApi queries;
  - canonical expansion ordering preserving the policy's semantics;
  - stopping thresholds being adequate under non-i.i.d. active querying;
  - the CIRCA-style criterion holding for news causal graphs.

### Gaps
- No source found for a theorem that unifies Steiner parsimony with Hawkes likelihoods. The MAP interpretation in (1) is my construction.
- The cost-sensitive adaptive-submodular maximization theorem and the EC2 extensions for correlated noise (ECED; Chen, Hassani & Krause 2017) were not verified. Both matter if query costs differ (e.g., SerpApi engine-specific pricing) or if query outcomes are correlated.
- No empirical evidence was gathered on how often Hawkes priors assign low probability to the true explanation. That is what decides whether the exp(surprisal) bound is practically small.
- Whether the "first pop is optimal" argument survives the extra hard constraints (Reiter conflicts, time-respecting edges) depends on keeping the state space (node, terminal subset). Conflict constraints that span branches may break the subset-DP decomposition and need a branch-and-bound outer loop. Not analyzed here.
