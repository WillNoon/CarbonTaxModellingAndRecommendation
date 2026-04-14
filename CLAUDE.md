# Carbon Tax Policy Effectiveness Research
## Claude Code Configuration & Research Context

> **Read this file first.** It contains everything needed to work effectively on this project without re-explaining context each session.

---

## 🎯 PROJECT MISSION

**Goal:** Build a causal ML pipeline that (1) estimates how effective climate policies are for different types of countries, and (2) powers a **policy recommendation engine** — "Country X should implement policy Y at level Z, expecting W% emissions reduction."

**This is a learning project** — building skills in causal inference, ML, Bayesian modelling, and data products. The carbon tax question is the vehicle.

**NOT a prediction exercise.** The core challenge is causal identification — carbon taxes aren't randomly assigned, high-governance countries both adopt stronger taxes AND implement them more effectively. Every methodological decision must preserve causal validity.

**Key Paradigm:**
```
WRONG: Tax Price → Emissions (correlation)
RIGHT: Governance → Tax Adoption → Tax Price → Emissions (causal chain with endogeneity)
```

**End-state vision:**
```
Input:  "Indonesia, $30/tonne carbon tax, 50% coverage, 30% subsidy removal"
Output: "Predicted CO₂ reduction: -14.2% (95% CI: -8.1% to -20.3%)
         Breakdown: tax -6.8%, subsidy removal -4.1%, interactions -1.2%
         Confidence: MEDIUM — similar governance to Colombia (observed: -5.2%)"
```

---

## 🏗️ THREE-PHASE ARCHITECTURE

### Phase 1 — Causal Foundation (Weeks 1–4) ← CURRENT
- **Method:** DiD + OrthoForest/CausalForest + staggered-robust estimators (DID2S)
- **Goal:** Clean causal estimates with full heterogeneity characterisation
- **Output:** "Causal effects library" — how governance, GDP, fossil dependence etc. moderate tax effectiveness
- **Status:** OrthoForest running robustly. Governance heterogeneity confirmed. Democratic paradox discovered. Robustness checks (event study, ETS sensitivity, propensity overlap, effective carbon price) in progress.

### Phase 2 — Multi-Policy Causal Models (Weeks 5–9)
- **Method:** Separate causal models per policy lever (carbon tax, ETS, fuel subsidies), each with heterogeneous dose-response via CausalForestDML + DRLearner. Multi-task learning to transfer moderator effects across policies.
- **Goal:** Estimate how each policy's effectiveness varies by country characteristics, including policy interactions
- **Data:** ETS treatment (`has_ets`), fuel subsidies (`fuel_subsidy_gdp`), effective carbon price (`tax_price × coverage`), OECD green patents (optional)
- **New skills:** Continuous treatment dose-response, multi-task causal inference, DoWhy causal graphs

### Phase 3 — Structural Combination Engine + Dashboard (Weeks 10–14)
- **Method:** Bayesian hierarchical model (PyMC) encoding causal mechanisms: policy → energy prices → fuel switching → emissions. Structural interactions between policies. Counterfactual simulation for any country × policy combination.
- **Goal:** Policy recommendation engine with honest uncertainty quantification
- **Output:** Streamlit dashboard — pick a country, set policy sliders, get predicted impact with confidence intervals and breakdown by mechanism
- **New skills:** Bayesian modelling (PyMC), structural causal models, Streamlit, uncertainty propagation

---

## 📊 DATASET STATUS

### Primary Analysis File
**`final_analysis_data.csv`** — 3,892 obs × 58 cols, 163 countries, 1996–2019
- 511 treated observations from 40 carbon tax countries
- Outcome: `co2_per_capita_future_trend` (3-year forward lag)
- Treatment: `post_carbon_tax` (binary), `tax_price` (continuous)

### Raw Data File
**`combined_data.csv`** — 5,341 obs × 33 cols (pre-governance merge)

### Key Variable Groups
```python
# Treatment
treatment_vars = ['post_carbon_tax', 'tax_price', 'years_since_tax', 'treatment_year']

# Outcomes
outcome_vars = ['co2_per_capita_future_trend', 'co2_per_gdp_future_trend']

# Governance (6 WGI indicators + composites)
governance_vars = [
    'control_of_corruption', 'government_effectiveness', 'political_stability',
    'rule_of_law', 'regulatory_quality', 'voice_accountability',
    'implementation_capacity',  # PC1: technocratic capacity
    'democratic_legitimacy',    # PC2: democratic accountability ← paradox variable
    'carbon_tax_governance', 'governance_pc1', 'governance_pc2'
]

# OrthoForest confounders (TRUE confounders only — not mediators)
orthoforest_confounders = ['log_gdp', 'log_population', 'natural_resource_rents_per_gdp', 'years_since_tax']

# Economic controls
economic_controls = ['log_gdp', 'log_population', 'trade_openness', 'average_years_of_schooling',
                     'energy_intensity_per_capita', 'natural_resource_rents_per_gdp']

# Energy mix
energy_vars = ['fossil_pct_filled', 'renewable_pct_filled', 'nuclear_pct_filled']
```

---

## 🔬 CRITICAL METHODOLOGICAL INSIGHTS

### 1. Confounder vs. Mediator Distinction (HARD-LEARNED)
**Never include mediator variables as OrthoForest confounders.** Economic variables like `log_gdp` and `trade_openness` can be *pathways* through which governance operates — including them blocks the very mechanisms being studied.

```python
# WRONG — over-controls, blocks governance mechanisms
confounders = ['log_gdp', 'government_effectiveness', 'trade_openness', 'energy_intensity_per_capita']

# RIGHT — only true pre-treatment confounders
confounders = ['log_gdp', 'log_population', 'natural_resource_rents_per_gdp', 'years_since_tax']
```

### 2. The Democratic Governance Paradox
`democratic_legitimacy` (PC2) shows **negative** correlation with tax effectiveness despite `implementation_capacity` (PC1) showing positive effects. Hypothesis: democratic accountability slows decisive climate action even while improving overall governance quality. **This is a key finding — don't "fix" it.**

### 3. Policy Decay Effect
Carbon taxes lose ~1% effectiveness annually post-implementation. `years_since_tax` captures this. Always include it in specifications.

### 4. Parallel Trends
Always test and report. The 3-year forward lag outcome structure naturally restricts to periods with complete future data — account for this in sample selection commentary.

### 5. Clustered Standard Errors
Always cluster at country level: `cluster='country'` or equivalent. Within-country correlation is substantial.

---

## 📋 STANDARD CODE TEMPLATES

### DiD Specification
```python
import statsmodels.formula.api as smf

# Baseline DiD
formula_baseline = '''
co2_per_capita_future_trend ~ post_carbon_tax 
    + C(year) + C(country)
    + log_gdp + log_population + trade_openness 
    + natural_resource_rents_per_gdp + fossil_pct_filled
'''

# With governance heterogeneity
formula_gov = '''
co2_per_capita_future_trend ~ post_carbon_tax * implementation_capacity
    + post_carbon_tax * democratic_legitimacy
    + C(year) + C(country)
    + log_gdp + log_population + natural_resource_rents_per_gdp
'''

model = smf.ols(formula_baseline, data=df).fit(
    cov_type='cluster', cov_kwds={'groups': df['country']}
)
```

### OrthoForest (Validated Configuration)
```python
from econml.orf import DMLOrthoForest

# Use this exact confounder set — validated across multiple seeds
CONFOUNDERS = ['log_gdp', 'log_population', 'natural_resource_rents_per_gdp', 'years_since_tax']
MODERATORS = ['implementation_capacity', 'democratic_legitimacy']  # or other heterogeneity vars

est = DMLOrthoForest(
    n_trees=1000,
    min_leaf_size=10,
    max_depth=5,
    subsample_ratio=0.5,
    random_state=42  # always set for reproducibility
)
```

### Data Validation Template
```python
def validate_after_merge(df, dataset_name):
    """Run after every data integration step."""
    print(f"\n=== {dataset_name} Validation ===")
    print(f"Shape: {df.shape}")
    print(f"Countries: {df['country'].nunique()} | Years: {df['year'].min()}-{df['year'].max()}")
    print(f"Treated obs: {df['post_carbon_tax'].sum()} ({df['post_carbon_tax'].mean()*100:.1f}%)")
    
    # Missing data report
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if len(missing):
        print(f"\nMissing data:\n{missing}")
    
    # Check treatment variation preserved
    assert df.groupby('country')['post_carbon_tax'].nunique().max() > 0, "Treatment variation lost!"
    return True
```

---

## 🚫 REJECTED APPROACHES (Do Not Revisit Without Strong Justification)

| Approach | Reason Rejected |
|----------|----------------|
| Including governance vars as OrthoForest confounders | Over-controls, blocks mechanisms being studied |
| Using `co2_per_capita` as outcome (no lag) | Doesn't allow time for policy effect materialisation |
| Country-year FE without clustering | Understates SEs, spurious precision |
| Pooled OLS without FE | Omitted variable bias from country-level confounders |
| Synthetic control without parallel trends check | Identification assumption untested |
| Extrapolating `industry_share_gdp` pre-1995 | Data quality too poor for early years |

---

## 📁 REPO STRUCTURE

```
carbon-tax-research/
├── CLAUDE.md                      ← YOU ARE HERE
├── docs/
│   ├── RESEARCH_PLAN.md           ← Full 16-week plan & academic goals
│   ├── FINDINGS_LOG.md            ← Running log of key discoveries
│   ├── DATA_DICTIONARY.md         ← All variables with sources & notes
│   └── FUTURE_DATA_EXPANSION.md   ← Phase 2/3 data collection guide
├── data/
│   ├── final_analysis_data.csv    ← Primary analysis dataset (3,892 obs)
│   └── combined_data.csv          ← Raw merged data (5,341 obs)
├── notebooks/
│   ├── data_cleaning.ipynb        ← Data pipeline
│   ├── phase1_did_analysis.ipynb  ← Classical DiD (binary & continuous)
│   └── phase1_causal_ml.ipynb     ← OrthoForest/CausalForest analysis
├── scripts/                       ← Standalone Python scripts (future)
└── outputs/                       ← Figures, tables, robustness checks
```

---

## ⚡ STARTING A NEW SESSION

Before writing any code, confirm:
1. Which phase are we in? (Currently: **Phase 1, Week ~2**)
2. What was completed last session? (Check `docs/FINDINGS_LOG.md`)
3. What is the specific deliverable for this session?
4. Does the planned approach preserve causal identification?

**Default session structure:**
```
1. Validate previous outputs (5 min)
2. Focused implementation block (2-3 hrs)
3. Robustness checks (30 min)
4. Document findings in FINDINGS_LOG.md (15 min)
5. Commit with descriptive message
```

---

## 🎯 CURRENT PRIORITIES (Phase 1 Remaining)

- [x] Event study visualisation + parallel trends check
- [x] Staggered-robust DiD (DID2S via pyfixest)
- [x] CausalForest min_samples_leaf fix (was overfitting)
- [x] ETS control group sensitivity (3 specs)
- [x] Propensity score overlap diagnostics
- [x] Effective carbon price (tax_price × coverage_pct)
- [ ] Expand heterogeneity analysis beyond governance to: `fossil_pct`, `log_gdp`, `trade_openness`, `average_years_of_schooling`, `industry_share_gdp`
- [ ] Placebo tests (fake treatment dates) + leave-one-out country analysis
- [ ] Rambachan & Roth (2023) sensitivity analysis for parallel trends (`diff-diff` package)
- [ ] Oster (2019) bounds for omitted variable sensitivity (`PySensemakr`)
- [ ] Fuel subsidies as interaction term in DiD (not just confounder)
- [ ] Comprehensive "causal effects library" — treatment effect estimates by country characteristics

---

## 📚 KEY REFERENCES FOR METHODOLOGY

**Phase 1 (Causal Inference):**
- Athey & Imbens (2018) — Design-based analysis in DiD
- Chernozhukov et al. (2018) — Double ML (foundation for OrthoForest)
- Callaway & Sant'Anna (2021) — Staggered DiD
- Gardner (2022) — Two-stage DID (DID2S, used via pyfixest)
- Wager & Athey (2018) — Causal forests for heterogeneous treatment effects
- Rambachan & Roth (2023) — Sensitivity analysis for parallel trends
- Oster (2019) — Omitted variable bias bounds
- Dolphin & Xiahou (2024, Nature Comms) — Meta-analysis of 80 carbon pricing evaluations (benchmark)

**Phase 2 (Multi-Policy Modelling):**
- Kunzel et al. (2019, PNAS) — Meta-learners (S/T/X/R-learner) for heterogeneous effects
- Kennedy (2023) — Continuous treatment dose-response with causal forests
- Pearl (2009) — Structural causal models and do-calculus

**Phase 3 (Bayesian + Dashboard):**
- McElreath (2020) — Statistical Rethinking (Bayesian hierarchical models)
- PyMC documentation — Bayesian modelling in Python

---

*Last updated: April 2026 | Solo researcher project | Target: 3 academic papers over 16 weeks*
