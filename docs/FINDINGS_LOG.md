# Findings Log — Carbon Tax Research

> Append new findings at the TOP. Each entry: date, what was found, what it means for the research.

---

## 11 June 2026 — Post-deployment full audit + corrections (AUDIT_2026-06-11)

Full four-track audit (data, methodology, documentation, dashboard) run after dashboard deployment.
Numbers below all verified and reproduced from `scripts/audit_sensitivity.py` and the audit_fixes docs.

### Treatment-coding fix (F1+F2+F3)

**`has_ets` had five countries incorrectly coded as never-treated.** The EU member list had name
mismatches and no accession logic. After correction:

| Country | Before | After |
|---|---|---|
| Czechia | never coded (name mismatch) | 2005–2021 |
| United Kingdom | never coded | 2005–2021 (UK ETS 2021 @ EUA proxy) |
| Norway | never coded | 2008–2021 (EEA member) |
| Iceland | never coded | 2008–2021 (EEA member) |
| South Korea | never coded (filter dropped "Korea, Rep.") | 2015–2021 (KETS) |
| Bulgaria, Romania | coded from 2005 | corrected to 2007 (accession year) |
| Croatia | coded from 2005 | corrected to 2013 (accession year) |

**`has_tax` onsets** were price-data artefacts (`has_tax = (tax_price > 0)`), not implementation
years. Corrected for Denmark (1992→1996 panel start), Finland (1990→1996), Slovenia (1996 from 2007),
Estonia (2000 from 2011), Latvia (2004 from 2014), Ukraine (2011 from 2016), Portugal (2015 from 2019),
Mexico (2014 from 2015), South Africa (2019 from 2020).

**`years_since_tax`** was actually "years since first ANY pricing (tax OR ETS)" — renamed
`years_since_any_pricing`. New per-instrument `years_since_tax` and `years_since_ets` added.

Total adopters: **44** (was ~39); outcome `co2_per_capita_future_trend` is byte-for-byte unchanged.

### Conclusions survive and strengthen

Re-runs on corrected data (see `docs/audit_fixes/rerun_numbers.md`):

| Spec | Before fix | After fix | Verdict |
|---|---|---|---|
| Dose `b_ets` per $10 | −0.0102 (p<.0001) | **−0.0100 (p<.0001)** | Headline unchanged |
| Dose `b_tax` per $10 | −0.0014 (p=.15) | **−0.0013 (p=.15)** | Tax still weak |
| Binary `has_ets` | −0.108 (p=.12) | **−0.153 (p=.005)** | ETS *strengthens* (5 new countries) |
| Binary `has_tax` | −0.027 (p=.57) | **+0.010 (p=.80)** | Tax weakens further |

Phase 1 robustness suite (corrected data + real `fossil_pct`): TWFE ATT −0.154 (SE=0.044, p=0.001);
DID2S −0.161 (SE=0.051, p=0.002); placebo −0.020 (p=0.649, n.s.); LOO [−0.153, −0.101], 0 sign flips;
Goodman-Bacon 4.3% bad weight (weighted avg −0.154 matches TWFE); Rambachan-Roth F=2.243 (p=0.067),
max δ̄=0.0672; Oster δ*=2.529 at Rmax=1.5 (OVB must be 2.5× observed selection to zero the effect).

### Pre-trend correction (sector DiD, C-1)

The Phase-4 "pre-trends pass, χ²(8)=8.3, p=0.41" claim was computed as a diagonal Wald (ignoring
coefficient covariances). The correct **full-covariance Wald rejects parallel trends**:

- χ²(8) = **31.23**, p = **0.0001**
- Conservatively F(8,26) = **3.90**, p = **0.0038**
- Wild-cluster bootstrap p = **0.019**

Pre-2005 covered-vs-uncovered gaps decline monotonically. Pre-period covered-specific trend:
**−1.25%/yr (SE 0.72, p=0.093)**, extrapolating to **−20% by 2021** — equals/exceeds the entire
−19% endpoint. Rambachan-Roth robust-CI breakdown M̄ = **0.04** (extremely fragile).

**Sector DiD demoted from "clean ID ⭐" to supportive evidence.** The sector decomposition
(power/heat −0.049 p=0.018, manufacturing −0.046 p=0.005, refining null) remains genuine mechanism
evidence — but the pre-existing trend means the magnitude cannot be attributed cleanly to the ETS.

### Fossil-dependence finding retired

With real `fossil_pct` (0–100 scale) instead of the imputation flag:
- `has_tax × fossil_z` = +0.071 (p=0.27) — null (was +0.042/SD, p=0.004 with the flag)
- `has_ets × fossil_z` = −0.119 (p=0.092) — suggestive sign flip (fossil-heavy countries may
  respond more to ETS, mechanistically coherent with coal-switching), but coding-sensitive

**Retire the "fossil dependence hurts" claim everywhere.**

### CI widening

Dashboard posterior CIs widened 1.51× for `b_ets` (lag-1 residual autocorrelation 0.56; MA(2)
overlap was making iid posterior SDs 30–35% too narrow). `b_ets` sd: 0.001338 → **0.001883**.

### Dashboard redesign

Three-page map-first app: Engine (choropleth country picker + hero CI bar + dose curve), Evidence
(7-method table + event study), Methods (identifying assumption + honesty). Correctness fixes: A2
percent conversion (expm1), A3 extrapolation thresholds corrected to $35 ETS (in-sample max $34.5),
A1 interaction guard (tax flips positive at ETS ≥ $27.7 — flagged as "unproven not harmful").

---

## 11 June 2026 — CAPSTONE: Phase 4 sector DiD is the best ETS identification public data allows; threshold-RD frontier documented

> ⚠️ [SUPERSEDED — see 11 June 2026 audit entry above]
> The "pre-trends pass (p=0.41)" claim in this entry used a diagonal Wald; the correct full-covariance
> Wald rejects (p=0.0001). The "clean ID ⭐" status is demoted to supportive evidence. The sector
> decomposition finding (power/manufacturing negative, refining null) survives as mechanism evidence
> but the claimed magnitude is not cleanly identified. See `docs/audit_fixes/pretrend_correction.md`.

Closed the identification arc. Pushed public data across three resolutions — **country** (dose-response / synthetic control), **sector** (Eurostat covered-vs-uncovered DiD), **installation** (EUTL auctioning DiD). The **Phase 4 within-country sector DiD is the cleanest** (clean control group, pre-trends pass p=0.41, −3.4%/$10) and stands as the **identification capstone**.

The one rung higher — an **RD/matching on the ~20MW ETS inclusion threshold** (barely-covered vs barely-uncovered plants; Colmer et al. 2024) — is **blocked by data access, not method**: it needs plant-level emissions *below* the ETS threshold, which EUTL (covered-only) and E-PRTR (100kt threshold, above the ETS cutoff) don't provide; the literature used confidential UK/French secure-lab micro-data. Full design + access path recorded in `docs/FUTURE_DATA_EXPANSION.md` (won't pursue — no institutional access).

**Final ETS verdict:** robustly real and directionally consistent across all designs (~−7 to −10%/€30 dose; covered sectors ~−19% vs uncovered by 2021), best-identified by the sector DiD; clean point magnitude remains inherently uncertain (price trends with time; treated sectors decarbonised for many reasons). **Tax: unproven** in aggregate, transport-only per Andersson. **Next: ship the dashboard.**

---

---

## 11 June 2026 — PHASE 4b / EUTL installation-level (gold-standard data): confirms direction, but the confound is fundamental

Got the actual installation-level data — EU ETS Data Package (Abrell, Zenodo rec 20509231, 492MB; kept a 1.1MB compact installation-year panel `data/raw/eutl_installation_panel.csv.gz`, dropped the 408MB transaction log). 195k installation-years, 17k installations, 32 countries, verified emissions + free allocation per installation. Code `scripts/eutl_auctioning_did.py`, figure `outputs/eutl_auctioning_eventstudy.png`.

**The natural experiment:** EU ETS Phase 3 (2013) — power/combustion installations LOST free allocation (full auctioning; free-alloc/emissions 1.24→0.81→**0.37 by 2020**) while energy-intensive industry KEPT it (~0.89). DiD with **installation + year FE** (absorb the aggregate price trend), clustered by country.

**Result — large but NOT clean:**
- **combustion:post2013 = −0.32 (p<0.001) → power emissions −27% vs industry** after losing free allocation; event study grows to −47% by 2020.
- **⚠️ Pre-trends NOISY:** 2009-10 gaps significantly *positive* (+0.09, +0.14; financial-crisis era hit the two groups differently). Not clean parallel trends.
- **⚠️ Fundamental confound:** auctioning was assigned to *exactly* the sector (power) that decarbonised most for **non-ETS** reasons (collapsing solar/wind costs, coal phase-outs). So −27% conflates "had to pay for carbon" with "the power transition." **Upper bound, not clean ETS isolation.**

**Honest verdict:** the gold-standard *data* doesn't deliver gold-standard *identification* — because the policy assigned the treatment to the most-confounded sector. Ironically the Eurostat sector design (Phase 4, *passing* pre-trends) is the cleaner of the two. The genuinely clean design is an **RD on the ~20MW/25kt ETS inclusion threshold** (barely-covered vs barely-uncovered installations; Colmer/Martin/Muûls/Wagner 2024) — that needs threshold/matching data and is the true next frontier.

**Recurring lesson, now confirmed at every data resolution (country, sector, installation):** the ETS effect is *directionally* robust everywhere (covered/power decarbonised ~10-27% more than controls), but a *clean magnitude* is elusive because the carbon price trends with time AND the treated sectors decarbonised for many overlapping reasons. More/better data sharpened the picture but did not dissolve this — it's the nature of the question, not a fixable data gap. The defensible headline remains the Phase-4 sector DiD (−3.4%/\$10, pre-trends pass) with this as corroborating granularity.

---

## 11 June 2026 — PHASE 4 / THE DATA FIX WORKED: within-country covered-vs-uncovered DiD CLEANLY identifies the EU ETS

> ⚠️ [SUPERSEDED — see 11 June 2026 audit entry above]
> This entry's "clean ID" headline and "pre-trends pass χ²(8)=8.3, p=0.41" are incorrect. The
> correct full-covariance Wald rejects parallel trends (p=0.0001). The sector decomposition
> (power/manufacturing vs refining) survives as mechanism evidence; the magnitude does not.
> The defence that "covered-trend is over-controlling because pre-trends are flat" also fails —
> that defence was contingent on the (faulty) p=0.41. Status: supportive evidence, not clean ID.

The whole project's ceiling was "no control group" (every rich country priced carbon at once → cross-country and synthetic-control designs fail). **Fix: look INSIDE a country.** The EU ETS covers some sectors (power, refining, energy-intensive industry) and NOT others (road transport, buildings/households). Comparing **covered vs uncovered emissions within country×year** gives a control group, and **country×year fixed effects absorb every country-wide confound** (recessions, weather, national decarbonisation trends) — exactly what killed the cross-country estimates.

**New data:** pulled Eurostat `env_air_gge` (GHG by CRF source sector, CO2, thousand tonnes) → `data/raw/eurostat_ghg_sectors.csv` (32 geos, 1990-2024, 6 sectors). Covered = CRF1A1A power/heat + CRF1A1B refining + CRF1A2 manufacturing; Uncovered = CRF1A3B road transport + CRF1A4A commercial + CRF1A4B households. Code: `scripts/within_country_ets_did.py`. Figure: `outputs/ets_covered_vs_uncovered_eventstudy.png`.

**Result (27 EU countries, 1995-2021, country×year + country×sector FE, clustered by country):**
- **Dose DiD: `covered × ETS-price` = −0.034 per $10/t (p=0.029).** Covered sectors fall ~3.4%/$10 MORE than uncovered, *within country-year* → at €30 a −10% differential, at €70 −24%.
- **Binary DiD: `covered × post-2005` = −0.106 (p=0.08).**
- **Event study: parallel pre-trends roughly hold** (1996-2003 gaps small + insignificant, mean ~+3.6%), then the gap **widens steadily and significantly to −19% by 2021** (p=0.02), tracking the ETS price recovery (€5→€47) + cap tightening. Effect concentrates in the high-price era — converging with the dose-engine's era-stability finding from a totally different design.
- **NOT a crisis artefact:** dropping 2008-09 *strengthens* it (−0.042, p=0.018).

**Why this is the strongest ETS evidence in the project:** it uses a **clean within-country control group**; country×year FE absorb every *country-wide* confound (this part IS robust by construction); five independent designs now converge on a real ETS effect; and this one finally has a defensible counterfactual. **Fixing the data (sectoral coverage) materially improved the identification.**

**TIGHTENING (#1, run same day) — honest mixed result:**
- **Formal pre-trend test PASSES:** joint test of 1996-2003 covered:year gaps χ²(8)=8.3, **p=0.41** → parallel trends formally holds (better than the tax ever managed).
- **Sector decomposition (great mechanism evidence):** power/heat −0.049 (p=0.02), manufacturing −0.046 (p=0.005), **refining +0.001 (p=0.95, null)** — concentrated in sectors with real abatement options, not refining (few options + free allocation). A pure secular trend wouldn't single those out.
- **⚠️ BUT covered:Pets does NOT survive a covered-specific linear trend** (−0.034 → −0.0014, p=0.81). The **same price-vs-trend collinearity that sank the tax**: the ETS price drifts up over the sample, so "price effect" vs "covered-sector trend" can't be fully separated. *Defence:* since pre-trends are FLAT, a covered-linear-trend is **over-controlling** (it imposes a trend on a post-2005 break, absorbing the treatment — the standard "don't add unit trends when pre-trends are clean" caution). So the result stands, but is NOT bulletproof.

**Corrected bottom line:** strongest ETS identification we have (clean control group + passing pre-trends + sector-specificity + not crisis-driven), genuinely stronger than the tax — but it still shares the project's deep, recurring fragility: **the carbon price trends with time, so no design here fully escapes price-vs-trend collinearity.** Honest, not bulletproof.

**Other caveats:** "manufacturing" only partly ETS-covered (sub-threshold plants excluded → bias toward zero); design identifies the ETS, not the tax (taxes also cover transport/heating). 

**Next frontier:** EUTL installation-level — installation entry/exit + free-allocation variation could provide *non-trend* identification that finally breaks the price-vs-trend collinearity. That's the gold standard.

---

## 11 June 2026 — TAX DATA EXPANSION (Nordic synthetic control, pre-1990): tax weak everywhere (SC hinted transport; a dose cross-check demoted it)

> Reading order note: this entry's *initial* SC results hinted at a transport effect; the **CROSS-CHECK bullet below
> demotes that** — a same-night dose-engine test on oil CO₂ did not reproduce it. Net conclusion: **tax weak on total
> AND transport in our data.** Kept the original bullets for the learning trail, with the correction inline.

Extended emissions back to 1965 (OWID raw, history to 1750) so the Nordic carbon-tax adopters (Finland 1990, Norway 1991, Sweden 1991, Denmark 1992) finally get a pre-treatment period. Classic synthetic control, pre 1970→tax-year, post tax-year→2004 (pre-ETS, so donors stay untreated → isolates the *tax*); donor pool = 22 high-income non-tax economies; Abadie in-space placebo inference. Notebook Step 15; figure `outputs/nordic_tax_oil_sc.png`.

- **On TOTAL CO₂/cap: ≈ null** (Sweden −5.7%, Finland −2.3%, both p=0.91; Denmark/Norway positive, n.s.). **Independently confirms the engine's "tax unproven on total CO₂"** — now with a proper pre-period and a credible donor pool (synthetic Sweden ≈ France).
- **On OIL CO₂/cap (transport-fuel proxy): large negative** — Sweden **−20.7%**, Finland **−27.0%**, Denmark **−15.3%**, Nordic-3 aggregate **−15.6%**. Directionally + mechanistically **corroborates Andersson (2019)** (−6.3% transport). Norway (oil producer) is the expected outlier (~0).
- **Initial (over-)reading — SEE CROSS-CHECK, now demoted:** *transport ≈ ¼ of emissions, so a −20% transport cut → ~−5% total — looked like "tax bites transport, vanishes in total."* This is **not supported** once stress-tested (the oil estimates are insignificant + pre-tax-confounded + not reproduced by the dose engine). Retained for the learning trail.
- **Honest caveats:** NOT statistically significant (Abadie p>0.25 — cross-country oil paths noisy); and Sweden's oil-CO₂ decline **began in the early-1980s nuclear rollout**, pre-tax (visible in the figure), so the raw gap overstates the tax. So: *suggestive, mechanism-coherent, Andersson-consistent — not confirmed.*


- **CROSS-CHECK (added same night):** re-running our *dose engine* on oil CO₂ (1996+) shows the **tax is NOT significant on transport either** (Ptax −0.0008, p=0.37), so the SC's large oil estimates do **not** survive an independent design. Corrected conclusion: **tax effect weak everywhere in our data**; Andersson's within-Sweden transport design is the only robust transport evidence. ETS robust on oil too (caveat: ETS doesn't cover road transport pre-2027).

**Net:** the expansion succeeded as a method and delivered the convergent, honest answer the 1996+ data could not. The remaining ceiling is statistical power / sectoral data, not design.

---

## 11 June 2026 — DEEPEN (synthetic control / SDID): there is NO clean control group for the EU ETS — and why our price-engine is the right tool

Built classic synthetic control then Synthetic DiD (Arkhangelsky et al. 2021) **from scratch** to try to identify the ETS effect with a gold-standard design (notebook Step 14). It **fails — informatively** — and the failure is the result.

- **Classic SC, naive (all 118 never-treated donors, match outcome only):** near-perfect pre-fit (RMSE 0.0001) achieved by an **absurd** synthetic — Germany ≈ Qatar+Bahrain+Algeria+Zimbabwe. Textbook overfitting: matched the *numbers*, not the *country*. The −8% "effect" is meaningless.
- **SC, comparable donors + covariate matching:** sensible donors (S.Korea/US/HK) but **poor pre-fit** (pre-treatment gap −7%) → the post "effect" is just trajectory divergence.
- **SC, match full pre-path within comparable pool:** finally credible pre-fits, but estimates are **wildly unstable across countries that adopted the same policy the same year**: Germany ≈ **0%**, Italy **−40%**, Austria **−30%**. The spread *is* the finding — each "effect" is the country's own post-2005 macro story (Italian recession, German reunification tail), not the ETS.
- **SDID (block, all 13 EU-2005 ETS-only vs donors):** unit weights collapse to **near-uniform** (top weight ≈ 0.02–0.08) because no donor resembles the treated group → "synthetic EU" ≈ simple average of developing/emerging economies, which *grew* emissions while the EU fell → spurious **−30 to −40%** with a placebo "p=0.000" that is itself an artifact (the placebo pool lacks the mature-economy-decline confound).

**Root cause (the real result):** the treated units are mature, high-income, *already-decarbonizing* economies; a valid counterfactual needs *similar* economies that **didn't** price carbon — and those barely exist (≈ the US is the only one). **No estimator manufactures a control group that doesn't exist.** This rigorously confirms the audit's "single-cluster" concern.

**Unifying insight (why our engine is right):** synthetic control needs a comparable *control group* (absent here → fails); our **continuous-price engine** needs within-country *price variation* (present: the ETS price crash/recovery → works). For this data, **price-variation identification is correct and control-group identification is not — SDID failing is the proof.** Our pooled, trend-robust ETS estimate (−0.0081/$10, ≈ −7%/3yr @ €30) stands as the most defensible number precisely because it never needed a control group.

**Implication:** the binding constraint is **data, not method** — real progress needs *within-country* variation that creates a control group (sub-national/sectoral ETS coverage) or a longer pre-period. The latter is achievable for the **tax** → pivoting to the pre-1990 data expansion (Nordics adopted ~1990–92; OWID emissions reach back to 1750, so a clean pre-period + an untreated-OECD donor pool both exist).

---

## 11 June 2026 — EXTERNAL ANCHOR (Sweden/Andersson) + country-trend robustness: ETS survives, tax collapses

Two paired checks. (1) Anchored the engine to the one country with a gold-standard published causal estimate — Andersson (2019, AEJ:EP), Sweden's carbon tax. (2) The anchor exposed a confound, which a country-specific-trend robustness check then tested generally.

**(1) Sweden anchor — partial pass.** Engine prediction for Sweden @ its prices = **−8.1%/3yr** (CI [−12.3,−4.1]), which sits inside the Dolphin–Xiahou meta range (−4 to −15%) with the right sign → **calibration PASS** (not broken). BUT it **over-attributes**: −8.1%/3yr ≈ −2.7%/yr ≈ *Sweden's entire observed −2.65%/yr CO₂/cap decline* (7.17→3.70 t, −48% over 1996–2021) — implausible, since much of Sweden's drop is grid decarbonization (nuclear/hydro/district heat), not the tax. Sweden's **own** within-country tax→total-CO₂ response is only ~−1%/3yr, far below the pooled engine's −7.5% tax-only. Reconciles with Andersson (his −6.3% is **transport**; our weak **total** response is what you'd expect if the tax bites transport but total CO₂ is dominated by non-tax electricity decarbonization). Scope mismatch (transport vs total) means no exact numeric match was expected.

**(2) Country-specific linear trends (each country its own decarbonization slope), on top of country+year FE, clustered:**
- **ETS SURVIVES:** `b_ets` −0.0109 → **−0.0081 (p<0.001)**; ~26% attenuation but still strong. €30 ETS: −9.8% → **−7.3%/3yr**. "ETS carries it" holds even under this demanding control.
- **TAX COLLAPSES:** `b_tax` −0.0026 → **+0.0022 (p=0.25)** — flips sign, insignificant. The (already weak) tax effect on *total* CO₂ is **not separately identifiable from secular decarbonization**: tax adopters (Nordics) were decarbonizing anyway and the rising price rode that trend. This generalizes the Sweden over-attribution.
- **Caveat (other direction):** country-linear-trends is a *demanding* control that can over-absorb a treatment which itself trends ~linearly (a rising price). So ETS *surviving* = strong robustness evidence; tax *collapsing* = "can't separate from trend" (possibly over-control), not proven-zero — but either way no credible total-CO₂ tax claim.

**Net for the engine:** ETS dose-response is now robust to Student-t + era-split + country-trends → the solid deliverable; honest magnitude **€30 ETS ≈ −7 to −10%/3yr** (range = with/without trend control). The carbon-tax lever should carry a stronger caveat (total-CO₂ effect not robustly identified). Dashboard updated: ETS shown as a range; tax caveat added. Verified in scratch (anchor + 2-spec trend regression on the dose sample, 3729 rows / 163 countries).

---

## 10 June 2026 — LOCO VALIDATION: the covariate "personalization" does NOT survive out-of-sample (Tier-C demoted)

Ran leave-one-**country**-out cross-validation on the Tier-C covariate engine (`β_c = μ + X_c·θ + τ·z_c`, X = implementation-capacity + fossil). For each treated country: refit on the other ~30, predict the held-out country's effect from **its covariates only** (what the engine does for an unseen country), compare to that country's own empirical (per-country OLS) effect. 0 divergences across 31 refits. `outputs/loco_validation.csv`.

- **The covariate extrapolation has ZERO out-of-sample skill.**
  - TAX (n=18): RMSE-extrapolated **0.0348** vs grand-mean baseline **0.0302** (covariates *worse*); corr(pred,obs) = **0.01**.
  - ETS (n=29): RMSE-extrapolated **0.0282** vs baseline **0.0272** (tied/worse); corr = **−0.30** (points the wrong way).
  - **The in-sample Tier-C slope `θ_tax = −0.011` (implementation capacity) does NOT generalize.** Textbook in-sample-coefficient ≠ out-of-sample-prediction. This is exactly what LOCO exists to catch.
- **The extrapolation intervals are overconfident, and only partly fixably so.** 90% CI coverage = **0.39 (tax) / 0.28 (ETS)**. The engine drops the `τ·z_c` country residual when extrapolating; re-adding it lifts coverage only to 0.44 / 0.48 — because the fitted `τ` is **tiny** (`τ_tax=0.006`, `τ_ets=0.011`) vs the empirical effect scatter `sd≈0.03`. The gap is largely **estimation noise in the single-country benchmarks**, so "overconfident" is partly real, partly a noisy-yardstick artefact — *not* claimed as a pure calibration bug.
- **The one noise-free fact:** `RMSE_grand-mean ≈ sd(observed effects)` (0.030≈0.032 tax; 0.027≈0.028 ets). The best any model does here is **predict the average**; country-to-country differences are not recoverable from these covariates at this data scale.

**Implications (acted on):**
1. **Tier-C demoted** — covariates kept as *explored, not predictive*; `recommend()` reports the **grand-mean effect + honest (predictive-distribution) CI** for unobserved countries, not a covariate-personalized point. Observed-adopter countries still get their data-informed partial-pooled `β_c`.
2. **The honest product scope:** the engine estimates the **average** carbon-pricing effect (ETS ≈ −8%/3yr, tax ≈ 0) with reasonable confidence; it **cannot say which country beats the average**. The reference-class tags remain the right UI guardrail.
3. **This sharpens why continuous price matters:** the most likely *real, predictable* driver of cross-country effect differences is **the price faced** (€5 vs €47 both coded `has_ets=1`) — not governance/fossil. Continuous price is now the empirical test of whether the LOCO weakness is **fixable (price was the missing predictor)** or a **data-scale ceiling (26 treated units)**. Re-run LOCO on the dose model to decide.

---

## 10 June 2026 — AUDIT FIX TIER B: identification validation on the log outcome

Acted on the audit's CRITICAL-1/2/3. Frequentist diagnostics (pyfixest, country+year FE, clustered by country) on the Phase-3 log outcome `d_T`.

- **Parallel trends HOLDS (CRITICAL-2 resolved in the engine's favour).** Event study on `d_T`: pre-trend leads t−5…t−2 are tax {+0.011,−0.005,−0.007,+0.001} and ETS {+0.011,+0.006,−0.007,−0.007} — **none significant**. The identifying assumption we'd only *asserted* now has direct support on the actual estimand. Tax post-effect builds slowly (~0→−0.024@t+5, mostly insig) → tax weakness is real, not a pre-trend artefact.
- **ETS is NOT crisis-driven (CRITICAL-1's specific mechanism refuted).** Dropping crisis-contaminated windows (base yr 2006–09): ETS −0.025→−0.021 (still p=0.00); explicit EU×post-2008 control is insignificant (−0.002, p=0.72). The "it's really the 2008 crash" worry is not supported.
- **⚠️ NEW CAVEAT — the ETS effect is time-localized to the high-price pre-2008 era.** Pre-2008 ETS = −0.030 (p=0.00); **post-2010 ETS = +0.004 (p=0.39) — vanishes.** Mechanistically coherent: the EU ETS carbon price collapsed after 2008 (~€25–30 → ~€5 through the oversupplied 2010s). So **"ETS carries it" → "ETS carried it WHEN THE PRICE BIT."** The engine's pooled `has_ets` ≈ −0.027 is the 2005–08 experience, not a stable ongoing effect; recommending an ETS *today* has no recent-decade support. (Caveat-on-caveat: post-2010 also has weak identifying variation — nearly all EU already treated — so "no detectable effect," not proven zero.) **This is a price story a binary `has_ets` can't capture — strong motivation for the continuous `ets_price_only` work.**
- **Staggered-TWFE negative weighting (CRITICAL-3): low concern, not formally re-decomposed.** Tax effect is ~null regardless with clean event-study dynamics (no sign flips); ETS is a single 2005 cohort so Goodman-Bacon forbidden-comparisons don't apply. Formal Goodman-Bacon re-run deferred (low value given the above).

Net: the engine's causal basis is **firmer than the audit feared on parallel-trends & crisis-confounding**, but the ETS headline gains an important **high-price-era-only** qualifier. Verified in scratch (event study + 5-spec crisis robustness).

---

## 10 June 2026 — AUDIT (3-agent) corrections & caveats — READ BEFORE CITING PHASE 1–3 HEADLINES

Ran a full adversarial audit (causal methodology, data quality, technique research). Engine *machinery* is sound (outcome construction verified correct & leak-free to 3e-7; no dup rows; scales/standardization clean; treatment-adoption years correct; non-centered param, PPC/LOO, reference-class diagnostic all good practice). But several **headline claims are over-stated and are hereby DEMOTED:**

- **"Carbon pricing works; it's the ETS not the tax" — DEMOTE.** ETS is identified off essentially ONE shock: 26 of 31 ETS countries adopt in 2005 (EU launch) = ~94% of ETS rows; **effective treated clusters ≈ 1**. A common year-effect cannot separate "EU ETS" from EU-specific 2005-era shocks (2008–09 crisis hitting EU industry, 2009 Renewables Directive). `μ_ets`'s tight CI is statistically real but **causally over-precise**. Needs a crisis-robustness fit / gsynth before the claim stands.
- **Parallel trends NEVER tested on the Phase-3 log-change outcome** — only inherited from Phase-1's *level* outcome. Every Step 6–10 causal claim is conditional on an untested assumption for its actual estimand. (Fix in progress: event study on log outcome.)
- **Staggered-TWFE diagnostics not re-run** for the Phase-3 design (clean `has_tax` + log outcome + `delta`). Phase-1 Goodman-Bacon (2.7% bad weight) was on the conflated treatment + level outcome.
- **Kaya "mechanism decomposition" is an ACCOUNTING identity, not causal mediation.** `d_T = d_A+d_I+d_K` is definitional; summing per-bucket regressions is linearity of expectation. "Fuel-switching vs activity" is an interpretive overlay, not identified natural direct/indirect effects (needs no-mediator–outcome-confounding, violated by the business cycle). **Relabel as accounting decomposition** (or add Imai–Keele–Tingley ρ-sensitivity). Also `share = mean(channel)/mean(total)` is a fragile ratio-of-means; compute per-draw.
- **"Tax is REDUNDANT not weak" — DEMOTE to suggestive/data-limited.** The `delta` interaction is identified from an 83-row / 13-country tax-only cell (1990s Nordic pioneers + near-zero-price LatAm taxes + Ukraine's post-Soviet collapse). Matches Phase-2's own "suggestive, data-limited" language; the redundancy reframe is not robustly supported.
- **DATA BUG (critical): `*_pct_filled` are binary imputation FLAGS, not energy values** (`_filled = col.isna().astype(int)`; renewable_pct_filled all-zeros). The **2 June "fossil dependence reduces effectiveness (+0.049/SD, p=0.004)" finding is SUSPECT** — likely picking up data-availability, not fossil share. Re-run with real `fossil_pct` (0–100) before citing. Also: `tax_price` is conflated like `post_carbon_tax` (use `tax_price_only`); the 3 energy shares use different denominators, sum to ~107%, nuclear_pct includes hydro → never a simplex. CLAUDE.md templates corrected 10 June.
- **Prior calibration:** literature (Dolphin–Xiahou 2024, bias-corrected) puts effects at **−4% to −15%**; our −13/−15% anchor is at the aggressive end (consistent with ETS-shock inflation). Recalibrate.

**Triage chosen (A+B+C before dashboard):** A=these honesty/doc fixes (done); B=identification validation (event-study parallel-trends on log outcome + de Chaisemartin/Goodman-Bacon weight diagnostic + ETS crisis-robustness); C=covariate-on-effects hierarchy `β_c ~ Normal(X_c·θ, τ)` + prior recalibration. Research track (deferred): Callaway–Sant'Anna/BJS, Bayesian Causal Forests, gsynth, Manski bounds, continuous dose.

---

## 10 June 2026 — Phase 3 step 9: model validation (PPC, LOO) + robustness (Student-t)

Ran the back half of the Bayesian workflow we'd skipped (convergence ≠ fit), then fixed what it found.

- **PPC:** Normal-likelihood engine reproduces the centre (mean/sd/q95 Bayes-p ≈ 0.5) but **fails the tails** (q05 0.00, min 1.00, max 0.00) — can't reach the extremes, smears the core to compensate.
- **LOO (PSIS, 0 bad Pareto-k → reliable):** the **fixed effects earn their keep predictively** — Normal+FE beats no-FE by elpd_diff −230 (dse 25, ~9σ; 92% model weight). Independent validation of the causal architecture.
- **Cause of the fat tails:** tiny-emission / conflict **control** countries (Laos, Yemen, Afghanistan, Sierra Leone — median co2/cap ≈ 0.4 vs 2.6) with huge log-swings off a tiny base. None are tax/ETS countries.
- **Fix — Student-t likelihood** (estimated `nu ≈ 2`, very heavy tails): decisively better by LOO (**elpd +560, dse 54**); robustly down-weights the noisy controls instead of inflating `sigma`. **Adopted across all 4 channels of the engine.**
- **Robustness result:** effects **attenuate ~25%** (ETS −0.027, tax-alone −0.019, both ≈ ETS) — a *good* result (no longer outlier-driven); every finding holds and "both ≈ ETS alone" (redundancy) **strengthened**. Cost: mechanism *shares* become directional-only under robustness (heavy-tailed channels), so the engine's deliverable is the **robust totals + CI + P(reduce)**, breakdown qualitative.

**Backend complete:** a validated, outlier-robust causal recommendation engine. Remaining Phase 3: Streamlit dashboard (build-fast); continuous-dose levers remain a deliberate scope choice. **Coverage caveat (the real limit):** identification rests on ~26 tax / 29 ETS countries, almost all high-income EU — so the engine is accurate *for that reference class* and honestly-uncertain (wide CI, EXTRAPOLATED flag) everywhere else, incl. the highest-leverage targets (China, India, Indonesia).

---

## 10 June 2026 — Phase 3 steps 7–8: counterfactual engine + "tax is redundant, not weak"

Completed the recommendation engine on top of the structural model.

- **Step 7 — counterfactual engine.** A recommendation is a within-posterior-draw contrast (policy on vs off), so country baseline `alpha_c` and year effect cancel and the contrast collapses to the posterior of the relevant coefficients — uncertainty propagated end-to-end, no delta method. **Partial pooling makes it honest by construction:** observed-taxed countries get data-informed (tighter) `beta_c`; never-taxed countries revert to the population `Normal(mu,tau)` → automatically wider CI, flagged EXTRAPOLATED. `recommend(country, use_tax, use_ets)` returns total Δ + 90% CI + P(reduce) + Kaya mechanism breakdown.
- **Step 8 — backlog folded in (heterogeneous `beta_ets` + tax×ETS interaction `delta`).** Identification checked first: ETS well-identified (29 countries, median 14 ETS-yrs) but `tau_ets` small → effects fairly homogeneous (mild country-differentiation); interaction weak-but-estimable (cells: tax-only 83, both 105).
  - **`delta` = +0.017 (P(>0)=0.96) → sub-additive.** Decomposing: **tax alone ≈ −0.023 (P(reduce)=0.98)**, but **tax on top of ETS ≈ −0.006** (negligible). So the standalone tax DOES cut emissions — the earlier "tax is weak" was the both-cell dragging `mu_tax` to zero. **Reframe: the tax is REDUNDANT, not weak** — carbon-pricing instruments are substitutes, not complements; don't double-instrument expecting double the cut. The engine now drops "both" (−0.043→−0.038) since it no longer sums the two naively.
  - **Caveat (important):** standalone `mu_tax` leans on the 83-row tax-only cell (non-EU / pre-ETS Nordic) — least robust number; the redundancy and ETS strength are firmer. Channel closure ~80%; activity channel is an association, not a proven mechanism.

**Engine is functionally complete** (binary adopt/not). Remaining: standard Bayesian validation (posterior-predictive checks, LOO-CV — skipped so far), the continuous dose levers (price/coverage) the end-state vision promises ("$30/tonne, 50% coverage" — engine is currently on/off only), and the Streamlit dashboard.

---

## 10 June 2026 — Phase 3 steps 4–6: de-confounding + Kaya mechanism decomposition

Extended the Bayesian engine (`phase3_bayesian_engine.ipynb`) from the causal baseline to a structural decomposition.

- **Step 4 — second treatment (de-confound tax from ETS).** Adding a pooled `has_ets` coefficient halves the tax effect (`mu_tax` −0.121 → **−0.068**, P<0=0.97) and isolates **`mu_ets` = −0.165** (P<0=1.00). Reproduces the Phase-2 de-conflation *inside* the hierarchical model: ETS carries it, tax marginal. `mu_tax` now reads as "tax holding ETS + FE fixed."
- **Step 5 — anchored priors (honestly).** Did NOT center priors on our own −0.13 (same-data → circular → false precision). Instead tightened scales toward "effects are modest" (external/literature knowledge), centers at 0 so sign is earned. Tightening priors 2.5× moved top-level `mu`/`mu_ets` only in the 3rd decimal (n=4,218 → data dominates = robustness check passed); the treated-country `beta_c` spread shrank (0.044 → 0.041 = the regularization payoff, lands where data is thin). Phase 1/2 thus serves as *validation*, not input.
- **Step 6 — Kaya mechanism layer.** Switched to a log-change outcome so `dlog(CO2/pop) = dlog(affluence) + dlog(energy-intensity) + dlog(carbon-intensity)` decomposes exactly (identity closes: level max rel err 0.6%, log decomposition max resid 3.5e-3). Re-ran the DiD per channel (pooled treatments, anchored priors, 0 divergences). **Mechanism breakdown (annualized log-pts):**
  - **ETS −0.0286/yr** splits ≈ **half fuel-switching** (carbon intensity −0.0143, P<0=1.00, the "good" channel) + ≈ **a third lower activity** (affluence −0.0093, P<0=1.00, the *worry* channel — leakage/suppressed activity); efficiency ≈ 0. Over a 3-yr window ≈ −8% ≈ −4% decarbonization + −3% activity.
  - **Carbon tax −0.0133/yr** is weak and runs through **efficiency** (−0.0121), NOT fuel-switching (carbon intensity −0.0062, uncertain P<0=0.86); its affluence channel is *positive* (+0.0094 — taxing countries grew, masking the effect). Mechanistic echo of Phase 2's null outcome-sensitivity.

**Implications for the engine:** (1) recommend ETS as the primary lever but **flag the activity share** of its headline reduction (not pure decarbonization). (2) Treat the carbon tax as a marginal, efficiency-channel mover. **Caveats:** channel closure is ~85–90% not exact (priors + partial-pooled FE shrink each channel independently — trust shape, not last decimal); the affluence channel is an *association*, not a proven causal mechanism (mediation assumes no mediator–outcome confounding). Deferred: heterogeneous `beta_ets`, tax×ETS interaction (memory `project-phase3-backlog`).

---

## 9 June 2026 — Phase 3 step 3: Bayesian two-way-FE DiD validates the Phase-1 ATT

Built the causal core of the Phase 3 engine in PyMC (`phase3_bayesian_engine.ipynb`). Started from a no-FE baseline hierarchical model (country partial-pooling on `has_tax`), then added **partial-pooled country intercepts + year effects** — the Bayesian expression of the Phase-1 two-way fixed effects (`C(country) + C(year)`). All non-centered (`β = μ + τz`, etc.) to avoid Neal's funnel; year-effect mean pinned at 0 to anchor the additive level into the country intercepts.

- **`mu` (population-mean tax effect): −0.164 (no FE) → −0.121 (+ FE)**, P(μ<0) = 0.999. The ~0.04 shift toward zero is the cross-country baseline + common-time confounding the FE absorbed (`sigma_a` ≈ 0.11, `sigma_g` ≈ 0.055); residual `sigma` dropped 0.348 → 0.327.
- **Cross-method validation:** −0.121 lands on the Phase-1/2 ATT (≈ −0.13). Frequentist two-way-FE DiD and the Bayesian partial-pooled model — different machines, same identification, same number.
- Converged: R-hat ≈ 1.00, ESS hundreds-to-thousands, 0 divergences (nutpie backend; PyTensor C backend broken on this Windows/py3.13 box).

**Caveats / next:** (1) `has_tax` only — Phase 2 found **ETS carries the effect**, so `mu` is slightly overstated until `has_ets` is added as a second treatment (then it reads "tax holding ETS fixed"). (2) Priors are still weakly-informative at zero; step "anchor priors" will tighten them to Phase 1/2. (3) `mu` is the mean of heterogeneous `beta_c` (`tau` ≈ 0.086) — that spread drives country-specific recommendations later. Causal identification preserved; still conditional on parallel trends (stress-tested Phase 1).

---

## 3 June 2026 — Fuel-subsidy interaction re-run on clean treatments (Phase 2 fully closed)

Closed the last "partial" Phase 2 item. `fuel_subsidy_analysis.ipynb` previously interacted fuel subsidies with the **conflated `post_carbon_tax`** — contradicting the de-conflation that defines Phase 2. Re-ran with clean `has_tax` / `has_ets` and added an ETS symmetry check. Subsidy subsample: 1,781 obs (202 tax, 339 ETS country-years).

- **Tax × subsidy = +0.084 (p=0.15)**, hypothesized direction. At zero subsidy the tax effect is **−0.097 (p=0.065)**, eroding to ~+0.07 at ~2% GDP subsidy, crossing zero near ~1.2% GDP. Suggestive, **not significant** — subsidy-data overlap is thin.
- **ETS × subsidy = +0.056 (p=0.52)** — null. The blunting is **tax-specific**, mechanistically sensible: consumer fuel subsidies offset the retail price signal a tax raises, whereas the ETS bites upstream.
- **Caveat:** `has_ets` flips positive (+0.12) in this subsample — selection artefact of the ~26-country subsidy overlap, not a real reversal. Trust the *interaction*, not subsample levels.

**Verdict:** consistent with tax–subsidy antagonism but can't establish it; needs broader time-varying subsidy coverage (Phase 3 data lever), not a different estimator. With this + the ForestDRLearner capstone, **Phase 2 is fully complete** — clean treatment used throughout, no conflated-variable loose ends.

---

## 3 June 2026 — Phase 2 capstone: ForestDRLearner multi-policy heterogeneity (Phase 2 COMPLETE)

Built the 4-cell `ForestDRLearner` (0=none, 1=tax-only, 2=ETS-only, 3=both) as `phase2_multipolicy.ipynb` §4. DR-learner chosen over CausalForestDML because the treatment is multi-valued categorical; it returns a CATE per cell vs control. W = 4 validated confounders; X = 7 moderators (median-imputed). The forest has no country FE, so its absolute levels are confounded — anchored to a parametric within-FE `C(policy)` model in the same section.

- **Anchored levels (within-FE, clustered):** tax-only −0.069 (p=0.056), ETS-only −0.141 (p=0.049), both −0.139 (p=0.081). Same "ETS carries it, tax marginal" story as §1, now confirmed under a clean 4-cell categorical spec.
- **Forest levels are uninformative** (ATEs near 0, very wide CIs) — small treated cells + no FE. Used for shape only, as planned.
- **Heterogeneity:** CATE sd ≈ 0.13–0.16 per cell. **Implementation capacity is the dominant moderator in every cell** (importance ≈ 0.33), then schooling and industry share. Fossil share ≈ 0 importance in the *both* cell — consistent with fossil-dependence mattering for the *tax* margin specifically (§1), not the combined contrast.
- **Phase 3 implication:** recommendation engine should treat implementation capacity as the primary effect modifier and keep magnitudes anchored to within-FE parametric estimates, not forest levels.

**Phase 2 is now COMPLETE.** Clean causal questions were answered parametrically; the DR-learner adds the nonlinear heterogeneity map (and the method itself, a learning deliverable). Next: Phase 3 (PyMC hierarchical model + Streamlit), framed uncertainty-first.

---

## 2 June 2026 — Outcome sensitivity check (null): sharper outcome doesn't rescue the tax

Tested whether the weak carbon-tax signal is a measurement artefact of using economy-wide CO2/capita. Re-ran the de-conflated DiD on fuel-specific, mechanism-aligned outcomes (3-yr forward trend): oil+gas (tax channel), coal (ETS channel).

- has_tax on oil+gas: +0.010 (p=0.90) — zero effect on the fuels the tax most directly prices.
- has_tax on coal: -0.131 (p=0.27); on total: -0.045 (p=0.31).
- has_ets on coal: -0.021 (p=0.71) — no effect on its supposed power-sector channel; on oil+gas -0.290 (p=0.12).

**Conclusion:** sharper/channel-aligned outcomes do NOT strengthen the tax signal; effects don't localize to mechanism-implied fuels. The weak standalone carbon-tax effect is robust across every outcome definition — not a blunt-outcome artefact. (Documented in `phase2_multipolicy.ipynb` §3.) Of the three foundation levers, #2 (sharper outcome) is now exhausted as a null; #3 (effective price) is gated on time-varying coverage data; #1 (subnational units) remains the only untapped lever and is a standalone data project.

---

## 2 June 2026 — Data expansion to 2021 (refreshed 2024 emissions)

Refreshed OWID CO2 data (now reaches 2024) and extended the panel from 2019 to 2021. The 3-yr forward outcome needs emissions at year+3, so 2024 emissions unlock evaluable years through 2021.

- Panel: 3,892 -> **4,218 obs**, 1996-2019 -> **1996-2021**.
- Evaluable carbon-tax obs: 211 -> **261**; tax countries 23 -> **26** (added South Africa, Luxembourg, Netherlands).
- Pipeline was not cleanly re-runnable top-to-bottom; fixed 3 latent bugs: pandas-3.0 `groupby().apply()` dropping the grouping column (cell 69), a `gdp.notna()` filter that also dropped post-2021 `co2_per_capita` forward-lookups (cell 18), and a country-map sourced from the wrong frame (cell 77).
- **Result: the tax-vs-ETS finding is robust to the expansion.** Carbon tax alone -0.056 (p=0.22, still ns); ETS alone -0.129 (p=0.04, still sig); tax dose-response still flat. The weak carbon-tax effect is NOT a power artefact that more data fixes.
- Note: 2025 emissions not yet published, so 2022 adopters (Uruguay) remain unevaluable. The Phase 1 robustness and effects-library notebooks were built on the 2019 panel and need re-running on the expanded data (headline ATT shifts ~-0.151 -> ~-0.128).

---

## 2 June 2026 — Phase 2 start: carbon tax vs ETS (de-conflated)

`post_carbon_tax` conflated carbon tax with EU ETS (EU countries treated in 2005 = ETS launch, not their national tax). Re-estimating with clean `has_tax` / `has_ets` (same country+year FE, clustered SEs):

| Treatment | Effect | p |
|-----------|--------|---|
| Conflated `post_carbon_tax` | -0.151 | 0.004 |
| Carbon tax alone (`has_tax`) | -0.072 | 0.19 (ns) |
| ETS alone (`has_ets`) | -0.143 | 0.02 |
| Both additive: tax | -0.047 | 0.42 (ns) |
| Both additive: ETS | -0.138 | 0.03 |
| Interaction tax x ETS | +0.092 | 0.32 (ns) |

**Takeaway:** the Phase 1 headline was largely the EU ETS effect. The standalone national carbon tax effect is weaker (~-0.07) and not significant in this sample. Caveat: tax-only cell is small (94 obs, 15 heterogeneous countries) so power is low; with an interaction term carbon tax alone is significant (-0.093, p=0.02). Notebook: `phase2_multipolicy.ipynb`.

---

## 2 June 2026 — Phase 1 Complete (summary)

> ⚠️ [SUPERSEDED — see 11 June 2026 audit entry]
> (a) "Carbon tax lowers..." — the ATT −0.151 is **combined carbon pricing** (tax + ETS conflated via
> `post_carbon_tax`). Phase 2 showed the ETS carries this effect; the standalone carbon tax is unproven.
> (b) "fossil dependence hurts (+0.049/SD, p=0.004)" — retired: this used the `fossil_pct_filled`
> imputation flag; with real `fossil_pct` the interaction is −0.065 (p=0.37).
> (c) Robustness numbers updated on corrected data — see audit entry above.

Carbon pricing lowers the 3-yr-forward CO2/capita trend by ~0.15 (p=0.004), robust to every standard check. Effectiveness is driven by state capacity (helps). The democratic paradox is retired.

- **Baseline DiD** (country + year FE, clustered SEs): ATT -0.151, p=0.004.
- **Event study:** dynamic effect — ~0 at t=0, peak -0.168 at t+3, fades by t+5. Pre-trends jointly insignificant (F=1.87, p=0.12).
- **Heterogeneity:** implementation capacity -0.118/SD (p=0.07, helps); fossil dependence +0.049/SD (p=0.004, hurts). GDP, trade, schooling insignificant.
- **Robustness (all pass):** placebo +0.056 p=0.28 (null); leave-one-out -0.16 to -0.12, no sign flips; Goodman-Bacon 2.7% on forbidden comparisons; Rambachan-Roth pre-trends p=0.12, peak breakdown M=0.59 (point) / 0.21 (CI); Oster delta*=2.4, adjusted effect -0.088.
- **Democratic paradox retired:** old `democratic_legitimacy` was PC2 (= political stability); redefined as PC3 (voice & accountability) it is insignificant (p=0.27) and sign-unstable across DiD / CausalForest / OrthoForest.
- **Effects library** (`outputs/effects_library.csv`): per-country predicted effect, -0.63 (Luxembourg) to +0.13 (Ukraine).
- **Fuel subsidy x tax:** +0.077 (p=0.30) — blunts the tax in the right direction but underpowered.
- **Phase 2 blocker:** ETS coincides perfectly with carbon tax here (no ETS-only variation); fuel-subsidy/coverage data thin. Needs data expansion before multi-policy modelling.

---

## 2 June 2026 — Robustness Suite Completed + Heterogeneity / Effects Library

### Robustness checks all pass (phase1_robustness_checks.ipynb, §4–7)
- **Placebo (fake date -5yr):** +0.056, p=0.280 — null and wrong-signed; no pre-trend driving the result.
- **Leave-one-out (40 treated countries):** ATT in [-0.156, -0.115], 0 sign flips, 0 lost significance. Most influential drop: Luxembourg.
- **Goodman-Bacon:** implemented from scratch, validated by exactly reconstructing TWFE (-0.1554). Only **2.7%** of weight on forbidden (already-treated) comparisons → negative-weight bias negligible (consistent with DID2S -0.168 ≈ TWFE -0.156).
- **Rambachan-Roth (2023):** joint pre-trends F=1.87, p=0.12 (not rejected). Effect is dynamic — ~0 on impact, peak -0.168 at t+3. RM breakdown at peak: point M≈0.59, robust-CI M≈0.21 (moderately robust, not bulletproof).
- **Oster (2019):** with FE partialled out (FWL), δ\*=2.4 at Rmax=1.3·R² and β\*(δ=1)=-0.088 (identified set excludes 0). Robust to proportional OVB.

### Democratic paradox does NOT survive re-validation (KEY CORRECTION)
- The data refactor redefined `democratic_legitimacy` from **PC2 (really political stability)** to **PC3 (voice & accountability)** — a better-justified proxy (PC3 loads 0.84 on voice_accountability).
- Under the new PC3 definition **and** within-FE DiD interactions with clustered SEs, the democratic interaction is **insignificant** (PC2: +0.052, p=0.42; PC3: +0.049, p=0.27) and **sign-unstable** (causal forest gives the opposite sign cross-country).
- **The "democratic paradox" should be downgraded from a headline finding to a weak, unresolved signal.** The earlier negative result was an artefact of the old PC2 definition + cross-country (no-FE) identification.

### Heterogeneity + effects library (causal_effects_library.ipynb)

> ⚠️ [SUPERSEDED — fossil-dependence result retired; see 11 June 2026 audit entry]
> "+0.049/SD (p=0.004)" used `fossil_pct_filled` (an imputation flag, not a fossil share).
> With real `fossil_pct`: −0.065 (p=0.37) — noise. Retire the "fossil dependence hurts" claim.
> Implementation capacity result survives on corrected data: −0.111/SD (p=0.073).

- Effect is **concentrated in high-implementation-capacity countries**: implementation capacity moderates the ATT by **-0.118/SD (p=0.07)**; fossil dependence moderator was an artefact (see above). Other moderators insignificant.
- **Effects library** (`outputs/effects_library.csv`): predicted ATT per country from -0.63 (Luxembourg) to +0.13 (Ukraine) — the Phase 3 recommendation-engine input.
- Causal forest used for nonlinear shape/feature importance only; its absolute level is confounded without country FE (mean over treated ≈0), so levels are anchored to the DiD.

### Fuel subsidy interaction (fuel_subsidy_analysis.ipynb)
- `post_carbon_tax × fuel_subsidy_gdp = +0.077 (p=0.30)` — hypothesized direction (subsidies blunt the tax) but insignificant; implied effect flips from -0.06 (low subsidy) to +0.10 (high subsidy). Underpowered subsample (342 treated obs) — resolve in Phase 2.

### Notes
- Data schema adopted but **not yet committed** (per decision): moderators exposed as `_pc`/`_z`; `democratic_legitimacy = PC3`.
- Stray robotics code (`smoke_pp.py` pure-pursuit controller) found pasted into a cell of `fuel_subsidy_analysis.ipynb` — flagged for removal.

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

> ⚠️ [SUPERSEDED — see 2 June 2026 and 11 June 2026 entries]

### Democratic Governance Paradox (KEY FINDING — RETIRED)

> ⚠️ [SUPERSEDED]
> The `democratic_legitimacy` variable used here was **PC2**, which loads primarily on
> `political_stability` (not voice/accountability). PC3 is the correct democracy proxy.
> Under PC3 + within-FE DiD, the interaction is p=0.27 and sign-unstable across methods.
> **The democratic paradox is retired.** It was a methodological artefact, not a publishable finding.

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

> ⚠️ [SUPERSEDED — unvalidated on corrected data]
> The ~1%/yr decay estimate was computed using the **conflated** `post_carbon_tax` treatment
> (mixing tax and ETS) and the legacy `years_since_tax` variable (which was "years since any
> pricing"). The corrected per-instrument `years_since_tax` / `years_since_ets` had not been
> used to re-run this estimate as of the June 2026 audit. Do not cite without re-validation.

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
