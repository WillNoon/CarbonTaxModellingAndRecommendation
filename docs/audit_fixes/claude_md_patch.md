# CLAUDE.md patch — exact find→replace blocks

> Apply these changes to `CLAUDE.md` (permission-guarded — cannot be edited directly).
> Each block shows the exact string to find and the replacement.
> Generated 11 June 2026 by the post-audit documentation agent.

---

## Patch 1 — Dataset Status section: treatment-coding fix + new timing columns + adopter count

**FIND:**

```
### Primary Analysis File
**`final_analysis_data.csv`** — **4,218 obs × 69 cols, 1996–2021** (expanded 2026-06-02 with refreshed 2024 OWID emissions). 26 carbon-tax countries.
- Outcome: `co2_per_capita_future_trend` (3-year forward lag); caps panel at 2021 (needs emissions at t+3 = 2024).
- **Treatment — use the CLEAN, de-conflated indicators:** `has_tax` and `has_ets`. **`post_carbon_tax` CONFLATES carbon tax + EU ETS** (EU treated in 2005 = ETS launch) — do not use it for tax-specific work. Continuous: `tax_price_only`, `ets_price_only`. Governance moderators are `_z` (standardized); `democratic_legitimacy` = PC3.
```

**REPLACE WITH:**

```
### Primary Analysis File
**`data/cleaned/final_analysis_data.csv`** — **4,218 obs × 73 cols, 1996–2021**
(treatment-coding fix applied 2026-06-11; original 2026-06-02 data expansion unchanged).
**44 carbon-pricing adopters** (26 tax, 36 ETS; corrected from ~39 by adding Czechia, UK,
Norway, Iceland, South Korea to `has_ets` and fixing tax-onset years for 9 countries).

- Outcome: `co2_per_capita_future_trend` (3-year forward lag); caps panel at 2021.
- **Treatment — use the CLEAN, de-conflated indicators:** `has_tax` and `has_ets`.
  **`post_carbon_tax` CONFLATES carbon tax + EU ETS** (EU treated in 2005 = ETS launch) —
  do not use for tax-specific work. Continuous: `tax_price_only`, `ets_price_only`.
- **NEW timing columns** (June 2026 fix): `years_since_tax`, `years_since_ets`,
  `years_since_any_pricing` (replaces the old mis-named `years_since_tax`), `tax_onset_year`,
  `ets_onset_year`. Untreated convention: −1 for never-treated / pre-onset rows.
- Governance moderators are `_z` (standardized); `democratic_legitimacy` = PC3 (voice &
  accountability); `implementation_capacity` = PC1 (technocratic capacity).
```

---

## Patch 2 — fossil-SUSPECT paragraph: resolved/retired

**FIND:**

```
### 2. The Democratic Governance Paradox — RETIRED (re-validated 2026-06-02)
```
(the paragraph starting with this heading and ending before "### 3. Policy Decay Effect")

**REPLACE WITH** (keep the democratic-paradox text, add resolved fossil note):

```
### 2. The Democratic Governance Paradox — RETIRED (re-validated 2026-06-02)
```
(no change to the democratic-paradox text itself)

**THEN FIND in the §3 note block:**

```
### 2. Robust heterogeneity findings instead:** `implementation_capacity` improves effectiveness (−0.118 per SD, p=0.07). ⚠️ **AUDIT 2026-06-10 — the "fossil dependence reduces effectiveness (+0.049/SD, p=0.004)" finding is SUSPECT and must be re-run:** it used `fossil_pct_filled`, which is a binary *imputation flag* (mean 0.12), NOT fossil share — so the result may be picking up data-availability (which correlates with country type), not fossil dependence. Re-estimate with the real `fossil_pct` (0–100) before citing. See `docs/FINDINGS_LOG.md` (2 June 2026 + audit entry 10 June 2026).
```

**REPLACE WITH:**

```
**Robust heterogeneity findings:** `implementation_capacity` improves effectiveness (−0.111 per SD, p=0.073 on corrected data). **The "fossil dependence reduces effectiveness (+0.049/SD, p=0.004)" finding is RETIRED (audit 2026-06-11):** it used `fossil_pct_filled`, a binary *imputation flag*, not fossil share. With real `fossil_pct` (0–100): −0.065 (p=0.37) — noise. Do not cite the fossil-dependence finding. See `docs/FINDINGS_LOG.md` (11 June 2026 audit entry).
```

---

## Patch 3 — Phase 4 sector-DiD description: demoted

**FIND** (in CLAUDE.md — the capstone/Phase 4 section description or wherever it appears):

```
**Phase 4 within-country sector DiD is the cleanest** (clean control group, pre-trends pass p=0.41, −3.4%/$10) and stands as the **identification capstone**.
```

**REPLACE WITH:**

```
**Phase 4 within-country sector DiD is demoted to supportive evidence** (pre-trends reject
on the correct full-covariance Wald, χ²(8)=31.2, p=0.0001; a pre-existing covered-sector
trend of −1.25%/yr can account for the entire −19% endpoint). The sector decomposition
(power/manufacturing negative, refining null) is genuine mechanism evidence. See
`docs/audit_fixes/pretrend_correction.md` and the 11 June 2026 FINDINGS_LOG entry.
```

---

## Patch 4 — Repo structure block: real notebook names + data paths

**FIND:**

```
├── notebooks/
│   ├── data_cleaning.ipynb        ← Data pipeline
│   ├── phase1_did_analysis.ipynb  ← Classical DiD (binary & continuous)
│   └── phase1_causal_ml.ipynb     ← OrthoForest/CausalForest analysis
```

**REPLACE WITH:**

```
├── notebooks/
│   ├── data_cleaning.ipynb              ← Data pipeline (treatment-coding fix applied June 2026)
│   ├── did_analysis.ipynb               ← Phase 1 exploratory DiD (superseded)
│   ├── did_analysis_2.ipynb             ← Phase 1 second-gen DiD (superseded)
│   ├── causal_forest_analysis.ipynb     ← CausalForestDML / OrthoForest (superseded)
│   ├── phase1_robustness_checks.ipynb   ← Placebo, LOO, Goodman-Bacon, RR, Oster
│   ├── causal_effects_library.ipynb     ← Heterogeneity interactions + effects library
│   ├── phase2_multipolicy.ipynb         ← De-conflated DiD, dose-response, ForestDRLearner
│   ├── fuel_subsidy_analysis.ipynb      ← Subsidy interaction
│   └── phase3_bayesian_engine.ipynb     ← PyMC hierarchical dose engine (Steps 1–15)
├── data/
│   ├── cleaned/final_analysis_data.csv  ← Primary analysis dataset (4,218 obs, June 2026 fix)
│   ├── cleaned/combined_data.csv        ← Intermediate merged data
│   └── raw/                             ← Source files (OWID, WB prices, Eurostat, EUTL)
```

---

## Notes for the person applying the patch

- The `years_since_tax` in `ORTHOFOREST_CONFOUNDERS` in CLAUDE.md should be updated to
  `years_since_any_pricing` (the variable was renamed in the June 2026 fix).
- The `fossil_pct_filled` entry in the `DID_CONTROLS` list and `HETEROGENEITY_CANDIDATES` list
  should be changed to `fossil_pct`.
- Remove `carbon_tax_governance` from `GOVERNANCE_VARS_ALL` (column no longer in the dataset).
- Add `governance_pc3`, `implementation_capacity_pc`, `democratic_legitimacy_pc`,
  `political_stability_pc` to the documented governance vars (they now exist in the data).
