---
name: causal-analysis
description: Use when writing causal inference code for this project. Enforces validated variable sets, confounder discipline, clustering, and methodology rules. Trigger when user asks to run DiD, CausalForest, OrthoForest, dose-response, or any treatment effect estimation.
---

# Causal Analysis Skill

When writing causal inference code for this project, always follow these rules:

## Variable Sets

```python
OUTCOME_PRIMARY = 'co2_per_capita_future_trend'
OUTCOME_SECONDARY = 'co2_per_gdp_future_trend'
TREATMENT_BINARY = 'post_carbon_tax'
TREATMENT_CONTINUOUS = 'tax_price'
TREATMENT_EFFECTIVE = 'effective_carbon_price'  # tax_price * coverage_pct

ORTHOFOREST_CONFOUNDERS = ['log_gdp', 'log_population', 'natural_resource_rents_per_gdp', 'years_since_tax']
DID_CONTROLS = ['log_gdp', 'log_population', 'trade_openness', 'natural_resource_rents_per_gdp', 'fossil_pct_filled']
GOVERNANCE_MODERATORS = ['implementation_capacity', 'democratic_legitimacy']
```

## Rules

1. **Never include governance variables as confounders** in OrthoForest/CausalForest. They are moderators (heterogeneity variables), not confounders. Including them blocks the mechanisms being studied.

2. **Always cluster standard errors at country level**: `cov_type='cluster', cov_kwds={'groups': df['country']}`

3. **Always use the 3-year forward lag outcome** (`co2_per_capita_future_trend`), not the contemporaneous level.

4. **Always include `years_since_tax`** in specifications to capture policy decay (~1%/year).

5. **CausalForestDML settings**: `min_samples_leaf=50`, `max_depth=4`, `random_state=42`. The old `min_samples_leaf=5` produced artefacts.

6. **For continuous treatment dose-response**: use `treatment_featurizer=PolynomialFeatures(degree=2, include_bias=False)` because CausalForestDML assumes linear treatment effect by default.

7. **For multi-policy comparison**: use `ForestDRLearner` with categorical treatment encoding (0=none, 1=carbon tax, 2=ETS, 3=both).

8. **The democratic paradox is a finding, not a bug.** `democratic_legitimacy` showing negative correlation with effectiveness should not be "fixed."

## Before Writing Code

- Explain the method to the user before implementing it
- Keep code clean and readable — no banner prints, no excessive formatting
- Follow standard practices naturally, like a good student project
