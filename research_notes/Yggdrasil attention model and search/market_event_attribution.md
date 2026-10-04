# Market Event Attribution: Prior Art and Methods for "Market Event Forensics" (Yggdrasil)

Scope note: research conducted 2026-10-03. Every source is tagged with its year. "(agg.)" marks an aggregator or syndicated copy rather than the original outlet. Formulas are plain text. Where a number differs across sources, both values are given.

## 1. Attributing large market moves to news: what is known, how studies coded explanations, and what share stays unexplained

### Takeaway
A century of studies agrees that many big moves cannot be tied to identifiable news. Estimates of the unexplained share include: about two-thirds of aggregate return variance not explained by macro news (Cutler, Poterba & Summers 1988/89); "many" large intraday futures moves with no matching event (Fair 2002); and 17% of US index jumps since 1900 with no identifiable reason in next-day newspapers, falling from about 35% to about 10% over 90 years (Baker, Bloom, Davis & Sammon, revised 2025). The best methodological template for Yggdrasil is Baker et al. They use multiple independent reads per jump, primary and secondary causes with fractional weights, an explicit "Unknown & No Explanation" category, recorded disagreement (coders may "agree to disagree"), and a composite clarity index. No classic study gives each competing explanation its own evidential label (supported, contradicted, and so on). That is the gap Yggdrasil targets.

### Cited Findings
**Classic studies (1971-2002)**
- Niederhoffer, "The Analysis of World Events and Stock Prices", Journal of Business 44(2), April 1971, pp. 193-219 — [IDEAS/RePEc (1971)](https://ideas.repec.org/a/ucp/jnlbus/v44y1971i2p193-219.html). Baker et al. (2025) say Niederhoffer (1971) and Cutler et al. (1989) "considered major jumps to assess whether they could be explained by identifiable news events, reaching mixed conclusions" — [Baker et al., NBER w28687 rev. May 2025](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf).
- Cutler, Poterba & Summers, "What Moves Stock Prices?" (NBER WP 2538, March 1988; published in J. Portfolio Management 1989). Abstract: it is "difficult to explain more than one third of the return variance" from macroeconomic news, and "large market moves often occur on days without any identifiable major news releases" — [NBER w2538 (1988)](https://www.nber.org/papers/w2538).
- Their method, as described in secondary accounts: they used the World Almanac and New York Times front-page or lead-business stories to define "big news", then searched the NYT for explanations of the largest daily S&P 500 moves — [NY Fed EPR, Fleming & Remolona (1997)](https://www.newyorkfed.org/medialibrary/media/research/epr/97v03n4/9712flem.html). Note: the NBER PDF at nber.org/papers/w2954 is Schwert's "Stock Volatility and the Crash of '87" (1989), not Cutler et al. Do not cite it for CPS.
- Fair, "Events That Shook the Market", Journal of Business 75(4), Oct 2002, pp. 713-732. It uses tick data on S&P 500 futures (1982-1999) and newswire searches to match events to large 1- to 5-minute price changes. It identifies 69 events behind large changes, 53 of them directly or indirectly related to monetary policy. "Many large stock price changes have no events associated with them" — [Fair (2002) abstract, Yale](https://fairmodel.econ.yale.edu/rayfair/pdf/2000a.htm); [IDEAS (2002)](https://ideas.repec.org/a/ucp/jnlbus/v75y2002i4p713-732.html).
- Mangee (2015) re-examined Fair (2002) using Bloomberg News market reports (conference presentation; findings not available online) — [Georgia Southern (2015)](https://digitalcommons.georgiasouthern.edu/finance-facpres/12).

**Baker, Bloom, Davis & Sammon, "What Triggers Stock Market Jumps?" (NBER w28687, April 2021, revised May 2025)**
- Two versions exist with different headline numbers. The 2021 version covered about 6,200 jumps in 16 markets and found newspapers attribute one-third of national jumps to US developments — [SIEPR page (2021)](https://siepr.stanford.edu/publications/working-paper/what-triggers-stock-market-jumps). The May 2025 revision covers 8,049 daily jumps across 19 national markets plus 455 US bond-market jumps (1970-2020), and attributes 38% of jumps in national markets to US economic and policy developments — [NBER w28687 rev. 2025](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf). Cite the version explicitly.
- Jump definition: the US market moves at least 2.5% up or down, close to close. That gives 1,179 jumps from 1900 to 2023. They are 3.5% of trading days but about 20% of total absolute daily variation and half of daily quadratic variation. Thresholds for other countries range from 2% to 4%, higher for more volatile markets — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf).
- Justification for the threshold: for 389 days in 1945-2019 with moves between 2.0% and 2.5%, 17.2% of next-day accounts give no explanation, versus 9.6% for jumps above 2.5%. In a small random sample of non-jump days, 43% of next-day accounts give no explanation — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf).
- Unexplained share: "In our US sample back to 1900, 17 percent of jumps occur for no identifiable reason." Over 90 years, "the share of jumps due to unknown forces fell from about 35 percent to 10 percent" in both the US and UK — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf).
- Distribution of causes: over 36% of US jumps reflect policy developments, more than macro news (23.5%) and corporate news (11.2%) combined. Globally, policy accounts for 28% — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf).
- Coding protocol:
  - 17 categories, including "Unknown & No Explanation".
  - Coders also rate journalist confidence and ease of coding.
  - Only articles published before the market reopens the next day are used. Pieces under 300 words are excluded. The first qualifying article is used.
  - US papers: WSJ, NYT, Washington Post, Chicago Tribune, FT, LA Times.
  - More than 45 trained readers. Each passed a 50-article test pre-coded by the authors; those who failed were dropped.
  - Codings are public at stockmarketjumps.com.
  — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf)
- Handling multiple explanations:
  - Coders assign a primary reason and, if warranted, a secondary one. A tertiary reason is allowed but not used.
  - If an article lists several reasons without ranking them, order of appearance breaks the tie.
  - Weights: primary = 1 if there is no secondary; otherwise primary = 0.75 and secondary = 0.25. These are averaged over reads, then over jumps.
  — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf)
- Handling disagreement:
  - Each US jump gets 4-6 newspapers and 8-10 distinct reads.
  - Disagreements go to a group meeting. Misreadings are corrected. Genuine ambiguity triggers a search for another article in the same paper. Otherwise "we let the original classifications stand, effectively letting the coders agree to disagree. Our final dataset reflects these disagreement cases."
  - Example: the 26 Dec 2018 jump is low-clarity because "some papers explicitly attribute it to unknown forces, others offer a variety of reasons, and newspapers disagree."
  — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf)
- Clarity index:
  - Four components: (i) pairwise agreement across reads, where two "Unknown" reads count as disagreement "to avoid treating hard-to-explain jumps as high-clarity events"; (ii) mean journalist confidence; (iii) ease of coding; (iv) the fraction of reads naming a known reason.
  - Each component is z-scored, summed, and re-z-scored.
  - A 1 s.d. rise in clarity goes with a 0.64 s.d. rise in intraday concentration of the move.
  - Low-clarity jumps have 15-24% higher volatility 3-10 days before and 8-10% higher 3-10 days after.
  - The post-jump clarity coefficient loses significance once pre-jump volatility controls are added.
  — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf)

**Firm-level and modern evidence**
- Boudoukh, Feldman, Kogan & Richardson (NBER 2013 digest of "Which News Moves Stock Prices?"):
  - Data: S&P 500 firms, 2000-2009, more than 1.9M Dow Jones Newswire stories, of which about 50% were identified as relevant events.
  - Taxonomy: 14 event categories and 56 subcategories.
  - "The volatility of stock prices on identified news days is over twice that of other days." No-news days and unidentified-news days have similar volatility.
  — [NBER Digest (June 2013)](https://www.nber.org/digest/jun13/which-news-moves-stock-prices)
- Boudoukh et al., "Information, Trading, and Volatility: Evidence from Firm-Specific News", RFS 32(3), 2019, pp. 992-1033:
  - Sample: 896 S&P 500 firms, 2000-2015, Dow Jones Newswire.
  - Fundamental news explains 49.6% of overnight idiosyncratic volatility and 12.4% during trading hours.
  - "Complex" days (multiple news types) are 27% of overnight news days but explain 32.4% of overnight idiosyncratic variance (6.1% intraday).
  — [HUJI CRIS (2019)](https://cris.huji.ac.il/en/publications/information-trading-and-volatility-evidence-from-firm-specific-ne/); [CFA Digest (2019)](https://rpc.cfainstitute.org/research/cfa-digest/2019/08/dig-v49-n8-2)
- Brogaard, Nguyen, Putnins & Wu, "What Moves Stock Prices? The Roles of News, Noise, and Information", RFS 35(9), 2022:
  - Variance decomposition: 31% noise, 24% private firm-specific information, 37% public firm-specific information, 8% market-wide information.
  - Noise has declined since the mid-1990s.
  — [IDEAS (2022)](https://ideas.repec.org/a/oup/rfinst/v35y2022i9p4341-4386..html)
- Jeon, McCurdy & Zhao, "News as Sources of Jumps in Stock Returns", JFE 145(2), 2022:
  - 21 million articles covering more than 9,000 firms.
  - Jump intensity and jump-size distributions are significantly related to news frequency and content, and the effect has grown over recent decades.
  - Sensitivity is stronger for firms with high media visibility, analyst coverage, and institutional ownership.
  — [IDEAS (2022)](https://ideas.repec.org/a/eee/jfinec/v145y2022i2p1-17.html)
- Lee & Mykland, RFS 2008: detected intraday jumps matched against Factiva (WSJ, FT, Dow Jones, Reuters). For individual stocks, "except in one or two cases, jumps were always associated with news events", and a majority were unscheduled company-specific news rather than earnings. Caveat: the sample was small (three months, a few stocks) — [Lee & Mykland (2008) PDF](https://www.scheller.gatech.edu/directory/research/finance/lee/pdf/leemykland08.pdf).
- Chan, "Stock Price Reaction to News and No-News: Drift and Reversal After Headlines", JFE 2003: strong drift after bad news, and reversal after extreme moves with no public news, mainly in small illiquid stocks — [SUFE abstract (2003)](https://academicnewsletter.sufe.edu.cn/info/357702).

### Inferences
- The unexplained share depends on the unit of analysis. It is high for aggregate index days without newswire matching (CPS 1988; Fair 2002) and much lower for single stocks with dense newswire coverage and intraday timing (Lee & Mykland 2008; Boudoukh et al. 2019). For a large-cap single-stock event like NVDA on 2025-01-27, Yggdrasil should usually find candidate news. The hard part is choosing among competing candidates, not finding any candidate.
- Baker et al.'s structure maps almost one-to-one onto Yggdrasil's outputs:
  - "Unknown & No Explanation" corresponds to "we do not know".
  - Primary/secondary weighting (0.75/0.25) gives a baseline for ranking competing hypotheses.
  - "Agree to disagree" corresponds to "unresolved".
  - The clarity index (agreement, confidence, ease, known-reason share) is a ready template for an explanation-uncertainty score. Counting "Unknown + Unknown" as disagreement is a useful guard against false confidence.
- Chan (2003) suggests a falsifiable downstream check. If no-news extreme moves tend to reverse while news-driven moves drift, post-event price paths can be a weak validation signal for "explained" versus "unexplained" labels. It should only be used for retrospective evaluation, never as a forecast, consistent with Yggdrasil's no-forecasting constraint.
- Boudoukh et al.'s "complex news days" (several news types at once) are the firm-level analogue of competing explanations. They carry a disproportionate share of variance, so multi-hypothesis output is the normal case, not an edge case.

### Gaps
- I could not retrieve Niederhoffer (1971) full text (JSTOR) to confirm his method or the share of unexplained moves.
- I could not confirm from full text CPS's list of the 50 largest moves or how many lacked news. The NBER w2538 abstract is the only primary source used. The PDF found was a scanned file of a different paper.
- Fair (2002): the exact count of large price changes with no matched event was not retrievable. The Yale PDF is scanned, and the Mangee (2015) reexamination is not online.
- No study found explicitly labels each competing explanation as supported, contradicted, or unresolved. Baker et al. come closest by recording disagreement and clarity.

## 2. Defining an abnormal market event rigorously (event studies, jump tests, volume and volatility anomalies, robust z-scores)

### Takeaway
Two families of methods are standard. Daily event-study abnormal returns (market or factor model, with SAR, BMP, and Kolari-Pynnönen tests) say whether a day's move is abnormal relative to the stock's own systematic exposure. High-frequency jump tests (Lee-Mykland 2008, Barndorff-Nielsen-Shephard 2006) locate when a discontinuity happened, intraday. A defensible Yggdrasil trigger combines a standardized abnormal return or robust z on the daily residual, an intraday Lee-Mykland timestamp, and an abnormal-volume confirmation. It also handles event-date clustering, since on 2025-01-27 many AI-exposed names fell together.

### Cited Findings
- MacKinlay, "Event Studies in Economics and Finance", Journal of Economic Literature 35(1), March 1997, pp. 13-39. It is the canonical reference: normal-return model (the market model is most common), estimation window, event window, abnormal and cumulative abnormal returns — [IDEAS (1997)](https://ideas.repec.org/a/aea/jeclit/v35y1997i1p13-39.html).
- Standard formulas — [EventStudyTools methodology page (accessed 2026)](https://www.eventstudytools.com/methodology/test-statistics):
  - AR_i,t = R_i,t - (alpha_i + beta_i * R_m,t), with alpha and beta from OLS over the estimation window.
  - CAR_i = sum of AR_i,t over the event window [T1+1, T2].
  - Estimation window typically 120-250 trading days; event window typically 1-5 days.
  - SAR_i,0 = AR_i,0 / S_AR_i,0, where S_AR_i,0^2 = S_AR_i^2 * [1 + 1/M_i + (R_m,0 - mean(R_m))^2 / sum_t (R_m,t - mean(R_m))^2]. This is the prediction-error correction.
  - Single-firm tests: t = AR_i,t / S_AR_i. For the CAR, t = CAR_i / S_CAR_i with S_CAR_i^2 = L2 * S_AR_i^2. These tests are "sensitive to event-induced volatility and non-normality."
  - BMP (standardized cross-sectional) test: t = sqrt(N) * mean(SAR_0) / S(SAR_0). It is robust to event-induced variance.
  - Kolari-Pynnönen adjustment: z_adj = z * sqrt((1 - r_bar) / (1 + (N-1) * r_bar)), where r_bar is the mean pairwise correlation of estimation-window abnormal returns. Used when events cluster on the same date.
  - Non-parametric alternatives: Corrado rank test, generalized sign test, generalized rank test. Recommended practice is to report one parametric and one non-parametric test.
- Boehmer, Musumeci & Poulsen (1991, JFE): even small event-induced variance increases make common tests over-reject the null of zero abnormal return — [SMU (1991)](https://ink.library.smu.edu.sg/lkcsb_research/4666).
- Kolari & Pynnönen (2010, RFS): with event-date clustering, "even relatively low cross-correlation among abnormal returns is serious in terms of over-rejecting the null." They propose a cross-correlation-adjusted BMP statistic — [SSRN (2010)](https://papers.ssrn.com/abstract=1830364).
- Lee & Mykland, "Jumps in Financial Markets: A New Nonparametric Test and Jump Dynamics", RFS 21(6), 2008, pp. 2535-2563 — [paper PDF (2008)](https://www.scheller.gatech.edu/directory/research/finance/lee/pdf/leemykland08.pdf):
  - L(i) = log(S(t_i)/S(t_{i-1})) / sigma_hat(t_i).
  - sigma_hat(t_i)^2 = (1/(K-2)) * sum_{j=i-K+2}^{i-1} |log(S(t_j)/S(t_{j-1}))| * |log(S(t_{j-1})/S(t_{j-2}))|. This is local bipower variation, robust to earlier jumps.
  - Recommended K: 7 (weekly data), 16 (daily), 78 (hourly), 110 (30-min), 156 (15-min), 270 (5-min).
  - Rejection rule: reject "no jump at t_i" if (|L(i)| - C_n)/S_n > beta*, where C_n = (2 log n)^(1/2)/c - (log pi + log(log n)) / (2c (2 log n)^(1/2)), S_n = 1/(c (2 log n)^(1/2)), c = E|U| = sqrt(2/pi) ≈ 0.7979, and n is the number of observations.
  - beta* = -log(-log(1 - alpha)), so beta* = 4.6001 at alpha = 1%.
- Barndorff-Nielsen & Shephard, "Econometrics of Testing for Jumps in Financial Economics Using Bipower Variation", Journal of Financial Econometrics 4(1), 2006, pp. 1-30. It gives nonparametric tests of continuous sample paths by comparing realized variance with bipower variation. Most detected FX jumps were tied to macroeconomic announcements. An R implementation exists (highfrequency::BNSjumpTest) — [IDEAS WP (2003/2006)](https://ideas.repec.org/p/nuf/econwp/0321.html); [R docs](https://rdrr.io/cran/highfrequency/man/BNSjumpTest.html).
- Robust z-score (Iglewicz & Hoaglin, via NIST): M_i = 0.6745 * (x_i - median(x)) / MAD, where MAD is the median absolute deviation. Label |M_i| > 3.5 as a potential outlier — [NIST/SEMATECH e-Handbook](https://itl.nist.gov/div898/handbook/eda/section3/eda35h.htm).
- Baker et al. (2025) set index-level thresholds by market volatility (2-4%). They also note that high-clarity jumps are more concentrated intraday, so intraday concentration "could itself serve as a proxy for clarity" and "is easily automated" — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf).

### Inferences
Recommended concrete triggers. These are my synthesis from the cited methods; thresholds are design choices to calibrate.

- **T1. Daily abnormal-return trigger (primary).**
  - Fit AR_i,t = R_i,t - (alpha_i + beta_i * R_m,t + gamma_i * R_sector,t) by OLS on [t-260, t-11] trading days. The 10-day gap keeps leakage from the run-up out of the estimation window. Including a sector ETF factor means a sector-wide shock is not mistaken for a firm-specific one.
  - Compute SAR_t with the prediction-error correction above.
  - Fire if |SAR_t| >= 4. Also fire if the robust z on residuals is high: M_t = 0.6745 * (AR_t - median(AR_window)) / MAD(AR_window), with |M_t| >= 5 for a stringent default or 3.5 for a sensitive mode.
  - Report both, because fat tails make the normal-based SAR over-fire.
- **T2. Raw-move trigger (fallback for thin history).** Fire if |R_i,t| >= k_i, where k_i scales with the stock's trailing volatility. This mirrors Baker et al.'s 2-4% thresholds by market volatility. For a single stock, use something like k_i = max(2.5%, 4 * sigma_hat_60d), where sigma_hat is a robust estimate (1.4826 * MAD of daily returns).
- **T3. Intraday timestamp (localization).** Run Lee-Mykland on 5-minute returns with K = 270 and alpha = 1%. Record each t_i where (|L(i)| - C_n)/S_n > 4.6001. The timestamp is what links the move to news published before t_i. It is the key defence against hindsight attribution.
- **T4. Daily jump-share diagnostic.**
  - RV_t = sum_j r_j^2 and BV_t = (pi/2) * sum_{j>=2} |r_j| * |r_{j-1}| on intraday returns.
  - RJ_t = (RV_t - BV_t)/RV_t is the jump share of the day's variance.
  - Use the BNS test (e.g., highfrequency::BNSjumpTest) for significance. I did not re-derive the exact BNS ratio-statistic variance constant this session, so take it from the implementation.
  - A high RJ with a single Lee-Mykland timestamp suggests a discrete trigger. A low RJ with a large daily AR suggests a diffuse, narrative-driven repricing. Per Baker et al., the second case is harder to explain and should lower stated confidence.
- **T5. Abnormal-volume confirmation.** Use v_t = log(share volume_t) or log turnover. Compute M_v = 0.6745 * (v_t - median(v over [t-60, t-1])) / MAD and confirm if M_v >= 3.5. Price moves without volume confirmation should get lower priority.
- **T6. Clustering handling.** If many stocks in a peer set fire on the same day (on 2025-01-27: NVDA, AVGO, VST, CEG, ASML and others), open one cluster event plus per-stock sub-events. Apply the Kolari-Pynnönen correction to any cross-sectional significance test, and search the narrative graph for a shared driver before searching for idiosyncratic ones.
- **Gating rule.** Open a forensic case if T1 fires (or T2 when history is short) AND (T3 finds at least one jump OR T5 fires). Store the T3 timestamps, because they set the information cutoff used in Section 4.

### Gaps
- I did not fetch a primary source for abnormal-volume event-study conventions (e.g., Campbell & Wasley 1996, Ajinkya & Jain 1989). T5 is my own construction from the robust z-score method.
- I did not research implied-volatility or options-based anomaly triggers.
- I did not obtain MacKinlay's full text (the JSTOR scan has no text layer). Formulas come from EventStudyTools' documentation rather than the paper itself.
- I did not compute NVDA's actual SAR or Lee-Mykland statistics for 2025-01-27; that needs price data.

## 3. How narrative and attention measures have been built in finance

### Takeaway
Finance has moved through three generations of measures:
- Dictionary tone from single columns (Tetlock 2007).
- Attention proxies from search and news volume (Da, Engelberg & Gao 2011; EPU 2016; NVIX 2017).
- Topic-attention indices over full news archives (Bybee, Kelly, Manela & Xiu, JF 2024), plus firm co-mention networks that capture attention spillovers (Guo, Peng, Tao & Tu 2018; Scherbina & Schlusche).

Shiller (2017, AER) supplies the theory that narratives spread epidemically. Flynn & Sastry (NBER 2024) give the first quantitative evidence of narrative contagion between firms with macro effects. GDELT-based finance work exists but sits mostly in lower-tier venues and theses.

### Cited Findings
- Tetlock, "Giving Content to Investor Sentiment", JF 2007. He applies dictionary-based pessimism to the WSJ "Abreast of the Market" column for 1984-1999 (more than 3,700 editions). High media pessimism predicts downward price pressure followed by reversion to fundamentals. Unusually high or low pessimism predicts high trading volume — [Tetlock (2007) PDF](https://www.columbia.edu/~pt2238/papers/Tetlock_Media_Sentiment_JF.pdf).
- Da, Engelberg & Gao, "In Search of Attention", JF 2011. Sample: Google Search Volume Index (SVI) for Russell 3000 stocks, 2004-2008. SVI captures attention more promptly than existing proxies and likely measures retail attention. A rise in SVI predicts higher prices over the next two weeks and an eventual reversal within the year. It also contributes to IPO first-day returns and long-run underperformance — [paper PDF (2011)](https://rady.ucsd.edu/faculty/directory/engelberg/pub/portfolios/GOOGLE.pdf); [EconBiz (2011)](https://econbiz.de/Record/in-search-of-attention-zhi/10010626242).
- Shiller, "Narrative Economics", AEA Presidential Address, 7 Jan 2017, published in AER April 2017. It treats narratives as having an epidemiology: they "go viral" and drive fluctuations such as the 1920-21 depression, the Great Depression, and the Great Recession. It argues economics should study changing popular narratives quantitatively — [NBER w23075 (2017)](https://www.nber.org/papers/w23075.pdf); [AEA program (2017)](https://www.aeaweb.org/conference/2017/preliminary/1626).
- Bybee, Kelly, Manela & Xiu, "Business News and Business Cycles", JF 79(5), Oct 2024; earlier NBER w26648 "The Structure of Economic News", Jan 2020. A topic model on about 800,000 WSJ articles (1984-2017) measures the share of news attention per theme over time. News attention tracks economic activity, forecasts aggregate stock returns, and adds incremental power in a text-augmented VAR — [WashU profile (2024)](https://profiles.wustl.edu/en/publications/business-news-and-business-cycles/); [NBER w26648 (2020)](https://www.nber.org/papers/w26648).
- Baker, Bloom & Davis, "Measuring Economic Policy Uncertainty", QJE 2016. The EPU index counts newspaper coverage frequency and was validated by human audits of 12,000 articles. Policy uncertainty is linked to higher stock volatility and lower investment and employment in policy-sensitive sectors — [NBER w21633 (2015/2016)](https://nber.org/papers/w21633).
- Manela & Moreira, "News Implied Volatility and Disaster Concerns", JFE 2017. NVIX uses word frequencies on the WSJ front page to extend VIX back to 1890. It is high during crashes, wars, and policy uncertainty, and predicts above-average returns or disasters — [OSU PDF (2017)](https://files.fisher.osu.edu/department-finance/public/news_implied_volatility_and_disaster_concerns.pdf).
- Guo, Peng, Tao & Tu, "News Co-Occurrence, Attention Spillover and Return Predictability" (SMU/Baruch WP, Nov 2018; arXiv 1703.02715):
  - Joint news coverage triggers attention spillover across firms, "a contagion in investor attention that causes marketwide overvaluations and subsequent reversals."
  - The News Network Triggered Attention (NNTA) index negatively predicts market returns (monthly in-sample R2 5.97%, out-of-sample 5.80%).
  - A co-occurrence long-short portfolio earns 68 bp/month alpha.
  — [arXiv 1703.02715](https://arxiv.org/pdf/1703.02715)
- Scherbina & Schlusche, "Economic Linkages Inferred from News Stories": firms co-mentioned in news cross-predict each other's returns (Brandeis WP; year not confirmed on the page) — [Brandeis ScholarWorks](https://scholarworks.brandeis.edu/esploro/outputs/workingPaper/Economic-linkages-inferred-from-news-stories/9924037131801921).
- Flynn & Sastry, "The Macroeconomics of Narratives", NBER w32602, June 2024. They use NLP proxies for narratives in 10-Ks. Firms' hiring responds to narratives, and narratives spread contagiously among firms with intensity that depends on macro conditions. Optimistic narratives lead to expansion despite having no predictive power for fundamentals. Narrative optimism accounts for about 32% of the output decline in the early-2000s recession and 18% in the Great Recession — [NBER w32602 (2024)](https://www.nber.org/papers/w32602).
- Jeon, McCurdy & Zhao (JFE 2022): news-flow frequency and content drive jump intensity, more so for high-visibility firms — [IDEAS (2022)](https://ideas.repec.org/a/eee/jfinec/v145y2022i2p1-17.html).
- GDELT in finance:
  - BBVA Research (2022) built five GDELT measures for Chinese stock markets: Tone, Optimism, Attention, Tone Dispersion, Emotional Polarity. All have significant predictive power for returns and volatility, and sentiment-augmented EGARCH improves forecasts — [BBVA Research (2022)](https://www.bbvaresearch.com/en/publicaciones/measuring-news-media-sentiment-using-big-data-for-chinese-stock-markets).
  - A DCU study used GDELT frequency and tone from more than 500,000 Brexit news items (2015-2018) to forecast FTSE 100 conditional variance — [DCU repository](https://doras.dcu.ie/25442).
  - The GDELT blog lists thesis-level S&P 500 narrative studies — [GDELT blog](https://blog.gdeltproject.org/?p=17120).
- RavenPack, the commercial standard for academic event data on WRDS, provides an Event Novelty Score (0-100, novelty within a 24-hour window). Its daily sentiment weights events by (relevance/100)^2 × (novelty/90)^2, as documented — [Bigdata.com docs (2025/26)](https://docs.bigdata.com/blog/market-data/entity-sentiment-signals); [WRDS](https://wrds-www.wharton.upenn.edu/pages/news/enhanced-ravenpack-analytics-gives-researchers-extensive-scope-and-depth-of-events/).

### Inferences
- For a stock-agnostic narrative graph, the closest academic analogue is a fusion of Bybee et al.'s topic-attention shares (node-level attention over time) with Guo et al.'s co-occurrence network (edges that carry attention spillover). Attention to a topic such as "AI efficiency" or "China AI" can spill to firms without them being named. That is what happened to utilities such as Vistra and Constellation on 2025-01-27, through a "data-center power demand" narrative edge.
- Da-Engelberg-Gao and Shiller jointly give a testable mechanism for the DeepSeek one-week lag. Information arrived on 2025-01-20 (R1). Retail and media attention spiked over the 2025-01-25/26 weekend (App Store #1, a viral blog post, Andreessen's "Sputnik moment"). Prices moved on the next trading session. Yggdrasil should track attention velocity separately from information arrival, because the two can be days apart.
- RavenPack's novelty score shows why novelty must be computed per narrative. Most "DeepSeek" stories on 2025-01-27 were not novel at the information level (V3 cost was public since 2024-12-27), but the attention surge was novel.
- GDELT-finance evidence is mostly from working papers and theses, so Yggdrasil should not treat it as proof that GDELT tone predicts returns. Forecasting is out of scope anyway. GDELT's value here is timestamped coverage, not predictive signal.

### Gaps
- Not verified this session: the exact number of topics in Bybee et al. (commonly reported as 180) and the details of Shiller's 2019 book "Narrative Economics" (Princeton University Press). Both are left out of the cited findings.
- I found no peer-reviewed top-journal paper using GDELT as the primary data source for equity attribution.
- I found no paper that builds a stock-agnostic narrative graph and then queries it after an equity event. That appears to be Yggdrasil's novel contribution.

## 4. Look-ahead and hindsight bias: point-in-time practice, LLM temporal leakage, and post-hoc search results

### Takeaway
Three leakage channels threaten an explanation system:
1. Data look-ahead: using information timestamped after the event.
2. Model look-ahead: LLM parametric memory of outcomes. Lopez-Lira et al. (2025) show LLMs reproduce pre-cutoff economic data and headlines exactly, and that neither instructions nor masking prevent it.
3. Retrieval look-ahead: search engines' date filters leak post-event content. In a 2026 audit of Google's "before:" filter, 71% of questions returned at least one page with substantial post-cutoff leakage, and 41% returned a page revealing the answer.

The DeepSeek episode falls within the training window of most current LLMs, so a replay is maximally exposed to all three. The fixes in the literature are frozen, timestamped corpora (which is what GDELT and RSS ingestion with crawl timestamps provide), chronologically consistent models, and anonymization.

### Cited Findings
- Glasserman & Lin, "Assessing Look-Ahead Bias in Stock Return Predictions Generated by GPT Sentiment Analysis", arXiv 2309.17322, Sept 2023. There are two biases: look-ahead (the LLM knows subsequent returns) and a "distraction effect" (general knowledge of the firm contaminates sentiment). In-sample, anonymized headlines outperform, implying distraction outweighs look-ahead, especially for large firms. They propose entity anonymization — [arXiv (2023)](https://arxiv.org/abs/2309.17322).
- Sarkar & Vafa, "Lookahead Bias in Pretrained Language Models" (SSRN 4754678, June 2024; ICML 2025). Direct tests find look-ahead bias in predicting risk factors from earnings calls and election winners from candidate biographies — [ICML 2025](https://icml.cc/virtual/2025/48685); [CXO Advisory summary](https://www.cxoadvisory.com/investing-expertise/lookahead-bias-in-large-language-model-training-data).
- He, Lv, Manela & Wu, "Chronologically Consistent Large Language Models" (arXiv 2502.21206, Feb 2025, updated through mid-2025; AEA/AFA 2026 program). ChronoBERT and ChronoGPT are trained only on text available at each point in time. In next-day return prediction from news, their Sharpe ratios are comparable to a much larger Llama model, "indicating that lookahead bias is modest" in that application — [arXiv (2025)](https://arxiv.org/html/2502.21206v3); [AEA 2026 program](https://www.aeaweb.org/conference/2026/program/paper/BrRDGQHe). A follow-up on instruction-tuning chronologically consistent models exists (arXiv 2510.11677, Oct 2025) — [HF papers](https://huggingface.co/papers/2510.11677.md).
- Lopez-Lira, Tang & Zhu, "The Memorization Problem: Can We Trust LLMs' Economic Forecasts?" (SSRN 5217505 / arXiv 2504.14765, April 2025):
  - LLMs perfectly recall exact values of key economic variables, news headlines, stock returns, and conference-call content from before their cutoff.
  - "Instructions to respect historical boundaries fail to prevent recall-level accuracy, and masking fails as LLMs reconstruct entities and dates from minimal context." After the cutoff, no recall is observed.
  - Forecasting skill is "non-identified" when the model has seen the realized values.
  — [SSRN (2025)](https://papers.ssrn.com/abstract=5217505); [arXiv (2025)](https://arxiv.org/html/2504.14765v2)
- DatedGPT (arXiv 2603.11838, March 2026): twelve 1.3B-parameter models, each trained from scratch on about 100B tokens with strict annual cutoffs from 2013 to 2024, built for leak-free financial backtests — [arXiv (2026)](https://arxiv.org/html/2603.11838v1). Related 2026 work: "All Leaks Count, Some Count More: Interpretable Temporal Contamination Detection in LLM Backtesting" (arXiv 2602.17234) — [arXiv (2026)](https://arxiv.org/html/2602.17234v1); "Evaluating LLMs in Finance Requires Explicit Bias Consideration" (arXiv 2602.14233) — [arXiv (2026)](https://arxiv.org/html/2602.14233). (Only titles and abstracts were seen for these two 2026 papers.)
- Paleka et al., "Pitfalls in Evaluating Language Model Forecasters" (arXiv 2506.00723, May/June 2025). Many forecasting systems use search restricted to time T, but "document date metadata is often inaccurate allowing future data to leak in." The retrieval model itself may have been trained on future data — [arXiv (2025)](https://arxiv.org/html/2506.00723v1).
- El Lahib, Xia, Li, Wang & Pi, "Temporal Leakage in Search-Engine Date-Filtered Web Retrieval" (arXiv 2602.00758, 31 Jan 2026):
  - Audit: Google's "before:" filter on 393 resolved Metaculus questions, about 39,000 pages.
  - 71% of questions returned at least one page with substantial post-cutoff information. 41% returned a page that directly revealed the answer.
  - Brier score was 0.108 with leaked documents versus 0.242 with clean ones.
  - Leakage mechanisms: pages updated after publication, related-content modules, absence-based signals, and unreliable or stale self-reported timestamps.
  - Recommendation: "evaluation on frozen, time-stamped web snapshots."
  — [arXiv (2026)](https://arxiv.org/html/2602.00758v1)
- Point-in-time practice in the human-coded literature: Baker et al. use only articles published before the market reopens the next day. They note that in the internet era, articles often appear online after the close on the jump day itself — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf).

### Inferences
- Yggdrasil's ingestion design (a continuously built graph from GDELT and RSS, with Yggdrasil's own first-seen timestamps) is the right structural defence against retrieval look-ahead. It is effectively the "frozen, time-stamped snapshot" that El Lahib et al. (2026) recommend. Each graph node should carry: first_seen_ts (ingestion time), published_ts (source-claimed), and last_modified_ts if the page changed. Evidence used to explain an event at time t_event should require first_seen_ts < t_event (or < the T3 jump timestamp), not just published_ts < t_event, because self-reported dates are unreliable.
- For the DeepSeek replay, any LLM used for extraction or labeling almost certainly knows the outcome: NVDA's fall, the later rebound, the SemiAnalysis estimates, and the Nature paper. Mitigations from the literature, layered:
  - Restrict the LLM's role to extraction and entailment over supplied evidence, never open-ended "why did NVDA fall" generation.
  - Anonymize tickers, firms, and dates in evidence passages where possible (Glasserman & Lin 2023), while recognizing Lopez-Lira et al. (2025) show masking can fail.
  - Run a contamination probe: ask the model for the outcome with no evidence. If it answers correctly, flag the case as "memorization-exposed".
  - Where feasible, use a chronologically consistent model (ChronoGPT/DatedGPT-style) as a cross-check labeler.
- Yggdrasil should state two separate things in each report: which evidence existed before the move, and which evidence arrived after it. Post-move evidence (e.g., the SemiAnalysis hardware estimate of 2025-01-31, the Nature cost disclosure of 2025-09-17) can legitimately update the verdict on whether a hypothesis is true. It cannot be presented as what moved the price.

### Gaps
- I did not retrieve a canonical source on point-in-time financial databases (e.g., vintage fundamentals, survivorship bias in constituents) or on GDELT's own timestamp semantics and update cadence. Both should be verified separately.
- I found no study that measures look-ahead leakage specifically in "why did it move" explanation tasks, as opposed to return prediction or forecasting.

## 5. Commercial landscape: who explains why a stock moved, and where the gap is

### Takeaway
Commercial products fall into four groups:
- Single-narrative "why is it moving" explainers: Benzinga WIIM (human-curated), Robinhood Cortex Digests (genAI, 2025), Google Finance AI (Gemini, 2025), Perplexity Finance.
- Event-detection and sentiment feeds: RavenPack, Dataminr, Permutable.
- Cited research and search tools: AlphaSense, Bloomberg AI summaries, Google Deep Search.
- Entity and extraction infrastructure: Kensho.

None of the materials found shows a product that presents several competing explanations side by side, each labeled with supporting and contradicting evidence, or that outputs an explicit "unknown". Provenance (citations) is increasingly common. Contradiction tracking and calibrated uncertainty are absent from vendor descriptions. Independent evaluation of generative search citations shows only about half of sentences fully supported (Liu et al. 2023).

### Cited Findings
- **Benzinga "Why Is It Moving" (WIIM)**: real-time catalyst explanations covering earnings, analyst commentary, macro, company announcements, and breaking news, "in a format designed to be fast, clear, and actionable". The feed combines "trusted third-party news sources with human curation". It is syndicated into broker platforms such as Stake (press release; year not stated on page, likely 2025-26) — [Stake/Benzinga press release](https://www.yourwyominglink.com/benzinga-enhances-stake-platform-with-real-time-market-catalyst-insights/article_ba9bbdcc-6fcc-56d0-be30-13c0c1436e04.html).
- **Robinhood Cortex Digests** (US launch summer 2025; UK rollout 19 Aug 2025):
  - Generative AI reviews and synthesizes breaking news, analyst reports, technical signals, and Robinhood proprietary data into "a concise, plain-English summary that decodes why a stock may be moving" on the stock page.
  - Robinhood reports that 95% of surveyed users value its clarity, relevance, and ease of use (vendor self-report).
  — [Robinhood newsroom (2025)](https://robinhood.com/us/en/newsroom/digests-by-robinhood-cortex-uk); [tech.eu (2025)](https://tech.eu/2025/08/19/robinhood-launches-stock-picking-ai-summaries/)
- **Bloomberg** (15 Jan 2025): AI-Powered News Summaries put three bullet points atop Bloomberg News stories on the Terminal. They are "evaluated by the company's subject matter experts" to refine the LLM. The product follows AI earnings-call summaries. It summarizes articles; it does not attribute moves — [Bloomberg press (2025)](https://www.bloomberg.com/company/press/bloomberg-launches-gen-ai-summarization-for-news-content).
- **Google Finance AI** (2025): Gemini-based Q&A that can "investigate price movements" and "compare bullish and bearish cases"; "Why did NVIDIA move today?" is an example prompt. Deep Search (announced 6 Nov 2025) runs "hundreds of simultaneous searches", produces "fully cited" reports, and shows its research plan. Prediction-market data from Kalshi and Polymarket was added — [Google blog (2025)](https://blog.google/products/search/new-google-finance-ai-deep-search/); [PPC Land (2025)](https://ppc.land/google-finance-expands-ai-capabilities-with-deep-search-and-prediction-markets/).
- **Perplexity Finance**: live prices, "explanations of notable price movement", earnings, and historical data — [CO/AI (2024/25)](https://getcoai.com/news/perplexitys-new-finance-tool-makes-stock-research-a-breeze).
- **AlphaSense**: retrieval-augmented Generative Search and Smart Summaries over premium content (broker research, expert-call transcripts). "Each answer provides citations to the exact snippet of text," positioned as hallucination mitigation — [AlphaSense blog](https://www.alpha-sense.com/blog/product/essential-features-of-knowledge-discovery-tools/); [AlphaSense on hallucination](https://prod.alpha-sense.com/blog/product/combat-generative-ai-hallucination/).
- **RavenPack / Bigdata.com**: entity-level event detection with sentiment, relevance, novelty (ENS 0-100 within 24h), and market-impact scores. Bigdata.com adds chunk-level impact sentiment (-1 to +1) and delivers a tearsheet "inside Claude, ChatGPT, and Copilot" — [Bigdata.com docs (2025/26)](https://docs.bigdata.com/blog/market-data/entity-sentiment-signals).
- **Dataminr**: "earliest detection of market-relevant events" from over 1M public data sources in real time, delivered as structured alerts — [Dataminr Financial Services](https://www.dataminr.com/solutions/financial-services/).
- **Permutable**: processes "millions of daily narratives from more than 250,000 global information sources" into structured signals for systematic trading. It claims to detect when "narrative momentum evolves from temporary market noise into structural repricing" (vendor claim) — [Permutable](https://permutable.ai/systematic-traders-solutions/).
- **Kensho (S&P Global)**: infrastructure rather than explanation. NERD does named-entity recognition and disambiguation linking text to structured financial knowledge; Extract does document-to-structured-data conversion — [Kensho NERD docs](https://nerd.kensho.com/docs/); [Kensho product news](https://kensho.com/news/category/Product).
- Independent evidence on provenance quality: Liu, Zhang & Liang (2023) evaluated four generative search engines (Bing Chat, NeevaAI, Perplexity.ai, YouChat). "Only 51.5% of generated sentences" were fully supported by citations, and only 74.5% of citations supported their statement — [arXiv 2304.09848 (2023)](https://arxiv.org/abs/2304.09848).

### Inferences
- Gap 1, one story versus several. Explainer products answer "why is it moving" with one summary ("why a stock may be moving"). Even Google's bull-versus-bear comparison concerns outlook, not attribution. None of the descriptions found shows ranked competing causal hypotheses.
- Gap 2, contradictions. No vendor material describes surfacing evidence that contradicts an explanation. Example: the DeepSeek-V3 report itself saying the $5.576M excluded prior research. Citations are used to show support, not to test claims.
- Gap 3, abstention. No product found says "we do not know". By contrast, about 17% of US index jumps since 1900 had no identifiable reason even to contemporaneous journalists (Baker et al. 2025), so a calibrated system should abstain a material fraction of the time.
- Gap 4, temporal integrity. Explainers built on live web search inherit the date-filter leakage documented by El Lahib et al. (2026). No vendor describes enforcing a strict information cutoff at the price-jump timestamp.
- Gap 5, stock-agnostic pre-built graph. Event feeds (Dataminr, RavenPack, Permutable) detect events and narratives but do not do post-event forensic search with hypothesis labels. Explainers start from the ticker and search outward. Yggdrasil's "graph first, ticker second" design plus four-way labels is not described by any product found.
- Positioning risk: Robinhood, Google, and Perplexity have distribution and are fast-following (2025). Yggdrasil's defensibility lies in its epistemics (multi-hypothesis, contradiction, abstention, point-in-time provenance), not in summarization.

### Gaps
- I could not verify current product details for Accern (no usable result) or for any Bloomberg Terminal function that explicitly attributes price moves, beyond news summaries.
- I did not inspect what each product actually output for NVDA on 2025-01-27. Doing so (e.g., via archived pages) would be the strongest evidence for the gap claim.
- Vendor claims (Permutable's narrative-to-repricing detection, Robinhood's 95% satisfaction) are self-reported and unaudited.

## 6. Proof-of-concept case: DeepSeek and NVIDIA (2025-01-27), with dated facts and competing explanations

### Takeaway
The key primary-source facts were all public before the move. DeepSeek-V3's report (arXiv v1, 2024-12-27) disclosed 2.788M H800 GPU-hours, priced at $5.576M at $2/hour. It explicitly excluded "prior research and ablation experiments". R1 was released 2025-01-20 under an MIT license, with o1-parity claims. Yet NVDA did not fall 17% until Monday 2025-01-27, after a weekend attention surge: App Store #1 in the US on 2025-01-26, a viral short thesis dated 2025-01-24/25, and Andreessen's "Sputnik moment" post on 2025-01-26. Most competing explanations (cost skepticism, chip counts and export controls, distillation, Jevons rebuttal) emerged or were amplified on or after the move day. That makes the case a clean test of separating information arrival from attention arrival, and pre-move from post-move evidence.

### Cited Findings
**Pre-move primary facts**
- 2024-12-27 (04:03 UTC; US evening of 2024-12-26): DeepSeek-V3 technical report, arXiv 2412.19437v1. It describes a 671B-parameter MoE (37B active) trained on 14.8T tokens. Full training took "only 2.788M H800 GPU hours": 2,664K pre-training, 119K context extension, 5K post-training. At $2 per GPU-hour, the total is $5.576M. The report says verbatim: "Note that the aforementioned costs include only the official training of DeepSeek-V3, excluding the costs associated with prior research and ablation experiments on architectures, algorithms, or data." It cites a cluster of 2,048 H800 GPUs — [arXiv abstract (2024)](https://arxiv.org/abs/2412.19437v1); [arXiv HTML full text (2024)](https://arxiv.org/html/2412.19437v1).
  - Conflict: one aggregator says "DeepSeek-V3 model launched on Jan. 10" — [Plus500 (2025, agg.)](https://www.plus500.com/newsandmarketinsights/deepseek-triggers-tech-selloffs). This likely conflates the consumer app launch with the model release. Use the arXiv date for the model.
- 2025-01-20: "DeepSeek-R1 Release", with "Performance on par with OpenAI-o1", an MIT license, and API outputs usable for fine-tuning and distillation. Six distilled models were released, with 32B and 70B claimed on par with o1-mini. API pricing: $0.14/M input tokens (cache hit), $0.55/M (cache miss), $2.19/M output — [DeepSeek API docs (2025-01-20)](https://api-docs.deepseek.com/news/news250120).
- 2025-01-22: R1 paper, arXiv 2501.12948v1, "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning". It claims performance comparable to OpenAI-o1-1217 and open-sources R1-Zero, R1, and six distilled dense models (1.5B-70B) based on Qwen and Llama — [arXiv (2025)](https://arxiv.org/abs/2501.12948v1).
- 2025-01-21: Stargate announced, with up to $500B of AI infrastructure by 2029 (OpenAI, Oracle, SoftBank) — [Wikipedia, Stargate LLC (agg.)](https://en.wikipedia.org/wiki/Stargate_LLC).
- 2025-01-23: Scale AI CEO Alexandr Wang told CNBC at Davos, "My understanding is that DeepSeek has 50,000 H100s", which DeepSeek "can't talk about" because of export controls. This is an unverified claim — [OfficeChai (2025, agg. of CNBC)](https://officechai.com/ai/scale-ai-ceo-says-deepseek-had-50000-nvidia-h100-gpus-elon-musk-agrees/).
- 2025-01-24: Meta guided 2025 capex to $60-65B and said it would end the year with over 1.3M GPUs — [Yahoo Finance/AP (2025)](https://finance.yahoo.com/news/meta-invest-65-billion-capital-141439561.html).
- 2025-01-24 or 25 (sources differ): Jeffrey Emanuel, "The Short Case for Nvidia Stock". The post's own header says 25 Jan 2025 — [original post](https://youtubetranscriptoptimizer.com/blog/05_the_short_case_for_nvda); diginomica says 24 Jan — [diginomica (2025)](https://diginomica.com/node/28410).
  - Arguments: DeepSeek trained competitive models for about $5M with about 45x training efficiency and about 95% cheaper inference; threats from Cerebras/Groq and hyperscaler custom silicon; erosion of the CUDA moat; NVDA's roughly 20x forward sales valuation.
  - Spread: shared by Chamath Palihapitiya (1.8M followers) and Naval Ravikant (2.6M followers).
  - MarketWatch (via Slashdot) headlined "One Blogger Helped Spark NVIDIA's $600B Stock Collapse" — [Slashdot (2025-02-01)](https://tech.slashdot.org/story/25/02/01/2235213/).
- Friday 2025-01-24 to Monday morning 2025-01-27: DeepSeek app downloads doubled from about 1M to 2.6M across iOS and Google Play. On Sunday 2025-01-26 it reached No. 1 on the US App Store, ahead of ChatGPT, and was No. 1 in 51 other countries — [TechCrunch (2025-01-27)](https://techcrunch.com/2025/01/27/deepseek-displaces-chatgpt-as-the-app-stores-top-app).
- Sunday 2025-01-26: Marc Andreessen posted "DeepSeek-R1 is AI's Sputnik moment" — [Fortune (2025-01-27)](https://fortune.com/2025/01/27/marc-andreessen-deepseek-sputnik-ai-markets).

**The move: Monday 2025-01-27**
- NVDA fell "just under 17%". AP reports a close of $118.42, down 16.9% — [AP via Investment Executive (2025)](https://investmentexecutive.com/writer/matt-obrien-the-associated-press). Bloomberg called it the "biggest drop since March 2020" — [Bloomberg (2025-01-27)](https://www.bloomberg.com/news/articles/2025-01-27/asml-sinks-as-china-ai-startup-triggers-panic-in-tech-stocks).
- Market-cap loss, conflicting figures: $589B per Bloomberg ("Nvidia's $589 Billion DeepSeek Rout Is Largest in Market History") — [Bloomberg (2025)](https://www.bloomberg.com/news/articles/2025-01-27/asml-sinks-as-china-ai-startup-triggers-panic-in-tech-stocks); $593B per Reuters and Fortune — [Fortune (2025-01-28)](https://fortune.com/2025/01/28/deepseek-nvidia-tech-buy-dip); [Reuters via Rappler (2025, agg.)](https://www.rappler.com/?p=2907009). The gap likely reflects share-count or price-basis conventions. Either way it was a record one-day loss for any US company. The previous record was NVDA's own drop of about 9% in Sept 2024, which erased about $279B — [IG (2025-01-28)](https://www.ig.com/au/news-and-trade-ideas/why-nvidia-s-share-price-dropped-17--after-deepseek-news-250128).
- Other names (Reuters via Rappler, 2025; agg.):
  - Broadcom: down 17.4%.
  - Vistra: down 28.27%.
  - Constellation Energy: down 20.85%.
  - Nasdaq: down 3.1%.
  — [Rappler/Reuters (2025)](https://www.rappler.com/?p=2907009)
- Philadelphia Semiconductor Index: down 9.2%, its largest decline since March 2020 — [Plus500 (2025, agg.)](https://www.plus500.com/newsandmarketinsights/deepseek-triggers-tech-selloffs). Fortune says "over 9%" and "biggest single-day drop since 2020" — [Fortune (2025-01-28)](https://fortune.com/2025/01/28/deepseek-nvidia-tech-buy-dip).
- Same aggregator, lower confidence: Microsoft down 2.1%, Alphabet down 4.2%; ASML and ASM International "down more than 10% in Amsterdam" (likely intraday, not close); Tokyo Electron closed nearly 5% lower — [Plus500 (2025, agg.)](https://www.plus500.com/newsandmarketinsights/deepseek-triggers-tech-selloffs).
- Semiconductor, power, and infrastructure companies exposed to AI "collectively shed more than $1 trillion" — [Motley Fool (2025-01-28)](https://www.fool.com/investing/2025/01/28/why-nvidia-stock-skyrocketed-today).
- European and Asian names fell before the US open: Bloomberg's URL slug is "asml-sinks-as-china-ai-startup-triggers-panic-in-tech-stocks" — [Bloomberg (2025)](https://www.bloomberg.com/news/articles/2025-01-27/asml-sinks-as-china-ai-startup-triggers-panic-in-tech-stocks).
- Nvidia's same-day statement called DeepSeek "an excellent AI advancement" and said inference "requires significant numbers of NVIDIA GPUs and high-performance networking" — [IG (2025-01-28)](https://www.ig.com/au/news-and-trade-ideas/why-nvidia-s-share-price-dropped-17--after-deepseek-news-250128).
- Satya Nadella (dated 2025-01-27 by Fortune): "Jevons paradox strikes again! As AI gets more efficient and accessible, we will see its use skyrocket" — [Fortune (2025-01-27)](https://fortune.com/2025/01/27/microsoft-ceo-satya-nadella-deepseek-optimism-jevons-paradox). European "AI bulls" also invoked Jevons — [MarketScreener/Reuters (2025)](https://www.marketscreener.com/quote/stock/NVIDIA-CORPORATION-57355629/news/Europe-s-AI-bulls-pin-hopes-on-Jevons-Paradox-after-DeepSeek-rout-48944596/).

**After the move**
- 2025-01-28: NVDA rose about 8.9% to close at $128.99 — [Motley Fool (2025-01-28)](https://www.fool.com/investing/2025/01/28/why-nvidia-stock-skyrocketed-today). Analysts questioned whether the $6M claim was "deeply misleading and probably untrue" — [Fortune (2025-01-28)](https://fortune.com/2025/01/28/deepseek-nvidia-tech-buy-dip).
- 2025-01-28/29, distillation allegations:
  - David Sacks said there is "substantial evidence" DeepSeek used OpenAI model outputs — [Fortune (2025-01-29)](https://dc.fortune.com/2025/01/29/deepseek-openais-what-is-distillation-david-sacks/).
  - Bloomberg (2025-01-29): Microsoft and OpenAI are investigating whether a DeepSeek-linked group improperly obtained OpenAI data. Microsoft researchers saw large API data exfiltration in the fall of 2024.
  - OpenAI said it is "aware of and reviewing indications that DeepSeek may have inappropriately distilled our models".
  — [BNN Bloomberg (2025-01-29)](https://bnnbloomberg.ca/business/technology/2025/01/29/microsoft-probing-if-deepseek-linked-group-improperly-obtained-openai-data)
  - Note: DeepSeek's own "distillation" refers to distilling small models from R1, which is a different claim — [BNN Bloomberg (2025)](https://bnnbloomberg.ca/business/technology/2025/01/29/microsoft-probing-if-deepseek-linked-group-improperly-obtained-openai-data); [DeepSeek R1 paper (2025)](https://arxiv.org/abs/2501.12948v1).
- About 2025-01-31: SemiAnalysis estimated High-Flyer/DeepSeek had about 50,000 Hopper GPUs (including 10,000 H800 and 10,000 H100, plus H20s), about $1.6B in hardware capex, and total costs "well over $500M". These are estimates; critics note the $5.6M referred only to the final run — [Tom's Hardware (2025)](https://tomshardware.com/tech-industry/artificial-intelligence/deepseek-might-not-be-as-disruptive-as-claimed-firm-reportedly-has-50-000-nvidia-gpus-and-spent-usd1-6-billion-on-buildouts); [M.J. Tsai roundup (2025-02-10)](https://mjtsai.com/blog/2025/02/10/deepseeks-true-training-cost).
- About 2025-01-31: the US Commerce Department was reported to be probing whether DeepSeek obtained restricted Nvidia chips via third parties, including Singapore — [Fox Business (2025)](https://www.foxbusiness.com/technology/us-reportedly-investigating-whether-chinas-deepseek-used-restricted-ai-chips). On 2025-02-01, Singapore's trade ministry cited Nvidia saying there was "no reason to believe" DeepSeek obtained export-controlled products from Singapore — [Malay Mail (2025-02-01)](https://www.malaymail.com/news/singapore/2025/02/01/singapore-reaffirms-compliance-with-us-export-laws-amid-deepseek-nvidia-chip-diversion-concerns/165187). Singapore later opened a fraud probe into Nvidia server shipments (March 2025); this source does not state a DeepSeek link — [Fortune Asia (2025-03-03)](https://fortune.com/asia/2025/03/03/singapore-probes-potential-fraud-in-nvidia-ai-chip-shipments/).
- 2025-02-01: Bloomberg reported the DeepSeek app held the top global download spot, led by India — [Bloomberg (2025-02-01)](https://www.bloomberg.com/news/articles/2025-02-01/deepseek-app-holds-top-global-spot-in-downloads-led-by-india).
- 2025-09-17: DeepSeek's Nature paper reported R1's training cost as $294,000 (an 80-hour run on 512 H800s), on top of the V3 base model costing about $6M. The Register argues this does not mean R1 cost $294K end-to-end — [Daily Star/Reuters (2025-09)](https://d11.thedailystar.net/tech-startup/news/deepseek-spent-294000-train-its-popular-ai-model-3989806); [The Register (2025-09-19)](https://www.theregister.com/2025/09/19/deepseek_cost_train/).

### Inferences
Hypothesis map for the replay, labeled the way Yggdrasil would label them. This is my synthesis; labels are as of the move day unless stated.
- **H1. Efficiency shock, so lower GPU demand.** The claim: R1/V3 show frontier capability at much lower compute, so hyperscaler GPU demand will fall. Pre-move evidence: the V3 report (2024-12-27), the R1 release (2025-01-20), and Emanuel's post (2025-01-24/25). Label: consistent but unproven. It is a claim about future demand that same-day data could not test, and it was contested by H2 on the same day.
- **H2. Jevons paradox (counter-hypothesis).** The claim: efficiency raises total demand. Evidence: Nadella (2025-01-27) and Nvidia's own statement. Label: consistent but unproven. Note that both H1 and H2 are forecasts, and Yggdrasil should flag them as such rather than adjudicate them.
- **H3. The "$5.6M total cost" framing.** The primary source contradicts the strong framing that DeepSeek built frontier AI for $5.6M all-in. The V3 report itself said the figure excludes prior research and ablations (2024-12-27, pre-move). The narrow claim that the final run took 2.788M H800 GPU-hours is unrefuted (consistent but unproven, since it cannot be independently verified). Later SemiAnalysis estimates (post-move, 2025-01-31) contradict the all-in framing further but are themselves estimates.
- **H4. Hidden chip stock or export-control evasion.** Pre-move evidence: Wang's claim (2025-01-23). Post-move evidence: the Commerce probe report (2025-01-31). Label: unresolved, since allegations are not findings, and Singapore and Nvidia pushed back (2025-02-01).
- **H5. Distillation from OpenAI.** All evidence is post-move (2025-01-28/29). It cannot have caused the 2025-01-27 move. Truth label: unresolved.
- **H6. Attention and narrative cascade as the timing trigger.** The claim: information was public by 2025-01-20, but the price moved after the weekend attention spike (App Store #1 on 2025-01-26, viral post, "Sputnik moment", pre-US-open falls in ASML and Asian names). Label: supported as a timing explanation, by the documented chronology. As a causal claim it is consistent but unproven, since no causal identification is available. This is where Yggdrasil's attention graph is most useful.
- **H7. Valuation and capex-ROI fragility.** The claim: Stargate (2025-01-21) and Meta's $60-65B capex (2025-01-24) made ROI on AI capex salient, and NVDA's roughly 20x forward sales left little margin (Emanuel). Label: consistent but unproven.
- **Spillover structure.** The co-moves in power and utilities (VST -28%, CEG -21%) and semi-cap names (ASML, Tokyo Electron) fit an attention-spillover edge along an "AI capex to data-center power to chips" narrative chain (Guo et al. 2018). Yggdrasil should explain the cluster, not just NVDA.
- **Pre versus post summary.** Known before the move: the V3 cost table and its caveat, R1 o1-parity claims, the MIT license and low API prices, Wang's GPU claim, Stargate, Meta capex, the viral short thesis, and App Store rank. Known only after: the size of the move and the rebound, the distillation probe, SemiAnalysis estimates, the export-control probe, and the Nature cost disclosure.

### Gaps
- I could not fetch Reuters, CNBC, or Axios originals (HTTP 403). Several numbers (Broadcom -17.4%, Vistra -28.27%, Constellation -20.85%, SOX -9.2%, ASML/ASMI) come from syndicated or aggregator copies. Verify against exchange closing data.
- Not verified: S&P 500 and Dow moves on 2025-01-27; NVDA's move on Friday 2025-01-24; the exact closing percentage for ASML and TSMC ADRs; the timestamp of Nadella's post relative to the US open.
- I did not verify whether the H1 "demand destruction" hypothesis was later supported or contradicted by hyperscaler capex revisions or Nvidia results in 2025. That needs a separate pass (e.g., Meta and Microsoft Q4 2024 earnings on 2025-01-29, Nvidia FY25 Q4 results in Feb 2025).
- The DeepSeek consumer app launch date (reported by one aggregator as 2025-01-10) was not confirmed from a primary source.

## 7. How explanation and attribution systems in this domain have been evaluated

### Takeaway
Evaluation in this area relies on four approaches:
1. Inter-coder agreement against expert human coding (Baker et al.: 78.0% within-WSJ agreement on 17 categories versus 18.6% under random assignment).
2. External validation against scheduled events (jumps coded "monetary" cluster on FOMC days).
3. Timestamp matching of detected jumps to newswire (Lee & Mykland).
4. For LLM systems, citation support rates (Liu et al. 2023) and LLM-as-judge calibrated against humans (FNP 2026; El Lahib et al. 2026).

No study found evaluates coverage of contradicting evidence or calibration of "unknown" verdicts, which are Yggdrasil's core claims, so those metrics must be designed.

### Cited Findings
- Baker et al. (2025), Table 2, pairwise agreement on the primary jump reason:

  | Comparison | 1980-2023, granular | 1980-2023, Policy vs Non-policy | 1900-1979, granular | 1900-1979, Policy vs Non-policy |
  |---|---|---|---|---|
  | Within WSJ | 78.0% | 92.6% | 76.6% | 91.9% |
  | All coders within paper | 74.2% | 90.3% | 71.3% | 89.5% |
  | All coders and all papers | 58.2% | 81.0% | 45.9% | 76.4% |
  | Random assignment benchmark | 18.6% | 58.1% | 12.6% | 52.8% |

  Sample: 3,715 codings of 377 US jumps (1980-2023) and 6,684 codings of 802 jumps (1900-1979). Agreement drops "markedly" across newspapers because "newspapers sometimes differ in their explanations for a given jump" — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf).
- Baker et al. (2025) external validation: an FOMC meeting at t or t-1 raises the probability that a jump is coded "Monetary Policy" (coefficient 3.48, s.e. 0.361). A macro announcement at t raises "Macro News" coding (0.56, significant at 1%). It has no significant effect on "Monetary" coding (-0.08). Coder screening used a 50-article test against author codings — [Baker et al. (2025)](https://www.nber.org/system/files/working_papers/w28687/w28687.pdf).
- Lee & Mykland (2008): detected jump timestamps were checked against Factiva news around arrival times. Nearly all individual-stock jumps matched a news event, and the earnings day always showed a jump — [Lee & Mykland (2008)](https://www.scheller.gatech.edu/directory/research/finance/lee/pdf/leemykland08.pdf).
- Barndorff-Nielsen & Shephard (2006): most detected FX jumps coincide with macro announcements, used as face validity — [IDEAS (2006)](https://ideas.repec.org/p/nuf/econwp/0321.html).
- Kosai, Xie, Tsuchida & Utsuro, "LLM-as-a-Judge Evaluation of Financial News Articles Generated Based on Factors of Stock Price Fluctuation", FNP Workshop, May 2026. The system generates stock-move articles from news, disclosures, and price-fluctuation data, extracting causal factors with 3-day fluctuation windows. Evaluation combines item-wise human ratings with LLM-as-judge (zero-shot versus few-shot), using correlation analysis to assess "factual and causal consistency" — [ACL Anthology (2026)](https://aclanthology.org/2026.fnp-1.10/).
- El Lahib et al. (2026): their LLM leakage judge was validated against human annotators at 76.1% agreement and quadratic weighted kappa 0.85, which is a usable template for validating an LLM evidence-labeler — [arXiv (2026)](https://arxiv.org/html/2602.00758v1).
- Liu, Zhang & Liang (2023): citation recall of 51.5% (share of sentences fully supported) and citation precision of 74.5% (share of citations that support their sentence), from human evaluation of four generative search engines — [arXiv (2023)](https://arxiv.org/abs/2304.09848).
- Industry evaluation is mostly user satisfaction or SME review: Robinhood reports 95% of surveyed users value Digests' clarity and relevance — [Robinhood (2025)](https://robinhood.com/us/en/newsroom/digests-by-robinhood-cortex-uk). Bloomberg says SMEs evaluate its AI summaries — [Bloomberg (2025)](https://www.bloomberg.com/company/press/bloomberg-launches-gen-ai-summarization-for-news-content).

### Inferences
Proposed evaluation protocol for Yggdrasil, synthesized from the above:
- **(a) Category agreement with Baker et al. codings.** Replay Yggdrasil on US index jumps for 1985-2023 using their public WSJ codings (stockmarketjumps.com). Measure agreement of Yggdrasil's top hypothesis category against the human primary reason. Benchmark against the human-human ceiling (78.0% within WSJ, 58.2% across papers) and the random floor (18.6%).
- **(b) Abstention calibration.** On jumps humans coded "Unknown & No Explanation", Yggdrasil should output "we do not know" or "unresolved" at a comparable rate. Track false-confident explanations as the key failure metric.
- **(c) Temporal integrity.** Measure the share of cited evidence with first_seen_ts before the T3 jump timestamp. Run a leakage audit in the style of El Lahib et al., with an LLM judge validated against humans (target kappa of at least 0.8).
- **(d) Provenance precision and recall.** Following Liu et al. (2023), measure the share of hypothesis claims fully supported by cited evidence, and the share of citations that actually support their claim.
- **(e) Contradiction coverage.** This is a new metric. Expert annotators list known contradicting evidence per case (e.g., the V3 cost caveat for the "$5.6M" hypothesis). Measure the recall of contradicting evidence surfaced.
- **(f) Post-hoc consistency.** Retrospectively check whether hypotheses labeled "supported" align with later-resolved facts. This is evaluation only, never forecasting.

### Gaps
- I found no published benchmark for multi-hypothesis attribution of market moves, no metric for contradiction coverage, and no study of calibration of "unknown" outputs in finance explainers.
- I found no independent (non-vendor) evaluation of Benzinga WIIM, Robinhood Digests, or Google Finance AI explanations.
