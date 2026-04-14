# Findings Log — Carbon Tax Research

> Append new findings at the TOP. Each entry: date, what was found, what it means for the research.

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
