# Carbon-Pricing Policy Recommendation Engine — Dashboard

An uncertainty-first Streamlit app: set a carbon price, pick a country, get a predicted CO₂ effect
with honest confidence. Built on the Phase-3 Bayesian dose-response engine (corrected June 2026).

## Structure — three pages

### ① Engine (default)
A world choropleth as the country picker, coloured by policy/evidence status only (teal = adopter /
data-informed, blue = near support, slate = far from support). LOCO-compliant: the colour encodes
*status*, never per-country effect size.

Sliders → hero impact number with a gradient credible-interval bar → dose-response curve. The robust
**−7 to −10% per $30 ETS** range is built into the presentation.

CIs are honest: widened 1.51× from the iid posterior after a June 2026 audit found MA(2) overlap was
making them ~30–35% too narrow (lag-1 residual autocorrelation 0.56).

### ② Evidence
Seven-method evidence table (SUPPORTIVE / ROBUST / UPPER BOUND / CONTEXT / NULL ID), each with
an ETS line and a carbon-tax line. The committed event-study figure
(`outputs/ets_covered_vs_uncovered_eventstudy.png`). Corrected sector-DiD row: *"Within-country
sector DiD: −3.4%/$10 (p=0.03), but the 2026-06-11 audit found the original pre-trend test was
miscomputed — the full-covariance test rejects (p≈0.004) and a pre-existing covered-sector trend
can account for the endpoint. Supportive, not clean identification."* The old "⭐ clean ID —
pre-trends pass" row is gone.

### ③ Methods & honesty
The identifying assumption stated plainly: EUA price is a market equilibrium price; identification
leans on within-country price swings net of country and year FE; all EU members share one price
path — robust association plus mechanism coherence, not an RCT. Common-path caveat documented.
"Tax and ETS are substitutes" labelled suggestive only (83-row cell, insignificant interaction).

## What it shows

- **Price sliders are the lever** (ETS / carbon tax, $/tonne; all prices in US$, not euros).
- **Country picker drives the *confidence*** — a reference-class badge (data-informed / near-support
  / far), because LOCO validation showed country covariates have zero out-of-sample skill at
  predicting which country beats the average effect.
- **Outputs:** predicted 3-yr CO₂/capita change (via `expm1` — not linear approximation), 90%
  Bayesian credible interval, P(reduce), dose-response curve with extrapolation guard beyond
  observed-support ceiling ($35 ETS; in-sample ETS max = $34.5).
- **Honest headline:** ETS works (≈ −7 to −10% per $30, robust); the carbon tax is unproven in
  aggregate data. Andersson (2019) found −6.3% in Swedish transport — the only solid tax estimate.

## Correctness (June 2026 audit fixes applied)

| Fix | Detail |
|---|---|
| **CI widening** | b_ets posterior sd widened 1.51× (iid → cluster-robust ratio); b_tax 1.08× |
| **Percent conversion** | `100 * expm1(eff * 3)` everywhere (was linear, overstating reductions) |
| **Extrapolation threshold** | ETS_OBS_MAX = $35 (in-sample p99 = $34.5; was $50 which is out-of-sample) |
| **Interaction guard** | Warning when tax contribution flips positive (ETS ≥ ~$27.7); labelled "unproven not harmful" |
| **Empty state** | Zero prices → "—" + prompt; no "P(reduces)=0%" |
| **Sector-DiD row** | Corrected to "supportive evidence" with the p=0.004 pre-trend rejection noted |

## Run locally

```bash
uv run streamlit run dashboard/app.py
```
Opens at http://localhost:8501. No model fitting at runtime — loads precomputed posterior draws.

## Architecture

| file | role |
|---|---|
| `app.py` | Three-page Streamlit UI |
| `build_artifacts.py` | Fits dose engine once, writes posterior.npz (+ H-3 widening) |
| `posterior.npz` | Posterior draws: `b_tax`, `b_ets`, `b_int` (per $10/tonne) |
| `country_support.csv` | 163 countries × confidence tag, reason, observed prices (44 adopters) |

### Regenerate artifacts (only if model or data changes)
```bash
uv run python dashboard/build_artifacts.py
```
(~1–2 min; requires PyMC/nutpie environment. The committed artifacts are the June 2026 versions.)

## Notes

- Effects are 3-year, on CO₂ per capita; identification rests on ~36 ETS / 26 tax countries,
  EU-heavy, so far-from-support countries get deliberately wide predictions.
- All prices in US$; EUA prices noted in EUR only as an approximate reference in captions.
- The posterior `b_int` (tax×ETS interaction) is kept in the engine but the tax contribution
  at default ETS=$30 is positive (interaction flips sign above ETS≈$27.7) — this is flagged
  as "unproven not harmful" whenever tax > 0.
- The causal modelling lives in `../notebooks/phase3_bayesian_engine.ipynb`.
