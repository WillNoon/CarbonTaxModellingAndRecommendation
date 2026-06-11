# Data Fix — Treatment-Coding Errors (AUDIT 2026-06-11, Part 1)

Fixes F1, F2, F3, F6 + the New Zealand 2016 ETS gap, at source in
`notebooks/data_cleaning.ipynb`. The notebook was re-executed end-to-end and
`data/cleaned/final_analysis_data.csv` (plus the intermediate `combined_data.csv`,
`analysis_data.csv`, `carbon_tax_wb_yearly_cleaned.csv`) regenerated.

Validation: `scripts/validate_treatment_fix.py` — **all checks pass**.

---

## What changed (by finding)

### F1 — `has_ets` / `ets_price_only` membership (accession-aware)
**Before:** cell ~50 expanded a static `eu_countries` list and assigned EU ETS from 2005 to all
members, relying on the `tax_price>0` melt filter. Name mismatch (`"Czech Republic"` ≠ OWID
`"Czechia"`) and missing UK/Norway/Iceland meant five countries were never coded; accession
states (Bulgaria/Romania/Croatia) were coded from 2005. Korea (`"Korea, Rep."`) was silently
dropped by the `isin(valid_countries)` filter at cell ~43.

**After:** cell ~50 now defines an explicit `ETS_MEMBERSHIP` dict, `country → (entry_year, exit_year)`,
with OWID names. A new accession-correction cell (inserted after the panel merge, where every
`(country, year)` row exists) enforces those windows: in-window → `has_ets=1` with the EUA price
(read live from `data/raw/carbon_tax_wb_prices.csv` row `ETS_EU`); out-of-window → `has_ets=0`,
price 0. The same cell rescues South Korea KETS (row `ETS_KR`), proxies UK ETS 2021 with the EUA
price (no separate UK-ETS row exists in the WB price file), and fills the NZ 2016 gap.

| Country | ETS before | ETS after |
|---|---|---|
| Czechia | never coded | 2005–2021 |
| United Kingdom | never coded | 2005–2021 (EU ETS to 2020, UK ETS 2021 @ EUA proxy) |
| Norway | never coded | 2008–2021 |
| Iceland | never coded | 2008–2021 |
| South Korea | never coded (dropped by filter) | 2015–2021 (KETS prices) |
| Bulgaria | 2005–2021 | 2007–2021 (accession year) |
| Romania | 2005–2021 | 2007–2021 (accession year) |
| Croatia | 2005–2021 | 2013–2021 (accession year) |

### F2 — `has_tax` onsets = implementation years, not first-priced years
**Before:** cell ~64 set `has_tax = (tax_price_only > 0)`, so onset = first year the WB price series
reports a value. WB price coverage starts late for several taxes, backdating onsets and leaving
treated countries in the control pool for years.

**After:** the correction cell applies a documented `TAX_ONSET` dict (implementation years) and sets
`has_tax=1` from that year. `tax_price_only` is **left untouched** (still the observed WB price, 0
where WB lacks an early datum) — the binary indicator is corrected while the dose variable stays
honest. WB `carbon_tax_wb_general.csv` carries a `Status` field but no machine-readable
implementation-year column, so onsets come from a documented hardcoded dict (matching the
audit-verified values).

| Country | has_tax onset before | actual implementation | has_tax onset after |
|---|---|---|---|
| Denmark | 2007 | 1992 | 1996 (panel start) |
| Finland | 2000 | 1990 | 1996 (panel start) |
| Slovenia | 2007 | 1996 | 1996 |
| Estonia | 2011 | 2000 | 2000 |
| Latvia | 2014 | 2004 | 2004 |
| Ukraine | 2016 | 2011 | 2011 |
| Portugal | 2019 | 2015 | 2015 |
| Mexico | 2015 | 2014 | 2014 |
| South Africa | 2020 | 2019 | 2019 |

(Denmark/Finland implemented pre-1996; the panel starts 1996, so the onset shows 1996 — they are
correctly treated for the entire panel rather than entering late.)

### F3 — per-instrument treatment timing
**Before:** cell ~69 computed `treatment_year` / `years_since_tax` / `years_relative_to_treatment`
from **any** carbon pricing (tax OR ETS); `years_since_tax` was therefore "years since first any
pricing" and sat in the validated confounder set under a wrong name.

**After:**
- The any-pricing concept is renamed `years_since_any_pricing` (the legacy `treatment_year`,
  `years_relative_to_treatment`, `post_carbon_price`, and the conflated `post_carbon_tax` continue
  to track any-pricing, preserving their documented meaning — `post_carbon_tax` stays BANNED for
  tax-specific work).
- **New** `years_since_tax`, `years_since_ets` (and `tax_onset_year`, `ets_onset_year`) are built
  from the **corrected** per-instrument onsets.
- **Untreated convention:** `-1` for never-treated / pre-onset rows (kept from the original so
  confounder code expecting `-1` still works); `year − onset ≥ 0` from the onset year onward.

### F6 — `fossil_pct` fill vs overwrite (cheap bonus)
**Before:** cell ~90 set `fossil_pct = 100 − renewable − nuclear` for a 21-country `non_nuclear`
list **without** an `isna()` mask, overwriting observed WB values.
**After:** added the `& fossil_pct.isna()` mask — it now only fills missing cells. `fossil_pct`
remains within [0, 100].

### New Zealand 2016 ETS gap (bonus)
NZ had a single spurious `has_ets=0` at 2016 (missing price datum). The correction cell sets
`has_ets=1` and linearly interpolates the price between 2015 and 2017
(`(4.93 + 12.51)/2 = 8.72`).

---

## Validation results (`scripts/validate_treatment_fix.py` — ALL PASS)

- Row count **4,218**; **no** `(country, year)` duplicates; `years_since_tax`/`years_since_ets`/
  `years_since_any_pricing` present; `fossil_pct ∈ [0, 100]`.
- All F1 membership windows and accession-zeroing checks pass (incl. UK 2021 EUA proxy, NZ 2016
  interpolation).
- All F2 tax onsets match the table above.
- **Outcome `co2_per_capita_future_trend` is byte-for-byte unchanged vs the committed file**
  (0 / 4,218 rows differ; spot-checked Germany 2010, Sweden 2005, USA 2012, Japan 2008,
  Brazil 2015). The fix only re-labels treatment, never the outcome.

---

## Regression comparison (corrected coding, clustered by country)

Dose: `d3 ~ Ptax + Pets + C(country) + C(year)` (sample: non-null `d3`, t+3 ≤ 2021).
Binary TWFE: `co2_per_capita_future_trend ~ has_tax + has_ets + C(country) + C(year) + log_gdp + log_population + natural_resource_rents_per_gdp`.

| Spec | Audit "corrected" target | New file (this fix) |
|---|---|---|
| Dose `Pets` (per $10) | −0.0100 (p<.0001) | **−0.01001 (se .00181, p<.0001)** |
| Dose `Ptax` (per $10) | −0.0013 (p=.15) | **−0.00131 (se .00091, p=.1507)** |
| Binary `has_ets` | −0.124 (p=.054) | **−0.12329 (se .06448, p=.0559)** |
| Binary `has_tax` | +0.024 (p=.56) | **+0.02379 (se .04149, p=.5664)** |

The regenerated data reproduces the audit's verified corrected-coding numbers to the fourth
decimal. Running `scripts/audit_sensitivity.py` against the new file now shows its "original" and
"corrected" columns as **identical** — confirming the source data already embeds exactly the
corrections that script applied in-memory.

**Story unchanged and slightly strengthened:** ETS carries the effect (dose `Pets` ≈ −0.010,
strongly significant; binary `has_ets` ≈ −0.12, p≈.056); the tax remains weak/unproven
(dose `Ptax` n.s.; binary `has_tax` now small positive, n.s.).

The fossil-dependence re-run (real `fossil_pct`, z-scored) also reproduces the audit:
`has_tax×fossil_z` = +0.071 (p=0.27) — the old "+0.049/SD, p=0.004" was an artifact of the
`fossil_pct_filled` imputation flag; `has_ets×fossil_z` = −0.119 (p=0.092), suggestive only.

---

## Judgment calls

- **Dropped-jurisdiction audit (cell ~43 `isin` filter):** the full dropped list is **overwhelmingly
  subnational** — US states (California, RGGI, Washington…), Canadian provinces (Quebec, BC…),
  Chinese provincial pilots (Guangdong, Hubei, Shenzhen…), Mexican states, Japanese cities (Tokyo,
  Saitama). The **only** national jurisdiction that maps to a panel country is **`ETS_KR` = "Korea,
  Rep." → South Korea**, which was rescued. None of the others correspond to a panel country, so
  none were rescued. China's *national* ETS (2021) has no row in this WB file (only provincial
  pilots), so it could not be rescued from this source.
- **UK 2021 price:** the WB price file has no separate UK-ETS row, so UK 2021 `ets_price_only` is
  proxied with the 2021 EUA price (49.78), flagged in code as an approximation.
- **`tax_price_only` not backfilled** for the corrected tax onsets (e.g. Denmark 1996–2006): kept as
  the observed WB price (0 where unavailable) so the dose variable stays honest while the binary is
  corrected — exactly the audit's prescription.
- **Legacy conflated columns** (`post_carbon_tax`, `treatment_year`, `years_relative_to_treatment`)
  intentionally repointed to `years_since_any_pricing` so their documented (conflated) meaning does
  not silently change; they remain banned for tax-specific work in favour of `has_tax`/`has_ets`.

## Scope note
Only `notebooks/data_cleaning.ipynb`, `data/cleaned/*`, and `scripts/validate_treatment_fix.py`
(+ this doc) were created/modified by this task. (`scripts/within_country_ets_did.py` shows as
modified in git but is pre-existing uncommitted audit work, untouched here.) Nothing was committed
or pushed.
