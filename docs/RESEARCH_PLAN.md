# Research Plan — Carbon Tax Policy Recommendation Engine
## Implementation Timeline

> **Note (11 June 2026): This is a historical planning document.**
> It was written at the start of the project (April 2026) and documents intended methods and
> early findings. Several claims have been revised or retired since. See `docs/FINDINGS_LOG.md`
> for the current state of all findings. Key corrections to specific items are annotated inline.

---

## Vision

Build a system that answers: **"What climate policy should Country X implement, and what effect should they expect?"**

Pipeline:
1. **Phase 1:** Establish causal effects — do carbon taxes work, for whom, and why?
2. **Phase 2:** Build per-policy causal models — carbon tax, ETS, fuel subsidies — each predicting effect as a function of country characteristics and policy design
3. **Phase 3:** Combine into a structural model with Bayesian uncertainty, ship as interactive tool

This is also a learning project — building skills in causal inference, ML heterogeneity estimation, Bayesian modelling, and data products.

---

## Phase 1: Causal Foundation (Weeks 1–4) ← CURRENT

**Core Question:** Do carbon taxes reduce CO₂ emissions, and what country characteristics moderate effectiveness?

**Methods:**
- Difference-in-Differences (TWFE + Gardner DID2S for staggered robustness)
- OrthoForest / CausalForestDML for heterogeneous treatment effects
- Event study with 13 treatment cohorts
- Continuous treatment (effective carbon price = tax_price × coverage_pct)

**Deliverables:**
- [x] DiD with governance interaction terms (democratic paradox found)
- [x] OrthoForest with validated confounder set (stable across seeds)
- [x] CausalForestDML (fixed: min_samples_leaf=50, max_depth=4)
- [x] Staggered-robust DiD (DID2S via pyfixest)
- [x] Event study with parallel trends visualisation
- [x] ETS control group sensitivity (3 specs)
- [x] Propensity score overlap diagnostics
- [x] Effective carbon price variable (tax_price × coverage)
- [ ] Expanded heterogeneity: fossil_pct, log_gdp, trade_openness, education, industry
- [ ] Trade-weighted spatial lag (captures policy spillovers without full GNN — one extra variable)
- [ ] Placebo tests + leave-one-out country robustness
- [ ] Rambachan & Roth parallel trends sensitivity
- [ ] Oster bounds for omitted variable sensitivity
- [ ] Fuel subsidies as interaction/moderator (not just control)
- [ ] Complete "causal effects library" — all moderator × treatment estimates
- [ ] Model validation with RScorer (econml) — compare CausalForest vs OrthoForest fit

**Key Findings So Far:**
- Carbon tax ATT: ~-0.18 (significant, robust across specs)
  *(Note: number wrong and label wrong. The validated ATT is −0.154 on the corrected data, and it
  measures **combined carbon pricing** (tax + ETS conflated), not the carbon tax alone. The
  standalone tax is +0.010, p=0.80 after de-conflation. See FINDINGS_LOG 2 June + 11 June 2026.)*
- Democratic paradox: democratic_legitimacy (PC2) negatively correlated with effectiveness
  *(Note: RETIRED. PC2 loads on political_stability, not democracy. Under the correct PC3 proxy
  the interaction is p=0.27 and sign-unstable. See FINDINGS_LOG 2 June 2026.)*
- Policy decay: ~1% effectiveness loss per year post-implementation
  *(Note: unvalidated on corrected data; estimate used conflated treatment + mis-named
  years_since_tax variable. Do not cite. See FINDINGS_LOG April 2026 annotation.)*
- OrthoForest stable across seeds (SD 0.031–0.055)

---

## Phase 2: Multi-Policy Causal Models (Weeks 5–9)

**Core Question:** How does each climate policy's effectiveness vary by country, and can we predict effects for untried policies?

**Approach — three separate causal models:**

### Model A: Carbon Tax Dose-Response
- Treatment: `effective_carbon_price` (continuous)
- Method: `CausalForestDML` with `treatment_featurizer=PolynomialFeatures(degree=2)` — **critical: CausalForestDML assumes linear treatment by default**, polynomial featurizer captures diminishing returns at higher tax rates
- Complement with **Gaussian Process dose-response** (GPyTorch) — GPs give smooth dose-response surface with principled uncertainty bands, designed for small N
- Robustness: **Bayesian Causal Forests (BCF)** via R `bartCause` — better uncertainty intervals than CausalForest, handles irrelevant covariates automatically
- Heterogeneity variables: governance, GDP, fossil dependence, coverage rate
- Output: for any country × tax design → predicted emissions effect with confidence bands

### Model B: Multi-Policy Comparison (Carbon Tax vs ETS vs Both)
- Treatment: categorical — {none, carbon tax only, ETS only, both} — ~20 countries have overlapping policies
- Method: **ForestDRLearner** — handles categorical multi-treatment, estimates CATE for each treatment vs baseline
- Key question: does ETS produce different effects than carbon tax? Does having both compound?
- **DRPolicyForest** (`econml.policy.DRPolicyForest`) — learns optimal policy assignment per country directly. Feeds into Phase 3 recommendations.

### Model C: Fuel Subsidy Interaction
- Treatment: `fuel_subsidy_gdp` (continuous — subsidy level as % GDP)
- Method: CausalForestDML with `treatment_featurizer=PolynomialFeatures(degree=2)`
- Key question: do fuel subsidies offset carbon tax effectiveness? By how much?
- This directly feeds the recommendation engine: "remove X% of subsidies to amplify tax effect"

### Cross-Policy Transfer
- **Core insight:** country features that moderate carbon tax effectiveness (governance, fossil dependence) likely moderate ALL policy effects similarly
- Compare moderator importance across the three models — if `implementation_capacity` matters for carbon tax AND ETS, that's strong evidence for the recommendation engine
- Use `RScorer` (econml) for model comparison: which CATE estimator best explains outcome variation?

### Policy Interaction Identification
- Only ~20 countries have overlapping carbon tax + ETS — limited statistical power
- Strategy: assume additive effects as baseline, test for interactions using RScorer (does a model with interactions score better?)
- Phase 3 Bayesian model handles this via shrinkage prior: `interaction ~ Normal(0, sigma)` where sigma is small — interactions only emerge when data supports them

**Data additions:**
- OECD Effective Carbon Rates (sector-level, 79 countries) — optional enrichment
- OECD green innovation patents — mechanism evidence for democratic paradox
- IRENA renewable policy database — if expanding to renewable subsidies

**New skills learned:**
- Continuous treatment dose-response estimation (polynomial featurizer + GP)
- Gaussian Processes for causal inference (GPyTorch)
- Multi-treatment causal inference (ForestDRLearner)
- Optimal policy assignment (DRPolicyForest)
- DoWhy causal graphs
- Model selection for causal models (RScorer, DRTester)

**Deliverables:**
- [ ] Carbon tax dose-response model (country features + policy design → effect)
- [ ] ETS causal model with governance heterogeneity
- [ ] Fuel subsidy interaction estimates
- [ ] Cross-policy moderator comparison (do the same features predict all three?)
- [ ] Counterfactual predictions for 10 test countries

---

## Phase 3: Structural Combination Engine + Dashboard (Weeks 10–14)

**Core Question:** What policy MIX should Country X adopt, and what's the expected impact?

**Approach — Bayesian structural model:**

### Why Bayesian?
- **Handles sparse data**: only ~20 countries have overlapping carbon tax + ETS + subsidy data. Bayesian partial pooling borrows strength from similar countries.
- **Encodes economic theory as priors**: carbon taxes should reduce emissions (negative prior). The data updates the magnitude.
- **Honest uncertainty**: wide confidence intervals where data is thin, tight where it's rich.
- **Structural interactions**: carbon tax + subsidy removal both raise effective fossil fuel prices → compound effect modelled through the mechanism, not as a black-box interaction term.

### Causal Structure
```
Carbon Tax ($X/tonne, Y% coverage)
    → Raises effective fossil fuel price by f(X, Y)
        → Fuel switching: coal→gas→renewables (moderated by existing energy mix)
        → Demand reduction (moderated by GDP, industry structure)
        → Innovation incentive (moderated by governance, education)
    → Effectiveness moderated by: implementation_capacity, years_since_tax

Fuel Subsidy Removal (Z%)
    → Raises effective fossil fuel price by g(Z, current_subsidy_level)
        → Same downstream mechanisms as carbon tax
    → INTERACTS with carbon tax: both push fossil prices up → super-additive

ETS (cap-and-trade)
    → Price uncertainty vs tax certainty → different investment signals
    → Coverage typically narrower than carbon tax → different sectoral impact
    → Effectiveness moderated by: market design, governance, trade exposure

Combined Effect = structural_combination(individual_effects, interactions)
```

### Implementation
- **Framework:** PyMC for Bayesian estimation, DoWhy for causal graph specification
- **Parameters:** estimated from Phase 2 individual policy models
- **Interactions:** structural (through mechanisms) not black-box
- **Simulation:** for any country, simulate any policy combination with uncertainty propagation

### Dashboard (Streamlit)
```
┌─────────────────────────────────────────────────┐
│  Climate Policy Recommendation Engine           │
├─────────────────────────────────────────────────┤
│  Country: [Indonesia              ▼]            │
│                                                 │
│  Policy Levers:                                 │
│  Carbon tax ($/tonne):  [====30==========]      │
│  Tax coverage (%):      [====50%=========]      │
│  Subsidy removal (%):   [==30%===========]      │
│  ETS:                   [Off]                   │
│                                                 │
│  ═══════════════════════════════════════════     │
│  Predicted CO₂ reduction: -14.2%                │
│  95% CI: [-8.1% to -20.3%]                     │
│                                                 │
│  Breakdown:                                     │
│    Carbon tax alone:      -6.8%                 │
│    Subsidy removal:       -4.1%                 │
│    Interaction effect:    -1.2%                  │
│    Existing trend:        -2.1%                 │
│                                                 │
│  Similar countries:                             │
│    Colombia (observed -5.2% from carbon tax)    │
│    South Africa (observed -3.8%)                │
│                                                 │
│  Confidence: MEDIUM                             │
│  (governance similar to Colombia, but higher    │
│   fossil dependence → wider uncertainty)        │
└─────────────────────────────────────────────────┘
```

**New skills learned:**
- Bayesian hierarchical modelling (PyMC)
- Structural causal models
- Uncertainty propagation
- Streamlit dashboard development
- Deploying a data product

**Deliverables:**
- [ ] Bayesian structural model fitted and validated
- [ ] Counterfactual simulation for all 163 countries
- [ ] Interactive Streamlit dashboard
- [ ] Model validation: compare predictions vs observed effects for held-out countries
- [ ] Documentation of model assumptions and limitations

---

## Timeline Summary

| Week | Phase | Focus | Key Deliverable |
|------|-------|-------|-----------------|
| 1-2 | Phase 1 | DiD + CausalForest + robustness | Main estimates + robustness suite |
| 3-4 | Phase 1 | Heterogeneity + sensitivity + causal effects library | Complete Phase 1 |
| 5-6 | Phase 2 | Carbon tax dose-response model | Continuous treatment model |
| 7-8 | Phase 2 | ETS model + fuel subsidy model | Three policy models |
| 9 | Phase 2 | Multi-task transfer + cross-policy comparison | Phase 2 complete |
| 10-11 | Phase 3 | Bayesian structural model (PyMC) | Structural combination engine |
| 12-13 | Phase 3 | Streamlit dashboard | Working interactive tool |
| 14 | Phase 3 | Validation + documentation | Ship it |

---

## Data Sources

| Dataset | Status | Used In |
|---------|--------|---------|
| `final_analysis_data.csv` (3,892 obs, 163 countries) | In use | Phase 1-3 |
| Carbon tax coverage rates (World Bank) | Downloaded | Phase 1-2 |
| RFF World Carbon Pricing Database (GitHub) | Available | Phase 2 (optional) |
| OECD Effective Carbon Rates | Available | Phase 2 (optional) |
| OECD Green Innovation Patents | Available | Phase 2 (optional) |
| IRENA Renewable Policy Database | Available | Phase 3 (optional) |

---

## Variables Rejected (Do Not Revisit)

| Variable | Reason |
|----------|--------|
| Sectoral emissions breakdowns | Time-intensive, largely captured by energy mix |
| *(Note: ironically, sectoral emissions became Phase 4's best identification attempt — the Eurostat covered-vs-uncovered sector DiD. Still supportive rather than clean ID after the June 2026 audit, but it was worth pursuing.)* | |
| City-level policy variations | Scope creep |
| Carbon intensity improvements | Outcome, not input — reverse causality |
| Clean tech deployment | Potentially caused by carbon taxes — endogenous |
| Historical fuel subsidies pre-2010 | Data quality too poor |
| Public opinion data | Hard to get consistently, low priority for core model |

---

## Risk Register

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Parallel trends violated | Medium | Event study + Rambachan-Roth sensitivity |
| Over-controlling in causal ML | Happened once, resolved | Strict confounder/mediator discipline |
| ETS model too few countries (26) | Medium | Bayesian partial pooling, wide CIs |
| Multi-policy interactions unidentifiable | Medium | Structural model constrains interactions via mechanisms |
| Bayesian model misspecification | Medium | Compare structural vs reduced-form predictions |
| Dashboard scope creep | High | MVP first, iterate after |
| Timeline pressure | Medium | Phase 3 dashboard can be simplified if needed |

---

## Key Python Packages by Phase

**Phase 1:** statsmodels, econml, pyfixest, sklearn, PySensemakr, diff-diff
**Phase 2:** econml (CausalForestDML, ForestDRLearner, DRPolicyForest), DoWhy, GPyTorch, rpy2 + bartCause (for BCF)
**Phase 3:** PyMC, ArviZ, Streamlit, plotly

---

*Solo researcher project | Learning ML + causal inference | April 2026*
