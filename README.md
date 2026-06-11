# Carbon Pricing Policy Effectiveness — Causal Inference Research

A causal ML pipeline that estimates how effective carbon-pricing policies are across countries, and
powers a policy recommendation engine. The research question is one of causal identification: carbon
taxes and emissions trading schemes (ETS) are not randomly assigned, so separating the policy effect
from the characteristics of countries that adopt them requires careful methodology.

**Dashboard:** deployed on Streamlit Community Cloud (June 2026), or run locally with
`uv run streamlit run dashboard/app.py` (see `dashboard/README.md` for details).

---

## Headline findings

**EU ETS:** robust negative effect — approximately **−7 to −10% CO₂/capita over three years per
$30/tonne**, robust across the designs the data supports (Bayesian dose-response engine,
staggered-robust DiD, country-trend checks), with supportive — not clean — evidence from a
within-country sector DiD. The effect is
primarily transmitted through fuel-switching in power and manufacturing (the sectors the ETS
actually covers).

**Carbon tax (standalone):** unproven in aggregate cross-country data. Binary TWFE +0.010 (p=0.57);
dose slope −0.0013/tonne (p=0.15); collapses to near-zero under country-specific linear trends
(collinear with a smoothly rising price). The one rigorous country-level tax evaluation is Andersson
(2019, AEJ:EP), which found −6.3% in Swedish transport emissions — a real effect that is transport-
concentrated and invisible in total CO₂.

Both conclusions survive the June 2026 full audit, including corrected treatment coding (see below).

---

## Data

**Panel:** 4,218 country-year observations, 163 countries, 1996–2021.

**Sources:** OWID CO₂ emissions (1750–2024 release), World Bank WDI (GDP, population, energy,
governance WGI indicators), World Bank Carbon Pricing Dashboard (tax and ETS prices), Eurostat GHG
by sector.

**Outcome:** 3-year forward log-change in CO₂/capita (`co2_per_capita_future_trend`), constructed
so that t+3 ≤ 2021 (requires emissions through 2024, unlocked by the 2024 OWID release).

**Treatment variables (clean, de-conflated):**

| Variable | Description |
|---|---|
| `has_tax` | Binary carbon tax indicator (implementation-year onsets, not first-priced year) |
| `has_ets` | Binary ETS indicator (accession-aware: Czechia, UK, Norway, Iceland, South Korea all correctly included after June 2026 fix) |
| `tax_price_only` | Observed WB tax price, $/tonne (0 where WB lacks an early datum) |
| `ets_price_only` | EUA/KETS price, $/tonne |
| `years_since_tax`, `years_since_ets` | Per-instrument timing (−1 = pre-onset or never-treated) |

`post_carbon_tax` and `tax_price` are **legacy conflated columns** (mix tax and ETS) — do not use
in models. See `docs/DATA_DICTIONARY.md` for the full variable reference.

**44 carbon-pricing adopters** in the corrected data (up from ~39 before the treatment-coding fix).

---

## Methods journey

The project moved through five identification strategies, each motivated by a limitation of the last:

1. **Classical DiD (TWFE + staggered-robust DID2S)** — established the combined carbon-pricing ATT
   (~−0.15) and its robustness (placebo p=0.649, LOO [−0.153, −0.101], Goodman-Bacon 4.3% bad
   weight, Rambachan-Roth breakdown M=0.34, Oster δ*=2.53). Problem: conflated tax with ETS.

2. **Causal forests / OrthoForest** — heterogeneity analysis; implementation capacity moderates
   effectiveness (−0.111/SD, p=0.073); fossil-dependence finding retired (old +0.049/SD was an
   imputation-flag artefact; real `fossil_pct` gives −0.065, p=0.37).

3. **De-conflated DiD + CausalForestDML / ForestDRLearner** — established "ETS carries the effect,
   tax unproven" by running clean `has_tax`/`has_ets` side by side: ETS −0.153 (p=0.005), tax
   +0.010 (p=0.80).

4. **Bayesian dose-response engine (PyMC)** — continuous ETS price as the lever; `b_ets` ≈ −0.010
   per $10/tonne (−7 to −10% per $30 over 3 years). Posterior CIs widened 1.51× after a June 2026
   audit found MA(2) autocorrelation was making them too narrow. Identifying assumption: within-
   country ETS price variation (the 2008–13 crash and subsequent recovery); all EU members share
   one price path, so effective treated clusters ≈ 1 for cross-country identification. This is
   stated plainly in the dashboard Methods page.

5. **Within-country sector DiD (Phase 4)** — compared EU ETS-covered sectors (power, refining,
   manufacturing) against uncovered sectors (road transport, buildings) within country×year cells.
   Dose: −3.4%/$10 (p=0.029); sector decomposition (power/manufacturing significantly negative,
   refining null) is genuine mechanism evidence. *Demoted from "clean ID" to supportive evidence*
   after a June 2026 audit found the pre-trend test had used a diagonal Wald ignoring covariances;
   the correct full-covariance Wald rejects parallel trends (χ²(8)=31.2, p=0.0001), and a
   pre-existing covered-sector trend of −1.25%/yr can account for the entire −19% endpoint.

**Negative results documented:** SDID/synthetic control fails (no comparable untreated economies);
Nordic synthetic control (pre-1990 data) null on total CO₂; LOCO shows zero out-of-sample skill
for covariate personalization of country effects.

---

## Intellectual honesty — findings retired under scrutiny

The project documents what it retired, not just what survived:

- **Democratic governance paradox** (April 2026): `democratic_legitimacy` appeared to negatively
  moderate effectiveness. Retired when the variable was correctly identified as PC3 (voice and
  accountability) — the interaction is p=0.27 and sign-unstable across methods.
- **Fossil-dependence "hurts" finding** (+0.049/SD, p=0.004): retired June 2026. `fossil_pct_filled`
  is a binary imputation flag, not a fossil share. With real `fossil_pct` the interaction is
  −0.065 (p=0.37) — noise.
- **Policy decay ~1%/yr**: the `years_since_tax` estimate used the conflated treatment variable
  during the era when `post_carbon_tax` mixed tax and ETS. Not validated on the corrected data.
- **Sector DiD "clean identification ⭐"**: demoted to supportive evidence (see above).
- **"Tax is redundant, not weak"** (from the tax×ETS interaction): identified from an 83-row cell
  of mostly non-EU/pre-ETS adopters; labelled suggestive only.

---

## Repo map

```
├── notebooks/
│   ├── data_cleaning.ipynb              — full data pipeline (treatment-coding fix applied June 2026)
│   ├── did_analysis.ipynb               — early exploratory DiD (superseded)
│   ├── did_analysis_2.ipynb             — second-generation DiD (superseded)
│   ├── causal_forest_analysis.ipynb     — CausalForestDML / OrthoForest (superseded banner present)
│   ├── phase1_robustness_checks.ipynb   — placebo, LOO, Goodman-Bacon, Rambachan-Roth, Oster
│   ├── causal_effects_library.ipynb     — heterogeneity interactions + per-country predicted ATTs
│   ├── phase2_multipolicy.ipynb         — de-conflated DiD, dose-response, ForestDRLearner
│   ├── fuel_subsidy_analysis.ipynb      — subsidy interaction (suggestive, insignificant)
│   └── phase3_bayesian_engine.ipynb     — PyMC hierarchical dose engine (Steps 1–15)
├── scripts/
│   ├── within_country_ets_did.py        — Phase 4 sector DiD + corrected pre-trend test
│   ├── eutl_auctioning_did.py           — EUTL installation-level DiD (upper bound)
│   ├── audit_sensitivity.py             — treatment-coding sensitivity re-runs
│   └── validate_treatment_fix.py        — data validation after treatment-coding fix
├── dashboard/
│   ├── app.py                           — Streamlit UI (3-page map-first design)
│   ├── build_artifacts.py               — fits dose engine, writes posterior.npz
│   ├── posterior.npz                    — posterior draws (b_tax, b_ets, b_int)
│   └── country_support.csv             — 163 countries × confidence tag / observed prices
├── data/
│   ├── cleaned/final_analysis_data.csv  — 4,218 obs × 69+ cols (treatment-coding fix applied)
│   └── raw/                             — source files (OWID, WB prices, Eurostat, EUTL)
├── docs/
│   ├── FINDINGS_LOG.md                  — append-only research log (read before citing anything)
│   ├── DATA_DICTIONARY.md               — all variables with sources and caveats
│   ├── AUDIT_2026-06-11.md              — full four-track post-deployment audit
│   └── audit_fixes/                     — numbered fix documents with all verified numbers
└── outputs/                             — figures and tables
```

---

## Reproducing the results

```bash
# Install dependencies (requires Python 3.11; PyMC needs nutpie on Windows)
uv sync

# Regenerate the analysis dataset (runs data_cleaning.ipynb end-to-end)
uv run jupyter nbconvert --to notebook --execute notebooks/data_cleaning.ipynb

# Run the dashboard locally
uv run streamlit run dashboard/app.py

# Regenerate posterior artifacts (only if model changes; ~2 min)
uv run python dashboard/build_artifacts.py

# Phase 4 sector DiD with corrected pre-trend test
uv run python scripts/within_country_ets_did.py
```

The committed `posterior.npz` and `country_support.csv` are current (June 2026 audit versions)
and the dashboard runs without re-fitting the model.

---

## References

- Andersson (2019, AEJ:EP) — Swedish carbon tax, −6.3% transport emissions (the one solid tax estimate)
- Dolphin & Xiahou (2024, Nature Comms) — meta-analysis of 80 carbon pricing evaluations (−4% to −15%)
- Callaway & Sant'Anna (2021) — staggered DiD
- Gardner (2022) — DID2S
- Rambachan & Roth (2023) — parallel-trends sensitivity
- Oster (2019) — OVB bounds
- Arkhangelsky et al. (2021) — Synthetic DiD
- Chernozhukov et al. (2018) — Double ML
- McElreath (2020) — Statistical Rethinking

*Solo learning project | Building causal inference, Bayesian modelling, and data product skills*
*Data: 1996–2021 | 163 countries | Sources: OWID, World Bank, Eurostat*
