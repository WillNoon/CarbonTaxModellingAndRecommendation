# Data Dictionary — final_analysis_data.csv

3,892 observations | 163 countries | 1996–2019 | 58 columns

---

## Identifiers
| Variable | Type | Description |
|----------|------|-------------|
| `country` | str | Country name |
| `country_code` | str | ISO 3-letter code |
| `year` | int | Year |

## Treatment Variables
| Variable | Type | Description | Notes |
|----------|------|-------------|-------|
| `post_carbon_tax` | int (0/1) | Binary treatment indicator | 1 = country has active carbon tax this year |
| `tax_price` | float | Carbon tax rate (USD/tonne CO₂) | 0 for untreated; range 0–170 |
| `tax_type` | int | Type of carbon pricing instrument | |
| `years_since_tax` | int | Years since tax implementation | 0 for untreated |
| `treatment_year` | float | Year tax was introduced | NaN for never-treated |
| `years_relative_to_treatment` | float | Relative time (for event study) | |

## Outcome Variables
| Variable | Type | Description | Notes |
|----------|------|-------------|-------|
| `co2_per_capita_future_trend` | float | **PRIMARY OUTCOME** — 3-yr forward trend in CO₂/capita | Main DiD outcome |
| `co2_per_gdp_future_trend` | float | 3-yr forward trend in CO₂/GDP | Secondary outcome |
| `co2_per_capita` | float | CO₂ per capita (tonnes) | Level, not trend |
| `co2_per_gdp` | float | CO₂ per GDP | Level |
| `co2_per_capita_prior_trend` | float | 3-yr prior trend (pre-period) | Used in parallel trends |

## Governance Variables (World Bank WGI)
| Variable | Type | Range | Description |
|----------|------|-------|-------------|
| `control_of_corruption` | float | ~-2.5 to 2.5 | Perceived corruption control |
| `government_effectiveness` | float | ~-2.5 to 2.5 | Public service quality, policy implementation |
| `political_stability` | float | ~-2.5 to 2.5 | Political violence/terrorism absence |
| `rule_of_law` | float | ~-2.5 to 2.5 | Contract enforcement, property rights |
| `regulatory_quality` | float | ~-2.5 to 2.5 | Ability to formulate sound regulations |
| `voice_accountability` | float | ~-2.5 to 2.5 | Political rights, civil liberties |
| `implementation_capacity` | float | standardised | **PC1** — technocratic/bureaucratic capacity |
| `democratic_legitimacy` | float | standardised | **PC2** — democratic accountability (paradox var) |
| `carbon_tax_governance` | float | composite | Governance weighted for carbon policy context |
| `governance_pc1` | float | | Raw PC1 score |
| `governance_pc2` | float | | Raw PC2 score |

## Economic Variables
| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `gdp` | float | World Bank | GDP in current USD |
| `log_gdp` | float | derived | log(GDP) — use this in regressions |
| `population` | int | World Bank | Population |
| `log_population` | float | derived | log(population) — use in regressions |
| `trade_openness` | float | World Bank | (Exports+Imports)/GDP |
| `average_years_of_schooling` | float | World Bank | Mean years education |
| `energy_intensity_per_capita` | float | IEA/WB | Energy use per capita |
| `natural_resource_rents_per_gdp` | float | World Bank WDI `NY.GDP.TOTL.RT.ZS` | Oil+gas+mineral rents as % GDP |
| `industry_share_gdp` | float | World Bank | Industry value added % GDP |
| `industry_share_gdp_extrapolated` | int (0/1) | flag | 1 = value was imputed (use as robustness control) |

## Energy Mix Variables
| Variable | Type | Description | Notes |
|----------|------|-------------|-------|
| `fossil_pct` | float | Fossil fuel % of energy mix | Has missing values |
| `renewable_pct` | float | Renewable % of energy mix | |
| `nuclear_pct` | float | Nuclear % of energy mix | |
| `fossil_pct_filled` | float | Fossil % — forward/backward filled | Use this in models |
| `renewable_pct_filled` | float | Renewable % — filled | Use this in models |
| `nuclear_pct_filled` | float | Nuclear % — filled | Use this in models |

## Fuel Subsidy Variables
| Variable | Type | Source | Notes |
|----------|------|--------|-------|
| `fuel_subsidy_usd_million` | float | IMF/IEA | Absolute subsidies in USD million |
| `fuel_subsidy_gdp` | float | IMF/IEA | Subsidies as % GDP — prefer this for cross-country |

## Emissions Detail Variables
| Variable | Description |
|----------|-------------|
| `coal_co2_per_capita` | Coal-specific emissions |
| `gas_co2_per_capita` | Gas-specific emissions |
| `oil_co2_per_capita` | Oil-specific emissions |
| `land_use_change_co2_per_capita` | Land use emissions (volatile) |
| `land_use_change_co2_per_capita_lag` | Lagged land use (smoother) |
| `energy_per_capita` | Energy consumption per capita |
| `energy_per_gdp` | Energy intensity |

---

## Standard Model Variable Sets

```python
# Paste these into any analysis script

OUTCOME_PRIMARY = 'co2_per_capita_future_trend'
OUTCOME_SECONDARY = 'co2_per_gdp_future_trend'
TREATMENT_BINARY = 'post_carbon_tax'
TREATMENT_CONTINUOUS = 'tax_price'

ORTHOFOREST_CONFOUNDERS = [
    'log_gdp', 'log_population', 
    'natural_resource_rents_per_gdp', 'years_since_tax'
]

GOVERNANCE_MODERATORS = [
    'implementation_capacity', 'democratic_legitimacy'
]

DID_CONTROLS = [
    'log_gdp', 'log_population', 'trade_openness',
    'natural_resource_rents_per_gdp', 'fossil_pct_filled',
    'average_years_of_schooling'
]

GOVERNANCE_VARS_ALL = [
    'control_of_corruption', 'government_effectiveness', 'political_stability',
    'rule_of_law', 'regulatory_quality', 'voice_accountability',
    'implementation_capacity', 'democratic_legitimacy', 'carbon_tax_governance'
]

HETEROGENEITY_CANDIDATES = [
    # Governance
    'implementation_capacity', 'democratic_legitimacy', 'carbon_tax_governance',
    # Economic
    'log_gdp', 'trade_openness', 'average_years_of_schooling',
    # Energy/Resources
    'fossil_pct_filled', 'natural_resource_rents_per_gdp',
    # Industry
    'industry_share_gdp',
    # Subsidies
    'fuel_subsidy_gdp'
]
```
