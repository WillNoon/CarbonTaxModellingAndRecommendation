# Carbon-Pricing Policy Recommendation Engine — Dashboard

An uncertainty-first Streamlit app: set a carbon price, pick a country, get a predicted CO₂ effect with
honest confidence. Built on the Phase-3 Bayesian dose-response engine.

## What it shows

- **Price sliders are the lever** (ETS / carbon tax, $/tonne) — the effect comes from the *price*, not the country.
- **Country picker drives the *confidence*** — a reference-class tag (🟢 data-informed / 🟡 near-support / 🔴 far),
  because we validated (leave-one-country-out) that country covariates can't predict *which* country beats the average.
- **Outputs:** predicted 3-yr CO₂/capita change, 90% credible interval, P(reduce), a dose-response curve with an
  **extrapolation guard** beyond observed prices (≳ €50 ETS), and an **evidence-base expander** summarising every
  robustness check.

The honest headline baked in: **ETS works (≈ −7 to −10% per €30, robust); the carbon tax is unproven in aggregate
data.** See `../docs/OVERNIGHT_SESSION_2026-06-11.md` and `../docs/FINDINGS_LOG.md` for the full story.

## Run locally

```bash
uv run streamlit run dashboard/app.py
```
Opens at http://localhost:8501. No model fitting happens at runtime — the app loads precomputed posterior draws,
so it's instant.

## Architecture

The heavy Bayesian fit runs **once, offline**, and is persisted; the app only does fast arithmetic on the draws.

| file | role |
|---|---|
| `app.py` | the Streamlit UI (loads artifacts, computes dose-response, renders) |
| `build_artifacts.py` | fits the dose engine once → writes the two artifacts below |
| `posterior.npz` | posterior draws of `b_tax`, `b_ets`, `b_int` (per $10/tonne) |
| `country_support.csv` | per-country confidence tag + reason + latest observed prices |

### Regenerate the artifacts (only needed if the model changes)
```bash
uv run python dashboard/build_artifacts.py
```
(~1–2 min; requires the PyMC/nutpie environment. The committed artifacts are current.)

## Deploy (Streamlit Community Cloud)

1. Push the repo to GitHub.
2. At share.streamlit.io, point a new app at `dashboard/app.py` on this branch.
3. Dependencies: Streamlit Cloud reads `pyproject.toml`/`requirements.txt`. The app itself needs only
   `streamlit`, `numpy`, `pandas`, `matplotlib` at runtime (NOT pymc — the posterior is precomputed and committed),
   so a minimal `requirements.txt` keeps the deploy fast. The committed `posterior.npz` + `country_support.csv`
   ship with the repo, so no fitting happens in the cloud.

## Notes

- Effects are 3-year, on CO₂ per capita; identification rests on ~26 tax / 29 ETS countries (EU-heavy), so 🔴 FAR
  countries get a deliberately weak/wide prediction.
- The dashboard is the *build-fast* layer of the project; the causal modelling lives in
  `../notebooks/phase3_bayesian_engine.ipynb`.
