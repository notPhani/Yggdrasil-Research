# Point-process and collective-attention models for narrative attention in Yggdrasil

Scope: what the literature says about how much attention each news narrative gets over time, and how attention in one narrative excites or inhibits others. These notes are written so a designer can write down and defend an exact attention model, with each claim checked against the current Yggdrasil proposal.

Notation used throughout (plain text, no LaTeX). The proposal under review is:
- y[i][t] = attention mass on narrative i in 15-min window t (fractional, because membership is soft)
- z[j][m][t] = a_m*z[j][m][t-1] + (1-a_m)*y[j][t-1], with m indexing timescales {1h, 6h, 1d, 1w}
- eta[i][t] = b[i][t] + sum_j sum_m A[i][j][m]*z[j][m][t] - kappa*T_recent[t]
- lambda[i][t] = s*softplus(eta[i][t]/s), with quasi-Poisson likelihood (Var = phi*mean), Gaussian priors, and MAP fitting.

Unrolling the trace gives z[j][m][t] = sum_{k>=1} (1-a_m)*a_m^(k-1)*y[j][t-k]. Each kernel has total mass exactly 1, so A[i][j][m] reads as "expected extra attention units in i per unit of attention in j, routed through timescale m" (in the linear regime of the link).

Labels: [PROVEN] = a theorem with stated conditions. [EMPIRICAL] = a measured result. [HEURISTIC] = a modeling choice or argument with no proof. Years are publication years.

---

## Q1. Multivariate and network Hawkes models for information diffusion and influence: exact forms, estimators, guarantees

### Takeaway
The proposal is, almost term for term, the discrete-time network Hawkes model of Linderman & Adams (2015): a weight times a normalized lag profile built from basis functions. It is also the "dictionary of exponentials" parameterization of Bacry et al. (2020). So the structure is well supported. The literature differs from the proposal in how it regularizes. It uses sparsity (spike-and-slab or l1), low rank (nuclear norm), and stability-aware priors, and it carries oracle-inequality guarantees. Plain Gaussian (ridge) priors have none of these. Newer theory (2024-2026) covers time-varying baselines, latent confounders and binned data, all of which apply directly to GDELT batches.

### Cited Findings

**Zhou, Zha & Song 2013 (AISTATS), sparse low-rank multi-dimensional Hawkes**
- Model [HEURISTIC structure, standard Hawkes]: lambda_u(t) = mu_u + sum_{t_j < t} a_{u,u_j} * g(t - t_j), with exponential kernel g(t) = w*exp(-w*t). Log-likelihood: L(A, mu) = sum_i log lambda_{u_i}(t_i) - sum_u integral_0^T lambda_u(t) dt. The infectivity matrix A gets nuclear-norm plus l1 penalties at the same time, to encode community (low-rank) structure and sparsity. Optimization is ADMM combined with majorization-minimization. Tested on synthetic data and MemeTracker. — [Zhou, Zha & Song 2013](http://proceedings.mlr.press/v31/zhou13a.html)
- Follow-up: A is parameterized from node features ("Learning Parametric Models for Social Infectivity in Multi-Dimensional Hawkes Processes", AAAI 2014). This matters for cold start (see Q7). — [AAAI 2014](https://doi.org/10.1609/aaai.v28i1.8733)

**Linderman & Adams 2014 (ICML), network Hawkes**
- Impulse response decomposition [HEURISTIC]: h_{k,k'}(dt) = A_{k,k'} * W_{k,k'} * g_{theta_{k,k'}}(dt). A in {0,1} is a binary adjacency drawn from a random-graph prior (Erdos-Renyi, stochastic block model, latent distance, and others), with A_{k,k'} ~ Bernoulli(Theta(u_k, u_k')). W >= 0 holds Gamma-distributed weights. g is a normalized density with compact support, so W is in units of "expected number of child events". Together these form a spike-and-slab prior on (A, W). — [Linderman & Adams 2014](https://arxiv.org/abs/1402.0914)
- Inference: Gibbs sampling with auxiliary parent variables z_n, which by Poisson superposition make the conditionals conjugate. Weights get Gamma priors, background rates get Gamma priors, and the impulse shape is logistic-normal with a normal-gamma prior. A sparse log-Gaussian Cox process background captures shared fluctuations (intraday S&P 100 volume, seasonal homicide). Data: S&P 100 trades and Chicago gang homicides 1980-1995. — [Linderman & Adams 2014](https://arxiv.org/abs/1402.0914)
- Stability [PROVEN condition, standard; HEURISTIC prior tuning]: a stable network needs lambda_max = max|eig(A .* W)| < 1. Their generative prior uses random matrix theory. With W ~ Gamma(alpha, beta) and A ~ Bern(rho), the entry mean is mu = rho*alpha/beta and the largest eigenvalue is approximately N(mu*K, sigma^2). They pick rho so that min(sigma*sqrt(K), mu*K + 3*sigma) = 1. Larger networks need sparser or weaker priors. — [Linderman & Adams 2014](https://arxiv.org/abs/1402.0914)

**Linderman & Adams 2015, discrete-time network Hawkes (closest match to the proposal)**
- Model: lambda_{t,k} = lambda0_k + sum_{k'} sum_{t'<t} s_{t',k'} * h_{k'->k}[t - t'], where s are binned counts. Interactions inside the same bin are explicitly ignored ("events do not interact on time scales faster than dt"). The kernel factorizes as h_{k->k'}[d] = W_{k->k'} * sum_b g_b^{(k,k')} * phi_b[d], with fixed basis functions phi_b normalized so that sum_d phi_b[d]*dt = 1, and g ~ Dirichlet(gamma) so that sum_b g_b = 1. W follows a spike-and-slab prior: A ~ Bern(p), W | A=1 ~ Gamma(kappa, v), W | A=0 = 0. Inference is Gibbs plus stochastic variational inference (SVI). The discrete-time version "vastly outperforms" continuous time in cost per Gibbs sweep at high event rates. — [Linderman & Adams 2015](https://arxiv.org/abs/1507.03228)
- Mapping to the proposal: A[i][j][m] = W_{j->i} * g_m^{(j,i)}, with phi_m[d] = (1-a_m)*a_m^(d-1). The proposal's unconstrained A[i][j][m] equals this factorization when A >= 0. Letting A be signed adds inhibition, which Linderman-Adams do not allow. — [Linderman & Adams 2015](https://arxiv.org/abs/1507.03228)

**Bacry, Bompaire, Gaiffas & Muzy (arXiv 2015; JMLR 21, 2020), sparse and low-rank MHP**
- Kernel parameterization: phi_{j,j'}(t) = sum_{k=1..K} a_{j,j',k} * h_{j,j',k}(t), with ||h_k||_1 = 1. The default is a dictionary of exponentials h_k(t) = alpha_k*exp(-alpha_k*t) with fixed memory parameters alpha_1..alpha_K. A is then a d x d x K "cross-scale adjacency tensor". This is exactly the proposal's multi-timescale structure. — [Bacry et al. 2020](https://arxiv.org/abs/1501.00725)
- Estimator: least-squares functional R(theta) = ||lambda_theta||_T^2 - (2/T) * sum_j integral lambda_{j,theta}(t) dN_j(t), penalized by l1 plus trace norm on A. [PROVEN]: a sharp oracle inequality covering both the sparsity and low-rank penalties (their Theorem 6). It rests on new matrix-martingale concentration inequalities of Freedman/Bernstein type with data-driven weights. — [Bacry et al. 2020](https://arxiv.org/abs/1501.00725); [JMLR page](https://www.jmlr.org/beta/papers/v21/15-114.html)

**Hansen, Reynaud-Bouret & Rivoirard 2015 (Bernoulli 21(1):83-143), Lasso for multivariate point processes**
- Contrast: C(f) = -2*psi(f) . N_T + ||f||_T^2. Its compensator is minimized at the true intensity. For a dictionary expansion f_a this becomes C(f_a) = -2 a'b + a'Ga, with b_phi = psi(phi) . N_T and Gram matrix G_{phi1,phi2} = <phi1, phi2>_T. Weighted Lasso: a_hat in argmin { -2a'b + a'Ga + 2 d'|a| }. — [HRR 2015](https://arxiv.org/abs/1208.0570)
- Theorem 1 [PROVEN, non-probabilistic]: if G >= cI and |b_phi - bbar_phi| <= d_phi for all phi (where bbar_phi = psi(phi) . Lambda_T), then ||psi(f_hat) - lambda||_proc^2 <= C * inf_a { ||lambda - psi(f_a)||_proc^2 + c^(-1) * sum_{phi in S(a)} d_phi^2 }. Their Theorem 2 chooses data-driven weights d_phi from new Bernstein-type martingale inequalities, so the conditions hold with high probability. — [HRR 2015](https://arxiv.org/abs/1208.0570)

**Xu, Farajtabar & Zha 2016 (ICML), Granger causality for Hawkes**
- Uses Eichler et al.'s result that u' -> u is absent from the Granger graph iff phi_{u,u'}(t) = 0 for all t >= 0. Kernels are expanded on basis functions. The estimator is MLE with a sparse-group-lasso penalty (one group per pair (u,u'), across basis coefficients) plus pairwise kernel-similarity regularization (MLE-SGLP), solved with EM-type updates. — [Xu, Farajtabar & Zha 2016](https://arxiv.org/abs/1602.04511)

**Eichler, Dahlhaus & Dueck 2017 (J. Time Series Analysis 38(2):225-242), graphical modeling for Hawkes**
- Proposition 3.2 [PROVEN]: for a multivariate (linear) Hawkes process, N_i does not Granger-cause N_j with respect to N iff phi_{ji}(u) = 0 for all u. Granger noncausality and local independence coincide here. — [Eichler et al. 2017](https://arxiv.org/abs/1605.06759)
- Estimator: discretize with bin width h, so Y_t^h is approximately binary for small h, then fit a VAR(k) by least squares ("infinite-order autoregression"). Theorem 4.1 [PROVEN] gives consistency when k_T*h_T -> infinity, k_T*h_T^2 -> 0, and k_T^2/T -> 0, the kernel integral is finite, the kernel is Lipschitz with ||phi(u)|| <= C/u, and the tail mass beyond h_T*k_T vanishes. — [Eichler et al. 2017](https://arxiv.org/abs/1605.06759)

**Achab, Bacry, Gaiffas, Mastromatteo & Muzy (JMLR 2017/2018), NPHC**
- Estimates G = [g_ij], g_ij = integral_0^inf phi_ij(u) du (the average number of type-i events directly triggered by one type-j event), without estimating kernel shapes. It matches second- and third-order integrated cumulants (a generalized method of moments). Robust to kernel shape. Tested on MemeTracker and order-book data. — [Achab et al.](https://arxiv.org/abs/1607.06333)

**2018-2026: sample complexity, identifiability, online estimation**
- Hall & Willett (IEEE Trans. Inf. Theory 2016; arXiv 2014) "Tracking dynamic point processes on networks". Online Dynamic Mirror Descent on a time-discretized Hawkes loss: lambda_tilde_{t+1} = proj(lambda_hat_t - eta_t * grad l_t(lambda_hat_t)), then lambda_hat_{t+1} = Phi_t(lambda_tilde_{t+1}, W). Theorem 1 [PROVEN]: for contractive dynamics and eta_t proportional to 1/sqrt(t), regret against any comparator sequence is <= C * (1 + sum_t ||lambda_{t+1} - Phi_t(lambda_t)||_2) * sqrt(T). Regret therefore grows with how far the comparator departs from the assumed dynamics, which is the right guarantee when the network itself drifts. Theorem 2 extends this to learning W jointly. — [Hall & Willett](https://arxiv.org/abs/1409.0031)
- Yang, Etesami, He & Kiyavash 2017/2018, NPOLE-MHP. Nonparametric online estimation of triggering kernels in an RKHS, with cumulative regret O(log T) (stated in Sec. 1; the abstract reports O(1/T)-type per-step regret and stability) and runtime comparable to parametric online methods. — [Yang et al.](https://arxiv.org/abs/1801.08273)
- Cai, Zhang & Guan (JASA 2022; arXiv 2020): non-stationary Hawkes with both excitation and inhibition. Sparse least-squares estimation, concentration inequalities via thinning, non-asymptotic error bounds and selection consistency. Includes a least-squares test of whether the background intensity is constant. — [Cai, Zhang & Guan](https://arxiv.org/abs/2004.03569)
- Mossel & Sridhar 2026 (arXiv Jan 2026) [PROVEN]: for an n-variate Hawkes process with time-varying baselines and non-shift-invariant delay kernels, a dependency graph with bounded maximum degree can be recovered w.h.p. after T = polylog(n) observation time. This holds even with partial observation and imprecise event times. — [Mossel & Sridhar 2026](https://arxiv.org/abs/2601.11717)
- Jin & Huang (ICLR 2026): continuous-time event sequences can be represented by a discrete-time causal model as the interval shrinks. Gives necessary and sufficient path-based identifiability conditions for latent subprocesses (unobserved confounders) and causal influences, with an iterative discover-then-infer algorithm. — [Jin & Huang 2026](https://arxiv.org/abs/2508.11727)
- Chen, Kwan & Stindl 2024: estimation from a discretely observed sample path through a state-space representation with sequential Monte Carlo. The likelihood estimate is unbiased, which allows pseudo-marginal MCMC. Lower MSE than two benchmark binned-data estimators. — [Chen, Kwan & Stindl 2024](https://arxiv.org/abs/2401.11075)
- Dirichlet-Hawkes process (Du et al., KDD 2015) is directly about news. Documents are assigned to clusters by Dirichlet-process preferential attachment, but cluster "sizes" are replaced by each cluster's Hawkes intensity. It clusters news streams by content and arrival dynamics jointly, and creates new clusters online. — [Du et al. 2015](https://doi.org/10.1145/2783258.2783411); [Google Research page](https://research.google/pubs/dirichlet-hawkes-processes-with-applications-to-clustering-continuous-time-document-streams/)
- Domain precedent with GDELT: a 2023 study fit a bivariate Hawkes model with a Granger-causality test between Twitter interactions and GDELT protest reports (#BlackLivesMatter, summer 2020). It reports that social media activity Granger-caused mass-media protest reports early in the protests. — [Scitepress 2023](https://scitepress.org/PublishedPapers/2023/120895)

### Inferences
- The proposal's cross-scale tensor A[i][j][m] is the standard object (Bacry et al. 2020; Linderman & Adams 2015). Its weakness is regularization. With N narratives there are 4*N^2 coefficients. Gaussian priors (ridge) give neither sparsity nor low rank, and they have no oracle guarantee. Better-supported choices are a weighted l1 penalty in the HRR style (or spike-and-slab), optionally plus a nuclear norm on the N x N slices, or the factorization A[i][j][m] = W[j->i]*g_m^{(j,i)} with a Dirichlet g.
- Granger semantics: for a strictly monotone link (softplus is one), N_j fails to Granger-cause N_i iff A[i][j][m] = 0 for all m. This extends Eichler's proposition through the monotone link (inference, not a cited theorem). But the global term -kappa*T_recent makes every narrative Granger-cause every other by construction. Forensic "influence" claims should therefore be read off A only, with the mean-field competition reported separately.
- Mossel-Sridhar (2026) and Jin-Huang (2026) support learning edges under non-stationary baselines. Jin-Huang also warn that latent drivers (social media and wire services that GDELT does not see) produce spurious edges unless identifiability conditions hold.

### Gaps
- I found no sample-complexity result for the exact discrete-time, softplus, quasi-Poisson, fractional-count model. The existing bounds cover linear or ReLU/Lipschitz continuous-time models, or linear binned models.
- I found no peer-reviewed multivariate Hawkes model of GDELT narrative-level attention beyond the bivariate BLM study.

---

## Q2. Nonlinear Hawkes: stability, inhibition, links, explosion, and what is lost or recovered

### Takeaway
The scaled softplus link is a good choice. It is non-decreasing and 1-Lipschitz, so the Bremaud-Massoulie theory applies. The sharper sufficient condition (Costa et al. 2020; Sulem et al. 2024) needs only the spectral radius of the positive parts of the kernels to be below 1. Inhibition, including -kappa*T, cannot cause instability in that continuous-time theory. Exponential links are the risky choice: fitted exp-link GLMs routinely blow up in simulation. Nonlinearity costs the exact immigrant-offspring cluster decomposition, so attribution becomes approximate.

### Cited Findings
- Bremaud & Massoulie 1996 (Annals of Probability 24(3)) [PROVEN]: general conditions for existence of a stationary version and convergence to equilibrium of nonlinear mutually exciting processes lambda(t) = phi(integral_{-inf}^{t-} h(t-s) N(ds)). The classical sufficient condition is phi alpha-Lipschitz with alpha * integral |h| < 1 (multivariate: spectral radius of [alpha_i * ||h_ij||_1] < 1). Bounded-intensity processes with Lipschitz dynamics (Kerstan) always have a stationary version. — [Bremaud & Massoulie 1996](https://doi.org/10.1214/aop/1065725193)
- Sulem, Rivoirard & Rousseau (arXiv 2021; Bernoulli 2024), Lemma 2.1 [PROVEN]: for lambda_k(t) = phi_k(nu_k + sum_l integral h_lk(t-s) dN_l(s)), with each phi_k non-decreasing and L-Lipschitz, a unique stationary version with finite mean exists if either (C1) r(S+) < 1 with S+_lk = L*||h+_lk||_1 (positive parts only), or (C2) every phi_k is bounded. For inference they use the stronger ||S+|| < 1. Link families covered: ReLU (x)+, clipped exponential min(e^x, Lambda), sigmoid, and softplus log(1+e^x). They also give posterior concentration rates and graph-recovery consistency. — [Sulem et al.](https://arxiv.org/abs/2103.17164)
- Costa, Graham, Marsalle & Tran (Adv. Appl. Prob. 2020; arXiv 2018) [PROVEN]: Hawkes processes with signed reproduction functions and phi(x) = (x)+. They prove limit theorems and exponential concentration inequalities using renewal (regeneration) techniques instead of the cluster representation, which fails for signed kernels. Their Theorem 1 is the source of condition (C1). — [Costa et al.](https://arxiv.org/abs/1801.04645)
- Discrete-time inhibitory Hawkes is delicate. A J. Appl. Prob. paper is titled "Almost complete characterization of the stability of a discrete-time Hawkes process with inhibition and memory of length two". The title alone shows that exact stability regions are only partly characterized even for memory length 2 (contents not reviewed here). — [J. Appl. Prob.](https://resolve.cambridge.org/core/journals/journal-of-applied-probability/article/almost-complete-characterization-of-the-stability-of-a-discretetime-hawkes-process-with-inhibition-and-memory-of-length-two/B720C3C6391FE38998644EB57AACA905)
- Gerhard, Deger & Truccolo 2017 (PLoS Comp Biol) [EMPIRICAL plus approximate theory], on the exponential link lambda(t|H_t) = c*exp(I0 + integral eta(s) dS(t-s)):
  - Data-fitted point-process GLMs "are often unstable, leading to divergent firing rates" even when they pass standard goodness-of-fit tests. In monkey cortex data, 35 of 99 fitted models had finite divergence times in simulation.
  - A mean-field quasi-renewal approximation gives a transfer function f(A0) with fixed points f(A0) = A0. These classify models as stable, divergent, or fragile (metastable with an expected escape time).
  - They recommend stability analysis as a complementary goodness-of-fit check and stability-constrained MLE. Stabilized MLEs reproduce training statistics nearly as well.
  — [Gerhard et al. 2017](https://doi.org/10.1371/journal.pcbi.1005390)
- Mei & Eisner 2017 (NeurIPS), neural Hawkes [HEURISTIC]: chose exactly the proposal's link, f(x) = s*log(1 + exp(x/s)), with a learned scale s_k per event type. It approaches ReLU as s -> 0. It keeps intensities positive while allowing inhibition, and gives "an approximately additive effect inspired by the classical Hawkes process". — [Mei & Eisner 2017](https://arxiv.org/abs/1612.09328)
- Isotonic Hawkes (Wang, Xie, Du & Song, ICML 2016): learns a monotone link nonparametrically together with the kernel parameters, with a provable iterative algorithm. It fits nonlinear patterns that linear Hawkes cannot. — [Wang et al. 2016](https://proceedings.mlr.press/v48/wangg16.html)
- MLE for exponential Hawkes with self-excitation or inhibition (ReLU-type link): Bonnet, Martinez Herrera & Sangnier 2021. — [Bonnet et al. 2021](https://doi.org/10.1016/j.spl.2021.109214)
- Branching (cluster) structure: for linear Hawkes the branching factor n* = ||phi||_1 is the mean number of direct offspring per event. It gives the endogenous fraction of events, and n* < 1 is subcritical. — [Rizoiu et al. tutorial 2017](https://arxiv.org/abs/1708.06401); [Filimonov & Sornette 2015](https://arxiv.org/abs/1308.6756)
- Competing-product point processes with inhibition: Valera & Gomez-Rodriguez (ICDM 2015) let the usage of one product modulate the others. The fit is a convex program that decouples over nodes. — [Valera & Gomez-Rodriguez 2015](https://doi.org/10.1109/icdm.2015.40)

### Inferences
- Applying Sulem Lemma 2.1 (C1) to the proposal (continuous-time analogue): softplus_s has derivative sigmoid(x/s), which lies in (0,1), so L = 1. Sufficient condition: rho(P) < 1, where P[i][j] = ||(sum_m A[i][j][m]*kernel_m)+||_1 <= sum_m max(A[i][j][m], 0). The kappa term is purely inhibitory and does not enter. This is the condition to enforce, as a constraint or a prior penalty, during MAP fitting.
- The directly available discrete-time count result (Armillotta & Fokianos, see Q3) is a contraction condition with absolute values. Roughly: rho(sum_m |A[.][.][m]| + kappa*(all-ones coupling)) < 1. Because the all-ones N x N block has spectral radius N*kappa, this bound becomes very conservative for large N. Treat it as sufficient, not necessary. A positive-part-only discrete-time theorem is a gap.
- Softplus cannot explode in finite time because it grows linearly. Supercritical exponential growth is still possible when rho(P) > 1. An exp link can diverge in finite time, as in Gerhard's 35/99 fitted models, so it should not be used for excitation.
- What is lost: with a nonlinear link, lambda is not a sum of immigrant and offspring contributions, so the Poisson cluster representation and exact parent attribution do not exist (Costa et al. use renewal arguments for this reason). What can be recovered: (a) exact attribution in the linear regime (eta >> s) by the linear shares b/eta and A*z/eta; (b) a local linearization, d lambda/d term = sigmoid(eta/s)*term; (c) path attribution such as integrated gradients from a reference eta0, along eta0 + u*(eta - eta0). Option (c) is a heuristic choice, not from the Hawkes literature.

### Gaps
- I found no head-to-head comparison of softplus vs sigmoid vs exp vs ReLU links on news or attention count data. The evidence for softplus is theoretical (Lipschitz, monotone) and ML practice (Mei & Eisner).
- I found no discrete-time theorem extending Costa/Sulem's positive-part condition to Poisson or quasi-Poisson count autoregressions with signed coefficients.

---

## Q3. Discrete-time Hawkes and count models: INAR(infinity), INGARCH / Poisson autoregression, overdispersion, bin width

### Takeaway
Binned Hawkes counts converge to INAR(infinity) as the bin width goes to 0 (Kirchner). INGARCH and Poisson-network-autoregression theory gives stationarity conditions and shows Poisson quasi-MLE is consistent for the conditional mean. This supports quasi-Poisson fitting of fractional soft-membership counts. The concern is that 15-min bins are not small relative to the 1h timescale. About 22% of a 1h exponential kernel's mass falls inside the same bin and cannot be represented by a lag >= 1 model, so the fast coefficient will be biased.

### Cited Findings
- Kirchner 2016 (Stoch. Proc. Appl.; arXiv 1509.02007) [PROVEN]: INAR(p) generalizes to INAR(infinity). Existence and uniqueness hold when the reproduction mean K = sum_{k>=1} alpha_k < 1 (Theorem 1). From a Hawkes process N one builds a family of INAR(infinity) bin-count sequences X_n^(Delta) and point processes N^(Delta)(a,b] = sum_{n: n*Delta in (a,b]} X_n^(Delta). Theorem 3: N^(Delta) converges weakly to the Hawkes process N as Delta -> 0. — [Kirchner 2016](https://arxiv.org/abs/1509.02007)
- Kirchner 2017 (Quantitative Finance; arXiv 1509.02017) [PROVEN asymptotics, EMPIRICAL bias study]:
  - Bin-count approximation: E[X_n | past] ~ Delta*eta + sum_{k=1..p} Delta*h(Delta*k)*X_{n-k}. This rests on three approximations. (7) replaces the in-bin intensity by its value at the bin start. (8) truncates memory at support s = p*Delta. (9) discretizes, which ignores triggering among events inside the same bin. "If we observe two events in a bin... the second may very well be a result of the first... in the approximating model, we ignore this possibility."
  - Procedure: choose a small Delta and a large support s, fit INAR(p) by conditional least squares, and rescale to get the Hawkes baseline and kernel. CLS for VAR(p)/INAR(p) is consistent and asymptotically normal.
  - Simulations: bias becomes essentially invisible for Delta <= 0.01 in their units. Too-small support s biases the variance estimates, while Delta barely affects variance-estimate bias.
  — [Kirchner 2017](https://arxiv.org/abs/1509.02017)
- Cheysson & Lang (arXiv 2020; Annals of Statistics 2022) [PROVEN]: for linear stationary Hawkes processes observed only as counts over fixed-width bins, Whittle (spectral) estimation is consistent and asymptotically normal under a mild moment condition on the reproduction function. It works "even when time intervals are relatively large". The paper notes the INAR approach needs small bins and fails when "the bin size is larger than the typical range of the reproduction function". R package: hawkesbow. — [Cheysson & Lang](https://arxiv.org/abs/2003.04314)
- Shlomovich, Cohen, Adams & Patel 2022 (JCGS) [EMPIRICAL]: "existing methods are capable of producing severely biased and highly variable parameter estimates" on binned Hawkes data. Their binned-Hawkes EM (BH-EM) does much better. — [Shlomovich et al. 2022](https://doi.org/10.1080/10618600.2022.2050247)
- Browning, Sulem, Mengersen, Rivoirard & Rousseau 2021 (PLoS One): discrete-time Hawkes models on daily COVID-19 mortality counts across phases and 10 countries. Shows discrete-time self-exciting count models are workable. — [Browning et al. 2021](https://doi.org/10.1371/journal.pone.0250015)
- Poisson autoregression / INGARCH (Fokianos, Rahbek & Tjostheim, JASA 2009): linear model lambda_t = d + a*lambda_{t-1} + b*Y_{t-1}, with stationarity conditions on (a, b) and likelihood asymptotics via a perturbation argument. — [FRT 2009 (SSRN version)](https://doi.org/10.2139/ssrn.1323291)
- Poisson QMLE (Ahmad & Francq, JTSA 2016) [PROVEN]: regularity conditions under which the Poisson quasi-MLE of the conditional-mean parameter is consistent, plus its asymptotic distribution in the interior and at the boundary. Applies to INAR and INGARCH. Practical meaning: the Poisson score is valid even when the true conditional distribution is not Poisson. — [Ahmad & Francq](https://doi.org/10.1111/jtsa.12167)
- Negative binomial INGARCH (Christou & Fokianos, JTSA 2014): quasi-likelihood inference for NB time series models. — [Christou & Fokianos](https://doi.org/10.1002/jtsa.12050)
- Count Network Autoregression (Armillotta & Fokianos, JTSA 2023/2024) [PROVEN]:
  - Linear PNAR(p): lambda_{i,t} = beta0 + sum_h (beta1h * n_i^(-1) * sum_j a_ij * Y_{j,t-h} + beta2h * Y_{i,t-h}). Stationary and ergodic for fixed N if rho(sum_h G_h) < 1 with G_h = beta1h*W + beta2h*I. For N -> infinity, sum_h (beta1h + beta2h) < 1 suffices.
  - Log-linear PNAR: nu_{i,t} = log lambda_{i,t} = beta0 + sum_h (beta1h * n_i^(-1) * sum_j a_ij * log(1+Y_{j,t-h}) + beta2h * log(1+Y_{i,t-h})). Coefficients may be negative. Stationary if rho(sum_h |G_h|) < 1.
  - Poisson QMLE is consistent and asymptotically normal for both fixed and increasing N. Joint count dependence is handled with a copula-Poisson DGP.
  — [Armillotta & Fokianos](https://arxiv.org/abs/2104.06296)
- Nonlinear Network Autoregression (Armillotta & Fokianos 2022/2024), Theorem 2.1 [PROVEN]: for lambda_t = f(Y_{t-1}), if |f(y) - f(y*)| <= G|y - y*| componentwise with G = mu1*W + mu2*I and rho(G) < 1, then {Y_t} is stationary and ergodic with all moments. QMLE holds with increasing network dimension, and a quasi-score test checks linearity. Example 2 includes a divisive baseline, lambda_{i,t} = beta0/(1 + X_{i,t-1})^gamma + beta1*X_{i,t-1} + beta2*Y_{i,t-1}, where network activity X shrinks the baseline. — [Armillotta & Fokianos](https://arxiv.org/abs/2202.03852)
- Eichler et al. 2017 binning theory needs h -> 0 with k*h -> infinity (see Q1). Linderman & Adams 2015 explicitly ignore within-bin interactions. — [Eichler et al.](https://arxiv.org/abs/1605.06759); [Linderman & Adams 2015](https://arxiv.org/abs/1507.03228)

### Inferences
- Numbers for Delta = 15 min, assuming a_m = exp(-Delta/tau_m):

  | tau_m | a_m | Kernel mass inside one bin, 1 - exp(-Delta/tau) | Mean lag of the discrete kernel, 1/(1-a_m) bins |
  |---|---|---|---|
  | 1h | 0.7788 | 0.221 | ~4.5 bins = 1.13 h |
  | 6h | 0.9592 | 0.041 | — |
  | 1d | 0.98964 | 0.010 | — |
  | 1w | 0.998513 | 0.0015 | — |

  So the 1h component is the one hurt by binning (Kirchner approximation (9); the regime that Cheysson-Lang say breaks INAR methods). Same-bin cascades get absorbed into the baseline and the overdispersion. A[.][.][1h] should be read as a lower bound on fast excitation.
- Quasi-Poisson fits soft-membership counts well. Quasi-likelihood needs only E[y|past] = lambda and Var = phi*lambda, and Ahmad-Francq/Armillotta-Fokianos give consistency of the Poisson score under misspecification. But quasi-Poisson weights each window by 1/lambda. Bursty attention data are likely closer to NB2 (Var = mu + mu^2/r), which down-weights burst windows. Diagnostic: bin windows by fitted lambda and regress the squared Pearson residual variance on lambda. If the variance grows faster than linearly, switch the working variance to NB2 or Tweedie for intervals and residuals (point estimates can stay quasi-Poisson).
- Log-linear PNAR is the closest discrete-time relative of the proposal with signed coefficients. It has proven stationarity (rho(sum|G|) < 1) and QMLE theory. Using log(1+y) inputs inside a log link is a defensible alternative if multiplicative interactions are wanted (see Q5).

### Gaps
- I found no study of the 15-min vs 1h-kernel regime for news data specifically. A simulation study (fit the discrete model to continuous-time simulated Hawkes data binned at 15 min) is needed to quantify bias in A[.][.][1h].
- Whittle/spectral methods (Cheysson-Lang) are proven only for linear stationary Hawkes, not for softplus with competition.

---

## Q4. Empirical shape of collective-attention decay and supported timescales

### Takeaway
News and online attention decay on a cascade of timescales:
- under 5 min plateau (Twitter)
- about 1 hour novelty half-life (digg)
- 2.5 h news-to-blog lag and an 8 h log-shaped peak (MemeTracker)
- most news access gone within about 36 h, with a power-law tail (news portal)
- 12-18 h residence in the Twitter top 50, shrinking over the years
- power-law relaxation over days to months (YouTube)
- two-exponential decay over years (cultural memory)

Single exponentials are rejected almost everywhere. The evidence favors power-law or stretched-exponential kernels, which a sum of log-spaced exponentials (the proposal's 4-timescale basis) approximates over the range it spans.

### Cited Findings
- Wu & Huberman 2007 (PNAS) [EMPIRICAL, digg, about 1M users]: growth N_t = (1 + X_t*r_t)*N_{t-1}. The novelty decay factor fits a stretched exponential (Kohlrausch-Williams-Watts law) r_t ~ exp(-0.4*t^0.4), with t in minutes. It "decays slower than exponential" and "faster than power law". Half-life tau = 69 min, consistent with the observed 1-2 hours on the front page. The stretched exponential is attributed to a superposition of multiple relaxation processes. — [Wu & Huberman 2007](https://arxiv.org/abs/0704.1158)
- Leskovec, Backstrom & Kleinberg 2009 (KDD) [EMPIRICAL, 90M articles and posts from 1.65M sites, Aug 2008 - Apr 2009]:
  - Away from the peak, thread volume "decreases exponentially with time". Within an 8-hour window around the median, volume behaves like y(t) ~ a*log(|t|), which diverges at the peak.
  - News media peak 2.5 hours before blogs, with a "heartbeat" handoff pattern.
  - Generative model: each period, each of N sources picks one thread j with probability proportional to f(n_j)*delta(t - t_j). Here f is increasing in prior volume (for example f(n) = (a + b*n)^gamma, imitation) and delta is decreasing in age (recency, exponential or heavy-tailed).
  — [Leskovec et al. 2009](https://www.cs.cornell.edu/home/kleinber/kdd09-quotes.pdf)
- Dezso et al. 2006 (Phys. Rev. E) [EMPIRICAL, major Hungarian news portal]: a news document's visitation peaks after a few hours and then decays as a power law, not the exponential that simple models predict. This is attributed to power-law inter-visit times of individual users. "Access to most news items significantly decays after 36 hours of posting." — [Dezso et al. 2006](https://doi.org/10.1103/physreve.73.066132)
- Crane & Sornette 2008 (PNAS) [EMPIRICAL plus epidemic-branching model, daily views of about 5M YouTube videos]:
  - Memory kernel phi(t) ~ 1/t^(1+theta), 0 < theta < 1.
  - Predicted relaxation after a burst: exogenous-subcritical ~ 1/(t-tc)^(1+theta); exogenous-critical ~ 1/(t-tc)^(1-theta); endogenous-critical ~ 1/|t-tc|^(1-2theta).
  - Measured exponents cluster at about 1.4, 0.6 and 0.2, consistent with one theta = 0.4 +/- 0.1. About 90% of videos show little activity or Poisson-like dynamics. The other about 10% (about 500,000 videos) show herding with power-law relaxation.
  — [Crane & Sornette 2008](https://arxiv.org/abs/0803.2189)
- SEISMIC (Zhao et al., KDD 2015) [EMPIRICAL, Twitter]: memory kernel phi(s) constant for the first s0 = 5 minutes, then a power-law decay with theta = 0.242 (c = 6.27e-4 so the kernel integrates to 1). Response times are "heavy-tailed... power-law with exponent between 1 and 2". — [Zhao et al. 2015](https://arxiv.org/abs/1506.02594)
- TiDeH (Kobayashi & Lambiotte, ICWSM 2016) [EMPIRICAL, Twitter]: lambda(t) = p(t)*sum_i d_i*phi(t - t_i), using the SEISMIC-style power-law kernel. Infectious rate p(t) = p0*(1 - r0*sin(2*pi*(t + phi0)/Tm))*exp(-(t - t0)/tau_m), with Tm = 1 day and tau_m restricted to 0.5-20 days. The circadian rhythm modulates the excitation itself, not only the baseline. — [Kobayashi & Lambiotte 2016](https://arxiv.org/abs/1603.09449)
- HIP (Rizoiu et al., WWW 2017) [EMPIRICAL, YouTube]: lambda(t) = mu*s(t) + sum_i phi_{m_i}(t - t_i), with phi_m(tau) = kappa*m^beta*(tau + c)^(-(1+theta)). Here s(t) is an observed exogenous promotion series, and the model is fit to daily aggregate volumes through the expected-intensity equation. — [Rizoiu et al. 2017](https://arxiv.org/abs/1602.06033)
- Lorenz-Spreen, Monsted, Hovel & Lehmann 2019 (Nature Communications) [EMPIRICAL]:
  - Data: Twitter 2013-2016, Google Books, movies, Reddit 2010-2015, Wikipedia 2012-2017, publications.
  - A hashtag stayed in the global hourly top 50 for 17.5 h on average in 2013, falling to 11.9 h in 2016.
  - Gradients steepen and peak heights rise across domains, while time-to-peak stays about constant. 24 h resolution was used to avoid diurnal effects.
  — [Lorenz-Spreen et al. 2019](https://doi.org/10.1038/s41467-019-09311-w); [open copy](https://cora.ucc.ie/bitstreams/f4ae8a47-a98a-4a3e-942b-34dbb4a46b9a/download)
- Candia, Jara-Figueroa, Rodriguez-Sickert, Barabasi & Hidalgo 2019 (Nature Human Behaviour) [EMPIRICAL plus model]:
  - Model: du/dt = -(p + r)*u (communicative memory), dv/dt = -q*v + r*u (cultural memory), with u(0) = N, v(0) = 0. Solution: u(t) = N*exp(-(p+r)t), v(t) = N*r/(p+r-q)*(exp(-qt) - exp(-(p+r)t)), and S(t) = N/(p+r-q) * [(p - q)*exp(-(p+r)t) + r*exp(-qt)].
  - The critical time tc is defined by d log S/dt at tc = -(1+delta)*q, with delta about 1.
  - Fits better than log-normal and exponential decay by AICc and R^2 on APS papers (n = 485,105) and USPTO patents (n = 1,681,690), and also on songs, movies and biographies.
  - Communicative memory lasts about 5.6 years for music and 20-30 years for biographies. Critical times are 5-10 years for music, movies and papers.
  — [Candia et al. 2019](https://doi.org/10.1038/s41562-018-0474-5); [open copy](https://par.nsf.gov/servlets/purl/10124838)
- Yang & Leskovec 2011 (WSDM) [EMPIRICAL, 580M tweets and 170M blog/news items]: K-SC clustering finds six main temporal shapes of attention. — [Yang & Leskovec 2011](https://doi.org/10.1145/1935826.1935863)
- Finance analogue [EMPIRICAL]:
  - "The power-law nature of Hawkes kernels remains a solid empirical fact which, at least, calls to question all the approaches based on exponential Hawkes models."
  - Power laws are in practice often "expressed as a sum of 15 exponentials".
  - Hardiman, Bercot & Bouchaud (2013), using power-law kernels, found E-mini S&P reflexivity constant near ||Phi|| = 1.
  — [Bacry, Mastromatteo & Muzy 2015](https://arxiv.org/abs/1502.04592)
- Social-media modeling uses power-law kernels by default ("we use a power-law kernel for modeling information diffusion in Social Media"). — [Rizoiu et al. tutorial 2017](https://arxiv.org/abs/1708.06401)

### Inferences
- Empirically supported timescales for news attention, to compare with the proposal's {1h, 6h, 1d, 1w}:
  - sub-15-min (unresolvable at Delta = 15 min)
  - about 1 h (Wu-Huberman, 69 min)
  - 2-8 h (Leskovec: 2.5 h lag, 8 h log-shaped peak)
  - about 12-36 h (Lorenz-Spreen 11.9-17.5 h; Dezso 36 h)
  - multi-day to month power-law tails (Crane-Sornette, Dezso)
  - years (Candia)

  The 4 exponentials span about 2.2 decades (1h to 168h), with spacing ratios 6, 4 and 7. That is a coarse version of the "sum of exponentials approximating a power law" used in finance. It covers the news-relevant range but has no component beyond 1 week. Re-activation of old narratives (Q5, Garcia-Gavilanes) would be pushed into the baseline. Consider adding a slow (about 30-day) trace or a slowly varying level, and test a 5th timescale at about 2-3 h by likelihood.
- Lorenz-Spreen shows timescales drift over years (shortening). Kernel weights A[...][m] should be tracked online (Hall-Willett) or re-estimated periodically, not fixed.
- TiDeH suggests hour-of-week should also modulate the excitation gain, for example multiplying sum_j sum_m A*z by exp(c_how[t]), not only the baseline.

### Gaps
- I found no study estimating GDELT GKG or RSS article-volume decay kernels at 15-min resolution. All timescale evidence above is from proxies (digg, MemeTracker, news portal, Twitter, YouTube, Wikipedia).
- I found no direct likelihood comparison of a power-law kernel vs a 4-exponential mixture on news-narrative counts.

---

## Q5. Competition for limited attention: zero-sum or partially zero-sum, and how conservation has been tested

### Takeaway
The evidence supports the hypothesis that attention is "semi-conservative": the long-run carrying capacity is stable, short-run totals are elastic, and specific events crowd others out. It does not support subtracting a fixed amount of attention. Nearly every competition model and empirical test acts multiplicatively or proportionally: shares, mass-action exchange, per-capita Lotka-Volterra terms, depletion factors, or proportional dilution. Related narratives tend to excite each other while unrelated ones compete. A strictly conserved system is pushed to criticality (branching ratio about 1), which would contaminate Hawkes fits that ignore the budget.

### Cited Findings
- Zhu 1992 (Journalism Quarterly 69(4):825-836), zero-sum agenda-setting [EMPIRICAL, 3 issues: federal deficit, Persian Gulf conflict, recession]:
  - Argument: the public agenda has limited carrying capacity, so "the addition of any new issue onto the public agenda is at the cost of other issue(s)".
  - Model, a mass-action exchange: dP_t = b * sum_i (M_{t-1} x Q_{t-1,i}) - c * sum_i (N_{t-1,i} x P_{t-1}). P is salience of the focal issue, M its media coverage, Q_i the salience of competing issue i, and N_i its coverage.
  - Results: mutual competition (deficit vs war) and one-way attraction (recession). A preliminary test found that single-issue time-series models overestimated agenda-setting effects by 30%-78%, and that competition came mainly from the public's current concern about competing issues.
  — [Zhu 1992](https://fbaum.unc.edu/teaching/PLSC541_Fall06/Zhu%20JQ%201992.pdf)
- McCombs & Zhu 1995 (Public Opinion Quarterly) [EMPIRICAL, 40 years of Gallup "Most Important Problem" data plus 15,000 individual cases]: "no significant linear increase in the carrying capacity is found". Agenda diversity and issue volatility increased. This is a direct test that capacity is conserved over decades. — [McCombs & Zhu 1995](https://doi.org/10.1086/269491)
- Djerf-Pierre 2012 (Journalism Studies) [EMPIRICAL, Swedish TV news 1979-2009]: issue competition "crowds out" attention to other issues in the same outlet. Environmental news is crowded out by economic and war news during crises. — [Djerf-Pierre 2012](https://doi.org/10.1080/1461670x.2011.650924)
- Boydstun, Hardy & Walgrave 2014 (Political Communication) [EMPIRICAL, US and Belgium]: media storms change less explosively once begun but are more sharply skewed across issues than non-storm coverage. Online search responds strongly to storms. — [Boydstun et al. 2014](https://doi.org/10.1080/10584609.2013.875967)
- Eisensee & Stromberg 2007 (QJE) [EMPIRICAL, natural experiment]:
  - Data: about 5,000 disasters 1968-2002 (about 63,000 deaths per year, 125M people affected per year).
  - US relief depends on whether the disaster coincides with unrelated newsworthy events such as the Olympics, which crowd out coverage.
  - Secondary summary: a disaster during the Olympics needs 3x the deaths of an ordinary day for the same chance of relief, and during major events such as the O.J. Simpson trial 6x. The study used 700,000 stories from ABC, CBS, NBC and CNN.
  - Heterogeneous newsworthiness: for every person killed by a volcano, nearly 40,000 must die of food shortage for the same coverage probability.
  — [QJE abstract](https://doi.org/10.1162/qjec.122.2.693); [press summary](https://innovations-report.com/communications-media/report-54685); [OWID](https://ourworldindata.org/how-many-deaths-make-a-natural-disaster-newsworthy)
- Hirshleifer, Lim & Teoh 2009 (Journal of Finance 64(5)) [EMPIRICAL]:
  - Immediate reaction: the interdecile spread of announcement-period abnormal returns is 7.07% on low-news days vs 5.67% on high-news days (about 20% dilution).
  - 60-day post-announcement drift spread: 7.41% on high-news days vs 2.81% on low-news days.
  - Fama-French 3-factor alpha: 1.64%/month for the high-news drift portfolio vs 0.77% for low-news.
  - Industry-unrelated news distracts more than related news.
  — [HLT 2009 (MPRA)](https://mpra.ub.uni-muenchen.de/3110/); [JF listing](https://ideas.repec.org/a/bla/jfinan/v64y2009i5p2289-2325.html)
- Ribeiro, Gligoric, Peyrard, Lemmerich, Strohmaier & West 2021 (ICWSM) [EMPIRICAL, 12 Wikipedia editions in 2020]: total pageview volume rose after mobility restrictions. The rise correlated with time spent at home (Pearson r = 0.63). "This increase, however, was transient": in the long run there was a decrease or no significant increase in 11 of 12 languages, while topical composition shifted more permanently. — [Ribeiro et al. 2021](https://arxiv.org/abs/2005.08505)
- Lorenz-Spreen et al. 2019 (Nature Communications), model and data:
  - dL_i/dt = r_p*L_i(t)*[1 - (r_c/K)*integral_{-inf}^t exp(-alpha*(t-t'))*L_i(t') dt' - c*sum_{j != i} L_j(t)].
  - The terms are imitation-driven growth, self-saturation with exponential memory (rate alpha, "boringness"), carrying capacity K, and cross-topic competition c (Lotka-Volterra).
  - Weekly tweets containing top-50 hashtags grew over 2013-2016, so total volume is not conserved over years. Acceleration is explained by rising production and consumption rates exhausting limited attention faster.
  — [Lorenz-Spreen et al. 2019](https://cora.ucc.ie/bitstreams/f4ae8a47-a98a-4a3e-942b-34dbb4a46b9a/download)
- Weng, Flammini, Vespignani & Menczer 2012 (Scientific Reports) [MODEL plus Twitter validation]: agents can attend to only part of what they receive. Competition for limited attention plus network structure reproduces heavy-tailed meme popularity and persistence "without the need to assume different intrinsic values among ideas". — [Weng et al. 2012](https://doi.org/10.1038/srep00335)
- Gleeson, Ward, O'Sullivan & Lee 2014. Correction: this is Physical Review Letters 112:048701, not PNAS. [MODEL]:
  - Fixed screen capacity means each tweet births copies but overwrites the screens it lands on. Births and deaths "are, on average, exactly balanced, giving a critical branching process" when innovation mu = 0.
  - This "competition-induced criticality" gives popularity tails P_n ~ n^(-alpha) with alpha < 2 (about 1.5).
  — [Gleeson et al. 2014 PRL](https://arxiv.org/abs/1305.4328)
- The 2014 Gleeson PNAS paper is a different study: a generative model of Facebook app adoption. Only models that strongly emphasize recent popularity over cumulative popularity reproduce the observed temporal dynamics. This supports recency-weighted, short-memory excitation. — [Gleeson, Cellai, Onnela, Porter & Reed-Tsochas 2014](https://doi.org/10.1073/pnas.1313895111)
- Leskovec et al. 2009: each source reports on exactly one thread per period, with choice probability proportional to f(n_j)*delta(t - t_j). This is a strictly conserved, divisively normalized (share) model that reproduces news-cycle shapes. — [Leskovec et al. 2009](https://www.cs.cornell.edu/home/kleinber/kdd09-quotes.pdf)
- Finite-population depletion (HawkesN, Rizoiu et al. WWW 2018): lambda(t) = (1 - N_t/N)*[mu + sum phi(t - t_j)]. The equivalence with SIR epidemics makes the sink multiplicative, not subtractive. — [Rizoiu et al. 2018](https://arxiv.org/abs/1711.01679)
- Cross-excitation between related narratives (Garcia-Gavilanes et al., Science Advances 2017) [EMPIRICAL, Wikipedia aircraft-crash articles, about 85,000 article pairs]: a new event drives viewership to related past events according to similarity in time, geography, topic and hyperlinks. "The secondary flow of attention to past events... is larger than the primary attention flow to the current event." Per the institution's summary, combined past targets attract 142% more views than the source event. — [Garcia-Gavilanes et al. 2017](https://doi.org/10.1126/sciadv.1602368); [OII summary](https://www.oii.ox.ac.uk/wikipedia-articles-on-plane-crashes-show-what-we-remember/)
- Kleinberg's batched burst model is share-based: state q_i expects a fraction p_i = p0*s^i of relevant documents in each batch, with p0 = R/D (see Q6). — [Kleinberg 2002](https://www.cs.cornell.edu/home/kleinber/bhs.pdf)

### Inferences
- How conservation has been tested:
  - capacity constancy over decades (McCombs-Zhu: no growth)
  - cross-issue negative coefficients in exchange models (Zhu)
  - natural experiments with exogenous news pressure (Eisensee-Stromberg: Olympics; HLT: number of concurrent announcements)
  - responses of totals to shocks (Ribeiro: transient expansion, then reversion)
  - secular volume trends (Lorenz-Spreen: content volume grows even though attention is finite)

  Net reading: attention is partially zero-sum. There is a bounded, mean-reverting budget, displaced attention is partly delayed rather than destroyed (HLT drift), and there are sources (time at home, major shocks) and sinks.
- Subtractive vs divisive. Softplus_s behaves differently in its two regimes:
  - For eta >> s, lambda ~ eta. Subtracting kappa*T removes the same absolute attention from every hot narrative, so small narratives lose proportionally more and shares shift toward big narratives.
  - For eta << -s, lambda ~ s*exp(eta/s). The subtraction is multiplicative, scaling lambda by exp(-kappa*T/s).

  The empirical and model literature (Zhu's mass action, the Lotka-Volterra per-capita term, HawkesN's (1 - N_t/N), Leskovec's share normalization, HLT's proportional dilution of about 20%, Kleinberg's share-based bursts) points to proportional, share-preserving competition. That conflicts with the linear-regime subtraction in the proposal.
- A testable model in which conservation is a fitted parameter:
  - lambda[i][t] = f(eta_i[t]) * (B[t] / (B[t] + sum_j f(eta_j[t])))^omega, or equivalently, for a log link, eta_i -= omega*log(1 + sum_j f(eta_j)/B[t]).
  - Here B[t] is an exogenous capacity with an hour-of-week profile and source-count offset. omega = 0 means no competition and omega = 1 means full divisive normalization. Estimate omega.
  - Alternative two-stage form: total T[t] ~ quasi-Poisson or NB with its own baseline and global excitation, and shares pi[t] ~ Dirichlet-multinomial(softmax(eta)), giving lambda_i = T_hat[t]*pi_i[t].
- Artifact warning: if soft memberships per observation sum to 1, then sum_i y[i][t] equals the number of ingested observations in window t. That is set by GDELT/RSS ingestion volume (outlets, diurnal publishing cycles), not by attention dynamics. Part of the apparent "conservation" is then built into the measurement, and kappa*T_recent partly models the collection process. Model the total with an ingestion offset (log of articles or sources per window) before reading kappa as attention competition.
- Specific excitation plus generic competition matches the evidence: related narratives excite (Garcia-Gavilanes, positive A[i][j]) and unrelated news distracts (HLT). The proposal's split between a specific tensor A and a global kappa is structurally right, provided kappa (or omega) is applied proportionally.
- Criticality trap (Gleeson CIC): under exact conservation the effective branching ratio is pushed to 1, the conserved total acting as a neutral mode, much like conserved quantities produce marginal hydrodynamic modes in physics. If the model omits the budget, linear self-excitation will try to explain the conserved total, and the fitted rho(sum_m A) will drift toward 1. See Q6 for the matching baseline-misspecification bias.

### Gaps
- I found no study that explicitly fits a divisive vs subtractive competition term in a Hawkes intensity on news data and compares likelihoods. This is a direct empirical gap, and Yggdrasil could fill it with the omega model above.
- The IJOC article "Redirecting the Focus of the Agenda: Testing the Zero-Sum Dynamics of Media Attention in News and User-Generated Media" looks directly relevant but was not reviewed. — [IJOC](https://ijoc.org/index.php/ijoc/article/view/6753)
- The exact Eisensee-Stromberg "news pressure" definition was not verified from the primary text. The 3x/6x figures come from a secondary press summary.

---

## Q6. Separating background (exogenous) from triggered (endogenous) activity; burst and change detection; residual analysis

### Takeaway
Stochastic declustering (Zhuang-Ogata-Vere-Jones 2002) is the template for computing a probability that each event (or each unit of attention mass) is background or triggered. Its validity depends on the baseline being flexible enough. A baseline that is too rigid is the main documented cause of spurious near-critical branching ratios. Burst and change detection should run on Hawkes residuals (rescaled times, PIT, or Pearson residuals), not on raw counts. Run on residuals, it flags exogenous shocks; run on raw counts, it also flags endogenous cascades.

### Cited Findings
- Zhuang, Ogata & Vere-Jones 2002 (JASA), stochastic declustering [HEURISTIC algorithm on top of MLE]:
  - Background probability per event: phi_i = mu(x_i)/lambda(t_i, x_i). Triggering probabilities: rho_ij = g(t_i - t_j, ...)/lambda(t_i, x_i).
  - The background is estimated nonparametrically. Use m1(s) = lim (1/T) integral lambda(s,t) dt, and set mu_hat(s) = (1/T) * sum_i (1 - Pr(u_i != 0)) * k(s - s_i), a weighted kernel density using only the probable background events.
  - Iterate between the background and the triggering parameters. Thin the events randomly by these probabilities to get declustered catalogs. Repeating the thinning exposes declustering uncertainty.
  — [Zhuang, Ogata & Vere-Jones 2002](https://doi.org/10.1198/016214502760046925); [Reinhart 2018 review](https://arxiv.org/abs/1708.02647)
- Filimonov & Sornette 2015 (Quantitative Finance) [EMPIRICAL / simulation]: biases in the branching ratio n include:
  - strong upward bias with power-law kernels in the presence of outliers
  - strong sensitivity to the power-law kernel's regularization (cutoff)
  - edge effects for long-memory kernels
  - fitting Hawkes to mixtures of Poisson processes with regime changes "leads to completely spurious apparent critical values for the branching ratio (n ~ 1) while the true value is actually n = 0"
  - intraday seasonality (a non-stationary exogenous component) "is very difficult to remove and is the source of large biases"
  — [Filimonov & Sornette 2015](https://arxiv.org/abs/1308.6756)
- Wheatley, Wehrli & Sornette 2019 (Quantitative Finance 19(7)): EM plus BIC to choose how flexible the deterministic background intensity should be. With properly flexible baselines, they "strongly reject" criticality at univariate and bivariate microstructure levels. — [Wheatley et al. 2019](https://ideas.repec.org/a/taf/quantf/v19y2019i7p1165-1178.html)
- Omi, Hirata & Aihara 2017 (Phys. Rev. E): log-background modeled as a linear model with many variable-width basis functions, fit by a Bayesian method. It captures slow intraday seasonality and rapid jumps after macroeconomic news announcements. Fits better than constant or slowly varying baselines. Estimated branching ratio 0.41. "It is critically important to appropriately model the time-dependent background rate for the branching ratio estimation." — [Omi et al. 2017](https://doi.org/10.1103/physreve.96.012303)
- Contrast: Hardiman, Bercot & Bouchaud 2013, with power-law kernels, report near-critical ||Phi|| about 1, stable over a decade. The kernel shape and the baseline flexibility trade off against each other in identifying n. — [Bacry, Mastromatteo & Muzy 2015](https://arxiv.org/abs/1502.04592)
- Other time-varying baselines: a log-Gaussian Cox process background (Linderman & Adams 2014), a test for constant background (Cai, Zhang & Guan 2022), and graph recovery with time-varying baselines (Mossel & Sridhar 2026). — [Linderman & Adams 2014](https://arxiv.org/abs/1402.0914); [Cai et al.](https://arxiv.org/abs/2004.03569); [Mossel & Sridhar 2026](https://arxiv.org/abs/2601.11717)
- Kleinberg 2002 (KDD; DMKD 2003), burst automaton [HEURISTIC, Viterbi optimal]:
  - Two-state model: gaps ~ Exp(alpha0) in the base state and Exp(alpha1) with alpha1 > alpha0 in the burst state.
  - Infinite-state model A*_{s,gamma}: state q_i has rate alpha_i = (n/T)*s^i. Moving up costs gamma*ln(n) per state, moving down costs 0. The optimal state sequence minimizes emission plus transition cost.
  - Batched variant B*_{s,gamma}, built for document batches: batch t has r_t relevant out of d_t documents. State q_i has binomial probability p_i = p0*s^i, with p0 = R/D. Cost sigma(i, r_t, d_t) = -ln[C(d_t, r_t) * p_i^r_t * (1 - p_i)^(d_t - r_t)].
  — [Kleinberg 2002](https://www.cs.cornell.edu/home/kleinber/bhs.pdf)
- Adams & MacKay 2007, BOCPD [PROVEN recursion, exact under model assumptions]: tracks the posterior over run length r_t (time since the last changepoint) with a changepoint prior P(r_t | r_{t-1}) = H(r_{t-1}+1) if r_t = 0, and 1 - H(r_{t-1}+1) if r_t = r_{t-1}+1, where H is the hazard function. Run-length probabilities are updated recursively using the predictive probability of each new datum under each run length. — [Adams & MacKay 2007](https://arxiv.org/abs/0710.3742)
- Time-rescaling theorem [PROVEN]: if lambda is the true conditional intensity, the rescaled inter-event times tau_k = integral_{t_{k-1}}^{t_k} lambda(t) dt are i.i.d. Exp(1). The goodness-of-fit test is a KS test on 1 - exp(-tau_k). Ogata 1988 introduced residual analysis for point processes on transformed time. — [Brown et al. 2002](https://doi.org/10.1162/08997660252741149); [Ogata 1988](https://doi.org/10.1080/01621459.1988.10478560)
- Discrete-time correction [PROVEN]: with finite bins, rescaled intervals are not exactly exponential, so a correct model can fail the KS test. Haslinger, Pipa & Brown (Neural Computation 2010) offer two fixes: simulate the reference distribution from the fitted model, or use an analytically corrected discrete-time rescaling theorem. — [Haslinger et al. 2010 (PMC link from search results; PMC page not opened)](https://pmc.ncbi.nlm.nih.gov/articles/PMC2932849)
- Count-data calibration: the nonrandomized probability integral transform (PIT) and scoring rules for count predictive distributions. — [Czado, Gneiting & Held 2009](https://doi.org/10.1111/j.1541-0420.2009.01191.x)
- Hawkes-aware change detection:
  - Online recursive CUSUM for Hawkes networks with proven properties. It outperforms count-based Shewhart, GLR and score statistics. — [Wang, Xie, Xie, Cuozzo & Mak, Technometrics 2022/2023](https://doi.org/10.1080/00401706.2022.2054862)
  - Change detection in dynamic network events using Hawkes models. — [Li, Xie, Farajtabar, Verma & Song 2017](https://doi.org/10.1109/tsipn.2017.2696264)
- Reinhart 2018 review: residual maps and diagnostics for self-exciting processes. A constant-background misfit shows up as spatially structured residuals. — [Reinhart 2018](https://arxiv.org/abs/1708.02647)

### Inferences
- Discrete-time declustering for Yggdrasil. In the linear regime, the expected attention mass of narrative i in window t splits additively into baseline b[i][t] and cross terms A[i][j][m]*z[j][m][t]. Allocate y[i][t] across these terms in proportion to their share of eta (the multinomial split Linderman & Adams 2015 use with auxiliary variables). Outside the linear regime, use the softplus-scaled shares or path attribution (Q2). Repeating stochastic allocations gives attribution uncertainty, as in ZOV.
- The baseline must be flexible:
  - hour-of-week
  - scheduled-event dummies (Omi-style rapid components)
  - a slowly varying level (splines or a random walk)
  - an ingestion-volume offset

  Choose its flexibility by BIC or held-out likelihood (Wheatley et al.). Report rho(sum_m A) only with that caveat, since a rigid baseline inflates it toward 1 (Filimonov-Sornette) and the conservation constraint pushes the same way (Gleeson, Q5).
- Order of operations for a forensics engine:
  1. Fit the Hawkes model.
  2. Compute per-window residuals: nonrandomized PIT under the NB or quasi-Poisson working distribution, or Pearson residuals.
  3. Run BOCPD or Hawkes-CUSUM on the residuals to flag exogenous shocks or baseline shifts.
  4. Run Kleinberg's batched model on shares (r_t = y[i][t], d_t = sum_j y[j][t]) as a model-free cross-check.

  A burst that the Hawkes model predicts (endogenous cascade) should not raise a change-point alarm. That is the purpose of residualizing.
- KS tests on 15-min binned data should use Haslinger's simulation-based reference distribution or the PIT, not the plain exponential reference.

### Gaps
- I found no published combination of BOCPD with nonlinear discrete-time Hawkes residuals. Combining them is a design choice (heuristic).
- Declustering with fractional (soft-membership) mass, as opposed to integer events, is not covered in the literature reviewed.

---

## Q7. Bayesian treatment and cold start: priors, inference, initializing new nodes

### Takeaway
The standard Bayesian setup combines: Gamma priors on weights and baselines; spike-and-slab adjacency driven by a network prior (SBM or latent space); Dirichlet priors on mixtures over basis kernels; and stability-aware hyperparameters. Inference uses Gibbs with parent variables, SVI, or variational Bayes, with posterior concentration theory now available (2020-2025). Cold start fits naturally into hierarchical, block-structured, or low-rank or feature-based priors. The Dirichlet-Hawkes process gives a generative rule for when a new narrative appears.

### Cited Findings
- Priors and conjugacy:
  - Linderman & Adams 2014: W ~ Gamma(alpha_W, beta_W), A ~ Bernoulli(Theta(u_k, u_k')) from Aldous-Hoover graph priors (Erdos-Renyi, SBM, latent distance), lambda0 ~ Gamma, logistic-normal impulse with normal-gamma prior. Gibbs uses parent auxiliary variables, and collapsed Gibbs over A and the parents.
  - Linderman & Adams 2015: a Dirichlet(gamma) prior over basis weights g, conjugate given discrete parent counts: g | z ~ Dirichlet(gamma_b + sum z), plus a spike-and-slab Gamma on W, and SVI for long sequences.
  — [Linderman & Adams 2014](https://arxiv.org/abs/1402.0914); [Linderman & Adams 2015](https://arxiv.org/abs/1507.03228)
- Rasmussen (2011/2013): direct MCMC (Metropolis within Gibbs) and a cluster-structure (latent branching) sampler for Hawkes. Reinhart notes direct MCMC is O(n^2) per likelihood evaluation and mixes poorly, which is why latent-variable samplers are preferred. — [Rasmussen](https://doi.org/10.1007/s11009-011-9272-5); [Reinhart 2018](https://arxiv.org/abs/1708.02647)
- Posterior concentration [PROVEN]:
  - Donnet, Rivoirard & Rousseau 2020 (Annals of Statistics): nonparametric multivariate linear Hawkes, L1 rates for intensities and interaction functions, with piecewise-constant or Beta-mixture priors.
  - Sulem, Rivoirard & Rousseau 2024: nonlinear links with excitation and inhibition, including graph-consistency guarantees.
  - Sulem et al. VB (JMLR 26, 2025): scalable, adaptive variational Bayes, with a sparsity-inducing procedure for sigmoid Hawkes.
  - Rousseau, Rivoirard & Sulem 2025 (arXiv): high-dimensional sparse linear Hawkes.
  — [Donnet et al. 2020](https://doi.org/10.1214/19-aos1903); [Sulem et al.](https://arxiv.org/abs/2103.17164); [Sulem et al. VB](https://arxiv.org/abs/2212.00293); [JMLR page](https://www.jmlr.org/beta/papers/v26/23-1053.html); [Rousseau et al. 2025](https://arxiv.org/abs/2510.24182)
- Pseudo-marginal Bayesian estimation from binned data, using SMC for an unbiased likelihood plus Metropolis-Hastings. — [Chen, Kwan & Stindl 2024](https://arxiv.org/abs/2401.11075)
- Stability-aware priors: tune network sparsity rho so the largest eigenvalue of A .* W lies below 1 with high probability (random-matrix argument, Q1). Stability-constrained MLE (Gerhard et al., Q2). — [Linderman & Adams 2014](https://arxiv.org/abs/1402.0914); [Gerhard et al. 2017](https://doi.org/10.1371/journal.pcbi.1005390)
- Low-rank and feature-based structure for new nodes:
  - A with nuclear-norm (community) structure (Zhou et al. 2013), and an infectivity matrix parameterized by node features (AAAI 2014).
  - Under SBM or latent-space priors, a node's edge probabilities and weight scales come from its block or embedding (Linderman & Adams).
  — [Zhou et al. 2013](http://proceedings.mlr.press/v31/zhou13a.html); [AAAI 2014](https://doi.org/10.1609/aaai.v28i1.8733); [Linderman & Adams 2014](https://arxiv.org/abs/1402.0914)
- New-cluster birth: in the Dirichlet-Hawkes process, a new document joins an existing cluster with probability proportional to that cluster's current Hawkes intensity, or opens a new cluster with probability proportional to a base rate. Designed for news-document streams. — [Du et al. 2015](https://doi.org/10.1145/2783258.2783411)
- Online updating to track drift: dynamic mirror descent with tracking-regret guarantees (Hall & Willett) and nonparametric online kernels with O(log T) regret (Yang et al.). — [Hall & Willett](https://arxiv.org/abs/1409.0031); [Yang et al.](https://arxiv.org/abs/1801.08273)

### Inferences
- The proposal's Gaussian priors with MAP equal ridge regression: no sparsity, and no positivity unless constrained. Literature-backed alternatives, in order of increasing effort:
  1. A Laplace or horseshoe prior on signed A (keeps inhibition, adds sparsity), with weights scaled per timescale.
  2. The factorization A[i][j][m] = W[j->i]*g_m with g ~ Dirichlet over the 4 timescales, plus a signed W via spike-and-slab (Gaussian slab).
  3. A hierarchical SBM or latent-space prior on W driven by narrative embeddings.

  A Laplace approximation at the MAP is cheap and gives approximate posterior uncertainty. VB (Sulem et al.) is the scalable proven option.
- Cold start for a new narrative i0, borrowing strength from similar narratives:
  - prior mean of b[i0] = parent or most-similar narratives' baseline, scaled by membership mass
  - prior on A[i0][.][m] and A[.][i0][m] = embedding-similarity-weighted average of existing rows and columns (a feature-parameterized A, as in AAAI 2014), with variance shrinking as evidence accumulates
  - g_m for i0 drawn from the population-level Dirichlet

  A narrative that splits or merges in the graph should inherit traces z by membership-weighted sums, so that the total attention mass is conserved at the moment of re-clustering.
- Enforce rho(P+) < 1 (Q2) as a soft penalty or a projection at each MAP refit. Gerhard et al. show unconstrained fits often yield unstable generative models, which matters if Yggdrasil simulates counterfactual attention paths.

### Gaps
- I found no published prior-elicitation study for news-attention Hawkes models. The hyperparameter choices above are heuristic.
- I found no theory for cold start in Hawkes networks (adding nodes online) beyond the generative Dirichlet-Hawkes mechanism and feature-parameterized infectivity.

---

## Q8. Verdict on each component of the Yggdrasil proposal (confirm / refine / contradict)

### Takeaway
The structure is confirmed:
- a discrete-time multivariate Hawkes process
- a normalized multi-timescale basis
- a softplus link
- a quasi-Poisson likelihood
- a flexible baseline with scheduled events

Four pieces need refinement:
- Make the competition term proportional (divisive or log-space), not subtractive in linear space.
- Replace Gaussian priors with sparsity or low-rank and stability-aware priors.
- Correct for the 15-min bin vs 1h kernel mismatch and add a slower component.
- Separate ingestion-driven total volume from attention competition.

The main contradictions come from:
- power-law and stretched-exponential decay evidence (handled only approximately by 4 exponentials)
- the literature's near-universal use of multiplicative or share-based competition
- documented spurious criticality when baselines or conservation constraints are misspecified

### Cited Findings
- CONFIRM, normalized basis plus weight structure: equivalent to Linderman & Adams 2015 (W times a Dirichlet mixture of normalized basis functions) and Bacry et al. 2020 (a dictionary of unit-mass exponentials with fixed decays). — [Linderman & Adams 2015](https://arxiv.org/abs/1507.03228); [Bacry et al. 2020](https://arxiv.org/abs/1501.00725)
- CONFIRM, the s*softplus(x/s) link: used verbatim by Mei & Eisner 2017. Non-decreasing and 1-Lipschitz, so the Bremaud-Massoulie / Sulem (C1) stability condition applies with L = 1, and only positive parts count. — [Mei & Eisner 2017](https://arxiv.org/abs/1612.09328); [Sulem et al.](https://arxiv.org/abs/2103.17164)
- CONTRADICT the alternative exp link: fitted exp-link GLMs diverged in 35/99 cases. — [Gerhard et al. 2017](https://doi.org/10.1371/journal.pcbi.1005390)
- CONFIRM, quasi-Poisson: Poisson QMLE is consistent for the conditional mean under misspecification (Ahmad & Francq), including network count autoregressions (Armillotta & Fokianos). — [Ahmad & Francq](https://doi.org/10.1111/jtsa.12167); [Armillotta & Fokianos](https://arxiv.org/abs/2104.06296)
- REFINE, the variance function: NB quasi-likelihood exists (Christou & Fokianos). Heavy-tailed popularity (Gleeson alpha < 2; Crane-Sornette herding) suggests the variance grows faster than linearly in bursts. — [Christou & Fokianos](https://doi.org/10.1002/jtsa.12050); [Gleeson et al. 2014](https://arxiv.org/abs/1305.4328); [Crane & Sornette 2008](https://arxiv.org/abs/0803.2189)
- REFINE / PARTIAL CONTRADICTION, the kernel family: decay is stretched-exponential (Wu-Huberman) or power-law (Dezso, Crane-Sornette theta about 0.4, SEISMIC theta = 0.242, finance kernels) or biexponential at long horizons (Candia). Four log-spaced exponentials approximate this only over 1h-1w. Finance practice uses up to 15 exponentials for power laws. — [Wu & Huberman 2007](https://arxiv.org/abs/0704.1158); [Dezso et al. 2006](https://doi.org/10.1103/physreve.73.066132); [Zhao et al. 2015](https://arxiv.org/abs/1506.02594); [Bacry, Mastromatteo & Muzy 2015](https://arxiv.org/abs/1502.04592); [Candia et al. 2019](https://doi.org/10.1038/s41562-018-0474-5)
- REFINE, the bin width: within-bin triggering is ignored by construction (Kirchner approximation (9); Linderman-Adams). Naive binned estimators can be badly biased (Shlomovich et al.). Large bins relative to the kernel break INAR-style estimation (Cheysson-Lang). — [Kirchner 2017](https://arxiv.org/abs/1509.02017); [Shlomovich et al. 2022](https://doi.org/10.1080/10618600.2022.2050247); [Cheysson & Lang](https://arxiv.org/abs/2003.04314)
- CONTRADICT, the subtractive competition -kappa*total in linear space: competition in the literature is per-capita or share-based. Examples: Zhu's mass-action exchange; the Lotka-Volterra term r_p*L_i*c*sum L_j; HawkesN's (1 - N_t/N); Leskovec's one-thread-per-source normalization; Kleinberg's share-based bursts; about 20% proportional dilution in HLT. — [Zhu 1992](https://fbaum.unc.edu/teaching/PLSC541_Fall06/Zhu%20JQ%201992.pdf); [Lorenz-Spreen et al. 2019](https://doi.org/10.1038/s41467-019-09311-w); [Rizoiu et al. 2018](https://arxiv.org/abs/1711.01679); [Leskovec et al. 2009](https://www.cs.cornell.edu/home/kleinber/kdd09-quotes.pdf); [HLT 2009](https://mpra.ub.uni-muenchen.de/3110/)
- CONFIRM WITH REFINEMENT, the "semi-conservative" hypothesis:
  - Carrying capacity flat over 40 years (McCombs & Zhu).
  - Crowding-out natural experiments (Eisensee & Stromberg; HLT).
  - Transient expansion of the total, then reversion (Ribeiro et al.).
  - Secular content growth (Lorenz-Spreen).
  - Positive cross-excitation among related events larger than the primary event (Garcia-Gavilanes).
  — [McCombs & Zhu 1995](https://doi.org/10.1086/269491); [Eisensee & Stromberg 2007](https://doi.org/10.1162/qjec.122.2.693); [Ribeiro et al. 2021](https://arxiv.org/abs/2005.08505); [Garcia-Gavilanes et al. 2017](https://doi.org/10.1126/sciadv.1602368)
- REFINE, baseline flexibility: rigid baselines produce spurious n about 1 (Filimonov-Sornette). Flexible baselines with rapid news-announcement components give n of about 0.41 (Omi et al.) or reject criticality (Wheatley et al.). Scheduled-event covariates have direct precedent (HIP's s(t); Omi's macro-announcement jumps). — [Filimonov & Sornette 2015](https://arxiv.org/abs/1308.6756); [Omi et al. 2017](https://doi.org/10.1103/physreve.96.012303); [Wheatley et al. 2019](https://ideas.repec.org/a/taf/quantf/v19y2019i7p1165-1178.html); [Rizoiu et al. 2017](https://arxiv.org/abs/1602.06033)
- REFINE, circadian effects: the hour-of-week cycle should probably also modulate the excitation gain, as TiDeH's p(t) modulates infectiousness. — [Kobayashi & Lambiotte 2016](https://arxiv.org/abs/1603.09449)
- REFINE, priors: replace Gaussian priors with spike-and-slab or Gamma (Linderman-Adams), weighted l1 with oracle guarantees (HRR 2015), or l1 plus nuclear norm (Zhou 2013; Bacry 2020). Add stability-aware hyperparameters. — [Linderman & Adams 2014](https://arxiv.org/abs/1402.0914); [HRR 2015](https://arxiv.org/abs/1208.0570); [Zhou et al. 2013](http://proceedings.mlr.press/v31/zhou13a.html)

### Inferences
Proposed revised specification, written out:

1. Total-volume layer (absorbs ingestion and the conservation artifact):
   - V[t] = observation count in window t
   - log B[t] = log V_bar(how[t]) + level[t]
   - level[t] is a slow random walk or spline.
2. Narrative drive:
   - eta[i][t] = b0[i] + c_how[i][how[t]] + sum_e d[i][e]*D_e[t] + exp(g_how[how[t]]) * sum_j sum_m A[i][j][m]*z[j][m][t]
   - Optional 5th trace with tau about 30 days.
   - Optional 2-3 h trace if it is supported by likelihood.
3. Link with proportional competition:
   - lambda_raw[i][t] = s*softplus(eta[i][t]/s)
   - lambda[i][t] = lambda_raw[i][t] * (B[t]/(B[t] + sum_j lambda_raw[j][t]))^omega
   - omega lies in [0, 1] and is estimated, which turns "semi-conservation" into a measured quantity.
   - Alternative: put -omega*log(1 + sum_j lambda_raw[j][t]/B[t]) inside eta.
4. Likelihood:
   - quasi-Poisson score for point estimates
   - variance Var = phi*lambda*(1 + lambda/r) checked against Pearson residuals, with NB2 used for intervals and PIT
5. Priors:
   - A[i][j][m] = W[j->i]*g_m^{(j,i)}, with g ~ Dirichlet over timescales
   - W signed spike-and-slab (Laplace slab acceptable), with hierarchical scale from narrative-embedding similarity
   - b and c_how hierarchical across narratives
6. Constraints:
   - rho(P+) < 1, with P+[i][j] = sum_m max(A[i][j][m], 0), as a penalty or projection
   - report the fitted spectral radius with the baseline-flexibility caveat
7. Diagnostics:
   - discrete-time rescaling (Haslinger) or PIT
   - BOCPD or Hawkes-CUSUM on residuals for exogenous shocks
   - Kleinberg batched binomial on shares as a model-free cross-check

All of this is inference assembled from the cited components. No single paper validates the whole specification.

### Gaps
- None of the revised specification has been benchmarked on GDELT/RSS narrative data. A held-out-likelihood bake-off is needed: subtractive kappa vs divisive omega vs a log-space competition term, 4 vs 5-6 timescales vs a parametric power law, and quasi-Poisson vs NB2.
- No theory covers stationarity of the divisive-normalized softplus count model. Bounded links are always stationary (Sulem C2), and divisive normalization bounds the total by about B[t], which suggests stationarity follows. That is a conjecture, not a cited result.
