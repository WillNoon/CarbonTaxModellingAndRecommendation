# Findings Log — Carbon Tax Research

> Append new findings at the TOP. Each entry: date, what was found, what it means for the research.

---

## 10 June 2026 — Phase 3 step 9: model validation (PPC, LOO) + robustness (Student-t)

Ran the back half of the Bayesian workflow we'd skipped (convergence ≠ fit), then fixed what it found.

- **PPC:** Normal-likelihood engine reproduces the centre (mean/sd/q95 Bayes-p ≈ 0.5) but **fails the tails** (q05 0.00, min 1.00, max 0.00) — can't reach the extremes, smears the core to compensate.
- **LOO (PSIS, 0 bad Pareto-k → reliable):** the **fixed effects earn their keep predictively** — Normal+FE beats no-FE by elpd_diff −230 (dse 25, ~9σ; 92% model weight). Independent validation of the causal architecture.
- **Cause of the fat tails:** tiny-emission / conflict **control** countries (Laos, Yemen, Afghanistan, Sierra Leone — median co2/cap ≈ 0.4 vs 2.6) with huge log-swings off a tiny base. None are tax/ETS countries.
- **Fix — Student-t likelihood** (estimated `nu ≈ 2`, very heavy tails): decisively better by LOO (**elpd +560, dse 54**); robustly down-weights the noisy controls instead of inflating `sigma`. **Adopted across all 4 channels of the engine.**
- **Robustness result:** effects **attenuate ~25%** (ETS −0.027, tax-alone −0.019, both ≈ ETS) — a *good* result (no longer outlier-driven); every finding holds and "both ≈ ETS alone" (redundancy) **strengthened**. Cost: mechanism *shares* become directional-only under robustness (heavy-tailed channels), so the engine's deliverable is the **robust totals + CI + P(reduce)**, breakdown qualitative.

**Backend complete:** a validated, outlier-robust causal recommendation engine. Remaining Phase 3: Streamlit dashboard (build-fast); continuous-dose levers remain a deliberate scope choice. **Coverage caveat (the real limit):** identification rests on ~26 tax / 29 ETS countries, almost all high-income EU — so the engine is accurate *for that reference class* and honestly-uncertain (wide CI, EXTRAPOLATED flag) everywhere else, incl. the highest-leverage targets (China, India, Indonesia).

---

## 10 June 2026 — Phase 3 steps 7–8: counterfactual engine + "tax is redundant, not weak"

Completed the recommendation engine on top of the structural model.

- **Step 7 — counterfactual engine.** A recommendation is a within-posterior-draw contrast (policy on vs off), so country baseline `alpha_c` and year effect cancel and the contrast collapses to the posterior of the relevant coefficients — uncertainty propagated end-to-end, no delta method. **Partial pooling makes it honest by construction:** observed-taxed countries get data-informed (tighter) `beta_c`; never-taxed countries revert to the population `Normal(mu,tau)` → automatically wider CI, flagged EXTRAPOLATED. `recommend(country, use_tax, use_ets)` returns total Δ + 90% CI + P(reduce) + Kaya mechanism breakdown.
- **Step 8 — backlog folded in (heterogeneous `beta_ets` + tax×ETS interaction `delta`).** Identification checked first: ETS well-identified (29 countries, median 14 ETS-yrs) but `tau_ets` small → effects fairly homogeneous (mild country-differentiation); interaction weak-but-estimable (cells: tax-only 83, both 105).
  - **`delta` = +0.017 (P(>0)=0.96) → sub-additive.** Decomposing: **tax alone ≈ −0.023 (P(reduce)=0.98)**, but **tax on top of ETS ≈ −0.006** (negligible). So the standalone tax DOES cut emissions — the earlier "tax is weak" was the both-cell dragging `mu_tax` to zero. **Reframe: the tax is REDUNDANT, not weak** — carbon-pricing instruments are substitutes, not complements; don't double-instrument expecting double the cut. The engine now drops "both" (−0.043→−0.038) since it no longer sums the two naively.
  - **Caveat (important):** standalone `mu_tax` leans on the 83-row tax-only cell (non-EU / pre-ETS Nordic) — least robust number; the redundancy and ETS strength are firmer. Channel closure ~80%; activity channel is an association, not a proven mechanism.

**Engine is functionally complete** (binary adopt/not). Remaining: standard Bayesian validation (posterior-predictive checks, LOO-CV — skipped so far), the continuous dose levers (price/coverage) the end-state vision promises ("$30/tonne, 50% coverage" — engine is currently on/off only), and the Streamlit dashboard.

---

## 10 June 2026 — Phase 3 steps 4–6: de-confounding + Kaya mechanism decomposition

Extended the Bayesian engine (`phase3_bayesian_engine.ipynb`) from the causal baseline to a structural decomposition.

- **Step 4 — second treatment (de-confound tax from ETS).** Adding a pooled `has_ets` coefficient halves the tax effect (`mu_tax` −0.121 → **−0.068**, P<0=0.97) and isolates **`mu_ets` = −0.165** (P<0=1.00). Reproduces the Phase-2 de-conflation *inside* the hierarchical model: ETS carries it, tax marginal. `mu_tax` now reads as "tax holding ETS + FE fixed."
- **Step 5 — anchored priors (honestly).** Did NOT center priors on our own −0.13 (same-data → circular → false precision). Instead tightened scales toward "effects are modest" (external/literature knowledge), centers at 0 so sign is earned. Tightening priors 2.5× moved top-level `mu`/`mu_ets` only in the 3rd decimal (n=4,218 → data dominates = robustness check passed); the treated-country `beta_c` spread shrank (0.044 → 0.041 = the regularization payoff, lands where data is thin). Phase 1/2 thus serves as *validation*, not input.
- **Step 6 — Kaya mechanism layer.** Switched to a log-change outcome so `dlog(CO2/pop) = dlog(affluence) + dlog(energy-intensity) + dlog(carbon-intensity)` decomposes exactly (identity closes: level max rel err 0.6%, log decomposition max resid 3.5e-3). Re-ran the DiD per channel (pooled treatments, anchored priors, 0 divergences). **Mechanism breakdown (annualized log-pts):**
  - **ETS −0.0286/yr** splits ≈ **half fuel-switching** (carbon intensity −0.0143, P<0=1.00, the "good" channel) + ≈ **a third lower activity** (affluence −0.0093, P<0=1.00, the *worry* channel — leakage/suppressed activity); efficiency ≈ 0. Over a 3-yr window ≈ −8% ≈ −4% decarbonization + −3% activity.
  - **Carbon tax −0.0133/yr** is weak and runs through **efficiency** (−0.0121), NOT fuel-switching (carbon intensity −0.0062, uncertain P<0=0.86); its affluence channel is *positive* (+0.0094 — taxing countries grew, masking the effect). Mechanistic echo of Phase 2's null outcome-sensitivity.

**Implications for the engine:** (1) recommend ETS as the primary lever but **flag the activity share** of its headline reduction (not pure decarbonization). (2) Treat the carbon tax as a marginal, efficiency-channel mover. **Caveats:** channel closure is ~85–90% not exact (priors + partial-pooled FE shrink each channel independently — trust shape, not last decimal); the affluence channel is an *association*, not a proven causal mechanism (mediation assumes no mediator–outcome confounding). Deferred: heterogeneous `beta_ets`, tax×ETS interaction (memory `project-phase3-backlog`).

---

## 9 June 2026 — Phase 3 step 3: Bayesian two-way-FE DiD validates the Phase-1 ATT

Built the causal core of the Phase 3 engine in PyMC (`phase3_bayesian_engine.ipynb`). Started from a no-FE baseline hierarchical model (country partial-pooling on `has_tax`), then added **partial-pooled country intercepts + year effects** — the Bayesian expression of the Phase-1 two-way fixed effects (`C(country) + C(year)`). All non-centered (`β = μ + τz`, etc.) to avoid Neal's funnel; year-effect mean pinned at 0 to anchor the additive level into the country intercepts.

- **`mu` (population-mean tax effect): −0.164 (no FE) → −0.121 (+ FE)**, P(μ<0) = 0.999. The ~0.04 shift toward zero is the cross-country baseline + common-time confounding the FE absorbed (`sigma_a` ≈ 0.11, `sigma_g` ≈ 0.055); residual `sigma` dropped 0.348 → 0.327.
- **Cross-method validation:** −0.121 lands on the Phase-1/2 ATT (≈ −0.13). Frequentist two-way-FE DiD and the Bayesian partial-pooled model — different machines, same identification, same number.
- Converged: R-hat ≈ 1.00, ESS hundreds-to-thousands, 0 divergences (nutpie backend; PyTensor C backend broken on this Windows/py3.13 box).

**Caveats / next:** (1) `has_tax` only — Phase 2 found **ETS carries the effect**, so `mu` is slightly overstated until `has_ets` is added as a second treatment (then it reads "tax holding ETS fixed"). (2) Priors are still weakly-informative at zero; step "anchor priors" will tighten them to Phase 1/2. (3) `mu` is the mean of heterogeneous `beta_c` (`tau` ≈ 0.086) — that spread drives country-specific recommendations later. Causal identification preserved; still conditional on parallel trends (stress-tested Phase 1).

---

## 3 June 2026 — Fuel-subsidy interaction re-run on clean treatments (Phase 2 fully closed)

Closed the last "partial" Phase 2 item. `fuel_subsidy_analysis.ipynb` previously interacted fuel subsidies with the **conflated `post_carbon_tax`** — contradicting the de-conflation that defines Phase 2. Re-ran with clean `has_tax` / `has_ets` and added an ETS symmetry check. Subsidy subsample: 1,781 obs (202 tax, 339 ETS country-years).

- **Tax × subsidy = +0.084 (p=0.15)**, hypothesized direction. At zero subsidy the tax effect is **−0.097 (p=0.065)**, eroding to ~+0.07 at ~2% GDP subsidy, crossing zero near ~1.2% GDP. Suggestive, **not significant** — subsidy-data overlap is thin.
- **ETS × subsidy = +0.056 (p=0.52)** — null. The blunting is **tax-specific**, mechanistically sensible: consumer fuel subsidies offset the retail price signal a tax raises, whereas the ETS bites upstream.
- **Caveat:** `has_ets` flips positive (+0.12) in this subsample — selection artefact of the ~26-country subsidy overlap, not a real reversal. Trust the *interaction*, not subsample levels.

**Verdict:** consistent with tax–subsidy antagonism but can't establish it; needs broader time-varying subsidy coverage (Phase 3 data lever), not a different estimator. With this + the ForestDRLearner capstone, **Phase 2 is fully complete** — clean treatment used throughout, no conflated-variable loose ends.

---

## 3 June 2026 — Phase 2 capstone: ForestDRLearner multi-policy heterogeneity (Phase 2 COMPLETE)

Built the 4-cell `ForestDRLearner` (0=none, 1=tax-only, 2=ETS-only, 3=both) as `phase2_multipolicy.ipynb` §4. DR-learner chosen over CausalForestDML because the treatment is multi-valued categorical; it returns a CATE per cell vs control. W = 4 validated confounders; X = 7 moderators (median-imputed). The forest has no country FE, so its absolute levels are confounded — anchored to a parametric within-FE `C(policy)` model in the same section.

- **Anchored levels (within-FE, clustered):** tax-only −0.069 (p=0.056), ETS-only −0.141 (p=0.049), both −0.139 (p=0.081). Same "ETS carries it, tax marginal" story as §1, now confirmed under a clean 4-cell categorical spec.
- **Forest levels are uninformative** (ATEs near 0, very wide CIs) — small treated cells + no FE. Used for shape only, as planned.
- **Heterogeneity:** CATE sd ≈ 0.13–0.16 per cell. **Implementation capacity is the dominant moderator in every cell** (importance ≈ 0.33), then schooling and industry share. Fossil share ≈ 0 importance in the *both* cell — consistent with fossil-dependence mattering for the *tax* margin specifically (§1), not the combined contrast.
- **Phase 3 implication:** recommendation engine should treat implementation capacity as the primary effect modifier and keep magnitudes anchored to within-FE parametric estimates, not forest levels.

**Phase 2 is now COMPLETE.** Clean causal questions were answered parametrically; the DR-learner adds the nonlinear heterogeneity map (and the method itself, a learning deliverable). Next: Phase 3 (PyMC hierarchical model + Streamlit), framed uncertainty-first.

---

## 2 June 2026 — Outcome sensitivity check (null): sharper outcome doesn't rescue the tax

Tested whether the weak carbon-tax signal is a measurement artefact of using economy-wide CO2/capita. Re-ran the de-conflated DiD on fuel-specific, mechanism-aligned outcomes (3-yr forward trend): oil+gas (tax channel), coal (ETS channel).

- has_tax on oil+gas: +0.010 (p=0.90) — zero effect on the fuels the tax most directly prices.
- has_tax on coal: -0.131 (p=0.27); on total: -0.045 (p=0.31).
- has_ets on coal: -0.021 (p=0.71) — no effect on its supposed power-sector channel; on oil+gas -0.290 (p=0.12).

**Conclusion:** sharper/channel-aligned outcomes do NOT strengthen the tax signal; effects don't localize to mechanism-implied fuels. The weak standalone carbon-tax effect is robust across every outcome definition — not a blunt-outcome artefact. (Documented in `phase2_multipolicy.ipynb` §3.) Of the three foundation levers, #2 (sharper outcome) is now exhausted as a null; #3 (effective price) is gated on time-varying coverage data; #1 (subnational units) remains the only untapped lever and is a standalone data project.

---

## 2 June 2026 — Data expansion to 2021 (refreshed 2024 emissions)

Refreshed OWID CO2 data (now reaches 2024) and extended the panel from 2019 to 2021. The 3-yr forward outcome needs emissions at year+3, so 2024 emissions unlock evaluable years through 2021.

- Panel: 3,892 -> **4,218 obs**, 1996-2019 -> **1996-2021**.
- Evaluable carbon-tax obs: 211 -> **261**; tax countries 23 -> **26** (added South Africa, Luxembourg, Netherlands).
- Pipeline was not cleanly re-runnable top-to-bottom; fixed 3 latent bugs: pandas-3.0 `groupby().apply()` dropping the grouping column (cell 69), a `gdp.notna()` filter that also dropped post-2021 `co2_per_capita` forward-lookups (cell 18), and a country-map sourced from the wrong frame (cell 77).
- **Result: the tax-vs-ETS finding is robust to the expansion.** Carbon tax alone -0.056 (p=0.22, still ns); ETS alone -0.129 (p=0.04, still sig); tax dose-response still flat. The weak carbon-tax effect is NOT a power artefact that more data fixes.
- Note: 2025 emissions not yet published, so 2022 adopters (Uruguay) remain unevaluable. The Phase 1 robustness and effects-library notebooks were built on the 2019 panel and need re-running on the expanded data (headline ATT shifts ~-0.151 -> ~-0.128).

---

## 2 June 2026 — Phase 2 start: carbon tax vs ETS (de-conflated)

`post_carbon_tax` conflated carbon tax with EU ETS (EU countries treated in 2005 = ETS launch, not their national tax). Re-estimating with clean `has_tax` / `has_ets` (same country+year FE, clustered SEs):

| Treatment | Effect | p |
|-----------|--------|---|
| Conflated `post_carbon_tax` | -0.151 | 0.004 |
| Carbon tax alone (`has_tax`) | -0.072 | 0.19 (ns) |
| ETS alone (`has_ets`) | -0.143 | 0.02 |
| Both additive: tax | -0.047 | 0.42 (ns) |
| Both additive: ETS | -0.138 | 0.03 |
| Interaction tax x ETS | +0.092 | 0.32 (ns) |

**Takeaway:** the Phase 1 headline was largely the EU ETS effect. The standalone national carbon tax effect is weaker (~-0.07) and not significant in this sample. Caveat: tax-only cell is small (94 obs, 15 heterogeneous countries) so power is low; with an interaction term carbon tax alone is significant (-0.093, p=0.02). Notebook: `phase2_multipolicy.ipynb`.

---

## 2 June 2026 — Phase 1 Complete (summary)

Carbon tax lowers the 3-yr-forward CO2/capita trend by ~0.15 (p=0.004), robust to every standard check. Effectiveness is driven by state capacity (helps) and fossil dependence (hurts). The democratic paradox is retired.

- **Baseline DiD** (country + year FE, clustered SEs): ATT -0.151, p=0.004.
- **Event study:** dynamic effect — ~0 at t=0, peak -0.168 at t+3, fades by t+5. Pre-trends jointly insignificant (F=1.87, p=0.12).
- **Heterogeneity:** implementation capacity -0.118/SD (p=0.07, helps); fossil dependence +0.049/SD (p=0.004, hurts). GDP, trade, schooling insignificant.
- **Robustness (all pass):** placebo +0.056 p=0.28 (null); leave-one-out -0.16 to -0.12, no sign flips; Goodman-Bacon 2.7% on forbidden comparisons; Rambachan-Roth pre-trends p=0.12, peak breakdown M=0.59 (point) / 0.21 (CI); Oster delta*=2.4, adjusted effect -0.088.
- **Democratic paradox retired:** old `democratic_legitimacy` was PC2 (= political stability); redefined as PC3 (voice & accountability) it is insignificant (p=0.27) and sign-unstable across DiD / CausalForest / OrthoForest.
- **Effects library** (`outputs/effects_library.csv`): per-country predicted effect, -0.63 (Luxembourg) to +0.13 (Ukraine).
- **Fuel subsidy x tax:** +0.077 (p=0.30) — blunts the tax in the right direction but underpowered.
- **Phase 2 blocker:** ETS coincides perfectly with carbon tax here (no ETS-only variation); fuel-subsidy/coverage data thin. Needs data expansion before multi-policy modelling.

---

## 2 June 2026 — Robustness Suite Completed + Heterogeneity / Effects Library

### Robustness checks all pass (phase1_robustness_checks.ipynb, §4–7)
- **Placebo (fake date -5yr):** +0.056, p=0.280 — null and wrong-signed; no pre-trend driving the result.
- **Leave-one-out (40 treated countries):** ATT in [-0.156, -0.115], 0 sign flips, 0 lost significance. Most influential drop: Luxembourg.
- **Goodman-Bacon:** implemented from scratch, validated by exactly reconstructing TWFE (-0.1554). Only **2.7%** of weight on forbidden (already-treated) comparisons → negative-weight bias negligible (consistent with DID2S -0.168 ≈ TWFE -0.156).
- **Rambachan-Roth (2023):** joint pre-trends F=1.87, p=0.12 (not rejected). Effect is dynamic — ~0 on impact, peak -0.168 at t+3. RM breakdown at peak: point M≈0.59, robust-CI M≈0.21 (moderately robust, not bulletproof).
- **Oster (2019):** with FE partialled out (FWL), δ\*=2.4 at Rmax=1.3·R² and β\*(δ=1)=-0.088 (identified set excludes 0). Robust to proportional OVB.

### Democratic paradox does NOT survive re-validation (KEY CORRECTION)
- The data refactor redefined `democratic_legitimacy` from **PC2 (really political stability)** to **PC3 (voice & accountability)** — a better-justified proxy (PC3 loads 0.84 on voice_accountability).
- Under the new PC3 definition **and** within-FE DiD interactions with clustered SEs, the democratic interaction is **insignificant** (PC2: +0.052, p=0.42; PC3: +0.049, p=0.27) and **sign-unstable** (causal forest gives the opposite sign cross-country).
- **The "democratic paradox" should be downgraded from a headline finding to a weak, unresolved signal.** The earlier negative result was an artefact of the old PC2 definition + cross-country (no-FE) identification.

### Heterogeneity + effects library (causal_effects_library.ipynb)
- Effect is **concentrated in high-implementation-capacity, low-fossil-dependence countries**: implementation capacity moderates the ATT by **-0.118/SD (p=0.07)**; fossil dependence by **+0.049/SD (p=0.004)**. Other moderators insignificant.
- **Effects library** (`outputs/effects_library.csv`): predicted ATT per country from -0.63 (Luxembourg) to +0.13 (Ukraine) — the Phase 3 recommendation-engine input.
- Causal forest used for nonlinear shape/feature importance only; its absolute level is confounded without country FE (mean over treated ≈0), so levels are anchored to the DiD.

### Fuel subsidy interaction (fuel_subsidy_analysis.ipynb)
- `post_carbon_tax × fuel_subsidy_gdp = +0.077 (p=0.30)` — hypothesized direction (subsidies blunt the tax) but insignificant; implied effect flips from -0.06 (low subsidy) to +0.10 (high subsidy). Underpowered subsample (342 treated obs) — resolve in Phase 2.

### Notes
- Data schema adopted but **not yet committed** (per decision): moderators exposed as `_pc`/`_z`; `democratic_legitimacy = PC3`.
- Stray robotics code (`smoke_pp.py` pure-pursuit controller) found pasted into a cell of `fuel_subsidy_analysis.ipynb` — flagged for removal.

---

## 15 April 2026 — Phase 1 Robustness Checks

### Robustness Suite Added (6 fixes on `phase1-robustness-fixes` branch)
- **Event study**: Coefficients extracted from `es_model` with Q()-quoted labels. Pre-treatment coefficients need checking when notebook is run.
- **Staggered-robust DiD**: DID2S (Gardner 2022) via `pf.event_study()`. Compares against TWFE — pending results.
- **CausalForest fix**: `min_samples_leaf` changed from 10→50, `max_depth` from None→4. Previous spec produced CATE range ±10 for never-treated countries (artefacts). Conservative spec should give range ~±0.3.
- **ETS sensitivity**: Three control group specs — (A) original, (B) exclude ETS-only, (C) never-any-pricing. Tests whether EU ETS countries contaminate the control group.
- **Propensity score overlap**: Logistic regression PS with Crump et al. (2009) trimming diagnostic. Histogram + log-odds plots.
- **Effective carbon price**: `tax_price × coverage_pct` constructed from World Bank Carbon Pricing Dashboard data. 23 carbon tax countries matched at 100% rate. Effective price range: $0.004–$73.21/tonne.

### Project Direction Revised
- Dropped 3-paper academic target. Project reframed as learning vehicle + policy recommendation engine.
- Phase 2 changed from "neural nets on causal estimates" to multi-policy causal models (carbon tax + ETS + fuel subsidies with dose-response).
- Phase 3 changed from "multi-agent RL" to Bayesian structural combination model + Streamlit dashboard.
- Rationale: original DL/RL methods don't work with 3,892 observations and 40 treated countries. New approach uses methods designed for sparse data (Bayesian partial pooling, structural causal models).

### Methodological Gaps Identified
- Missing: Rambachan & Roth (2023) parallel trends sensitivity — now near-mandatory for DiD papers
- Missing: Oster (2019) bounds for omitted variable bias
- Missing: Placebo tests and leave-one-out country robustness
- Missing: Goodman-Bacon decomposition (diagnostic for TWFE)
- Benchmark paper: Dolphin & Xiahou (2024, Nature Comms) meta-analysis of 80 carbon pricing evaluations

---

## April 2026 — Phase 1 OrthoForest Results

### Democratic Governance Paradox (KEY FINDING)
- `democratic_legitimacy` (PC2) shows **negative** correlation with carbon tax effectiveness
- `implementation_capacity` (PC1) shows **positive** correlation as expected
- Interpretation: technocratic capacity enhances effectiveness; democratic accountability paradoxically weakens it
- Hypothesis: democratic processes slow decisive climate action despite better overall governance
- **Do not treat as a bug — this is a publishable finding**

### OrthoForest Stability Confirmed
- Results robust across multiple random seeds (SD of 0.031–0.055 for key correlations)
- Validated confounder set: `log_gdp`, `log_population`, `natural_resource_rents_per_gdp`, `years_since_tax`
- Over-controlling problem resolved — earlier specs with governance as confounders were blocking mechanisms

### Policy Decay Effect
- Carbon taxes lose approximately 1% effectiveness annually post-implementation
- Captured by `years_since_tax` coefficient in DiD specs
- Important for policy design: maintenance and escalation needed to sustain effect

### Quintile Heterogeneity Pattern
- Governance quintile analysis reveals striking non-linearities
- Least democratic countries showing better short-run reductions than most democratic
- Middle quintiles show expected positive gradient for implementation capacity

---

## Earlier — Data & Setup Phase

### Governance Interpolation Decision
- WGI missing years (1997, 1999, 2001) filled via linear interpolation
- Justified: governance quality changes slowly, interpolation introduces minimal error
- Alternative (complete case only) would drop substantial treated observations

### Sample Restriction Logic
- final_analysis_data.csv: 3,892 obs from combined_data's 5,341
- Restriction: requires complete governance data + complete future trend (3-year forward lag)
- Implication: analysis naturally restricted to 1996–2019 (not 1990–2022)
- Missing data pattern does NOT overlap with treatment variation — complete case valid

### Industry Share Extrapolation
- `industry_share_gdp_extrapolated` flag marks imputed pre-1995 values
- Decision: use filled values but include flag as robustness check control
- Early years have higher measurement error — sensitivity analysis warranted

---

## Decisions Log (things we won't revisit without strong justification)

| Decision | Rationale | Date |
|----------|-----------|------|
| Clustered SEs at country level | Within-country correlation is large | Phase 1 |
| 3-year forward lag outcome | Allows time for policy effects | Phase 1 |
| Linear interpolation for WGI missing years | Governance changes slowly | Setup |
| OrthoForest over classical IV | Handles confounding via orthogonalisation; better for governance endogeneity | Phase 1 |
| Complete case analysis (not imputation) | Missing pattern doesn't overlap with treatment variation | Setup |
