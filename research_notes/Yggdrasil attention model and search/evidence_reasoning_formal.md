# Formal and practical frameworks for judging competing explanations against conflicting evidence, with machine-checked (Lean 4) verdicts, for Yggdrasil

Scope note: these notes are for Yggdrasil, a market-event forensics engine. Yggdrasil produces several rival explanations for an abnormal market event, collects evidence from news sources that often contradict each other, and must label each explanation SUPPORTED, CONTRADICTED, CONSISTENT-BUT-UNPROVEN or UNRESOLVED, with provenance attached. The current date is 2026-10-03. Every item carries its year. Notation is plain text: |= is semantic entailment, |- is derivability, ¬ is negation, Σ2P / Π2P / Θ2P / DP are polynomial-hierarchy classes, and "-c" means complete.

Source-quality legend:
- "verified" means the claim was checked against the fetched page or paper during this research pass (2026-10-03).
- Claims cited only by DOI are standard results from canonical primary papers. They are recalled, not re-fetched in this pass. A single cell or detail is flagged where I am less certain.

---

## 1. Intelligence analysis: Heuer's ACH, diagnosticity, disconfirmation, empirical record

### Takeaway
ACH (Heuer 1999) is the right workflow shape for Yggdrasil: an evidence-by-hypothesis matrix, a focus on diagnosticity, and ranking hypotheses by how much evidence is inconsistent with them. It is not a semantics, though. The controlled studies that exist (2018 and 2019) found that ACH did not improve accuracy and may increase inconsistency. So keep its structure (disconfirmation, diagnosticity, sensitivity analysis) and replace its scoring step with a formal, deterministic semantics.

### Cited Findings
- Heuer's ACH (chapter 8 of "Psychology of Intelligence Analysis", CIA Center for the Study of Intelligence, 1999) has eight steps: (1) identify all plausible hypotheses; (2) list the significant evidence and arguments, including absence of evidence and assumptions; (3) build a matrix with hypotheses across the top and evidence down the side, then analyze each item's diagnosticity; (4) refine the matrix and delete evidence with no diagnostic value; (5) draw tentative conclusions by trying to disprove hypotheses rather than prove them; (6) run a sensitivity analysis on the few critical items; (7) report the relative likelihood of all hypotheses, not just the leading one; (8) identify milestones for future observation. In this scheme a hypothesis is ranked by the evidence inconsistent with it, and evidence consistent with every hypothesis is non-diagnostic — [Heuer 1999, CIA CSI](https://www.cia.gov/resources/csi/books-monographs/psychology-of-intelligence-analysis-2/)
- Dhami, Belton & Mandel (2019, Applied Cognitive Psychology 33(6)): 50 intelligence analysts were randomly assigned to use ACH or not on a hypothesis-testing task with probabilistic ground truth. Analysts trained in ACH did not follow all its steps, the evidence that ACH reduces confirmation bias was mixed, and "ACH may increase judgement inconsistency and error". The authors recommend studying when ACH helps and exploring alternatives (verified) — [Strathprints record](https://strathprints.strath.ac.uk/69049/)
- Mandel, Karvetski & Dhami (2018, Judgment and Decision Making 13(6):607-621): ACH-trained analysts judged the usefulness of information better than controls, but the control group was slightly more accurate and more coherent in its probability judgments. Statistical post-processing helped far more: coherentizing the judgments and then aggregating them cut mean absolute error by 61% (verified) — [Cambridge Core](https://www.cambridge.org/core/journals/judgment-and-decision-making/article/boosting-intelligence-analysts-judgment-accuracy-what-works-what-fails/1530E9DAE8F42B2E8FC2B5FE374DB50F)

### Inferences
- Heuer's "diagnosticity" is qualitatively the likelihood ratio P(e | H1) / P(e | H2): an item is diagnostic only if it discriminates between hypotheses (see Section 4). In a logical semantics the analogue is: e is diagnostic for H1 versus H2 iff removing e changes the verdict of H1 or H2. With hundreds of evidence items this is cheap to compute (n+1 solver runs), and it gives a mechanized ACH step 6 (sensitivity analysis) plus a provenance artifact (the "critical evidence" list).
- ACH's known weaknesses map onto concrete design requirements:
  - ACH has no explicit model of source credibility or source dependence, so syndicated or copied news is double-counted. Yggdrasil needs a source-dependence model (Section 6).
  - The cell ratings (C / I / N) are subjective and unstable across analysts, which is the inconsistency Dhami et al. observed. Yggdrasil needs ratings computed by a fixed semantics from encoded rules.
  - The matrix assumes the hypothesis set is exhaustive. Yggdrasil should carry an explicit "other / unknown cause" hypothesis.
  - Summing inconsistencies across items treats evidence as independent and equally weighted. Yggdrasil needs structured attack and support relations instead.
- ACH's emphasis on disconfirmation is a principled reason to make the verdict mapping asymmetric: a hypothesis that is refuted under some coherent reading of the evidence should be flagged rather than called "consistent". This is used in Section 8.

### Gaps
- The magnitudes in Dhami et al. 2019 (effect sizes, the exact error metrics) were not retrieved; only the abstract-level findings are verified.
- Whitesmith's ACH experiments (Edinburgh UP, 2020) are often cited as finding no mitigation of serial-position or confirmation bias. They were not verified in this pass.
- The weighting features of later ACH software (credibility and relevance weights in the PARC ACH tool, Heuer & Pherson's "Structured Analytic Techniques") were not verified.

---

## 2. Argumentation theory: Dung AFs, Caminada labellings, bipolar, probabilistic, ASPIC+/ABA, complexity, solvers, and the mapping to verdicts

### Takeaway
Abstract argumentation gives exactly what Yggdrasil needs: a finite, decidable, solver-backed semantics in which contradictory sources yield in / out / undec statuses instead of logical explosion.
- Grounded semantics is polynomial, unique and deterministic.
- Stable semantics sits at NP / coNP, which is the "sweet spot" where every answer has a certificate a SAT solver can produce: a witness for positive answers, an LRAT refutation for negative ones.
- Preferred and semi-stable skeptical reasoning sit at Π2P and are harder to certify.

For structured evidence, flat ABA (equivalently, normal logic programs under stable-model semantics) is computationally preferable to full ASPIC+. ASP-based ABA solvers won ICCMA 2025's ABA track.

### Cited Findings

Dung abstract argumentation frameworks (1995):
- An AF is F = (A, R) with R ⊆ A × A, where (a, b) ∈ R means "a attacks b". For S ⊆ A:
  - S is conflict-free iff there are no a, b ∈ S with (a, b) ∈ R.
  - S defends a iff for every b with (b, a) ∈ R there is a c ∈ S with (c, b) ∈ R.
  - The characteristic function is F(S) = {a | S defends a}.
  - Admissible: conflict-free and S ⊆ F(S).
  - Complete: conflict-free and S = F(S).
  - Grounded: the least fixpoint of F, equivalently the ⊆-least complete extension. It is unique.
  - Preferred: ⊆-maximal admissible.
  - Stable: conflict-free and attacks every a ∉ S.
- Every stable extension is preferred, every preferred extension is complete, and the grounded extension is contained in every complete extension. Stable extensions may not exist. If F is well-founded (for finite AFs: acyclic), there is exactly one complete extension, and it is simultaneously grounded, preferred and stable — [Dung 1995, AIJ 77](https://doi.org/10.1016/0004-3702(94)00041-X); overview in [Baroni, Caminada & Giacomin 2011, KER](https://doi.org/10.1017/S0269888911000166)
- Further semantics:
  - Semi-stable: complete extensions with ⊆-maximal range S ∪ S+, where S+ is the set of arguments S attacks.
  - Ideal: the ⊆-maximal admissible set contained in every preferred extension. It is unique.
  - Source — [Baroni, Caminada & Giacomin 2011](https://doi.org/10.1017/S0269888911000166)

Caminada labellings (2006):
- A labelling is L: A -> {in, out, undec}. L is complete iff for every a:
  - a is in iff every attacker of a is out;
  - a is out iff some attacker of a is in;
  - a is undec otherwise.
- Special cases:
  - Grounded: the complete labelling with minimal in (equivalently maximal undec).
  - Preferred: maximal in.
  - Stable: complete with no undec.
  - Semi-stable: complete with minimal undec.
- in(L) is a bijection between complete labellings and complete extensions, and it preserves each of these semantics — [Caminada 2006, JELIA](https://doi.org/10.1007/11853886_11); [Caminada & Gabbay 2009, Studia Logica](https://doi.org/10.1007/s11225-009-9218-x)

Rationality postulates:
- For structured argumentation, Caminada & Amgoud (2007) require closure under strict rules, direct consistency and indirect consistency of each extension's conclusions. Without these, a single extension can contain both phi and ¬phi — [Caminada & Amgoud 2007, AIJ 171](https://doi.org/10.1016/j.artint.2007.02.003)

ASPIC+ (Modgil & Prakken):
- An argumentation theory has:
  - a language L with a contrariness function;
  - strict rules Rs and defeasible rules Rd, plus a naming function n for defeasible rules;
  - a knowledge base K = Kn (axioms) ∪ Kp (ordinary premises);
  - an argument ordering.
- Arguments are inference trees. There are three attack types:
  - undermining: attacks an ordinary premise;
  - rebutting: attacks the conclusion of a defeasible rule;
  - undercutting: attacks the applicability of a defeasible rule via n(r).
- Rebuttals and underminings succeed as defeats only if the attacked argument is not strictly preferred. Undercuts always succeed. Orderings are "last-link" or "weakest-link".
- ASPIC+ satisfies the rationality postulates under well-definedness conditions: closure under transposition or contraposition, axiom consistency, well-formedness, and a "reasonable" ordering — [Modgil & Prakken 2013, AIJ 195](https://doi.org/10.1016/j.artint.2012.10.008); tutorial [Modgil & Prakken 2014, Argument & Computation](https://doi.org/10.1080/19462166.2013.869766)

Assumption-based argumentation (ABA):
- A framework is (L, R, Asm, contrary). It is flat if no assumption is the head of a rule.
- ABA generalizes logic-programming semantics: the stable extensions of the ABA encoding of a normal logic program coincide with its stable models — [Bondarenko, Dung, Kowalski & Toni 1997, AIJ 93](https://doi.org/10.1016/S0004-3702(97)00015-5)
- Flat ABA under stable semantics: credulous reasoning is NP-c and skeptical reasoning is coNP-c — [Dimopoulos, Nebel & Toni 2002, AIJ 141](https://doi.org/10.1016/S0004-3702(02)00245-X) (class assignment recalled)
- Declarative (SAT/ASP) algorithms for ABA that reason directly on assumption sets avoid enumerating exponentially many arguments — [Lehtonen, Wallner & Järvisalo 2021, JAIR](https://doi.org/10.1613/jair.1.12479)

Three-valued correspondence:
- Complete extensions coincide with 3-valued (partial) stable models of logic programs; grounded corresponds to the well-founded model, and preferred to regular models — [Wu, Caminada & Gabbay 2009, Studia Logica](https://doi.org/10.1007/s11225-009-9210-5)
- Well-founded semantics is computable in polynomial time — [Van Gelder, Ross & Schlipf 1991, JACM](https://doi.org/10.1145/116825.116838)

Bipolar argumentation (Cayrol & Lagasquie-Schiex 2005):
- A BAF is (A, R_att, R_sup). Two derived attacks are added:
  - supported attack: a supports, through a chain, some b, and b attacks c;
  - indirect (secondary) attack: a attacks b, and b supports, through a chain, c.
- Admissibility comes in d-, s- (safe) and c- (support-closed) variants — [Cayrol & Lagasquie-Schiex 2005, ECSQARU](https://doi.org/10.1007/11518655_33)
- Later work distinguishes deductive support, necessary support and evidential support. It shows these readings are dual and can be flattened into Dung AFs with derived (complex) attacks — [Cayrol & Lagasquie-Schiex 2013, IJAR](https://doi.org/10.1016/j.ijar.2013.03.001)

Probabilistic argumentation:
- Constellations approach: a probability distribution over which arguments and attacks are present. Introduced by Li, Oren & Norman (2011) with independence assumptions — [Li, Oren & Norman 2011, TAFA](https://doi.org/10.1007/978-3-642-29184-5_1)
- Hunter develops probabilistic logical arguments and contrasts the constellations approach with the epistemic approach (degrees of belief in arguments) — [Hunter 2013, IJAR](https://doi.org/10.1016/j.ijar.2012.08.003); [Hunter & Thimm 2017, JAIR](https://doi.org/10.1613/jair.5393)
- Complexity: computing the probability that a set of arguments is a σ-extension (σ among admissible, stable, complete, grounded, preferred, ideal) shows a dichotomy. It is either PTIME or FP#P-complete, depending on σ (verified) — [Fazzinga, Flesca & Parisi, IJCAI 2013](https://www.ijcai.org/Abstract/13/138)
- The extension to probabilistic bipolar AFs is also analyzed — [Fazzinga, Flesca & Furfaro, IJCAI 2018](https://www.ijcai.org/proceedings/2018/249)

Complexity of the standard semantics:
- The table below is the standard table from Dvořák & Dunne (2017/2018), "Computational problems in formal argumentation and their complexity" (Handbook of Formal Argumentation). Cells are recalled from that survey.
- The Π2P-completeness of skeptical preferred acceptance is confirmed (verified) in [Dvořák et al., KR 2021](https://proceedings.kr.org/2021/67/kr2021-0067-dvorak-et-al.pdf), which cites Dvořák & Dunne 2017. It was originally shown in [Dunne & Bench-Capon 2002, AIJ 141](https://doi.org/10.1016/S0004-3702(02)00261-8).
- Columns: Cred = credulous acceptance, Skept = skeptical acceptance, Ver = verifying that a given set is an extension, Exists = an extension exists, NE = a non-empty extension exists.

| Semantics | Cred | Skept | Ver | Exists | NE |
|---|---|---|---|---|---|
| admissible | NP-c | trivial | in L | trivial | NP-c |
| complete | NP-c | P-c | in L | trivial | NP-c |
| grounded | P-c | P-c | P-c | trivial | in L |
| stable | NP-c | coNP-c | in L | NP-c | NP-c |
| preferred | NP-c | Π2P-c | coNP-c | trivial | NP-c |
| semi-stable | Σ2P-c | Π2P-c | coNP-c | trivial | NP-c |
| stage | Σ2P-c | Π2P-c | coNP-c | trivial | in L |
| ideal | Cred = Skept: coNP-hard, in Θ2P ([Dunne 2009, AIJ 173](https://doi.org/10.1016/j.artint.2009.09.001)) | | | | |

- Restricting cycle length lowers the cost: for AFs with no even-length cycles of length ≥ 4, skeptical preferred acceptance drops to coNP-c (verified) — [Dvořák et al., KR 2021](https://proceedings.kr.org/2021/67/kr2021-0067-dvorak-et-al.pdf)

Solvers:
- ASPARTIX encodes AF semantics as ASP programs run on clingo or DLV — [Egly, Gaggl & Woltran 2010, Argument & Computation](https://doi.org/10.1080/19462166.2010.486479)
- ICCMA 2025 (6th competition) had a Main abstract-AF track, a Heuristics/Approximate track, a Dynamic track and an ABA track. Results were posted 2025-11-26 and announced on PlanetKR in February 2026 (verified) — [ICCMA 2025](https://www.argumentationcompetition.org/2025/index.html); [PlanetKR announcement, Feb 2026](https://kr.org/pipermail/planetkr/2026-February/003708.html)
- Main-track leaders were mutoksia, fudge, scallop and reducto. For example:
  - DC-CO: mutoksia, fudge, scallop
  - DS-PR: mutoksia, reducto, fudge
  - DS-ST: fudge, mutoksia, scallop
  - SE-ST: scallop, fudge, mutoksia
  - SE-ID: fudge, mutoksia, scallop
- "aspforaba" performed strongly across the ABA track (verified) — [ICCMA 2025 rankings](https://argumentationcompetition.org/2025/rankings.html)

### Inferences
- Labellings map naturally onto verdicts, but at the level of conclusions, not arguments. Each explanation H can be supported by several arguments and attacked by several more, so its status is per extension:
  - IN if some accepted argument concludes H;
  - OUT if some accepted argument concludes ¬H or a declared contrary of H;
  - NONE otherwise.

  The rationality postulates (consistency) are exactly what guarantees IN and OUT never co-occur within one extension. Across the set of extensions, the profile of H is a non-empty subset of {IN, OUT, NONE}. This profile is a Belnap-style four-plus-valued object (Section 6) and is the core of the recommended semantics (Section 8).
- Grounded versus multi-extension semantics is a real design choice, not a detail. Grounded is unique, polynomial and maximally skeptical, but it loses "floating conclusions": H reached by different routes in each rival reading. Horty (2002) argues that floating conclusions are sometimes rightly rejected — [Horty 2002, AIJ 135](https://doi.org/10.1016/S0004-3702(01)00160-6). Reporting both a grounded "core" and a stable-semantics profile exposes this rather than hiding it.
- Contradicting news sources mostly produce symmetric rebuttals. In symmetric, irreflexive AFs, stable = preferred = naive and stable extensions always exist (Coste-Marquis, Devred & Marquis, ECSQARU 2005; recalled, not re-verified). Asymmetry comes only from preferences (source tiers) and undercutters (copy detection, retractions). Odd attack cycles can then make stable extensions vanish. Cross-field link: an odd attack cycle is the argumentation analogue of geometric frustration (an antiferromagnetic triangle cannot be 2-colored), and there is no in/out "ground state" consistent with every constraint. Yggdrasil therefore needs an explicit, certified "no stable extension" outcome with a fallback.
- Bipolar support is best compiled away. Encode support as rule-based derivation (ASPIC+/ABA rules), so that "support" means "is a sub-argument of", rather than keeping a primitive support relation whose semantics is contested (deductive, necessary or evidential).
- Probabilistic argumentation is FP#P-hard in general and needs elicited probabilities. That makes it unsuitable as the verdict-determining layer, though it can serve as a secondary ranking.
- The top ICCMA solvers are SAT-based, but no evidence was found that any of them emits proof certificates. For certification, Yggdrasil should generate its own SAT/ASP encodings and run a proof-producing SAT solver (Section 7).

### Gaps
- The exact list of which semantics are PTIME versus FP#P-complete in Fazzinga et al.'s dichotomy was not verified.
- The complexity of ASPIC+ with preferences (weakest-link versus last-link) was not verified in this pass. Lehtonen, Wallner & Järvisalo have KR 2020 and KR 2022 papers on ASP for ASPIC+ that should be checked.
- I found no ICCMA solver with certified or proof-logging output.
- The "ideal" row and the exact P-completeness entries for grounded are recalled from Dvořák & Dunne, not re-fetched.

---

## 3. Explanatory coherence (Thagard/ECHO), Inference to the Best Explanation (Lipton), Bayesian confirmation measures

### Takeaway
Explanatory coherence and IBE describe how to rank explanations (breadth, simplicity, analogy, data priority). Exact coherence maximization is NP-hard and ECHO's connectionist settling is parameter-dependent, so both are better suited to tie-breaking or ranking than to proof-carrying verdicts. Among Bayesian confirmation measures, the log-likelihood-ratio measure lines up with forensic likelihood ratios and with Heuer's diagnosticity, and its value does not depend on the prior.

### Cited Findings
- Thagard's Theory of Explanatory Coherence (TEC) gives principles of symmetry, explanation (coherence divided among co-explaining hypotheses, which favors simplicity), analogy, data priority (evidence propositions get some acceptability on their own), contradiction (contradictory propositions incohere), acceptability, and system coherence. ECHO implements TEC as a connectionist network: excitatory links for coherence, inhibitory links for incoherence, run to settling — [Thagard 1989, Behavioral and Brain Sciences 12](https://doi.org/10.1017/S0140525X00057046)
- Coherence as constraint satisfaction: partitioning elements into accepted and rejected so as to maximize the weight of satisfied constraints is NP-hard (shown via MAX-CUT). Thagard & Verbeurgt give approximation algorithms, including connectionist and semidefinite-programming-based ones — [Thagard & Verbeurgt 1998, Cognitive Science 22(1)](https://doi.org/10.1207/s15516709cog2201_1)
- Lipton's IBE distinguishes the "likeliest" explanation (most probable) from the "loveliest" (the one that would provide the most understanding). He argues loveliness serves as a guide to likeliness — [Lipton 2004, Inference to the Best Explanation, 2nd ed., Routledge](https://www.routledge.com/Inference-to-the-Best-Explanation/Lipton/p/book/9780415242035)
- Bayesian confirmation measures of how much E confirms H:
  - difference: d = P(H|E) − P(H)
  - ratio: r = P(H|E) / P(H)
  - likelihood ratio: l = log[P(E|H) / P(E|¬H)]
  - also Kemeny-Oppenheim, Christensen-Joyce s, and Crupi's z.

  These measures are not ordinally equivalent and disagree on symmetry and other properties. Several papers argue for l (or its ordinal equivalents) — [Stanford Encyclopedia of Philosophy, "Confirmation"](https://plato.stanford.edu/entries/confirmation/); [Fitelson 1999, Philosophy of Science 66](https://doi.org/10.1086/392738)

### Inferences
- ECHO is mathematically a Hopfield-style energy (harmony) minimizer over a signed constraint graph. Its outcome depends on decay and excitation/inhibition parameters and on the settling schedule. So it is deterministic for fixed parameters, but it is not a certifiable semantic object, and exact optimization is NP-hard (Thagard & Verbeurgt 1998). If coherence scoring is wanted, encode it as a weighted MaxSAT or ASP optimization (#minimize) over the same atoms. The optimum then has a certificate: a witness plus an optimality proof via SAT/MaxSAT proof logging (Section 7). Treat it as a ranking among explanations that share the same verdict, never as the verdict.
- Lipton's "loveliness" virtues (breadth, specificity, unification) can be operationalized as explicit, deterministic tie-breakers: the number of observed signatures explained, the number of auxiliary assumptions, and minimality (compare HP's AC3 in Section 5).
- The confirmation measure l is the same quantity as the forensic likelihood ratio (Section 4) and is a numeric version of Heuer's diagnosticity. Using l keeps the probabilistic layer conceptually aligned with the logical layer.

### Gaps
- No primary source was retrieved in this pass for the competition principle added to TEC after 1989 (Thagard 1992, "Conceptual Revolutions").
- No empirical study was found comparing ECHO-style coherence ranking with argumentation semantics on real evidence sets.

---

## 4. Forensic science and law: likelihood ratios, hypothesis pairs, Bayesian networks, Wigmore charts, conflicting testimony

### Takeaway
Forensic science evaluates evidence relative to a pair of competing propositions, using the likelihood ratio LR = P(E | Hp) / P(E | Hd). Legal evidence theory supplies the structure: Wigmore and Schum chains of inference, credibility attributes of testimony, and proof standards in Carneades. Both strongly support evaluating each Yggdrasil explanation against an explicit rival, not in isolation. Courts leave conflicting testimony to the fact-finder, judged against a proof standard. The formal analogue is a threshold or proof standard attached to the verdict labels.

### Cited Findings
- The standard evaluative framework is the LR for evidence E under a prosecution proposition and a defence proposition. Posterior odds = LR × prior odds. The forensic scientist reports the LR, and the prior and posterior belong to the fact-finder — [Aitken, Taroni & Bozza 2021, Statistics and the Evaluation of Evidence for Forensic Scientists, 3rd ed., Wiley](https://doi.org/10.1002/9781119245438)
- The ENFSI guideline for evaluative reporting (2015) requires: (a) evaluation relative to at least one pair of propositions; (b) a conditioning framework of case information; (c) reporting the LR, optionally with a verbal scale — [ENFSI Guideline for Evaluative Reporting, 2015](https://enfsi.eu/wp-content/uploads/2016/09/m1_guideline.pdf)
- In R v T (2010), the English Court of Appeal criticized the use of LRs built from imprecise databases in footwear-mark evidence. This shows legal resistance to numeric LRs when the inputs are not robust — [R v T [2010] EWCA Crim 2439, BAILII](https://www.bailii.org/ew/cases/EWCA/Crim/2010/2439.html)
- Bayesian networks for legal arguments: Fenton, Neil & Lagnado propose reusable BN "idioms", including evidence accuracy, motive and opportunity, alibi, and explaining away, to structure legal arguments about evidence — [Fenton, Neil & Lagnado 2013, Cognitive Science 37](https://doi.org/10.1111/j.1551-6709.2012.01262.x)
- A review of Bayes in the law covers the uptake and the pitfalls — [Fenton, Neil & Berger 2016, Annual Review of Statistics and Its Application](https://doi.org/10.1146/annurev-statistics-041715-033428)
- Wigmore charts break ultimate probanda into chains of inference from evidence. Anderson, Schum & Twining modernize the method, including Schum's credibility attributes of testimonial evidence (veracity, objectivity, observational sensitivity) — [Anderson, Schum & Twining 2005, Analysis of Evidence, 2nd ed., CUP](https://doi.org/10.1017/CBO9780511610585)
- Reasoning about evidence can be formalized with argumentation schemes and generalisations, including a witness-testimony scheme with critical questions, which is the precursor of the ASPIC+ formalization of legal evidence — [Bex, Prakken, Reed & Walton 2003, AI and Law 11](https://doi.org/10.1023/B:ARTI.0000046007.11806.9a)
- Carneades formalizes proof standards over argument graphs: scintilla of evidence, preponderance of evidence, clear and convincing evidence, beyond reasonable doubt, and dialectical validity. It also formalizes the allocation of the burden of proof — [Gordon, Prakken & Walton 2007, AIJ 171](https://doi.org/10.1016/j.artint.2007.04.010)

### Inferences
- Hypothesis pairs: evaluate each explanation H_i against an explicit alternative (the rival explanations plus a catch-all "no identifiable news cause / microstructure noise"). This is the LR discipline and also ACH's matrix. In logical terms the contrary relation in ABA/ASPIC+ should be declared per explanation pair, which also forces analysts to state which explanations are mutually exclusive and which can co-occur.
- Schum's credibility attributes map directly onto news sources:
  - veracity: does the outlet report what it believes?
  - objectivity: is the claim based on the evidence or on expectation?
  - observational sensitivity: did the outlet actually observe the claim, or relay it second-hand?

  Each becomes an undercutter in ASPIC+/ABA, e.g. "outlet relays an anonymous source", "outlet has a conflict of interest", "outlet copied the wire". That turns credibility from a fudge factor into attackable structure with provenance.
- Carneades-style proof standards are the legal precedent for making verdict thresholds explicit. "SUPPORTED" can carry a parameter: "beyond reasonable doubt" ≈ skeptical acceptance and no undefeated counter-argument; "preponderance" ≈ an optional Bayesian LR threshold. The parameter should be fixed in the specification so the verdict stays a deterministic function of the evidence base.
- Bayesian networks give a richer quantitative model, but exact inference is NP-hard in general and the CPTs must be elicited. Like probabilistic argumentation, they suit a secondary ranking, not certified verdicts.

### Gaps
- I did not retrieve a primary source on how courts formally resolve conflicting witness testimony (e.g. jury instructions on credibility, or "falsus in uno"). The general statement that credibility is for the fact-finder is standard but is not cited here.
- No formal Wigmore-chart semantics with complexity results was found.

---

## 5. Actual causation and explanation: Halpern-Pearl definitions, minimality, complexity

### Takeaway
The HP definitions give a precise, finite, decidable notion of "event X caused market move Y". It requires a structural causal model (SCM), and deciding causality is at the second level of the polynomial hierarchy:
- original HP: Σ2P-c;
- updated HP: D2P-c;
- modified HP (Halpern 2015): DP-c.

For Yggdrasil, HP is the right definitional target for what an "explanation" claims, and AC3 is the right minimality notion. But market SCMs are rarely available, so explanation schemas should be encoded as defeasible rules with HP-inspired conditions (temporal precedence, counterfactual dependence where measurable, minimality), not as full SCM causality checks.

### Cited Findings
- Setting: a causal model M = (S, F) with exogenous variables U, endogenous variables V and structural equations F. A context u is a setting of U. [X ← x]phi means phi holds after intervening to set X to x.
- Updated HP definition (Halpern & Pearl 2005), as restated verbatim in the JAIR paper (verified). X = x is a cause of phi in (M, u) iff:
  - AC1: (M, u) |= (X = x) ∧ phi.
  - AC2: there is a partition (Z, W) of V with X ⊆ Z and a setting (x', w) of (X, W) such that, where (M, u) |= Z = z* for each Z ∈ Z:
    - (a) (M, u) |= [X ← x', W ← w] ¬phi;
    - (b) (M, u) |= [X ← x, W' ← w, Z' ← z*] phi for all subsets Z' of Z \ X and all subsets W' of W.
  - AC3: X is minimal; no strict subset of X satisfies AC1 and AC2.
- The original 2001 definition required AC2(b) only for W' = W (written AC2(b') in the paper). The change was made to handle counterexamples raised by Hopkins & Pearl — [Aleksandrowicz, Chockler, Halpern & Ivrii 2017, JAIR](https://www.jair.org/index.php/jair/article/view/11047); [Halpern & Pearl 2005, BJPS](https://doi.org/10.1093/bjps/axi147)
- The modified definition (Halpern 2015, used in Halpern 2016's "Actual Causality") replaces AC2 by AC2(a^m): there is a set W and a setting x' such that, with W held at its actual values w*, (M, u) |= [X ← x', W ← w*] ¬phi. AC1 and AC3 are unchanged — [Halpern 2015, arXiv 1505.00162](https://arxiv.org/abs/1505.00162) (statement recalled)
- Complexity (verified from the JAIR text):
  - Original HP: deciding causality is NP-complete in binary models and Σ2P-complete in general models (Eiter & Lukasiewicz).
  - Updated HP: D2P-complete, where DkP = {L1 ∩ L2 : L1 ∈ ΣkP, L2 ∈ ΠkP} and D1P = DP. For updated HP, AC2 alone is Σ2P-complete and AC3 alone is Π2P-complete.
  - Singleton causes under updated HP: Σ2P-complete for both binary and general models.
  - Modified HP (Halpern 2015): deciding causality is DP-complete.
  - Degree of responsibility and blame: FP^Σ2P[log n]-complete for the original, updated and modified definitions (Alechina, Halpern & Logan 2016).
  - Source — [Aleksandrowicz et al. 2017, JAIR (arXiv 1412.3076)](https://arxiv.org/abs/1412.3076); original results in [Eiter & Lukasiewicz 2002, AIJ 142](https://doi.org/10.1016/S0004-3702(02)00271-0)
- The authors note tractable special cases. One is a class from Chockler, Halpern & Kupferman 2008 where original and updated definitions agree. Another is modular legal-case models that allow modular computation of responsibility (verified) — [Aleksandrowicz et al. 2017](https://arxiv.org/abs/1412.3076)
- Logic-based abduction ("which hypotheses explain the observations?"): for propositional theories, deciding whether a solution exists is Σ2P-complete in general and NP-complete for Horn theories — [Eiter & Gottlob 1995, JACM 42](https://doi.org/10.1145/200836.200838) (class assignments recalled)

### Inferences
- The prior design note's step "use clingo/Z3 to search for explanations" is an abduction problem. General propositional abduction is Σ2P-complete. Keeping the rule base Horn-like or tight, and the hypothesis space a fixed enumerated set of candidate explanations, drops this to NP or below. Yggdrasil generates candidate explanations upstream anyway, so the verification layer should judge a fixed finite set rather than search an open space. That keeps the certified part within NP / coNP.
- HP-inspired conditions that are cheap and certifiable for market forensics:
  - AC1 (actuality): the trigger event is established, i.e. SUPPORTED, and the abnormal move is established.
  - Temporal precedence: the cause timestamp precedes the move-onset timestamp. Encode this as a strict rule; an explanation whose trigger is established to post-date the move is strictly refuted.
  - Counterfactual dependence (AC2-like): available only where a quantitative model exists, e.g. an event-study abnormal-return model. Otherwise encode it as a defeasible "signature match" rule.
  - Minimality (AC3): report subset-minimal explanation bundles. With a fixed candidate set this is a polynomial number of SAT checks.
- Full HP over an SCM of n binary variables is DP-c or worse, which is decidable and finite. Certifying it requires both an NP witness (the setting for AC2(a^m)) and a coNP certificate (AC3 minimality: no smaller X works). That fits the witness-plus-LRAT pattern in Section 7 if Yggdrasil ever builds explicit SCMs (e.g. contagion graphs among assets).

### Gaps
- The exact HP 2005 / Halpern 2016 definition of explanation (relative to an epistemic state K) was not re-fetched. Its complexity (Eiter & Lukasiewicz 2004, "Complexity results for explanations in the structural-model approach", AIJ 154) was not verified.
- No market-microstructure SCM literature applying HP causality was found in this pass.

---

## 6. Reasoning with contradictory sources without explosion: paraconsistency, Belnap/FDE, AGM, evidence logic, justification logic, truth discovery

### Takeaway
Explosion is avoided in three complementary ways:
1. Reify reports, "source S reported phi". This is what the prior note proposed, and it is necessary but not sufficient.
2. Make the step from reports to world-claims defeasible: default logic, ASP negation-as-failure, ABA/ASPIC+.
3. Evaluate skeptically and credulously over the maximal coherent readings, using maximal consistent subsets, van Benthem-Pacuit evidence logic, or stable extensions.

Belnap's four-valued logic (T, F, Both, Neither) is the right output vocabulary. It was designed for exactly a "computer receiving conflicting information from multiple sources". It is not a resolution mechanism, because it never prefers one source over another.

Truth-discovery algorithms supply source-reliability weights and copy detection, which are valuable inputs. Their output is a numeric fixpoint, not a logic, so their results should be used as fixed premises (preferences), not verified conclusions.

### Cited Findings
- Paraconsistent logics reject ex contradictione quodlibet: {A, ¬A} |= B fails. Families include Priest's LP, da Costa's C-systems, relevance logics and FDE — [SEP, "Paraconsistent Logic"](https://plato.stanford.edu/entries/logic-paraconsistent/)
- In LP (3-valued: true, false, both, with both designated), the tautologies are exactly the classical tautologies, so LP validity checking is coNP-complete like classical logic. LP invalidates modus ponens and disjunctive syllogism — [Priest 1979, JPL 8](https://doi.org/10.1007/BF00258428); [SEP Paraconsistent Logic](https://plato.stanford.edu/entries/logic-paraconsistent/)
- Belnap's "useful four-valued logic": the values T (told true only), F (told false only), B (told both) and N (told neither) form a bilattice ordered by truth and by information. It was proposed for a question-answering computer fed by multiple, possibly inconsistent sources. Its consequence relation is first-degree entailment (FDE) — [Belnap 1977, in Modern Uses of Multiple-Valued Logic](https://doi.org/10.1007/978-94-010-1161-7_2)
- Maximal consistent subsets (Rescher & Manor 1970): from an inconsistent base, infer what holds in all (skeptical), some (credulous) or the intersection of maximal consistent subsets — [Rescher & Manor 1970, Theory and Decision 1](https://doi.org/10.1007/BF00154005)
- AGM belief revision has postulates for expansion, contraction and revision of deductively closed belief sets — [Alchourrón, Gärdenfors & Makinson 1985, JSL 50](https://doi.org/10.2307/2274239)
- For propositional knowledge bases, deciding whether a formula follows from the revised KB is Π2P-complete for most proposed revision and update operators. Dalal's operator is lower, at P^NP[O(log n)] — [Eiter & Gottlob 1992, AIJ 57](https://doi.org/10.1016/0004-3702(92)90018-S) (class assignments recalled)
- Evidence logic (van Benthem & Pacuit 2011): neighborhood models in which each evidence set is a proposition the agent has evidence for, possibly from conflicting sources. Beliefs are what holds throughout every maximally consistent family of evidence (verified at report level) — [van Benthem & Pacuit 2011, ILLC report PP-2011-19 / Studia Logica](https://eprints.illc.uva.nl/423/)
- Follow-up work gives sound and complete axiomatizations for four model classes in the language of evidence, belief and safe belief, plus a representation theorem (verified) — [van Benthem, Fernández-Duque & Pacuit 2014, "Evidence and plausibility in neighborhood structures", arXiv 1307.1277](https://arxiv.org/abs/1307.1277)
- Justification logic replaces the modal box with explicit justification terms t:phi. It has application (t·s) and sum (t+s), so it tracks why something is believed. The Logic of Proofs (LP, a different LP from Priest's) is decidable — [Artemov 2008, Review of Symbolic Logic](https://doi.org/10.1017/S1755020308090060); [SEP, "Justification Logic"](https://plato.stanford.edu/entries/logic-justification/)
- Paraconsistent stable semantics for extended disjunctive programs: in standard ASP, deriving both p and -p (strong negation) yields no answer set. Paraconsistent variants keep reasoning — [Sakama & Inoue 1995, J. Logic and Computation 5(3)](https://doi.org/10.1093/logcom/5.3.265)
- Truth discovery:
  - TruthFinder iteratively estimates source trustworthiness from fact confidence, and fact confidence from source trustworthiness — [Yin, Han & Yu 2008, IEEE TKDE 20(6)](https://doi.org/10.1109/TKDE.2007.190745)
  - Dong, Berti-Equille & Srivastava model source accuracy jointly with copying between sources: shared false values are evidence of copying. Without copy detection, copied errors get amplified — [Dong, Berti-Equille & Srivastava 2009, PVLDB 2(1)](https://doi.org/10.14778/1687627.1687690)
  - Survey of the area — [Li et al. 2016, "A Survey on Truth Discovery", SIGKDD Explorations (arXiv 1505.02463)](https://arxiv.org/abs/1505.02463)

### Inferences
- Reification alone (the prior design) does not settle anything. reported(s1, p) ∧ reported(s2, ¬p) is classically consistent, so there is no explosion. But it is also inert: nothing about the world follows. Some bridge rule reported(s, phi) ∧ ... -> phi is needed. If the bridge is classical and both sources pass it, explosion returns one level up. In ASP the equivalent failure is a total absence of answer sets. So the bridge must be defeasible: an ABA assumption ok(r), "report r is accurate", whose contrary is derivable from conflicting, better or independent reports or from undercutters. That is the missing piece in the prior note.
- Three formalisms converge on the same structure, which is strong evidence that it is the natural one:
  - van Benthem-Pacuit "belief = truth in all maximal consistent evidence families";
  - Rescher-Manor skeptical inference over maximal consistent subsets;
  - Dung skeptical acceptance over stable or preferred extensions.

  Cayrol (1995) showed that the stable extensions of the logic-based AF built from a flat base correspond to its maximal consistent subsets (recalled; not re-verified in this pass). Choose the argumentation version, because it adds preferences, undercutters and mature solvers.
- Belnap supplies the user-facing vocabulary, and argumentation supplies the mechanism. For each explanation H, two bits:
  - "is there a coherent reading in which H is established?"
  - "is there a coherent reading in which H is refuted?"

  Together with their skeptical counterparts these give the four verdicts. FDE itself cannot express "trust Reuters over an anonymous blog", but preferences in ASPIC+/ABA can.
- Do not use incremental AGM revision as the engine. Iterated revision depends on the order in which news arrives, which breaks the "deterministic function of the evidence snapshot" requirement, and propositional revision is Π2P-complete anyway. Recompute verdicts statelessly from the full evidence snapshot instead. Evidence that arrives later is just a new snapshot; diff the verdicts between snapshots for audit.
- Justification logic is a good conceptual model for provenance: t:phi records the derivation. It is unnecessary as an engine, because argument trees and ABA derivations already carry the same information and are cheaper.
- Truth discovery belongs in the pre-processing layer:
  1. Collapse copied or syndicated reports to their origin (Dong et al. 2009), so that 40 outlets rewriting one wire story count as one witness.
  2. Derive coarse source-reliability tiers from historical accuracy.

  Feed the tiers into the argument preference ordering as fixed, logged premises. The verification then proves "given these tiers, the verdict is V". It does not prove that the tiers are correct. This boundary must be stated explicitly.
- Decidability summary (finite propositional case):
  - LP, FDE, maximal-consistent-subset inference, AGM base revision, Dung/ABA semantics over finite frameworks and ASP over finite ground programs are all decidable.
  - Evidence logic and justification logic have decidable propositional fragments, but their certification story in Lean is less direct.
  - Truth-discovery fixpoints are numeric procedures without a logical decision problem to certify.

### Gaps
- Exact complexity bounds for evidence logic (EL) satisfiability and for LP (justification logic) derivability were not verified. The SEP entry and Kuznets / Milnikel papers should be checked; Π2P-level bounds are recalled.
- Cayrol 1995 (stable extensions correspond to maximal consistent subsets) and Levesque 1984 (a polynomial case of tautological entailment for clausal forms) were not verified.

---

## 7. Machine-checked verification: Lean 4 decision procedures, SAT/SMT integration, LRAT, argumentation and ASP formalizations, certificates, scale

### Takeaway
Lean 4 can certify finite propositional verdicts today. Use proof by reflection: write a Bool checker, prove it sound once, and run it on per-incident certificates. Positive (NP) answers come with witness models that a checker verifies. Negative (coNP) answers come with SAT-solver LRAT refutations, checked by Lean core's verified LRAT checker. That checker sits behind bv_decide and is reused by lrat-catcher (2026).

The main caveats:
- The fast path (native_decide, bv_decide, lrat-catcher) adds the axiom Lean.ofReduceBool and so trusts the Lean compiler. The kernel-only path (decide, Mathlib's lrat_proof) has a smaller trusted base but is much slower.
- No Lean library for Dung, ABA or ASP semantics exists that I could find. Isabelle/HOL and Agda formalizations exist, plus one 2026 Lean 4 four-valued conflict model. The Yggdrasil formalization would be new work.
- Certified ASP is immature (ASP-DRUPE, 2019, has no verified checker found). The robust route is a verified translation from tight normal programs to SAT, followed by LRAT.

### Cited Findings

Lean decision procedures and their trusted base:
- native_decide proves p by synthesizing Decidable p and evaluating it with compiled code. It "adds the entire Lean compiler to the trusted part", and the axiom Lean.ofReduceBool appears in #print axioms for any theorem that depends on it (verified) — [Lean tactic docs mirror](https://www.cs.rochester.edu/~yzhu104/lean-gccjit/Lean/Parser/Tactic.html)
- Lean.Meta.Native: nativeEqTrue compiles and runs a closed Bool, checks that it is true, and adds an axiom asserting this. This is the basis of native_decide and bv_decide (verified) — [Lean API: Lean.Meta.Native](https://lean-lang.org/doc/api/Lean/Meta/Native.html)
- bv_decide (Lean 4.12, October 2024) reduces BitVec/Bool goals to SAT, which is refuted by CaDiCaL (bundled with Lean). The LRAT proof is checked in Lean with verified algorithms, and the goal is proved by reflection. Because it uses Lean.ofReduceBool, the compiler is in the trusted base (verified) — [Lean 4.12.0 release](https://lean-lang.org/blog/2024-10-3-lean-4120); [Lean reference, v4.12.0 notes](https://lean-lang.org/doc/reference/latest/releases/v4.12.0/)
- Mathlib's lrat_proof command (Mathlib.Tactic.Sat.FromLRAT) produces SAT proofs from CNF + LRAT files using the Lean kernel itself as the LRAT checker. The result is a standard propositional theorem with no native-code trust (verified) — [Mathlib docs: Tactic.Sat.FromLRAT](https://florisvandoorn.com/LeanCourse25/docs/Mathlib/Tactic/Sat/FromLRAT.html)
- lrat-catcher (Szeider, arXiv July 2026, revised September 2026) streams a SAT solver's LRAT certificate into a Lean 4 theorem while the solver is still running:
  - It makes Lean core's verified LRAT checker resumable and serializable.
  - Memory depends only on the live clause set.
  - A garbled or adversarial stream can only fail the check, never yield a false theorem.
  - It supports cube-and-conquer and proofs about the original formula after preprocessing.
  - 174 TB of certificates for the empty-hexagon problem were imported via streaming.
  - It runs the checker as compiled native code by reflection, so it carries the same compiler-trust caveat (verified) — [Szeider 2026, arXiv 2607.00815](https://arxiv.org/abs/2607.00815)

LRAT and verified SAT checkers:
- LRAT adds hints to DRAT so that checking takes linear time — [Cruz-Filipe, Heule, Hunt, Kaufmann & Schneider-Kamp 2017, CADE (arXiv 1612.02353)](https://arxiv.org/abs/1612.02353)
- cake_lpr is a SAT proof checker for LPR (LRAT with propagation redundancy), verified in CakeML/HOL4 down to machine code — [Tan, Heule & Myreen 2021, TACAS](https://doi.org/10.1007/978-3-030-72013-1_12)

SMT integration:
- Lean-SMT (CAV 2025): cvc5 emits CPC-format proofs with more than 662 rules. Lean-SMT reconstructs about 200 of them (around 30%) step by step into Lean proofs that the kernel checks (verified) — [Mohamed et al. 2025, arXiv 2505.15796](https://arxiv.org/abs/2505.15796)
- QuerySMT (January 2026) uses cvc5 proof "hints" to guide Lean automation without retaining a dependency on the SMT solver (verified) — [Clune, Barbosa & Avigad 2026, arXiv 2601.14495](https://arxiv.org/abs/2601.14495)
- Z3 proof objects have historically been reconstructed in Isabelle/HOL; the coarse theory-lemma steps make this hard — [Böhme & Weber 2010, ITP](https://doi.org/10.1007/978-3-642-14052-5_14)

Argumentation formalizations in proof assistants:
- Isabelle/HOL: Steen & Fuenmayor encode abstract AFs in classical higher-order logic. Extensions and labellings are synthesized for the standard semantics, and meta-theory is checked in Isabelle/HOL. In 2021 they stated that no other formalization of AFs in higher-order logic or in existing proof assistants existed (verified) — [Steen & Fuenmayor 2021, arXiv 2110.09174](https://arxiv.org/abs/2110.09174)
- Agda: van Gijzel's thesis implements Dung AFs and the Carneades model in Haskell and formalizes them in Agda, as a framework for verified argumentation models and translations (verified at abstract level) — [van Gijzel, PhD thesis, Nottingham](https://people.cs.nott.ac.uk/pszgmh/van-gijzel-thesis.pdf)
- Lean 4 (September 2026): Kato's "Quasi-Closed World Graph Model for Conflict Resolution" (QCW-GMCR) uses Belnap four-valued logic and an FDE-inspired transition semantics, formalized in Lean 4 + Mathlib:
  - Formalized: the classical GMCR stability hierarchy, properties of four-valued conjunction, canonical reduction operators from four-valued assessments to binary decisions, and a graded reachability hierarchy.
  - The formalization caught errors and led to replacing a knowledge-monotonicity axiom with truth monotonicity.
  - The four-valued layer is built from decidable, computable definitions over Fintypes, checkable via #eval/decide.
  - This is the closest Lean precedent found, but it is the graph model for conflict resolution (game-theoretic), not Dung semantics (verified) — [Kato 2026, arXiv 2609.11174](https://arxiv.org/abs/2609.11174)

Certified ASP and proof logging:
- ASP-DRUPE is an inconsistency-proof format for ASP. It is sound and complete for (normal) logic programs and checkable in time polynomial in proof length. No formally verified checker was found (verified) — [Alviano, Dodaro, Fichte, Hecher, Philipp & Rath 2019, TPLP (arXiv 1907.10389)](https://arxiv.org/abs/1907.10389)
- Pseudo-Boolean proof logging: VeriPB has the formally verified backend CakePB and is used for constraint programming, PB solving and MaxSAT certification (verified) — [VeriPB documentation (PB'26)](https://www.cril.univ-artois.fr/PB26/descr/Documentation_VeriPB_general.pdf)
- Certified branch-and-bound MaxSAT (AAAI 2026): proof logging is feasible with limited overhead, but "proof checking remains a challenge" (verified) — [Vandesande, Coll & Bogaerts 2025, arXiv 2511.10273](https://arxiv.org/abs/2511.10273)

ASP semantics facts used:
- For tight normal programs (no positive dependency cycles), stable models coincide with the models of Clark's completion. This is Fages' theorem, generalized by Erdem & Lifschitz — [Erdem & Lifschitz 2003, TPLP](https://doi.org/10.1017/S1471068403001765)
- For normal ground programs, stable-model existence and brave reasoning are NP-complete, and cautious reasoning is coNP-complete. For disjunctive programs these become Σ2P / Π2P — [Dantsin, Eiter, Gottlob & Voronkov 2001, ACM Computing Surveys](https://doi.org/10.1145/502807.502810)

### Inferences
- Proof-by-reflection template for Yggdrasil (design proposal):
  - `def checkStable (P : GroundProgram) (M : Finset Atom) : Bool` computes the Gelfond-Lifschitz reduct and its least model with fuel = number of atoms, and compares the result to M.
  - Prove `checkStable P M = true -> IsStableModel P M` once.
  - Per incident: `checkStable_sound P M (by decide)` for small instances, or `(by native_decide)` at scale.
  - Use the same pattern for grounded-labelling certificates and for the verdict function.
- A grounded labelling has a linear-time certificate checker (design proposal; the soundness argument is standard):
  - Give a rank to every IN and OUT argument. Each IN argument has all attackers OUT with lower rank. Each OUT argument has a lower-ranked IN attacker. This proves IN ⊆ grounded-in and OUT ⊆ grounded-out.
  - Check separately that the labelling is complete. Every complete labelling's IN contains grounded-in, so equality follows.
  - Both checks are linear in |R|, which makes this the cheapest certified layer.
- The stable/NP layer:
  - A witness extension or model is checked in linear time ("Ver in L" for stable).
  - Negative answers need UNSAT certificates. For normal programs, the cleanest certified route avoids ASP-specific proof formats. Require the evidence program to be tight (only negation cycles, no positive loops), and generate Clark's completion plus a Tseitin CNF with a Lean-verified translation. Run CaDiCaL with LRAT output, and check the LRAT in Lean with core's verified checker (as bv_decide and lrat-catcher do), or with Mathlib's kernel-only lrat_proof for small instances. The Fages / Erdem-Lifschitz theorem must then be proved in Lean once.
- Avoid Z3 in the certified path. For purely finite propositional verdicts, SAT + LRAT has the shortest trust chain (Lean kernel + verified LRAT checker, optionally + compiler). Pre-evaluate numeric side conditions such as timestamps and return thresholds into ground atoms; Lean checks those comparisons by `decide` on Nat/Int. If real arithmetic is ever needed, cvc5 + Lean-SMT has a reconstruction path; Z3 does not have a mature Lean reconstruction path that I found.
- Determinism has two meanings:
  - Semantic determinism (recommended): the verdict is a function of the evidence snapshot defined by skeptical/credulous quantification over a semantics, so any correct solver gives the same verdict. Lean proves the verdict, not the solver run.
  - Operational determinism matters only for provenance: which witness or which UNSAT core is reported. Make it canonical by fixing solver version and seed, choosing lexicographically minimal witnesses (clingo lexicographic #minimize), and extracting deletion-based MUS cores in a fixed order.
- Expected scale for hundreds to thousands of propositions (estimates, not benchmarked here):
  - Ground programs of roughly 10^3–10^4 atoms and 10^4–10^5 rules or clauses are small for clingo and CaDiCaL (typically sub-second).
  - The resulting LRAT proofs for such structured instances should be small. Native-code LRAT checking in Lean handles certificate volumes many orders of magnitude larger (lrat-catcher: 174 TB).
  - The binding constraint is the trusted base, not speed. Kernel-only reduction (decide, lrat_proof) on 10^4–10^5-clause instances is plausibly minutes or worse, and must be benchmarked before committing to a no-compiler-trust policy.
  - Kernel-reduction pitfalls (known Lean idioms, not verified in this pass): prefer structural recursion or fuel over well-founded recursion, and Array/Nat-based data over deep List recursion.

### Gaps
- I found no published benchmark of Lean kernel `decide` or Mathlib `lrat_proof` throughput (clauses per second or memory) at 10^4–10^6 clauses. This is the single most important number to measure before fixing the trust policy.
- No Lean 4 formalization of Dung semantics, ABA, ASPIC+ or ASP stable models was found. No Coq/Rocq argumentation formalization was found in this pass. Absence from search is not proof of absence.
- I found no verified checker for ASP-DRUPE and no proof-logging ICCMA solver.
- The precise options and behavior of `decide +kernel` in current Lean (4.2x) were not verified.
- Whether Lean core's LRAT checker (used by bv_decide) can be invoked as a kernel-only (non-native) proof at moderate scale was not verified.

---

## 8. Evaluation of the prior design note, and recommended semantics, encoding and verification pipeline

### Takeaway
The prior note gets three things right:
- reifying reports;
- using witness models for "not entailed" (cheap NP certificates) and refutation proofs for "entailed" (coNP certificates);
- the solver-searches / Lean-certifies split.

It has three structural flaws:
1. Classical entailment from "the premises" is undefined under conflict: it either explodes or, over reified reports alone, entails nothing.
2. It conflates "evidence entails explanation" with what explanations are, namely defeasible causal claims judged by consistency and diagnosticity (ACH, LR).
3. It does not distinguish CONSISTENT-BUT-UNPROVEN from UNRESOLVED.

Recommended fix:
- a defeasible bridge (flat ABA, equivalently a tight normal logic program under stable semantics);
- verdicts defined by the profile of each explanation's conclusion status across all stable models;
- a grounded / well-founded core in polynomial time;
- certification by witness models plus LRAT refutations checked in Lean via reflection.

### Cited Findings
- Classical consequence explodes on inconsistent premises. Paraconsistent and argumentative approaches exist precisely to avoid this — [SEP Paraconsistent Logic](https://plato.stanford.edu/entries/logic-paraconsistent/)
- Flat ABA, i.e. normal logic programs, under stable semantics: credulous reasoning is NP-c and skeptical is coNP-c — [Dimopoulos, Nebel & Toni 2002](https://doi.org/10.1016/S0004-3702(02)00245-X)
- The corresponding ASP tasks: brave reasoning NP-c, cautious reasoning coNP-c — [Dantsin et al. 2001](https://doi.org/10.1145/502807.502810)
- Grounded semantics corresponds to the well-founded model and is polynomial — [Wu, Caminada & Gabbay 2009](https://doi.org/10.1007/s11225-009-9210-5); [Van Gelder, Ross & Schlipf 1991](https://doi.org/10.1145/116825.116838)
- Tight programs: stable models = completion models — [Erdem & Lifschitz 2003](https://doi.org/10.1017/S1471068403001765)
- Lean core's verified LRAT checker with CaDiCaL, trusting the compiler via ofReduceBool — [Lean 4.12 release](https://lean-lang.org/blog/2024-10-3-lean-4120)
- The kernel-only alternative — [Mathlib FromLRAT](https://florisvandoorn.com/LeanCourse25/docs/Mathlib/Tactic/Sat/FromLRAT.html)
- Streaming at scale — [lrat-catcher 2026](https://arxiv.org/abs/2607.00815)
- Rationality postulates needed so that no single reading contains both H and ¬H — [Caminada & Amgoud 2007](https://doi.org/10.1016/j.artint.2007.02.003)

### Inferences

**8.1 Point-by-point evaluation of the prior note**

1. "Encode evidence as 'source S reported phi'." KEEP, but extend it. Reification prevents object-level explosion but derives nothing about the world. Add:
   - (a) a defeasible acceptance assumption per report, ok(r);
   - (b) contraries and undercutters for ok(r): conflicting accepted reports, copy-of, retraction, low-credibility-for-topic, and timestamp impossibility;
   - (c) source-dependence collapsing before argument construction (Dong et al. 2009);
   - (d) preferences from logged reliability tiers.
2. "Supported = premises |= E; contradicted = premises |= ¬E." REPLACE. With classical premises that include accepted conflicting claims, both hold (explosion). With reified reports only, neither holds. The direction is also too strong for explanations: news rarely entails "X caused the move". Redefine support as cautious (skeptical) acceptance of the explanation's conclusion atom expl(H) in the defeasible program. Here expl(H) is derived by an explicit, domain-written explanation schema: the trigger is established, temporal precedence holds, the predicted signatures are observed, and H is not refuted. This also matches HP's AC1 / precedence / minimality (Section 5).
3. "Independence = witness models for both E and ¬E." KEEP the certificate insight; witnesses are NP certificates and cheap to check. But apply it to stable models of the defeasible program, not classical models of raw premises. Split independence into two verdicts:
   - CONSISTENT-BUT-UNPROVEN: H is never refuted in any coherent reading, but not established in all.
   - UNRESOLVED: rival coherent readings establish and refute H respectively.
4. "Use clingo or Z3 to search; Lean certifies." KEEP clingo, which is the natural engine for ABA and normal programs. Drop Z3 from the certified path. Bound the search: explanation candidates are a fixed, enumerated set supplied upstream, which avoids Σ2P abduction. Lean certifies results relative to the ground program; the extraction from news text into facts is outside the proof boundary.

**8.2 Recommended formal semantics for the four verdicts (design proposal built on proven results)**

Objects:
- A finite ground, tight, normal logic program P (equivalently a flat ABA framework). Atoms include:
  - facts reported(r, s, lit, t), copy_of(r, r'), tier(s, k), time facts;
  - assumptions encoded as ok(r) :- not defeated(r);
  - bridge rules holds(lit) :- reported(r, _, lit, _), ok(r);
  - defeat rules, e.g. defeated(r) :- reported(r, _, lit, _), holds(neg(lit)), outranks_or_equal(r', r), with the preference policy explicit;
  - strict domain constraints, e.g. refuted(H) :- trigger(H, ev), holds(time(ev, t1)), move_onset(t0), t1 > t0, with comparisons pre-evaluated into ground facts;
  - explanation schemas expl(H) :- trigger(H, ev), holds(occurred(ev)), precedes(ev, move), signature_ok(H), not refuted(H).
- SM(P) is the set of stable models of P.

Per model M and explanation H:
- status_M(H) = IN if expl(H) ∈ M;
- status_M(H) = OUT if refuted(H) ∈ M;
- status_M(H) = NONE otherwise.

The "not refuted(H)" guard makes IN and OUT exclusive within any M. This is a rationality property, provable in Lean as a lemma about the schema.

Profile: Prof(H) = {status_M(H) : M ∈ SM(P)}. Precondition: SM(P) ≠ ∅, otherwise see the fallback below. Equivalently, compute four bits with clingo's brave and cautious modes:
- bIN = brave(expl(H))
- cIN = cautious(expl(H))
- bOUT = brave(refuted(H))
- cOUT = cautious(refuted(H))

Verdicts (total and mutually exclusive):

| Verdict | Condition on the bits | Profile |
|---|---|---|
| SUPPORTED | cIN | Prof = {IN} |
| CONTRADICTED | cOUT | Prof = {OUT} |
| UNRESOLVED | bOUT ∧ ¬cOUT | {IN, OUT}, {OUT, NONE} or {IN, OUT, NONE} |
| CONSISTENT-BUT-UNPROVEN | ¬bOUT ∧ ¬cIN | {NONE} or {IN, NONE} |

- The asymmetric placement of {OUT, NONE} under UNRESOLVED, rather than CONSISTENT-BUT-UNPROVEN, implements Heuer's disconfirmation emphasis: any coherent refuting reading is surfaced.
- The asymmetric placement of {IN, NONE} under CONSISTENT-BUT-UNPROVEN implements skeptical caution about "supported".
- Report the raw profile (7 possible values) internally and in the provenance record, so downstream users can re-project it.
- Sub-flag: core-SUPPORTED / core-CONTRADICTED when expl(H) / refuted(H) is true in the well-founded model (the grounded core). It is unique and polynomial, and robust to every choice among rival readings.
- Fallback: if SM(P) = ∅ (odd cycles), emit INCOHERENT-EVIDENCE with a certified UNSAT proof that no stable model exists. Then report verdicts from the well-founded / grounded labelling only: true -> SUPPORTED or CONTRADICTED, undefined -> UNRESOLVED if there are arguments both ways, otherwise CONSISTENT-BUT-UNPROVEN. Optionally use preferred / regular-model semantics, flagged as uncertified at the Π2P level.

Decidability and complexity (ground program size n; all results proven in the cited literature):
- Each of bIN and bOUT is NP-complete, and each of cIN and cOUT is coNP-complete (normal programs). The verdict is a fixed Boolean combination of four such queries, so it is in Θ2P (it lies in the Boolean hierarchy over NP), and it is decidable with at most 4 SAT calls per explanation plus 1 existence check.
- The well-founded / grounded core is polynomial: quadratic alternating fixpoint, and P-complete.
- Grounding non-ground templates is polynomial for bounded rule arity (a design constraint to impose).
- If tightness is violated (positive loops), stable-model reasoning stays NP / coNP, but the SAT translation needs loop formulas or ranking encodings. Keep the rule language tight by design.
- Disjunctive rules would raise everything to Σ2P / Π2P; forbid them.

**8.3 Recommended encoding of evidence and explanations (design proposal)**

- Evidence atoms are reified, timestamped and attributed: reported(report_id, source_id, literal, t_report). Literals are drawn from a fixed, typed vocabulary such as occurred(event_id), magnitude(event_id, bucket), time(event_id, bucket), entity_affected(event_id, ticker). Fixed finite domains keep the program finite.
- Pre-processing (outside the proof boundary, logged as premises):
  - (i) syndication / copy detection, producing copy_of facts, with origins kept as the only independent witnesses;
  - (ii) source reliability tiers, producing tier facts (truth discovery or historical accuracy);
  - (iii) numeric comparisons evaluated into ground facts (before(t1, t0), abnormal_return_exceeds(threshold)).
- Defeasible acceptance: ok(r) as an ABA assumption.
  - Contraries: an accepted contradicting report of higher or equal tier from an independent origin (equal tier yields mutual defeat, hence two stable models, hence UNRESOLVED).
  - Undercutters: retraction(r), anonymous_sourcing(r) for high-stakes literals, copy_of(r, r') (so r adds no support beyond r'), and Schum-style credibility defeaters.
- Explanations are a fixed enumerated set H1..Hk plus H_other, each with a schema:
  - (a) required trigger literals (AC1-like);
  - (b) temporal precedence, a strict refuter if violated;
  - (c) predicted signatures (which assets, direction, timing) checked against market data facts — ACH-style consistency;
  - (d) a declared contrary set among the explanations (only where truly exclusive).
- Provenance:
  - For SUPPORTED: one canonical witness is not enough, because cautious entailment holds across all models. Give the derivation of expl(H) in the well-founded core if it exists, plus the UNSAT certificate showing that no stable model lacks expl(H), plus a deletion-minimal set of ok(r) assumptions whose acceptance forces expl(H). The last is computed by fixed-order deletion on assumption literals and is deterministic.
  - For UNRESOLVED: two canonical witnesses (lexicographically minimal models with IN and with OUT) and the reports on each side.
  - For CONTRADICTED: the refuting derivation and its UNSAT certificate.
  - Always: the ACH-style diagnosticity / sensitivity list (evidence items whose removal flips the verdict).

**8.4 Concrete verification pipeline**

Steps 1–3 run outside Lean:
1. Ingest and pre-process (unverified): NLP extraction -> reified facts; copy collapsing; tiers; numeric pre-evaluation. Output: ground program P (canonical serialization) plus the explanation list.
2. Solve (untrusted): clingo computes the well-founded core (or a simple native fixpoint), the stable-model existence check, and brave / cautious queries for expl(H_i) and refuted(H_i). It also extracts lexicographically minimal witnesses (optimization) and deletion-based minimal assumption cores (fixed order).
3. Certify negative answers (untrusted generation, trusted checking): emit CNF = Tseitin(Comp(P)) ∧ query-literal for each "no model with / without X" claim, run CaDiCaL with LRAT output, and keep the LRAT file.

Step 4 runs in Lean 4 (trusted: kernel, plus the compiler if native):
- Specification (proved once): GroundProgram, IsStableModel (Gelfond-Lifschitz), WellFounded / grounded labelling, Prof, Verdict. The definitions are literally the 8.2 table.
- Generic theorems (proved once):
  - (T1) checkStable sound;
  - (T2) Fages: Tight P -> (IsStableModel P M ↔ M |= Comp P);
  - (T3) Tseitin / CNF correctness for Comp P ∧ query;
  - (T4) soundness of Lean core's LRAT checker (exists);
  - (T5) grounded-certificate checker sound and complete;
  - (T6) the exclusivity lemma (IN and OUT never co-occur, from the "not refuted" guard);
  - (T7) verdict_of_certificates: given verified witnesses and refutations for the four bits, Verdict P H = v.
- Per incident, auto-generated: `theorem incident_123_H2 : Verdict P123 H2 = .unresolved := verdict_of_certificates ... (by native_decide)`. Use `decide` when the instance is small enough for kernel-only checking, or use Mathlib lrat_proof for the UNSAT parts.
- Audit: `#print axioms` on each verdict theorem shows exactly which trust assumptions were used (ofReduceBool or not).

Step 5 (publish): the verdict, the profile, the provenance bundle (witnesses, cores, sensitivity list), the Lean theorem name and axioms list, and hashes of P, the solver versions and the certificates.

**8.5 What is proven versus proposed**

Proven in the literature (cited above):
- Dung / Caminada semantics and their correspondences.
- The complexity of each semantics.
- ABA / LP stable semantics: NP / coNP.
- Grounded = well-founded, polynomial.
- Fages / Erdem-Lifschitz tightness theorem.
- LRAT linear-time checking.
- Lean core's verified LRAT checker and its compiler-trust caveat.
- Mathlib's kernel-only LRAT import.
- HP complexity results.
- ACH's empirical record.

Design proposals (not yet existing; to be built and verified):
- the verdict projection table in 8.2 and its asymmetric treatment of {OUT, NONE} and {IN, NONE};
- the explanation-schema encoding;
- the Lean formalization of ASP stable semantics, Fages' theorem, the Tseitin translation and the grounded-certificate checker;
- the claim that Yggdrasil-scale instances (10^3–10^4 atoms) certify in seconds natively, which is an estimate;
- the claim that kernel-only certification is feasible at that scale, which is unknown and must be benchmarked.

Explicitly outside any proof: claim extraction from news, copy detection, reliability tiers and the choice of explanation schemas. Lean proves "given P, the verdict is V", not that P faithfully represents the world.

**8.6 Expected scale limits (estimates)**

- Solving: no bottleneck at 10^3–10^5 ground rules for clingo / CaDiCaL on structured instances. Unsupported by benchmark here; consistent with the general maturity of SAT and ASP solvers.
- Native certification: comfortably within demonstrated LRAT-in-Lean volumes (lrat-catcher streamed 174 TB).
- Kernel-only certification: the likely bottleneck. Budget for benchmarking. Fallback policy: kernel-only for the grounded core (linear-size certificates) and native for the LRAT parts, with `#print axioms` recorded per verdict.
- Π2P semantics (preferred / semi-stable skeptical): avoid in the certified path. Certifying them needs CEGAR-style sequences of SAT calls, each with its own LRAT, and a formalized CEGAR soundness argument. That is feasible, but much more work for marginal semantic benefit over stable plus the grounded core.

### Gaps
- No empirical comparison was found of argumentation-based versus ACH or Bayesian verdicts on real news-conflict datasets (for any domain, let alone market forensics).
- No published Lean timing data for kernel-only LRAT or decide-based checkers at the 10^4–10^5 clause scale. This is the key unknown for the trust policy.
- No existing Lean library for ASP, ABA or Dung semantics was found. All Lean components in 8.4, except the LRAT checker, are new work.
- How often real Yggdrasil evidence programs will lack stable models (odd cycles from preference policies) is unknown. Measure it on historical incidents before deciding whether the stable-semantics fallback path needs its own certification.
