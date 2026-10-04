# Cross-field formalisms for semi-conservative attention flowing between narratives (Yggdrasil)

Notation used throughout (plain text, no LaTeX). `y[i][t]` = attention mass on narrative i in 15-minute window t; `S_t = sum_i y[i][t]` = total attention; `n` = number of narratives; `G` = Hawkes branching (offspring) matrix with `G_ij` = expected attention generated on j per unit on i; `P` = transfer (transition) matrix, row-substochastic (`sum_j P_ij <= 1`, deficit = decay); `mu_t` or `Lambda_t` = exogenous source (new information); `delta_i` = decay rate; `0` (empty set) = an outside "reservoir" node (unattended attention). "Cited Findings" are sourced. "Inferences" contain derivations and mappings I made from those sources; derivations are labelled as mine so the report writer can tell them apart from literature claims.

A cross-cutting result first, because it recurs in every field: **semi-conservation on n nodes is exact conservation on n+1 nodes, where the extra node is a reservoir.** Hofbauer's Lotka-Volterra-to-replicator map, the susceptible class S in SIR, the environment compartment in compartmental models, the empty complex in reaction networks, and the creation/destruction terms in unbalanced optimal transport are all this construction under different names (Inferences in Q1, Q2, Q5, Q8).

---

## Q1. Ecology and evolution: Lotka-Volterra, replicator dynamics, Hofbauer equivalence, zero-sum structure, and estimation from time series (MAR, gradient matching)

### Takeaway
Lotka-Volterra (LV) competition does not conserve total abundance. The replicator equation conserves it exactly, on the simplex. Hofbauer (1981) proved that LV in n species is equivalent to the replicator in n+1 strategies, so semi-conservative attention on n narratives can be written as exactly conserved replicator dynamics with one added "unattended" strategy. In ecology, the standard way to estimate interactions from aggregate abundance series is MAR(1) (Ives et al. 2003) or gradient matching (Ellner et al. 2002). Both give **signed per-capita interaction coefficients, not mass flows**, so on their own they cannot provide transfer weights.

### Cited Findings
- **Generalized LV / replicator equations and the Hofbauer equivalence.** Hofbauer (1981) showed that the replicator equation in n+1 variables is equivalent to the LV equation in n variables. Orbits in the positive orthant of the LV system map to orbits in the interior of the replicator simplex and back. Hofbauer and Sigmund state that dynamic patterns in ecology are mirrored in evolutionary games and vice versa — [Higher-order equivalence of LV and replicator dynamics (bioRxiv 2025 preprint)](https://www.biorxiv.org/content/10.1101/2025.03.28.645916.full.pdf); [Josef Hofbauer publications list](https://homepage.univie.ac.at/josef.hofbauer/mypapers.htm)
- **2025 extension (preprint, not peer-reviewed as far as I could tell).** The equivalence still holds with higher-order (non-pairwise) interactions: "the general equivalence holds and non-linearities in either field leave this foundational connection intact" — [bioRxiv 2025.03.28.645916](https://www.biorxiv.org/content/10.1101/2025.03.28.645916.full.pdf)
- **MAR(1) estimation of community interactions and stability (Ives, Dennis, Cottingham & Carpenter 2003, Ecological Monographs 73:301-330).** They derive three stability properties of stochastic multispecies communities that can be estimated from multispecies time series with first-order multivariate autoregressive (MAR(1)) models. The paper shows how to estimate MAR(1) parameters and confidence intervals for parameters and stability measures. Application: plankton communities in three lakes under manipulated nutrient loading and fish abundance — [Notre Dame CurateND record](https://curate.nd.edu/articles/journal_contribution/Estimating_community_stability_and_ecological_interactions_from_time-series_data/24834828); [LTER bibliography](https://lternet.edu/biblio/estimating-community-stability-and-ecological-interactions-from-the-time-series-data). Reference implementation: R package MAR1 — [atsa-es/MAR1 on GitHub](https://github.com/atsa-es/MAR1)
- **Gradient matching (Ellner, Seifu & Smith 2002, Ecology 83(8):2256-2270).** Smooth the population series x(t) to estimate dx/dt, then fit the rate equations by penalized regression splines. Supporting routines include monotone and sign-constrained additive spline regression — [NCSU profile record](https://ci.lib.ncsu.edu/profiles/1565); [Ellner lab software page](https://ellner.eeb.cornell.edu/software.html)
- **Modern variant: Bayesian neural gradient matching for neural ODEs**, used to infer ecological interactions from time series quickly (2022) — [arXiv 2209.06184](https://arxiv.org/pdf/2209.06184)
- **Direct attention analog (Weng, Flammini, Vespignani & Menczer 2012, Scientific Reports).** In an agent-based model, agents attend to only part of the information they receive. A few memes go viral and most do not. The heterogeneity in meme popularity and persistence is explained by competition for limited attention plus network structure, without assuming different intrinsic meme quality, and it matches Twitter data — [PMC3315179](https://pmc.ncbi.nlm.nih.gov/articles/PMC3315179)

### Inferences
- **Governing equations (standard forms):**
  - Generalized LV: `dx_i/dt = x_i * ( r_i + sum_j a_ij x_j )`, i = 1..n.
  - Replicator: `dz_i/dt = z_i * ( (A z)_i - z.A z )`, i = 1..n+1, with `sum_i z_i = 1`.
- **Why the replicator conserves mass (my derivation).** `d/dt sum_i z_i = sum_i z_i f_i - fbar * sum_i z_i = fbar * (1 - sum_i z_i)`, which is 0 on the simplex. The constraint is exact and built into the dynamics. In LV, `dN/dt = sum_i x_i (r_i + (A x)_i)` has no conservation law.
- **Hofbauer map as the reservoir construction.** `z_i = x_i / (1 + sum_j x_j)` and `z_{n+1} = 1 / (1 + sum_j x_j)`, with a time rescaling (standard form; I did not read the 1981 original). Mapping: the n LV species are narratives, and strategy n+1 is "attention not on any tracked narrative." This is the formal version of the user's hypothesis. Mass is created or destroyed on the n tracked narratives only by exchange with the reservoir.
- **Mapping to narratives.**
  - species = narratives; abundance x_i = attention mass y_i
  - r_i = intrinsic growth (new-information inflow per unit attention)
  - a_ii < 0 = self-saturation or fatigue
  - a_ij < 0 = displacement (competition); a_ij > 0 = facilitation (for example "Fed hike" feeding "regional bank stress")
- **Estimation on 15-minute windows.**
  - MAR(1) on log scale: `log y_t = a + B log y_{t-1} + e_t`, with `e_t ~ N(0, Sigma)`.
  - B is estimated by (generalized) least squares, n regressions at O(T n^2) total. With n large relative to T, sparsity (lasso, or a kNN-in-embedding support) is required.
  - Zero counts need log(y + c) or a Poisson-lognormal state-space variant.
- **Gradient matching for GLV.** Regress `Delta log y_i / Delta t` on y(t). This is one linear regression per narrative and is cheap.
- **Critical caveat.** `B_ij < 0` means "j suppresses i's per-capita growth." It does not mean "mass moved from i to j." LV/MAR interaction matrices are signed influence, not transport. Turning them into transition weights requires a conservation constraint (the replicator form, or a transfer model as in Q5/Q6). Use them as features or priors for (a), not as the flows themselves.
- **Diagnostic for the user's semi-conservation hypothesis (my suggestion).** Compute the variance ratio `VR = Var(S_t) / sum_i Var(y[i][t])` on residuals after removing source events.
  - VR < 1: net negative covariance among narratives, the zero-sum or compensatory signature.
  - VR near 1: independent narratives.
  - VR > 1: common shocks dominate (for example FOMC days, when everything spikes together).
  - Ecologists use this kind of ratio as a test for compensatory dynamics. I did not verify the original citation (Schluter 1984) this session. If VR > 1 on most days, the user's semi-conservation hypothesis is weak for this data. That is plausible if y measures publication volume (supply side) rather than reader time (demand side).

### Gaps
- I did not access Hofbauer's 1981 original paper (Nonlinear Analysis). The equivalence is stated here via secondary sources and the standard textbook form.
- I could not confirm the exact names of Ives et al.'s three stability metrics from a primary text this session. From memory they are stationary variance relative to process error, return rate, and reactivity. Verify before quoting.
- I found no ecological work that estimates transfer flows (as opposed to interactions) from aggregate abundance series. Hubbell-style zero-sum neutral theory is relevant but was not sourced this session.

---

## Q2. Epidemiology: multi-strain competition and cross-immunity, next-generation matrix and R0, renewal equations, the Hawkes link, competing contagions

### Takeaway
The next-generation matrix (NGM) of epidemiology and the Hawkes branching matrix are the same object: the mean-offspring matrix of a multitype branching process. Both have a threshold at spectral radius 1. Epidemiology adds what a plain Hawkes model lacks: **a shared, depletable susceptible pool that makes competition multiplicative.** The SIR-Hawkes link (Rizoiu et al. 2018) makes this exact for one population. Multi-strain models with cross-immunity give similarity-weighted competition. Network results show that pure competition over a shared pool is winner-take-all unless audiences are partitioned.

### Cited Findings
- **NGM and R0.** R0 is the spectral radius of the next-generation matrix. The method was given by Diekmann et al. (1990) and van den Driessche & Watmough (2002) — [Next-generation matrix, Wikipedia](https://en.wikipedia.org/wiki/Next-generation_matrix)
- **van den Driessche & Watmough 2002 (Mathematical Biosciences).** Precise definition of R0 for general ODE compartmental models. If R0 < 1 the disease-free equilibrium is locally asymptotically stable; if R0 > 1 it is unstable. A centre-manifold analysis gives conditions for super- and sub-threshold endemic equilibria near R0 = 1. Suited to heterogeneous populations (stage, space, age, behaviour) — [author PDF](https://watmough.ext.unb.ca/papers/mgroup.pdf)
- **Hawkes branching ratio.** The branching ratio is the integral of the kernel, i.e. the mean number of children per event. Three regimes: sub-critical (< 1), critical (= 1), explosive (> 1). In the multivariate case, stationarity requires the spectral radius of the matrix of kernel integrals to be < 1 — [Hawkes process, Wikipedia](https://en.wikipedia.org/wiki/Hawkes_process). A separate literature warns that near-critical branching ratios fitted to real data can be calibration artifacts — [Apparent criticality and calibration issues in the Hawkes self-excited point process model (arXiv 1308.6756)](https://arxiv.org/pdf/1308.6756)
- **Discrete-time Hawkes = INAR (Kirchner).** Hawkes processes are continuous-time versions of integer-valued autoregressive (INAR) series, and INAR series are discrete-time Hawkes. Bin counts of a Hawkes process are approximated by INAR(p). Kirchner defines INAR(infinity), proves convergence of the INAR-based family to the Hawkes process, and gives an estimation procedure from bin counts — [Hawkes and INAR(infinity) processes (PH Bern repository)](https://phrepo.phbern.ch/7802/1/hawkes_and_inar_infty_processes.pdf); [An estimation procedure for the Hawkes process (arXiv 1509.02017)](https://arxiv.org/pdf/1509.02017)
- **SIR-Hawkes (Rizoiu, Mishra, Kong, Carman & Xie, WWW 2018).** The event rate of an extended Hawkes model is identical to the SIR new-infection rate after marginalizing out recovery events. This yields HawkesN, a Hawkes model with a finite population — [arXiv 1711.01679](https://arxiv.org/pdf/1711.01679)
- **Many-strain cross-immunity (Gog & Grenfell 2002, PNAS 99:17209-17214).** A status-based model where cross-immunity reduces transmission probability. Complexity scales linearly in the number of strains. Strains cluster. A short infectious period gives a single dominant cluster at any time, and replacement speed depends on cross-immunity specificity and mutation rate — [PMC139294](https://pmc.ncbi.nlm.nih.gov/articles/PMC139294)
- **Competing contagions on networks (Prakash, Beutel, Rosenfeld & Faloutsos, WWW 2012).** Under realistic conditions, on any graph topology, the stronger virus completely wipes out the weaker ("winner takes all"). Demonstrated on real graphs and with Google Insights data (Facebook vs MySpace) — [WWW 2012 anthology entry](https://ir.webis.de/anthology/2012.wwwconf_conference-2012.104/); [DTIC PDF](https://apps.dtic.mil/sti/pdfs/ADA556549.pdf)
- **Competing epidemics (Karrer & Newman 2011, PRE 84:036106).** Two diseases spread simultaneously on one network, and infection with either gives immunity to both. They derive the phase diagram and expected final sizes — [arXiv 1105.3424](https://arxiv.org/pdf/1105.3424)
- **Competition-induced criticality (Gleeson, Ward, O'Sullivan & Lee, Physical Review Letters 112:048701, 2014; not PNAS).** Competition among memes for limited user attention is what poises the system at criticality. Each meme's popularity follows a critical branching process, giving power-law popularity with exponent alpha < 2 — [arXiv 1305.4328](https://arxiv.org/abs/1305.4328); [PRL](https://link.aps.org/doi/10.1103/PhysRevLett.112.048701)

### Inferences
- **NGM equals Hawkes G (derivation from the definitions above).**
  - Linearized multitype renewal equation: `i_j(t) = imports_j(t) + sum_i integral K_ij(s) i_i(t - s) ds`.
  - This is exactly the expected-intensity equation of a multivariate linear Hawkes process: `lambda_j(t) = mu_j + sum_i integral phi_ij(s) dN_i(t - s)`, with `phi = K`.
  - Hence `G = integral K ds` is the NGM, and `rho(G)` is R0. Both are offspring means of the multitype Galton-Watson cluster representation.
  - Discrete 15-minute version: `E[y[j][t]] = mu_j[t] + sum_i sum_k G_ij[k] y[i][t-k]`, which is Kirchner's INAR(p).
- **Semantic consequence for Yggdrasil.** The current Hawkes G means offspring ("a unit of attention on i begets G_ij units on j"). It does **not** mean transfer, because the parent unit is not removed from i. A transition weight with conservation semantics needs a separate, mass-conserving migration term. That is the SIR structure: S -> I_i consumes susceptibles, and I_i -> I_j would move mass.
- **SIRS attention model with a shared pool (my construction from the cited models).**
  - Equations:
    - `dS/dt = -sum_i beta_i S I_i / N + omega R + (audience in - out)`
    - `dI_i/dt = beta_i(t) S I_i / N + mu_i(t) + sum_j (m_ji I_j - m_ij I_i) - gamma_i I_i`
    - `dR/dt = sum_i gamma_i I_i - omega R`
  - Conservation: `S + sum_i I_i + R = N` exactly in a closed audience.
  - Sources: mu_i (exogenous news, the epidemiology analog of "imported cases") and spikes in beta_i(t).
  - Sinks: gamma (fatigue, I -> R) and omega (forgetting, R -> S).
  - m_ij is the conserving narrative-to-narrative transfer, i.e. the transition weights the user wants.
  - Cross-immunity (Gog-Grenfell style): multiply beta_i by `(1 - sum_j sigma_ij R_j / N)`, with sigma_ij = semantic similarity. This yields "one dominant narrative cluster at a time" when attention spans (1/gamma) are short, which matches news-cycle behaviour.
- **The subtractive term is a misspecified linearization of pool depletion (my derivation).**
  - HawkesN form: `lambda_i = (S_t / N) * D_i`, with drive `D_i = mu_i + sum_j G_ji y_j`.
  - Writing `S_t = N - A_t`, where A_t is attention currently held: `lambda_i = D_i - (D_i / N) * A_t`.
  - So depletion matches `-kappa * A_t` only if `kappa_i = D_i / N`, i.e. proportional to each narrative's own drive.
  - A constant kappa across narratives over-suppresses weak narratives and under-suppresses strong ones relative to the resource-depletion mechanism.
  - Note that HawkesN depletes with cumulative counts (no replenishment). News needs SIRS-style replenishment (the omega term).
- **Coexistence needs partitioned pools.** Prakash et al. and Gleeson et al. imply that pure competition over one pool gives winner-take-all or critical dynamics. Coexisting narratives require niche separation, i.e. different audiences. Yggdrasil observes source outlets, so the natural structure is a metapopulation: one susceptible pool per outlet or audience segment, with NGM indexed by (narrative, outlet).
- **Criticality is a warning, not just a finding.** If fitted rho(G) is close to 1, Gleeson et al. say that can be a signature of competition rather than intrinsic virality. The arXiv 1308.6756 line says it can also be an artifact of a non-stationary baseline. Yggdrasil should fit time-varying mu (news sources) before reading rho(G) as strong excitation.
- **Estimation from aggregate counts.**
  - Fit `y[j][t] ~ Poisson( mu_j[t] + sum_i sum_k G_ij[k] y[i][t-k] )` with G >= 0, by EM over the branching structure or by non-negative Poisson regression.
  - Or factor G_ij[k] = G_ij * w[k] with a shared generation-interval kernel w, which reduces parameters to n^2 + L.
  - Cost: O(T n^2 L) per likelihood evaluation. Sparse G makes it O(T nnz(G) L).
  - R0-type summaries: rho(G), and the Perron vector as narrative "reproductive value."

### Gaps
- I did not fetch the Diekmann-Heesterbeek-Metz 1990 original.
- I found no published multivariate HawkesN with a replenishing shared pool. The SIRS-attention model above is my construction and needs validation.
- I did not verify a source for multivariate renewal-equation estimation (EpiEstim-style) from aggregated counts this session.

---

## Q3. Neuroscience: divisive normalization, the normalization model of attention, biased competition, and divisive vs subtractive competition

### Takeaway
Neuroscience uses division as the canonical competition operator (Carandini & Heeger). Reynolds & Heeger (2009) model attention as a gain field applied before divisive normalization. Grossberg's shunting networks show that division gives a hard capacity on total activity, a precise "semi-conservation." My derivation (Inferences) shows three advantages of divisive competition over subtractive:
- It bounds the total.
- It preserves the ratios between narratives.
- With exponent 1, it is invariant under merging or splitting narratives.

The subtractive `-kappa * total` term has none of these properties. In particular, its predictions depend on clustering granularity, which matters directly for level-of-detail (LOD) compression.

### Cited Findings
- **Normalization as a canonical computation (Carandini & Heeger, Nature Reviews Neuroscience 13:51-62, 2012).** A neuron's response is divided by a common factor that typically includes the summed activity of a pool of neurons. It operates throughout the visual system and in other modalities, and may underlie odour representation, attentional modulation, value encoding and multisensory integration. Canonical form in that literature: `R_j = gamma * D_j^n / ( sigma^n + sum_k D_k^n )` — [PMC3273486](https://pmc.ncbi.nlm.nih.gov/articles/PMC3273486)
- **Normalization model of attention (Reynolds & Heeger, Neuron 61:168-185, 2009).** Incorporates divisive normalization and produces different forms of attentional modulation depending on stimulus conditions and the spread of the attention field. It reconciles theories previously treated as alternatives. Model form: `R(x, theta) = A(x, theta) E(x, theta) / ( S(x, theta) + sigma )`, with `S = s * [A E]`, where E = stimulus drive, A = attention field, s = suppressive-pool kernel and * = convolution — [PMC2752446](https://pmc.ncbi.nlm.nih.gov/articles/PMC2752446); [Heeger lab PDF](https://www.cns.nyu.edu/heegerlab/content/publications/Reynolds-Neuron2009.pdf)
- **Biased competition (Desimone & Duncan, Annual Review of Neuroscience 18:193-222, 1995).** Simultaneous stimuli activate neural populations that automatically compete, and attention biases the competition toward the relevant stimulus — [MRC CBU bibliography](https://www.mrc-cbu.cam.ac.uk/bibliography/articles/3148)
- **Shunting networks conserve total activity (Grossberg 1973, Studies in Applied Mathematics 52:217-257).** Shunting on-center off-surround networks have a normalization property: total activity is independent of the number of active cells for fixed total input, and the networks tend to conserve total activity. This explains limited-capacity short-term memory and prevents saturation at high input — [Prelude to ART chapter (U. Idaho)](https://webpages.uidaho.edu/rwells/techdocs/Biological%20Signal%20Processing/Chapter%2015%20Prelude%20to%20ART.pdf); [HMC lecture slides](https://www.cs.hmc.edu/courses/2004/fall/cs152/nndslides/Ch15_pres.pdf)
- **Neuronal arithmetic (Silver, Nature Reviews Neuroscience 11:474-489, 2010).** Division and subtraction are both basic operations of inhibition. Divisive inhibition scales response amplitude while keeping selectivity intact — [Nature PDF](https://www.nature.com/articles/nrn2864.pdf)
- **Stability of nonlinear Hawkes (Bremaud & Massoulie, Annals of Probability 24:1563-1588, 1996).** General conditions for a stationary version and convergence to equilibrium of nonlinear mutually exciting point processes, including Lipschitz-type conditions on the nonlinearity — [Project Euclid](https://projecteuclid.org/journals/annals-of-probability/volume-24/issue-3/Stability-of-nonlinear-Hawkes-processes/10.1214/aop/1065725193.full)

### Inferences
- **Grossberg steady state as a capacity law (my derivation from the standard shunting equation).**
  - Equation: `dx_i/dt = -A x_i + (B - x_i) I_i - x_i * sum_{k != i} I_k`.
  - Steady state: `x_i = B I_i / (A + I)`, with `I = sum_k I_k`.
  - Total: `X = B I / (A + I) < B`. Shares: `x_i / X = I_i / I` exactly.
  - Reading: total attention rises with total news drive but saturates at capacity B with half-saturation A (Michaelis-Menten), and shares mirror input shares. This is the cleanest one-line formalism of "approximately conserved with sources."
- **Divisive vs subtractive, side by side (my derivation).** Let drive `D_i = mu_i + sum_j G_ji y_j`.
  - Subtractive (current proposal): `lambda_i = [ D_i - kappa * S ]_+`, with `S = sum_j y_j`.
  - Divisive (exponent 1): `lambda_i = C * D_i / ( sigma + sum_j w_ij D_j )`, with w = normalization-pool weights.
  - Reynolds-Heeger version: replace D_i by `a_i * D_i`, where a_i is an attention field such as a market-exposure or watchlist prior.
- **Property 1: total bound.**
  - Divisive, uniform pool: `sum_i lambda_i = C * D_tot / (sigma + D_tot) < C`. This is a hard capacity C, matching Grossberg.
  - Subtractive, linear region: `sum_i lambda_i = D_tot - n_active * kappa * S`. There is no intrinsic capacity. With small kappa the total can blow up; with large kappa all narratives are driven to zero.
- **Property 2: ratios.**
  - Divisive keeps `lambda_i / lambda_j = D_i / D_j` (Silver's "selectivity intact").
  - Subtractive changes ratios. Weak narratives hit zero first, giving threshold-linear sparsification and a winner-take-all tendency.
  - Subtractive is not wrong if sparsification is wanted, but it is a different mechanism.
- **Property 3: merge consistency, decisive for LOD.**
  - Split narrative i into children a and b with `D_a + D_b = D_i`.
  - Divisive with exponent 1 and uniform pool: `lambda_a + lambda_b = C (D_a + D_b) / (sigma + D_tot) = lambda_i`. Totals are invariant to granularity.
  - Subtractive: the children receive `-2 kappa S` together versus `-kappa S` for the parent, so predicted total attention depends on how finely narratives are clustered. Subtractive competition is not closed under the LOD operation.
  - With exponent n > 1 (typical in V1, around 2), divisive also fails merge consistency, so use n = 1 for narratives.
- **Property 4: linear algebra and stability.**
  - In the linear region, subtractive competition replaces G by `G - kappa * 1 1^T`, a rank-one negative perturbation, and dynamics are governed by rho of that matrix.
  - Bremaud-Massoulie-style sufficient conditions work with kernel magnitudes (|h|). Adding inhibitory kernels raises |h|, so the generic sufficient condition can become harder to certify even though inhibition intuitively stabilizes. This is my reading of the Lipschitz-condition form; tighter inhibition-specific results exist (not fetched).
  - Divisive dynamics are ratio dynamics (replicator or softmax-like) with the total controlled separately.
- **Property 5: a unifying equivalence.** With exponential drive `D_i = exp(u_i)`, divisive normalization with exponent 1 and sigma -> 0 is softmax. Softmax is the rational-inattention logit (Q4) and one step of discrete replicator / multiplicative-weights dynamics (Q1). Divisive competition therefore connects neuroscience, economics and evolutionary game theory. The subtractive term connects only to inhibitory Hawkes.
- **Recommended hybrid (magnitude x share).**
  - Total: model S_t with a 1-D semi-conservative balance, `S_{t+1} = (1 - delta) S_t + inflow(news_t)`, with Grossberg/Michaelis-Menten saturation.
  - Shares: `pi[i][t] = a_i D_i / (sigma + sum_j w_ij a_j D_j)`, then `y[i][t] = S_t * pi[i][t]`.
  - This separates conservation (in the total) from competition (in the shares). The suppressive pool w_ij can be local in embedding space, so narratives compete mainly with semantic neighbours, which is the Reynolds-Heeger suppressive-field width.
- **Mapping.**
  - neurons = narratives
  - stimulus drive E = exogenous news intensity (document count x relevance)
  - attention field A = market-relevance prior (positions, watchlists, asset exposure)
  - suppressive pool = semantic-similarity kernel
  - sigma = baseline "inattention" constant, which again plays the reservoir role
- **Cost.** O(n + nnz(w)) per window, so negligible.

### Gaps
- I found no empirical study comparing subtractive and divisive competition specifically on news or social-media attention data.
- Holt & Koch (1997) on when shunting inhibition acts subtractively was not fetched.
- I did not retrieve inhibition-specific Hawkes stability results this session (for example Costa et al. 2020).

---

## Q4. Economics: rational inattention, capacity constraints, limited investor attention, attention allocation as optimization

### Takeaway
Rational inattention (Sims 2003) treats attention as a Shannon channel-capacity constraint. With Shannon costs, optimal discrete attention allocation is a prior-weighted multinomial logit (Matejka & McKay 2015). Made dynamic, that is a replicator or multiplicative-weights update of narrative shares, and it can be estimated by regressions on log-share ratios. Limited-attention asset pricing (Peng & Xiong 2006) shows capacity-constrained investors process category-level (market, sector) information before firm-level information. That is an economic micro-foundation for hierarchical LOD: agents compress narratives themselves. Rational inattention gives allocations (shares), not flows.

### Cited Findings
- **Sims 2003 (Journal of Monetary Economics, pp. 665-690).** A constraint that actions depend on observations only through a finite-Shannon-capacity channel acts much like a signal-extraction problem or adjustment cost. The result is smooth, inertial responses to new information — [Princeton record](https://collaborate.princeton.edu/en/publications/implications-of-rational-inattention/)
- **Matejka & McKay 2015 (AER 105(1):272-298).** With Shannon-entropy information costs, choice probabilities take a generalized multinomial logit form that depends on true payoffs and prior beliefs. Form: `P(i | v) = P0_i exp(v_i / lambda) / sum_j P0_j exp(v_j / lambda)` — [DOI 10.1257/aer.20130047](https://doi.org/10.1257/aer.20130047)
- **Generalization:** "Discrete Choice and Rational Inattention: A General Equivalence Result" extends the equivalence beyond the Shannon case — [arXiv 1709.09117](https://arxiv.org/abs/1709.09117)
- **Peng & Xiong 2006 (JFE 80(3):563-602).** Attention is a scarce cognitive resource. Limited attention produces category learning: investors process more market- and sector-wide information than firm-specific information. Combined with overconfidence, this produces return-comovement patterns hard to explain otherwise, plus new cross-sectional predictability implications — [IDEAS/RePEc](https://ideas.repec.org/a/eee/jfinec/v80y2006i3p563-602.html); [NBER w11400](https://www.nber.org/system/files/working_papers/w11400/w11400.pdf)

### Inferences
- **Mapping.**
  - decision maker = aggregate market attention
  - actions = narratives
  - payoff v_i = expected trading relevance or surprise of narrative i
  - prior P0 = baseline narrative shares
  - lambda = marginal cost of attention (1/lambda = selection intensity)
- **Dynamic version (my derivation).** Set `P0 = pi[.][t-1]`. Then `pi[i][t] proportional to pi[i][t-1] * exp(v[i][t] / lambda)`, the discrete replicator / exponential-weights update.
  - Estimation by additive-log-ratio regression: `Delta log( pi_i / pi_ref ) = (v_i - v_ref) / lambda + noise`, with v linear in narrative features (news volume, price-move proximity, outlet tier).
  - Cost: one linear regression.
  - Shares are exactly conserved (sum to 1). Combine with a separate equation for total S_t to get semi-conservation, which is the same magnitude x share split as Q3.
- **Capacity in bits.** Sims's constraint conserves information-processing capacity (bits per window), not "attention units." A defensible alternative definition of attention mass is entropy-weighted (surprisal) document mass. This is speculative and not tested.
- **LOD justification.** In Peng & Xiong, capacity-constrained agents optimally allocate attention to coarse categories first, which suggests narrative attention factorizes as category attention times within-category share (a nested-logit structure). Nested logit is hierarchical normalization (Q3), and it is merge-consistent by construction, which supports a tree-structured LOD representation.
- **No flows.** These models do not say which narrative attention came from. They price allocation, not transitions. Their value for (a) is as a prior on destination attractiveness (column factors), not on origin-to-destination pairs.

### Gaps
- I found no rational-inattention model with explicit narrative-to-narrative switching dynamics. Dynamic RI models (for example Steiner, Stewart & Matejka 2017) were not verified this session.
- I did not verify the reverse water-filling (rate-distortion) allocation result for Gaussian attention. It is standard information theory, but no source was fetched.

---

## Q5. Physics and applied math: birth-death master equations, continuity and divergence on graphs, unbalanced OT (WFR/HK) with Sinkhorn, Waddington-OT, Schrödinger bridges and trajectory inference

### Takeaway
This is the strongest toolbox for both transitions and semi-conservation. Five pieces:
- **Monomolecular reaction networks** (inflow, decay, conversion between species) have an exact master-equation solution (Jahnke & Huisinga 2007): Poisson and multinomial. That gives a principled likelihood for "attention units migrate, appear and disappear." The deficiency-zero theorem guarantees product-Poisson stationary laws (Anderson, Craciun & Kurtz 2010).
- **Graph continuity plus Hodge theory** gives the key identifiability fact: a snapshot pair determines flows only up to circulations, and the minimum-energy flow is a potential flow.
- **Unbalanced OT** (Chizat et al. 2018; Liero, Mielke & Savare 2018) is the geometric version of semi-conservation and is solved by a one-line generalized Sinkhorn.
- **Waddington-OT** (Schiebinger et al. 2019) is almost exactly Yggdrasil's problem: no individual tracked, destructive snapshots, growth and death. Lavenant et al. (2024) prove that minimal-relative-entropy (Schrödinger bridge) reconstruction is exact for gradient-driven dynamics, and that unmodelled branching creates spurious transport.
- **2025-2026 work** adds unbalanced and branching Schrödinger bridges with discrete birth-death jumps.

### Cited Findings
- **Exact CME solution for monomolecular systems (Jahnke & Huisinga, J. Math. Biol. 2007).** For systems with only conversion (A_i -> A_j), inflow (0 -> A_i) and outflow (A_i -> 0), the chemical master equation has an exact solution for arbitrary initial conditions: a convolution of multinomial and product-Poisson distributions whose parameters follow the deterministic reaction-rate equations — [Maynooth PDF](https://mural.maynoothuniversity.ie/1729/1/JaHu2005MasterEquation.pdf); Doi-Peliti rederivation and extension — [arXiv 1911.00978](https://arxiv.org/pdf/1911.00978); 2024 application to an illness-death model — [arXiv 2404.07238](https://arxiv.org/pdf/2404.07238)
- **Product-form stationary laws (Anderson, Craciun & Kurtz, Bull. Math. Biol. 2010).** If the deterministic mass-action system admits a complex-balanced equilibrium, the stochastic system has a product-form stationary distribution (Poisson or constrained Poisson) on each closed irreducible set. Weakly reversible, deficiency-zero networks satisfy this by Feinberg's theorem. The distribution's parameter is the complex-balanced equilibrium — [arXiv 0803.3042](https://arxiv.org/pdf/0803.3042)
- **Hodge decomposition on graphs (Lim, SIAM Review 62(3), 2020).** An elementary, linear-algebra-only treatment of graph Hodge Laplacians and cohomology. Edge flows decompose into gradient, curl and harmonic parts — [arXiv 1507.05379](https://arxiv.org/abs/1507.05379v3); [SIAM PDF](https://epubs.siam.org/doi/pdf/10.1137/18M1223101)
- **Unbalanced OT scaling algorithms (Chizat, Peyre, Schmitzer & Vialard, Mathematics of Computation 87(314):2563-2609, 2018).** Extends entropic regularization to transport between arbitrary positive measures. The algorithms use only diagonal scaling of the coupling and generalize Sinkhorn. Covers unbalanced transport, gradient flows and barycenters, with growth models among the applications — [arXiv 1607.05816](https://arxiv.org/abs/1607.05816); [AMS](https://www.ams.org/journals/mcom/2018-87-314/S0025-5718-2018-03303-8)
- **Optimal Entropy-Transport and Hellinger-Kantorovich (Liero, Mielke & Savare, Inventiones 211:969-1117, 2018).** OT with marginal constraints relaxed by entropy penalties between non-negative finite measures. Logarithmic Entropy-Transport problems define the Hellinger-Kantorovich distance, which lies between Hellinger-Kakutani and Kantorovich-Wasserstein — [ar5iv 1508.07941](https://ar5iv.arxiv.org/html/1508.07941); [FU Berlin record](https://publications.imp.fu-berlin.de/2179)
- **Sinkhorn has many names.** Sinkhorn-Knopp scaling is also called iterative proportional fitting (IPFP), RAS, raking, biproportional fitting and Deming-Stephan — [Peyre & Cuturi, Computational Optimal Transport (arXiv 1803.00567)](https://arxiv.org/pdf/1803.00567)
- **Waddington-OT (Schiebinger et al., Cell, 7 Feb 2019).** OT recovers temporal couplings of a stochastic process in gene-expression space from 315,000 scRNA-seq profiles at 40 time points over 18 days. Validated by predicting held-out time points. Identified Obox6 and GDF9 as enhancers of reprogramming — [PMC6615720](https://pmc.ncbi.nlm.nih.gov/articles/PMC6615720); [CU Experts record](https://experts.colorado.edu/display/pubid_261879)
- **Trajectory inference theory (Lavenant, Zhang, Kim & Schiebinger, Annals of Applied Probability 2024, pp. 428-500)** — [arXiv 2102.09204](https://arxiv.org/abs/2102.09204):
  - **Non-identifiability without structure:** "if the drift v induces a periodic motion, then the distribution of cells may be constant in time even though the individual cells themselves move."
  - **Theorem 1.1:** if P is the law of `dX_t = -grad Psi(t, X_t) dt + sigma dB_t` with finite initial entropy, then any path law R with the same temporal marginals satisfies `H(P | W_sigma) <= H(R | W_sigma)`, with equality iff R = P. So the true law is the unique minimizer of relative entropy to Brownian motion given the marginals (the Schrodinger problem).
  - **gWOT estimator:** `F(R) = sigma^2 H(R | W_sigma) + (1/lambda) sum_i |t_{i+1} - t_i| H(rho_hat_{t_i} | R_{t_i})`. As lambda -> 0 it falls back to Waddington-OT, which "glues" pairwise entropic-OT couplings into a Markov chain. They prove consistency as time points densify on a fixed horizon.
  - **Branching:** "there is a problem of identifiability of the effects of transport and branching ... failure to appropriately account for branching can result in spurious mass transport." Their operator split applies the growth step `rho*(x) = rho(x) * exp(J(x) Delta t) = g(x) rho(x)`, with `J = tau^-1 (p_b - p_d)`, then a transport step.
  - The paper cites Weinreb et al. 2018 (PNAS 115:E2467) "Fundamental limits on dynamic inference from single-cell snapshots" for the identifiability discussion.
- **Regularized unbalanced OT for snapshots (Zhang et al., ICLR 2025).** Deep-learning solver for RUOT that infers continuous unbalanced stochastic dynamics from snapshots without prior knowledge of growth and death, connected to the Schrödinger bridge — [ICLR 2025 proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/32b8a612105de5c22db337b774ce7b61-Abstract-Conference.html); [arXiv 2410.00844](https://arxiv.org/html/2410.00844v1)
- **Unbalanced Mean-Field Schrödinger Bridge / CytoBridge (Zhang, Wang, Sun, Li & Zhou, NeurIPS 2025).** Learns growth, death and cell-cell interactions with neural networks from snapshots — [arXiv 2505.11197](https://arxiv.org/abs/2505.11197v3)
- **Unbalanced Schrödinger Bridge with discrete birth-death jumps (Ying, Wang, Yang, Zhou & Zhang, ICML 2026).** Models Brownian motion plus discrete birth-death jumps at single-cell resolution, with a simulation-free objective and a "rigorous microscopic interpretation" of the branching Schrödinger bridge — [ICML 2026 poster page](https://icml.cc/virtual/2026/poster/64979)

### Inferences
- **(5a) An "attention chemistry" with exact likelihood structure (my construction from Jahnke-Huisinga and Anderson-Craciun-Kurtz).**
  - Species: A_i (attention units on narrative i).
  - Reactions:
    - `0 -> A_i` at rate s_i(t) (news arrival)
    - `A_i -> 0` at rate delta_i (decay)
    - `A_i -> A_j` at rate k_ij (migration; conserving)
    - optional `A_i -> 2 A_i` (self-excitation; Hawkes-like)
    - optional `A_i + A_j -> 2 A_j` at rate c_ij (imitation/persuasion; conserving and frequency-dependent)
  - Mean field: `dy_j/dt = s_j - delta_j y_j + sum_i (k_ij y_i - k_ji y_j) + y_j * sum_i (c_ij - c_ji) y_i / N`. The last term is replicator-type.
  - Conservation: migration and conversion reactions have zero total stoichiometry (the left null vector 1 of their stoichiometric submatrix). Only the 0 <-> A_i reactions change S_t. That is semi-conservation stated exactly.
  - **Deficiency check (mine).** The monomolecular network {0 <-> A_i, A_i <-> A_j} has n+1 complexes, 1 linkage class and stoichiometric rank n, so deficiency = (n+1) - 1 - n = 0. It is weakly reversible if every narrative has inflow and outflow. Anderson-Craciun-Kurtz then gives a product-Poisson stationary law, consistent with Jahnke-Huisinga.
  - **Discrete-time aggregate likelihood.** `y_{t+1} = sum_i Multinomial( y[i][t]; P_i. ) + Poisson( Lambda_t )`, where P_i. is a row of the substochastic window transfer matrix and the deficit is decay. With Poisson input, `y[j][t+1] ~ Poisson( sum_i P_ij E y[i][t] + Lambda_j )`, independent across j.
- **(5a') Transfer-plus-reproduction decomposition (my derivation).**
  - Hawkes means: `E y_{t+1} = mu + G^T y_t`, with G >= 0 unconstrained.
  - Write `G = P + H`, where P is substochastic transfer (conserving) and H >= 0 is reproduction (excitation).
  - First moments identify only G = P + H. This is exactly Lavenant's "transport vs branching" confound.
  - Second moments partially separate them. Multinomial transfer is under-dispersed (binomial thinning variance y p (1 - p)), while reproduction and Poisson immigration add variance. Dispersion and lagged-covariance structure therefore carry information about P vs H, the same principle as Vardi's Poisson-variance identifiability and Bernstein-Sheldon's lagged-covariance estimator (Q6).
- **(5b) Continuity on the narrative graph (my derivation using Lim 2020).**
  - Equation: `y_{t+1} - y_t = s_t - d_t - B f_t`, where B is the n x m node-edge incidence matrix and f_t are edge flows.
  - Given Delta y and a model of s, d, the flow f is determined only modulo ker(B). For a graph, ker(B) is the cycle space (curl plus harmonic parts) with dimension m - n + c, where c = number of connected components.
  - The minimum-L2 solution `f* = -B^+ (Delta y - s + d)` lies in im(B^T), i.e. `f* = B^T phi`, a pure gradient flow. The potential phi solves the graph Poisson equation `L phi = s - d - Delta y`, with `L = B B^T`. This is Thomson's principle from electrical networks.
  - Interpretation: phi_i is "attention pressure," and the inferred flows run downhill.
  - The circulating component (A -> B -> C -> A rotation) is invisible in a single snapshot pair. This is the discrete counterpart of Lavenant's periodic-drift counterexample.
  - Cost: one sparse Laplacian solve, near-linear in m.
  - The minimum-L1 alternative (Beckmann / W1 min-cost flow) gives sparse flows.
  - Caveat: with a **time-homogeneous** P and **varying** y, circulations do become identifiable (Q6). The invisibility applies to single pairs or freely time-varying flows.
- **(5c) Entropic unbalanced OT for narrative flows.**
  - Problem: `min over pi >= 0 of <C, pi> + eps KL(pi | a x b) + lam1 KL(pi 1 | a) + lam2 KL(pi^T 1 | b)`.
  - Generalized Sinkhorn: `K = exp(-C / eps)`; `u <- ( a / (K v) )^( lam1 / (lam1 + eps) )`; `v <- ( b / (K^T u) )^( lam2 / (lam2 + eps) )`; `pi = diag(u) K diag(v)`. I reproduced these scaling-update forms from my knowledge of Chizat et al. 2018. Verify exponents against the paper before implementing.
  - Narrative-level use:
    - a = y_t, b = y_{t+1}, C_ij = semantic distance between narrative centroids (or -log of outlet-overlap affinity).
    - pi_ij = flow i -> j.
    - `a_i - sum_j pi_ij` = destroyed mass (decay); `b_j - sum_i pi_ij` = created mass (new information).
  - Knobs: eps sets how diffuse flows are. lam sets how expensive creation and destruction are relative to transport, i.e. how far attention travels before it is cheaper to destroy and recreate it.
  - From my knowledge of the HK geometry (not verified this session): mass beyond a cost-dependent cutoff is never transported, only destroyed and created. Distant narratives never exchange attention.
  - Cost: O(n^2) per iteration, trivial for n around 10^3 on GPU per window.
- **(5d) Waddington-OT mapping (direct analog).**
  - cells = documents (or attention units)
  - gene-expression vector = document embedding
  - cell clusters = narratives
  - time points = 15-minute windows
  - destructive sampling = each window has different documents (no unit tracked)
  - growth g(x) = per-narrative news proliferation prior (wire-story rate, outlet publication rate), analogous to proliferation and apoptosis gene signatures
  - Document-level variant: run UOT between soft-membership-weighted document clouds at t and t+1, then aggregate to narratives with memberships m: `W_ij = sum_{a,b} m[a][i] * pi_ab * m[b][j]`.
  - Composing couplings over windows (WOT gluing, `pi_{t1->t3} ~ pi_{t1->t2} pi_{t2->t3}`) answers the forensic question directly: where the attention on market-moving narrative j at t3 came from at t1 ("ancestors") and where a narrative's attention goes ("descendants").
- **(5e) Schrödinger bridge on a graph as a search-prior update (my construction).**
  - Take a prior kernel R (heat kernel `exp(-tau L)` on the narrative similarity graph, or historical outlet transition frequencies).
  - The min-KL path law matching consecutive marginals has `P*_ij = u_i R_ij v_j`, i.e. Sinkhorn scaling of the prior (unbalanced version: the UOT scaling above).
  - Lavenant's Theorem 1.1 is the justification: if true dynamics are potential-driven with known noise, the min-KL reconstruction is exact. gWOT pools all windows, and its consistency regime (dense time points over a fixed horizon) matches 96 windows per day.
  - Caveats:
    - The gradient-drift assumption excludes persistent rotations (market risk-on/risk-off cycles are exactly such rotations).
    - Lavenant warns that unmodelled branching (bursty news) inflates apparent transport, so Yggdrasil must model news arrival explicitly as growth.
  - The 2026 USB model's discrete birth-death jumps fit discrete narrative births and deaths better than continuous growth.

### Gaps
- I could not retrieve the Waddington-OT Methods S1 text, so the exact objective (the g^Delta t row-sum target and KL relaxation weights) is described from Lavenant's summary and the Chizat formulation, not quoted from Schiebinger et al.
- I did not verify the HK distance cutoff or the WFR dynamic formulation constants.
- I found no application of unbalanced OT or Schrödinger bridges to text, news or narrative attention (not exhaustively searched).
- Graph-based WFR (Maas-type discrete OT) was not covered.

---

## Q6. Statistics: Markov transition matrices from aggregate data, ecological inference, collective graphical models, identifiability and priors

### Takeaway
Estimating a transition matrix from per-state counts alone is a solved classical problem when the chain is time-homogeneous and the counts vary enough. Conditional least squares (Lee, Judge & Zellner 1970; Kalbfleisch & Lawless) is consistent and asymptotically normal, and Kalbfleisch-Lawless handle immigration. With noisy aggregates, a method-of-moments estimator based on **lagged covariance** is consistent (Bernstein & Sheldon 2016). Collective graphical models (CGMs) are the exact count-level framework, but exact inference is NP-hard even on trees, so a convex relaxation is used. Identifiability needs either variation (rank) in the attention vectors or second-moment (fluctuation) information. Otherwise priors such as sparsity, an OT/semantic prior kernel or Dirichlet priors are essential.

### Cited Findings
- **CLS and noisy-aggregate MoM (Bernstein & Sheldon, AISTATS 2016, PMLR 51:1142-1150)** — [ar5iv 1604.04182](https://ar5iv.labs.arxiv.org/html/1604.04182); [PMLR](https://proceedings.mlr.press/v51/bernstein16.html):
  - Setting: N individuals follow a time-homogeneous chain P, and only counts `n_t(i)` are observed.
  - CLS minimizes `|| X P - Y ||_F^2` over stacked consecutive counts. With exact counts it is consistent and asymptotically normal as T -> infinity, citing Lee et al. 1970 and Kalbfleisch et al. 1983.
  - CLS is **not** consistent under observation noise because it ignores the extra variance.
  - Their MoM estimator uses the lagged covariance: `P_hat = diag(mu_hat_t)^-1 ( N^-1 Sigma_hat_{t,t+1} + mu_hat_t mu_hat_{t+1}^T )`, under noise conditions `E[y_t | n_t] = A_t n_t` (A_t known and invertible) with noise independent across time.
  - The model is the special case of CGMs with a homogeneous Markov chain as the individual model, and this is "the first learning method with guarantees of any kind for a subclass of CGMs."
- **Kalbfleisch & Lawless.** For continuous-time Markov processes observed only as aggregate counts at observation times, they developed conditional least squares and approximate maximum likelihood, extended to immigration into the system, with consistency and asymptotic normality under mild conditions — [overview in arXiv 1009.1216](https://arxiv.org/pdf/1009.1216)
- **Collective graphical models (Sheldon & Dietterich, NIPS 2011).** Fit individual-level models when only aggregates (counts, low-dimensional contingency tables) are available, by working directly on the sufficient statistics. They give an efficient Gibbs sampler for the posterior of sufficient statistics given noisy aggregates — [NeurIPS proceedings](https://papers.nips.cc/paper/4220-collective-graphical-models)
- **Approximate CGM inference (Sheldon, Sun, Kumar & Dietterich, ICML 2013).** "Exact inference in CGMs is NP-hard even for tree-structured models." They give a tractable convex approximation to MAP, used inside EM, which cuts inference cost by about two orders of magnitude and learning cost by at least one with equal or better quality — [PMLR v28](https://proceedings.mlr.press/v28/sheldon13.html)
- **Network tomography (Vardi 1996, JASA).** Estimate origin-destination intensities from link counts that are known linear transforms of the unobserved OD counts. Identifiability conditions hold under a Poisson model. Estimation uses EM, a moment method, and a normal approximation — [Annals of Applied Statistics 2015 follow-up summarizing Vardi](https://projecteuclid.org/journals/annals-of-applied-statistics/volume-9/issue-1/Network-tomography-for-integer-valued-traffic/10.1214/15-AOAS805.pdf); [BibSonomy record](https://bibsonomy.org/bibtex/6c0e2a360dc884fd32117b1ad8c254f7)
- **Structural identifiability of linear compartment models (Meshkat, Sullivant & Eisenberg).** They characterize when compartment-model parameters are identifiable from input-output data, define "identifiable cycle models," and show that adding inputs or outputs, or removing leaks, restores identifiability. Identifiable strongly connected models combine into larger identifiable ones — [arXiv 1410.8587](https://arxiv.org/pdf/1410.8587)

### Inferences
- **Yggdrasil version of Lee-Judge-Zellner / Kalbfleisch-Lawless with sources and sinks (my formulation).**
  - Model: `y_{t+1} = P^T y_t + Lambda_t + e_t`, subject to P >= 0 and `P 1 <= 1` (substochastic, deficit = decay to the unobserved reservoir), with Lambda_t = immigration (new information, possibly regressed on news-arrival features).
  - Fit: a quadratic program. Rows decouple under the inequality constraints if the column-sum coupling is relaxed. Cost is O(T n^2) per pass with projected gradient or OSQP.
- **Identifiability (my derivation).**
  - Stack `X = [y_1 .. y_{T-1}]^T` and `Y = [y_2 .. y_T]^T`, so `Y = X P + 1 Lambda^T + E`.
  - P is identified iff [X, 1] has full column rank n+1, i.e. attention must move in at least n+1 independent directions within the fit window.
  - Near stationarity (y_t roughly constant), only `P^T y* + Lambda = y*` is identified: n equations for about n^2 unknowns.
  - With hundreds of narratives and 96 windows per day, a dense P is unidentified from means alone in one day. Use:
    - sparse support (kNN in embedding: n k parameters)
    - low rank
    - a Dirichlet / KL prior centred on an OT or Schrödinger-bridge kernel (Q5)
    - pooling across days, assuming homogeneity
- **Escape from the stationarity trap via fluctuations.** For a stationary linear process, `y_{t+1} - y* = P^T (y_t - y*) + e` implies `Gamma(1) = P^T Gamma(0)`, so `P^T = Gamma(1) Gamma(0)^-1` (Yule-Walker). Lagged covariances identify P even when means are flat, provided there are fluctuations. This is the logic of Bernstein-Sheldon's MoM and of Vardi's Poisson second-moment identifiability. Fluctuation-dissipation, in physics terms.
- **Single snapshot pair: deterministic bounds.** Without any model, Frechet-Hoeffding bounds (the "method of bounds" in ecological inference) constrain each cell of the balanced flow table: `max(0, a_i + b_j - N) <= N_ij <= min(a_i, b_j)`. With creation and destruction allowed, the lower bound relaxes to 0. These are standard bounds, not fetched this session.
- **CGM MAP is close to entropic OT (my derivation).** The log-probability of a flow table N_ij given origin counts a_i is `sum_ij N_ij log P_ij - sum_ij log N_ij! + const`. With Stirling, that is about `-sum_ij N_ij log( N_ij / (a_i P_ij) ) + const`. So MAP flow tables given both margins are about `argmin KL(N | diag(a) P)` subject to margins, which is entropic OT with cost -log P_ij solved by Sinkhorn. CGM-EM then alternates "Sinkhorn E-step with current P" and "M-step `P_ij proportional to sum_t N_ij(t)`." This is a cheap, principled estimator for (a). I believe this CGM/OT link has been published (multi-marginal OT for graphical models), but I did not verify it (see Gaps).
- **Outlets are the only tracked individuals.** An outlet that publishes on narrative i at t and on j at t+1 gives a direct, biased micro-observation of a transition. Combining aggregate CLS with outlet-level transition counts adds outputs in the Meshkat sense and greatly improves identifiability. Outlet transitions measure supply-side switching, not reader switching, so treat them as a prior or partial panel, not ground truth.
- **Tomography analogy.** Narrative totals play the role of link counts and the narrative-to-narrative flow table plays the OD matrix. Vardi's lesson carries over: Poisson structure makes second moments informative.

### Gaps
- I did not access the Lee, Judge & Zellner (1970) monograph or Kalbfleisch & Lawless (1984) directly. Attribution is via Bernstein & Sheldon and the arXiv 1009.1216 overview.
- I did not fetch King (1997) or Goodman ecological regression.
- I did not verify the papers explicitly linking CGMs to multi-marginal OT (I recall work by Haasler, Singh, Zhang, Karlsson & Chen, around 2020-2021).
- I found no work estimating transition matrices from aggregate counts with soft memberships (fractional counts).

---

## Q7. Coarse-graining and state compression: exact and approximate lumpability, KL-optimal aggregation, Laplacian RG, sufficiency of aggregated states

### Takeaway
An aggregated narrative node is a sufficient statistic for its own future exactly when the dynamics are lumpable with respect to the partition:
- **Strong (ordinary) lumpability** (Kemeny & Snell; Buchholz 1994).
- For linear mean dynamics, the matrix condition `V^T A = A_hat V^T`.
- Information-theoretically, **informational or computational closure** (Rosas et al. 2024), which they prove equivalent to causal closure and link to strong lumpability.

When lumpability fails, Mori-Zwanzig says the coarse dynamics acquire memory kernels, which is a principled reason coarse narratives need different (longer) Hawkes kernels. KL-optimal spectral aggregation (Deng, Mehta & Meyn 2011) and the Laplacian renormalization group (Villegas et al. 2023) provide partition-finding algorithms.

### Cited Findings
- **Exact and ordinary lumpability (Buchholz, J. Appl. Prob. 31:59-75, 1994).** Both define aggregations whose aggregated chain gives exact values of several stationary and transient quantities of the original chain. The paper identifies which quantities are exact, bounds the rest, and extends to near-lumpability for approximate aggregation — [Cambridge Core](https://resolve.cambridge.org/core/journals/journal-of-applied-probability/article/abs/exact-and-ordinary-lumpability-in-finite-markov-chains/2DC748F09D80BEEB03CCF18036E149D7)
- **KL-optimal aggregation (Deng, Mehta & Meyn, IEEE TAC 56(12):2793-2808, 2011).** Uses the KL divergence rate between the chain and its aggregated approximation. A relaxation of the bi-partition problem is solved by an eigenvalue problem tied to Markov spectral theory, and a recursive heuristic handles m-ary partitions — [Illinois Experts record](https://experts.illinois.edu/en/publications/optimal-kullback-leibler-aggregation-via-spectral-theory-of-marko/); [CDC-ECC 2011 PDF](https://skoge.folk.ntnu.no/prost/proceedings/cdc-ecc-2011/data/papers/1140.pdf). Related approach: "Optimal Kullback-Leibler Aggregation via Information Bottleneck" — [ar5iv 1304.6603](https://ar5iv.labs.arxiv.org/html/1304.6603)
- **Laplacian renormalization group (Villegas, Gili, Caldarelli & Gabrielli, Nature Physics 19:445-450, 2023).** A diffusion-based RG for heterogeneous networks that identifies spatiotemporal scales. It introduces Kadanoff supernodes across scales and a momentum-space procedure that integrates out fast diffusion modes to produce coarse-grained graphs while preserving key system properties — [arXiv 2203.07230](https://www.arxiv.org/abs/2203.07230); 2024 J. Stat. Mech. introduction — [Roma Tre IRIS PDF](https://iris.uniroma3.it/retrieve/6d83cf32-cec2-4c70-a2aa-cd55292c197a/J._Stat._Mech._2024_084002.pdf); [Complexity Digest summary](https://comdig.cssociety.org/2024/06/29/laplacian-renormalization-group-an-introduction-to-heterogeneous-coarse-graining/)
- **Informational, causal and computational closure (Rosas et al., arXiv 2402.09090, 2024)** — [arXiv HTML v2](https://arxiv.org/html/2402.09090v2):
  - Informational closure: the best predictions of the macro level come from the macro level itself ("all the details below the macro are not helpful for predicting the macro").
  - Computational closure: the macro epsilon-machine is a coarse-graining of the micro epsilon-machine, so the machines are strongly lumpable.
  - Causal and informational closure are proved equivalent, with links to lumpable time series that enable efficient estimation.
  - Later related preprints: "Symmetries at the origin of hierarchical emergence" (arXiv 2512.00984, Dec 2025) and "Emergence: from physics to biology, sociology, and computer science" (arXiv 2508.08548, 2025). Titles only; not read.
- **Mori-Zwanzig.** Coarse-graining a dynamical system generally introduces memory. The Mori-Zwanzig equation has mean (Markovian), memory and fluctuation terms. The Markovian approximation fails without time-scale separation, and the memory kernel can be computed from microscopic dynamics — [PMC4644152](https://pmc.ncbi.nlm.nih.gov/articles/PMC4644152); [Penn State record](https://pure.psu.edu/en/publications/incorporation-of-memory-effects-in-coarse-grained-modeling-via-th/)

### Inferences
- **Formal LOD criterion for linear mean dynamics (my derivation; standard Kemeny-Snell / Aoki-aggregation form).**
  - Let V be the n x m 0/1 membership matrix of the partition and `E y_{t+1} = A y_t + mu`, with `A = G^T` (Hawkes) or `A = P^T` (transfer).
  - The aggregate `Y = V^T y` is closed iff some A_hat satisfies `V^T A = A_hat V^T`.
  - Equivalently: for every source block J and target block I, `sum_{i in I} A_ij` is the same for all j in J. Every child exerts the same total influence on every other block.
  - For A = P^T this is exactly Kemeny-Snell strong lumpability (`sum_{k in I} P_jk` constant over j in J).
  - Then `A_hat = V^T A V (V^T V)^-1` (block average), and the macro mean dynamics are exact for every initial condition. The macro is a sufficient statistic for its own future mean.
- **Practical rule: lumpability defect.** Define `delta(V) = || V^T A - A_hat V^T ||` (Frobenius, or the Deng-Mehta-Meyn KL divergence rate). Collapse a subtree when delta is below a tolerance, and expand it when delta exceeds it, for example when a news shock breaks within-node homogeneity. Cost: O(nnz(A)) per block. This turns LOD from heuristic into a checkable condition.
- **Exact (Buchholz) lumpability supports "parent x fixed child shares."** If within-block proportions are preserved by the dynamics, children can be reconstructed from the parent by fixed shares. That justifies the magnitude x share (nested) representation of Q3/Q4.
- **Which models are closed under merging (my synthesis).**
  - Poisson-multinomial transfer plus Poisson immigration (Q5a): Poisson sums are Poisson and multinomial splits aggregate, so it stays in-class under a lumpable P.
  - Divisive normalization with exponent 1: merge-consistent (Q3).
  - Replicator and RI-logit: merge-consistent under Luce/IIA-type conditions.
  - Linear Hawkes: closed only under the block condition above.
  - Subtractive `-kappa S` competition: never merge-consistent (Q3).
- **Non-lumpable means a memory kernel at the coarse level.** By Mori-Zwanzig, a parent narrative whose children are not lumpable follows non-Markovian dynamics with a memory kernel generated by the integrated-out child dynamics. Practically: (i) fit separate (typically longer-tailed) excitation kernels per LOD level, or (ii) compute coarse kernels from fine ones. Rotating sub-narratives under a quiet parent are the textbook source of such memory.
- **Partition-finding options.**
  - Deng-Mehta-Meyn: a spectral bi-partition on the estimated transfer dynamics, applied recursively, which builds a tree directly from flows.
  - Laplacian RG on the narrative similarity graph: heat kernel exp(-tau L); merge narratives that diffusively mix faster than tau. tau can be tied to the 15-minute window times a relevance horizon, so "resolvable" narratives depend on time scale. From my reading (not verified), LRG uses entropy-based scale detection.
  - Informational-closure test (Rosas): for a candidate merge, compare out-of-sample predictive log-likelihood of the parent total using (i) parent history only vs (ii) parent plus children histories. A gain of about zero means the parent is closed and safe to compress. This is a Granger-style lumpability test costing two regressions per candidate.
- **Weak lumpability caveat.** Some aggregations are exact only for particular initial distributions. News shocks change within-node distributions, so closure should be tested in shock regimes, not just at quiet-time stationarity.

### Gaps
- I did not access the Kemeny & Snell text directly. The strong-lumpability condition is stated in its standard form.
- I did not verify the precise eigenvector construction in Deng-Mehta-Meyn (it relates to a reversibilized transition operator).
- I found no work on lumpability or aggregation of multivariate Hawkes processes specifically (not searched).
- I did not verify Wei & Kuo's 1969 lumping theory for monomolecular reaction systems, a likely direct analog.

---

## Q8. Other fields with usable equations: traffic flow, queueing networks, reaction networks, transport-planning gravity models, compartmental systems

### Takeaway
Four extra analogs give usable math:
- **Jackson queueing networks:** traffic equations `lambda = gamma + R^T lambda`, with product-form stationary laws. This is the conserving-routing twin of the Hawkes mean-intensity equation.
- **Traffic flow:** Daganzo's cell transmission model, a discrete conservation law with capacity-limited send/receive, gives saturation and spillback.
- **Transport planning:** Wilson's entropy-maximizing gravity model is IPF/RAS/Sinkhorn, which means estimating origin-destination flows from origin and destination totals, Yggdrasil's problem, has been routine in transport planning for decades.
- **Compartmental identifiability** says which flow parameters aggregate data can determine.

### Cited Findings
- **Cell transmission model (Daganzo 1994, Transportation Research B 28(4):269-287).** Simple difference equations shown to be the discrete analog of the hydrodynamic (LWR) traffic model. They generate density jumps where the hydrodynamic theory predicts shockwaves without separate shock tracking, and operate through a sending/receiving interface — [TRID](https://trid.trb.org/View/412943); [Berkeley ITS](https://its.berkeley.edu/publications/cell-transmission-model-dynamic-representation-highway-traffic-consistent-hydrodynamic); [TA benchmark CTM tutorial](https://tabenchmark.readthedocs.io/en/latest/tutorials/05-dnl/01-ctm.html)
- **Jackson networks.** With exponential service and Markov routing, if every station's traffic intensity is < 1, the queue-length vector has a unique product-form stationary distribution: queues are independent and each is M/M/1 with the same occupancy. Rates come from the traffic equations — [Jackson network, Wikipedia](https://en.wikipedia.org/wiki/Jackson_network)
- **Gravity / entropy maximization.** Wilson introduced the entropy-maximizing method in 1967, which became the accepted basis of macro spatial-interaction (gravity) models — [Erdkunde article](https://www.erdkunde.uni-bonn.de/article/download/2201/2190/2204). Its computation is the Sinkhorn/IPF/RAS scaling — [Peyre & Cuturi (arXiv 1803.00567)](https://arxiv.org/pdf/1803.00567). A September 2026 preprint "Optimal Transport in Economics" also covers this ground — [arXiv 2609.06277](https://arxiv.org/pdf/2609.06277) (title only; not read).
- **Reaction networks, network tomography, compartmental identifiability:** see Q5 (Anderson-Craciun-Kurtz; Jahnke-Huisinga) and Q6 (Vardi; Meshkat-Sullivant-Eisenberg).

### Inferences
- **Jackson traffic equations equal the Hawkes mean equation (my derivation).**
  - Jackson: `lambda = gamma + R^T lambda`, so `lambda = (I - R^T)^-1 gamma`.
  - Hawkes: `Lambda = (I - G^T)^-1 mu`. The algebra is identical.
  - The difference is semantic. R is substochastic routing (customers move, exit with probability `1 - sum_j r_ij`). G is offspring (events multiply).
  - So "semi-conservative Hawkes" means Hawkes with substochastic G, plus exogenous arrivals, with the Jackson network as its queueing reading.
  - The infinite-server (M/M/infinity) variant, where each attention unit dwells independently, has independent Poisson stationary laws, matching Jahnke-Huisinga and Anderson-Craciun-Kurtz. Three fields agree on this structure.
- **Gravity model as a flow estimator (my mapping).**
  - Doubly constrained model: `T_ij = A_i O_i B_j D_j exp(-beta c_ij)`, with O = y_t, D = y_{t+1}, c_ij = semantic distance.
  - This is exactly balanced entropic OT. beta is calibrated in transport planning by matching observed mean trip cost, here mean semantic distance of outlet-level transitions.
  - Singly constrained gravity models (one margin free) are one-sided unbalanced OT: mass created at destinations or lost at origins. These variants are standard in spatial interaction modelling but not sourced this session.
- **CTM on the narrative graph (my mapping).**
  - Conservation: `n_i(t+1) = n_i(t) + inflow_i - outflow_i + news_i - decay_i`.
  - Flow: `flow_ij = min( beta_ij * Send_i, Recv_j )`, with `Send_i = min(v n_i, Q_i)` and `Recv_j = min(Q_j, w (N_j - n_j))`.
  - N_j = narrative capacity (for example limited by how many outlets or analysts cover it).
  - Mechanism: saturated narratives refuse inflow, so attention spills to neighbours. Non-smooth (min); estimate with soft-min relaxations.
  - Value: medium, mainly as a capacity mechanism complementing divisive normalization.
- **Compartmental identifiability applied.** Yggdrasil observes all narrative compartments but not the reservoir (environment) flows. Leaks (decay) plus cycles produce unidentifiable parameter combinations unless more outputs are added. Outlet-level observations and engagement metrics act as additional outputs.

### Gaps
- I did not source opinion dynamics (voter model: opinion densities are martingales, i.e. conserved in expectation), hydrology (Nash linear-reservoir cascades give gamma-shaped impulse responses, a physical origin for Hawkes-like kernels; transit-time / StorAge Selection theory for "age of attention"), or Kelly networks this session. They are worth a follow-up but are unverified here.
- I did not source singly constrained gravity models.

---

## Q9. Synthesis: comparison table and ranked recommendation for (a) transition weights, (b) semi-conservation, (c) LOD compression

### Takeaway
No single formalism does all three jobs. The recommended stack:
- **(a) Transition weights:** a prior-regularized aggregate-Markov estimator, i.e. unbalanced OT / Schrödinger-bridge scaling of a semantic prior kernel per window pair, pooled into a substochastic P by constrained conditional least squares and lagged-covariance moments, plus outlet transitions as micro-data. Equivalently, CGM-EM with a Sinkhorn E-step.
- **(b) Semi-conservation:** an open monomolecular reaction network (Poisson-multinomial transfer + immigration + decay; the Jackson/M/M/infinity routing reading of a substochastic Hawkes). Competition goes in a magnitude x divisive-share layer, not in the subtractive `-kappa S` term.
- **(c) LOD compression:** strong/exact lumpability with a numeric defect, checked by an informational-closure predictive test, with partitions proposed by KL-spectral aggregation or the Laplacian RG.

On the user's current proposal: the subtractive competition term is the weakest component. It has no capacity bound, it changes ratios, it depends on clustering granularity, and it linearizes pool depletion incorrectly (Q2, Q3).

### Cited Findings
- Sources for every row below are given in Q1-Q8. Key anchors:
  - Hofbauer equivalence — [bioRxiv 2025](https://www.biorxiv.org/content/10.1101/2025.03.28.645916.full.pdf)
  - NGM spectral threshold — [van den Driessche & Watmough](https://watmough.ext.unb.ca/papers/mgroup.pdf)
  - SIR-Hawkes — [arXiv 1711.01679](https://arxiv.org/pdf/1711.01679)
  - Normalization — [Carandini & Heeger](https://pmc.ncbi.nlm.nih.gov/articles/PMC3273486)
  - RI logit — [Matejka & McKay](https://doi.org/10.1257/aer.20130047)
  - Monomolecular CME — [Jahnke & Huisinga](https://mural.maynoothuniversity.ie/1729/1/JaHu2005MasterEquation.pdf)
  - UOT scaling — [Chizat et al.](https://arxiv.org/abs/1607.05816)
  - Trajectory-inference identifiability — [Lavenant et al.](https://arxiv.org/abs/2102.09204)
  - Aggregate-Markov CLS/MoM — [Bernstein & Sheldon](https://ar5iv.labs.arxiv.org/html/1604.04182)
  - CGM hardness — [Sheldon et al. 2013](https://proceedings.mlr.press/v28/sheldon13.html)
  - Lumpability — [Buchholz](https://resolve.cambridge.org/core/journals/journal-of-applied-probability/article/abs/exact-and-ordinary-lumpability-in-finite-markov-chains/2DC748F09D80BEEB03CCF18036E149D7)
  - KL aggregation — [Deng, Mehta & Meyn](https://experts.illinois.edu/en/publications/optimal-kullback-leibler-aggregation-via-spectral-theory-of-marko/)
  - LRG — [Villegas et al.](https://www.arxiv.org/abs/2203.07230)
  - Closure — [Rosas et al.](https://arxiv.org/html/2402.09090v2)

### Inferences

**Comparison table** (cost per 15-minute window unless noted; n = narratives, m = graph edges, T = windows, L = kernel lags)

| # | Formalism (field) | Governing equation (plain text) | Conservation / sources and sinks | Estimation from per-narrative aggregate counts | Key theorem / condition | Cost | Narrative mapping | Best for |
|---|---|---|---|---|---|---|---|---|
| 1 | Generalized LV / MAR(1) (ecology) | `dx_i/dt = x_i(r_i + sum_j a_ij x_j)`; `log y_t = a + B log y_{t-1} + e` | None intrinsic | OLS/GLS per narrative; gradient matching | MAR stability from eigenvalues of B (Ives 2003) | O(T n^2) fit | species = narratives; a_ij = displacement or facilitation | Signed interaction features; not flows |
| 2 | Replicator + reservoir (evolutionary games) | `dz_i/dt = z_i((Az)_i - zAz)` | Exact `sum z = 1`; reservoir strategy n+1 = unattended | Log-ratio regression | Hofbauer: LV(n) equivalent to replicator(n+1) | O(n^2) | shares of attention; strategy n+1 = inattention | (b) share dynamics |
| 3 | Multi-strain SIRS + cross-immunity (epidemiology) | `dI_i/dt = beta_i S I_i/N + sum_j(m_ji I_j - m_ij I_i) - gamma I_i`, etc. | Exact `S + sum I + R = N`; imports = news | Poisson/INAR regression; state-space filtering | Threshold R0 = rho(NGM); competitive exclusion on shared pool (Prakash) | O(n^2) per step | S = available attention; I_i = narrative attention; R = fatigue; sigma_ij = similarity | (b) principled depletion; m_ij gives (a) |
| 4 | NGM / renewal = linear Hawkes / INAR (epidemiology, point processes) | `E y_j[t] = mu_j + sum_i sum_k G_ij[k] y_i[t-k]` | None (offspring) | Binned Poisson regression / EM (Kirchner) | Stationary iff rho(G) < 1; Hawkes = INAR(infinity) | O(T n^2 L) | G_ij = offspring of i on j | Excitation prior; not transfer |
| 5 | HawkesN (pool depletion) | `lambda_i = (S_t/N) * D_i` | Finite pool | Likelihood (Rizoiu 2018) | Equals SIR infection rate after marginalizing recoveries | O(n^2) | S_t = remaining attention | (b) replaces `-kappa S` |
| 6 | Divisive normalization / attention normalization / shunting (neuroscience) | `lambda_i = C a_i D_i / (sigma + sum_j w_ij a_j D_j)`; Grossberg `x_i = B I_i/(A+I)` | Hard capacity (total < C or B) | Nonlinear least squares / Poisson likelihood | Ratio-preserving; merge-consistent for exponent 1 (my derivation) | O(n + nnz w) | neurons = narratives; A = market-relevance field | (b) competition; (c) merge-consistent |
| 7 | Subtractive inhibition Hawkes (current proposal) | `lambda_i = [D_i - kappa S]_+` | No capacity; total depends on number of active narratives | As Hawkes, with signed kernels | Bremaud-Massoulie Lipschitz sufficient conditions | O(T n^2 L) | — | Sparsification only; weak for (b), fails (c) |
| 8 | Rational-inattention logit (economics) | `pi_i proportional to P0_i exp(v_i/lambda)` | Exact shares; capacity in bits | Log-ratio regression | Shannon cost gives logit (Matejka-McKay) | O(n) | actions = narratives; P0 = prior shares | Destination attractiveness prior; (c) category attention |
| 9 | Open monomolecular reaction network / Poisson-multinomial transfer (chemical physics; also Jackson / M/M/infinity) | `y_{t+1} = sum_i Mult(y_i; P_i.) + Poisson(Lambda)` | Exact on internal reactions; 0 <-> A_i = news / decay | CLS / Poisson pseudo-likelihood; dispersion separates transfer from reproduction | Exact Poisson-multinomial solution (Jahnke-Huisinga); deficiency 0 gives product-Poisson (Anderson-Craciun-Kurtz); Jackson product form | O(T n^2) | A_i = attention units on i | (b) best; (a) via P |
| 10 | Graph continuity + Hodge (discrete calculus) | `Delta y = s - d - B f` | Kirchhoff at nodes | Min-norm flow = gradient flow via Laplacian solve | Flows identified only modulo the cycle space (dim m - n + c); Thomson principle | ~O(m) | phi = attention pressure | (a) baseline and sanity check; shows which cycles are unseen |
| 11 | Entropic unbalanced OT (WFR/HK) / gravity-IPF (applied math, transport planning) | `min (C . pi) + eps KL + lam KL(margins)` | Soft; creation and destruction penalized by lam | Generalized Sinkhorn per window pair | Unbalanced Sinkhorn convergence; HK geometry (Liero-Mielke-Savare) | O(n^2) per iteration | C = semantic distance; pi = flows | (a) instantaneous flows; (b) geometric |
| 12 | Waddington-OT / gWOT / unbalanced Schrödinger bridge (single-cell biology) | min `H(R / prior)` + data fit; growth `g = exp(J dt)` | Growth and death explicit | Entropic OT on document clouds, aggregated by memberships; pooled across windows | Lavenant Thm 1.1 (gradient drift: min-entropy recovers the true law); consistency; transport-vs-branching confound | O(N_docs^2) per pair (sparse or low-rank possible) | cells = documents; clusters = narratives | (a) best for forensic ancestry |
| 13 | Aggregate-Markov CLS / MoM / CGM (statistics) | `Y = X P + 1 Lambda^T + E`; CGM over flow tables | Substochastic P + immigration | QP / CLS; lagged-covariance MoM; CGM-EM with convex MAP | CLS consistent (exact counts); MoM consistent with noise; CGM exact inference NP-hard | O(T n^2) | flow tables = units moving i -> j | (a) pooled, identifiable P |
| 14 | Lumpability / KL aggregation / LRG / closure / Mori-Zwanzig (probability, statistical physics) | `V^T A = A_hat V^T`; `I(Y_{t+1}; y_t / Y_t) = 0` | Preserved if lumpable | Defect metric; predictive closure test; spectral or RG partitioning | Kemeny-Snell / Buchholz exactness; causal = informational closure (Rosas); non-lumpable gives memory kernels | O(nnz A) per block; RG needs eigen-decomposition | parent node = block | (c) best |
| 15 | Cell transmission model (traffic) | `n_i(t+1) = n_i + in - out`; `flow = min(Send, Recv)` | Exact plus ramps | Soft-min relaxation fit | Discrete LWR analog; shock capture | O(m) | capacity N_j per narrative | (b) capacity and spillback complement |

**Ranked recommendation (a): narrative-to-narrative transition weights usable as a search prior**
1. **Prior-regularized aggregate-Markov estimator (rows 11 + 12 + 13 combined).**
   - Per window pair, compute unbalanced entropic-OT flows with semantic cost (narrative-level, or document-level aggregated by soft memberships). This is a Schrödinger-bridge update of a prior kernel, and it explicitly models news (growth) and decay (death) to avoid Lavenant's spurious-transport failure.
   - Pool into a time-homogeneous substochastic P via constrained CLS plus lagged-covariance MoM (Bernstein-Sheldon), regularized by KL toward the OT prior, with outlet-level transitions as partial micro-data.
   - Justification: Lavenant Theorem 1.1 (min-entropy identifiability for potential-driven dynamics), CLS/MoM consistency, Yule-Walker identifiability from fluctuations.
2. **CGM-EM with a Sinkhorn E-step (row 13).** Count-level exact framework. MAP flow tables are approximately entropic OT with cost -log P (my derivation); use when counts are small and integer structure matters.
3. **Hawkes G (row 4, current).** Retain as an excitation prior. Do not read it as transfer. Row-normalizing G does not create conservation semantics.
4. **Graph continuity minimum-norm gradient flows (row 10).** Cheapest baseline. It also tells you which circulations no snapshot method can see without time homogeneity or priors.
5. **LV/MAR interaction matrices (row 1).** Signed influence features only.

**Ranked recommendation (b): modelling semi-conservation**
1. **Open monomolecular reaction network / Poisson-multinomial transfer with immigration and decay (row 9).** Exact likelihood structure, exact conservation of internal moves, explicit source and sink reactions, product-Poisson theory, and three-field agreement (reaction networks, Jackson/M/M/infinity, and the `G = P + H` split of Hawkes). Add bimolecular `A_i + A_j -> 2 A_j` terms for imitation-driven replicator competition.
2. **Magnitude x divisive share (rows 6 + 2 + 8).** The total S_t follows a saturating balance (Grossberg capacity / SIRS pool). Shares follow divisive normalization with exponent 1 = replicator = RI-logit.
3. **SIRS with shared and outlet-partitioned susceptible pools and cross-immunity (rows 3 + 5).** The most mechanistic option for fatigue and replenishment, and the correct nonlinear version of what `-kappa S` approximates.
4. **Unbalanced OT (row 11).** Geometric semi-conservation. lam prices creation and destruction against transport.
5. **Subtractive `-kappa S` (row 7).** Ranked last for conservation: no capacity, ratio distortion, granularity dependence, and a misspecified linearization of depletion (kappa should scale with D_i).

**Ranked recommendation (c): justifying LOD compression**
1. **Strong / exact lumpability with a defect metric (row 14).** Exact sufficient-statistic condition for macro dynamics; cheap; gives an expand/collapse rule.
2. **Informational-closure predictive test (Rosas 2024).** Model-agnostic, data-driven validation of each merge. Equivalent to causal closure and linked to strong lumpability.
3. **KL-optimal spectral aggregation (Deng-Mehta-Meyn; information-bottleneck variant).** Proposes partitions from the estimated flow dynamics.
4. **Laplacian RG (Villegas 2023).** Builds a scale-adaptive multiscale tree from the similarity graph, with time-scale-dependent resolvability.
5. **Mori-Zwanzig.** Explains, and lets you compute, the memory kernels coarse nodes need when lumpability fails.
- Supporting condition: choose model components that are closed under merging (Poisson-multinomial transfer, divisive with exponent 1, nested logit), so that compression does not change the model class. Subtractive competition fails this.

**Concrete synthesis model (my proposal for the system designer; untested).**
- Mean structure: `E y_{t+1} = P^T y_t + R_t + mu_t`.
  - P: substochastic transfer with sparse support on semantic kNN, prior from unbalanced OT.
  - R_t: a reproduction term, `R_t = C_t * normalize( H^T y_t + mu_t )`, where normalize is divisive normalization with exponent 1 over a local pool and C_t is a saturating capacity.
  - mu_t: exogenous news arrivals.
- Observation model: Poisson-multinomial, with dispersion to help separate P from H.
- LOD: refine or collapse tree nodes by the lumpability defect and the closure test.
- Fit: windowed QP/EM. Read forensic "ancestry" by composing the OT couplings.

### Gaps
- None of the recommended combinations has been validated on news-attention data in the literature I found. The synthesis model, the merge-consistency derivation, the `G = P + H` dispersion-identifiability argument and the CGM-to-entropic-OT derivation are mine and need empirical and theoretical checking.
- The user's semi-conservation premise itself is untested. Run the variance-ratio diagnostic (Q1) and check whether total S_t is approximately invariant outside news shocks before committing to strongly conservative models. If y measures publication supply rather than reader time, conservation may be weak, and Hawkes-style excitation (row 4) plus divisive shares may be the better fit.
