# Data Dictionary — final_analysis_data.csv

**4,218 observations | 163 countries | 1996–2021 | 73 columns**
(Corrected dataset: treatment-coding fix applied 11 June 2026 per `docs/audit_fixes/data_fix.md`.)

---

## ⛔ Banned legacy columns — do NOT use in models

| Column | Problem |
|---|---|
| `post_carbon_tax` | Conflated: set from `any_carbon_price_dummy`, so EU countries appear as treated in 2005 via the ETS, not a national carbon tax. Preserved for any-pricing analyses only. |
| `tax_price` | Conflated: equals `tax_price_only + ets_price_only`. 325 rows have `has_tax=0` but `tax_price > 0` (all ETS-driven). Use `tax_price_only` and `ets_price_only` separately. |
| `fossil_pct_filled` | Not a fossil share — it is a binary imputation flag (`0` = observed, `1` = row was imputed). Using it as a continuous value was the source of the spurious "+0.049/SD fossil-dependence" finding (retired June 2026). |
| `renewable_pct_filled` | Same: binary imputation flag (all zeros in current data). |
| `nuclear_pct_filled` | Same: binary imputation flag. |

---

## Identifiers

| Column | Type | Description |
|---|---|---|
| `country` | str | Country name (OWID spelling, e.g. "Czechia" not "Czech Republic") |
| `country_code` | str | ISO 3-letter code |
| `year` | int | Year (1996–2021) |

---

## Treatment variables (clean, de-conflated)

These four are the validated treatment indicators. Use these; ignore `post_carbon_tax` and `tax_price`.

| Column | Type | Description | Notes |
|---|---|---|---|
| `has_tax` | int (0/1) | Binary carbon tax indicator | Onset = verified implementation year (not first-priced year per WB). Denmark/Finland pre-1996 adopters coded 1 from 1996 (panel start). |
| `has_ets` | int (0/1) | Binary ETS indicator | Accession-aware: EU members from their accession year (e.g. Croatia from 2013, not 2005); UK 2005–2021; Norway/Iceland from 2008; South Korea from 2015. Bulgaria/Romania from 2007. |
| `tax_price_only` | float | Carbon tax price (USD/tonne) | WB observed price; 0 where WB lacks an early datum (e.g. Denmark 1996–2006). Binary corrected independently; do not infer tax presence from this being 0. |
| `ets_price_only` | float | ETS price (USD/tonne) | EUA price for EU ETS members; KETS price for South Korea; UK 2021 proxied with EUA 2021. |

### Treatment timing

| Column | Type | Description |
|---|---|---|
| `years_since_tax` | int | Years since carbon tax implementation. −1 for never-treated or pre-onset rows. |
| `years_since_ets` | int | Years since ETS entry (accession-aware). −1 for never-treated or pre-onset rows. |
| `years_since_any_pricing` | int | Years since first of tax or ETS — the legacy "years_since_tax" concept. |
| `tax_onset_year` | float | Year of carbon tax implementation (NaN if never). |
| `ets_onset_year` | float | Year of ETS entry (NaN if never). |
| `treatment_year` | float | Legacy: year of first any carbon pricing. |
| `years_relative_to_treatment` | float | Legacy: years relative to first any pricing (for event studies on the conflated treatment). |
| `post_carbon_price` | int (0/1) | Legacy alias for `any_carbon_price_dummy`. |
| `any_carbon_price_dummy` | int (0/1) | 1 if the country has either tax or ETS this year. |
| `carbon_price_max` | float | max(tax_price_only, ets_price_only). |
| `tax_type` | int | WB instrument type code. |

---

## Outcome variables

| Column | Type | Description | Notes |
|---|---|---|---|
| `co2_per_capita_future_trend` | float | **PRIMARY OUTCOME** — 3-year forward log-change in CO₂/capita: `log(co2[t+3]) − log(co2[t])` | Requires emissions at t+3 ≤ 2024; panel capped at 2021. |
| `co2_per_gdp_future_trend` | float | 3-year forward log-change in CO₂/GDP | Missing for 2020–21 (GDP at t+3=2024 unavailable); outcome comparisons using this variable silently use a shorter year range. |
| `co2_per_capita_prior_trend` | float | 3-year prior log-change in CO₂/capita | Used in parallel-trends visualisation. |
| `co2_per_gdp_prior_trend` | float | 3-year prior log-change in CO₂/GDP | |
| `co2_per_capita_3yr_change` | float | Alias for `co2_per_capita_future_trend` (same column, older name) | |
| `co2_per_gdp_3yr_change` | float | Alias for `co2_per_gdp_future_trend` | |
| `co2_per_capita` | float | CO₂/capita (tonnes), level | Not the outcome — no forward lag. |
| `co2_per_gdp` | float | CO₂/GDP | Level. |
| `co2_per_capita_minus_3` | float | co2_per_capita three years prior | Used in trend construction. |
| `co2_per_capita_plus_3` | float | co2_per_capita three years forward | Used in trend construction. |
| `co2_per_gdp_minus_3` | float | co2_per_gdp three years prior | |
| `co2_per_gdp_plus_3` | float | co2_per_gdp three years forward | |

---

## Emissions detail

| Column | Description |
|---|---|
| `coal_co2_per_capita` | Coal-specific CO₂/capita (OWID) |
| `gas_co2_per_capita` | Gas-specific CO₂/capita |
| `oil_co2_per_capita` | Oil-specific CO₂/capita (transport-fuel proxy) |
| `land_use_change_co2_per_capita` | Land use CO₂/capita (volatile) |
| `land_use_change_co2_per_capita_lag` | One-year lagged land use (smoother) |

---

## Energy mix variables

⚠️ Three caveats about these columns:

1. **`nuclear_pct` is NOT nuclear-only** — it is the World Bank "alternative and nuclear energy" series,
   which includes hydropower. Paraguay = 100% (pure hydro). Do not interpret as nuclear share.

2. **The three shares use different World Bank denominators** and sum to approximately 107% on average
   (nuclear_pct includes hydro counted separately in some denominators). Do not treat them as a simplex
   or sum them to 100%.

3. **`fossil_pct` post-~2015** values for ~13% of rows (21 small, never-treated countries) are
   carried-forward extrapolations — the ffill/bfill in `data_cleaning.ipynb` extrapolates flat
   beyond the last observed data point. `fossil_pct_filled` records which rows were imputed (1 = imputed).

| Column | Type | Range | Description |
|---|---|---|---|
| `fossil_pct` | float | 0–100 | Fossil fuels as % of energy use (World Bank). **Use this, not `fossil_pct_filled`.** |
| `renewable_pct` | float | 0–100 | Renewables as % of energy use |
| `nuclear_pct` | float | 0–100 | WB "alternative + nuclear" incl. hydro — see caveat above |
| `fossil_pct_filled` | int (0/1) | 0 or 1 | **Imputation FLAG** — 1 = this fossil_pct row was imputed. NOT a fossil share. |
| `renewable_pct_filled` | int (0/1) | 0 or 1 | **Imputation FLAG** — all zeros in current data. |
| `nuclear_pct_filled` | int (0/1) | 0 or 1 | **Imputation FLAG** — NOT a nuclear share. |

---

## Governance variables (World Bank WGI)

Raw WGI indicators are on the ~−2.5 to +2.5 scale. `_pc` variants are raw PCA scores;
`_z` variants are standardised (mean 0, SD 1) — use `_z` in regression interactions.

| Column | Type | Description |
|---|---|---|
| `control_of_corruption` | float | WGI control of corruption |
| `government_effectiveness` | float | WGI government effectiveness |
| `political_stability` | float | WGI political stability / absence of violence |
| `rule_of_law` | float | WGI rule of law |
| `regulatory_quality` | float | WGI regulatory quality |
| `voice_accountability` | float | WGI voice and accountability |
| `governance_pc1` | float | Raw PCA component 1 (= implementation capacity) |
| `governance_pc2` | float | Raw PCA component 2 |
| `governance_pc3` | float | Raw PCA component 3 (= democratic legitimacy) |
| `implementation_capacity_pc` | float | PC1 score (technocratic/bureaucratic capacity: loads on government effectiveness, rule of law, regulatory quality, control of corruption) |
| `implementation_capacity_z` | float | PC1 standardised — **use this in models** |
| `democratic_legitimacy_pc` | float | PC3 score (loads 0.84 on voice_accountability) |
| `democratic_legitimacy_z` | float | PC3 standardised — **use this in models**. Note: the "democratic paradox" finding used the old PC2 (which loads on political_stability). PC3 is the correct democracy proxy; the interaction is insignificant (p=0.27) and sign-unstable. |
| `political_stability_pc` | float | PC2 score (loads on political_stability) |
| `political_stability_z` | float | PC2 standardised |

---

## Economic variables

| Column | Type | Source | Description |
|---|---|---|---|
| `gdp` | float | World Bank WDI | GDP in current USD |
| `log_gdp` | float | derived | log(GDP) — use this in regressions |
| `population` | int | World Bank WDI | Population |
| `log_population` | float | derived | log(population) |
| `trade_openness` | float | World Bank WDI | (Exports+Imports)/GDP |
| `average_years_of_schooling` | float | World Bank | Mean years of education |
| `energy_per_capita` | float | IEA/WB | Energy use per capita (kWh) |
| `energy_per_gdp` | float | IEA/WB | Energy intensity |
| `log_energy_per_capita` | float | derived | log(energy_per_capita) |
| `energy_intensity_per_capita` | float | IEA/WB | Alternative energy intensity measure |
| `natural_resource_rents_per_gdp` | float | World Bank WDI `NY.GDP.TOTL.RT.ZS` | Oil+gas+mineral rents as % GDP |
| `industry_share_gdp` | float | World Bank | Industry value added % GDP |
| `industry_share_gdp_extrapolated` | int (0/1) | flag | 1 = value was KMeans-model imputed (4.7% of rows). Include as robustness control when using `industry_share_gdp`. |

---

## Fuel subsidy variables

| Column | Type | Source | Notes |
|---|---|---|---|
| `fuel_subsidy_usd_million` | float | IMF/IEA | Absolute subsidies in USD million |
| `fuel_subsidy_gdp` | float | IMF/IEA | Subsidies as % GDP — prefer this for cross-country comparisons |

Coverage is thin (~1,781 obs with non-null values). The subsidy interaction with carbon pricing is suggestive but insignificant in this sample.

---

## Standard model variable sets (validated)

```python
# Clean treatment variables — use these
TREATMENT_BINARY_TAX = 'has_tax'
TREATMENT_BINARY_ETS = 'has_ets'
TREATMENT_DOSE_TAX   = 'tax_price_only'    # per $/tonne
TREATMENT_DOSE_ETS   = 'ets_price_only'    # per $/tonne

# Outcomes
OUTCOME_PRIMARY   = 'co2_per_capita_future_trend'
OUTCOME_SECONDARY = 'co2_per_gdp_future_trend'   # missing 2020-21

# Validated OrthoForest confounders (true pre-treatment confounders only)
ORTHOFOREST_CONFOUNDERS = [
    'log_gdp', 'log_population',
    'natural_resource_rents_per_gdp', 'years_since_any_pricing'
    # Note: years_since_tax was renamed years_since_any_pricing in the June 2026 fix
]

# Governance moderators (standardised versions)
GOVERNANCE_MODERATORS = [
    'implementation_capacity_z',   # PC1 — technocratic capacity
    'democratic_legitimacy_z',     # PC3 — voice & accountability (paradox RETIRED)
]

# DiD controls (economic confounders; use real fossil_pct, NOT fossil_pct_filled)
DID_CONTROLS = [
    'log_gdp', 'log_population', 'trade_openness',
    'natural_resource_rents_per_gdp', 'fossil_pct',
    'average_years_of_schooling'
]

# Full governance variable list (raw WGI)
GOVERNANCE_VARS_ALL = [
    'control_of_corruption', 'government_effectiveness', 'political_stability',
    'rule_of_law', 'regulatory_quality', 'voice_accountability',
    'implementation_capacity_z', 'democratic_legitimacy_z',
]

# Energy mix — use the unsuffixed columns (0-100 scale); do NOT sum to 100%
ENERGY_VARS = ['fossil_pct', 'renewable_pct', 'nuclear_pct']
# fossil_pct is the cleanest single fossil-dependence measure
```

---

## Known data limitations

- **`nuclear_pct` includes hydro**: do not use as a nuclear-only measure.
- **Energy shares sum to ~107%**: different WB denominators. Never treat as a simplex.
- **`fossil_pct` ~2015+ extrapolation**: ffill/bfill is flat beyond last observed point for 21 small countries.
- **`has_tax` pools trivial taxes**: Poland $0.08/tonne appears treated the same as Sweden $120+. The dose variable `tax_price_only` captures this distinction.
- **`co2_per_gdp_future_trend` missing 2020–21**: outcome comparisons involving this variable silently use different year ranges than comparisons using `co2_per_capita_future_trend`.
- **Stale siblings**: `analysis_data.csv` and `treatment_sample.csv` exist in `data/cleaned/` but are intermediate artefacts; `final_analysis_data.csv` is the analysis file.
- **Australia repeal**: correctly coded (has_tax drops to 0 after 2014 repeal).
