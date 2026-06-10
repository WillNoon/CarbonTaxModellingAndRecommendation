# Overnight Autonomous Session — 11 June 2026

> A working + learning document. Built incrementally through the night. Goal: port/log the SDID
> negative result, then pivot to the **carbon-tax data expansion** (give the Nordics a pre-1990
> period so synthetic control can finally isolate the tax effect), keep deepening, polish the
> dashboard last. Written so you can **learn the methods and recreate them**.

**Start:** ~04:20 AEST, 11 June 2026. Target: work until ~09:00.

---

## Session plan (what I set out to do)

1. **Port + log the SDID/synthetic-control negative result** (Step 14 in the notebook + FINDINGS_LOG). ✅ see §1
2. **Tax data expansion** — pull pre-1990 OWID emissions so Nordic tax adopters (Sweden 1991, Finland 1990,
   Norway 1991, Denmark 1992) get a real pre-treatment window; then Andersson-style synthetic control for
   the *tax* (the one lever our 1996+ panel could not identify). → §2
3. **Deepen** — placebo inference, robustness, compare to Andersson's ~−6% transport estimate. → §3
4. **Dashboard polish** (last priority). → §4
5. **This document** — the methods, the findings, the code, and how to recreate it all.

---

## Background: why we are here (the story so far, in one breath)

The Phase-3 engine estimates carbon-pricing effects on CO₂/capita. Through validation we learned:
- **ETS effect is robust** (survives Student-t, era-splits, country-trends) — identified off the ETS *price*
  crash/recovery (€30→€5→€47), which is variation a trend can't mimic.
- **Tax effect is "unproven on total CO₂"** — it collapses under country-specific trends because a smoothly
  rising tax price is collinear with a linear decarbonization trend. Can't separate them in 1996+ data.
- **LOCO** killed covariate personalization (can't predict *which* country beats the average).
- **SDID/synthetic control** (this session, §1) confirmed there is **no clean control group** for the EU ETS —
  rigorously proving the "single-cluster" limit. The unifying insight: *price-variation* identification is the
  right tool for this data; *cross-country-control* identification is not.

The tax expansion (§2) is the one remaining shot at the tax: go back before 1990, when many OECD countries had
**not** yet priced carbon, so a credible donor pool of untreated economies actually exists.

---

## §1 — SDID port + log (DONE)

**Notebook Step 14** now contains a from-scratch synthetic-control + Synthetic-DiD implementation and the
negative-result narrative. **FINDINGS_LOG** has the full entry (11 June, "DEEPEN").

**The method, in code (so you can recreate it):**
- `_simplex(M_pre, target, zeta, rs)` — solves donor weights on the simplex (`w≥0, Σw=1`) to match a target
  trajectory over pre-periods, with the intercept concentrated out by *centering* the residual, plus a ridge
  penalty `zeta²·rs·‖w‖²`. SLSQP under the hood.
- `sdid(Ytr, Yco)` — (1) unit weights match the treated pre-mean path with the ADHIW ridge
  `zeta = (N_tr·T_post)^¼ · sd(Δ controls)`; (2) time weights make pre-periods predict each control's post-mean;
  (3) effect `τ = mean_treated(gᵢ) − Σ wᵢ·g_control`, where `gᵢ = post-mean − Σ λₜ·preₜ` (a weighted DiD).
- **Placebo inference:** re-assign "treatment" to random control units, recompute `τ`, build the null
  distribution; SE = sd(placebos), p = share of placebos at least as extreme.

**Result (verified):** comparable-pool SDID → pre-fit RMSE **0.75** (huge), unit weights **near-uniform**
(Belarus 0.08, Israel 0.08, Russia 0.07, US 0.07…), τ = **−29.9%** (artefact), placebo p=0.000 (also an
artefact). **Lesson:** the near-uniform weights mean *no donor resembles the EU* → the "effect" is EU-declining
vs emerging-economies-growing, not the ETS. A control-group design cannot work without a control group.

**Key takeaways to remember:**
- A *perfect* synthetic-control pre-fit is a **red flag** (overfitting with absurd donors), not a success.
- Synthetic control / SDID only works when *comparable untreated units exist*. For carbon pricing in rich
  countries, they mostly don't — almost everyone priced.
- The right identification strategy depends on what variation your data actually has: we have **within-country
  price variation** (ETS price crash) → use a dose-response; we lack a **control group** → SDID fails.

**Committed:** notebook Step 14 + FINDINGS_LOG + this doc.

---

## §2 — Carbon-tax data expansion: synthetic control on the Nordics (DONE — the key finding)

**Method.** Pulled OWID emissions back to 1965 (`data/raw/emissions_owid.csv`, history to 1750). For each Nordic
adopter (Finland 1990, Norway 1991, Sweden 1991, Denmark 1992) built a classic synthetic control: **pre-period
1970→tax-year**, **post-period tax-year→2004** (stops before the 2005 EU ETS, so DONORS stay untreated and the
effect isolates the *tax*). Donor pool = 22 high-income economies without a carbon tax pre-2005 (US, Japan,
Canada, France, Germany, …). Inference = **Abadie in-space placebo** (apply SC to each donor; rank the treated
country's post/pre RMSPE ratio).

**Why this is the design that finally *can* work for the tax:** before 2005, lots of comparable economies had
NOT priced carbon → a real donor pool exists (unlike the EU-ETS case in §1, where everyone priced at once).

**Result — the tax effect is TRANSPORT-CONCENTRATED, not total:**

| country | TOTAL CO₂/cap | OIL CO₂/cap (transport-fuel proxy) |
|---|---|---|
| Sweden  | −5.7% (p=0.91) | **−20.7%** (p=0.52) — synth ≈ Canada |
| Finland | −2.3% (p=0.91) | **−27.0%** (p=0.26) — synth ≈ US |
| Denmark | +12% (n.s.)    | **−15.3%** (p=0.78) — synth ≈ Canada |
| Norway* | +10% (n.s.)    | +0.2% (n.s.) — *oil producer, expected outlier* |

**Interpretation (the honest, important bit):**
- **On TOTAL CO₂ the tax is ≈ null / undetectable** — even with a proper pre-period and credible donors. This
  *independently confirms* our engine's "tax unproven on total CO₂."
- **On OIL (transport) CO₂ the tax shows large negative effects (−15 to −27%)** for the three non-oil-producers —
  *directionally corroborating Andersson (2019), who found −6.3% in transport.* Our magnitudes are larger and
  noisier (different proxy/method), but the **mechanism story matches**: the carbon tax bites transport fuels.
- **The two diluting facts reconcile everything:** transport is ~¼ of emissions, so a −20% transport cut →
  only ~−5% total — swamped by noise in the aggregate. *That is why every total-CO₂ method, including ours,
  finds the tax "weak."* The tax isn't weak; the **aggregate outcome is the wrong place to look.**
- **Statistical significance: NOT reached** (Abadie p>0.25). Cross-country oil-CO₂ paths are noisy (oil shocks,
  producer dynamics). So: *suggestive + mechanism-coherent + Andersson-consistent, but not confirmed.*

**Headline takeaway:** the data expansion succeeded as a *method* (proper pre-periods, sensible synthetics like
Sweden≈France, Finland≈US) and delivered a **convergent, honest answer the 1996+ data could not**: the carbon
tax's effect is real-looking and transport-concentrated, invisible in total CO₂ — and our dose-response engine,
the country-trend check, the Sweden anchor, AND this independent synthetic control now all tell the same story.


## §3 — Cross-method scrutiny: the dose engine disciplines the SC's "tax bites transport" claim (DONE)

§2's synthetic control suggested the Nordic tax cut *oil/transport* CO₂ (−15 to −27%). Before believing it, I
tested the same hypothesis with our **own dose-response engine, re-run on oil CO₂** (1996+ panel, merged transport
proxy). The result **fails to corroborate it:**

| outcome | TAX (Ptax) base / +trends | ETS (Pets) base / +trends |
|---|---|---|
| Total CO₂ | −0.0026 (p=.01) / +0.002 (n.s.) | −0.0109 / −0.0081  (robust) |
| **Oil CO₂ (transport)** | **−0.0008 (p=.37) / +0.001 (n.s.)** | −0.0107 / −0.0113  (robust) |

**Reading it honestly:**
- In 1996+, the **tax has no significant effect on oil/transport CO₂** either — *weaker* than on total. So our
  data does **not** reproduce a tax-transport effect with a clean within-period design.
- The §2 SC oil estimates were large but **never significant** (Abadie p>0.25) and **partly pre-tax** (Sweden's
  oil decline began with the early-1980s nuclear rollout). Under cross-method scrutiny they don't hold up.
- **Corrected conclusion (simpler + more honest):** the carbon **tax effect is weak / unidentified across the
  board** in our data — total *and* transport. **Andersson's within-Sweden transport design remains the only
  robust evidence for a transport effect; our cross-country data cannot reproduce it at significance.** The
  reproducible result across *every* method we ran is: **ETS effect real and robust; tax effect weak.**
- Bonus: the **ETS shows a robust effect on oil CO₂ too** — but note EU ETS doesn't cover road transport until
  ETS2 (2027), so this likely reflects oil used in ETS-covered sectors (industry/shipping/aviation/heat) and/or
  the ETS price proxying for broader EU decarbonization. *Don't over-interpret it as a causal road-transport effect.*

**Methodological lesson (worth keeping):** a suggestive result from one design (SC) should be stress-tested with
an independent design before it goes in the headline. Here the dose engine *demoted* a finding I was tempted to
believe — which is the system working as intended.


## §4 — Dashboard improvements (DONE)

Folded the night's findings into the Streamlit app (`dashboard/app.py`):
- **Tax caveat enriched:** now states the tax is weak across *every* design (country-trend control, transport-CO₂
  dose test, Nordic synthetic control) — not just total CO₂ — while crediting Andersson's within-Sweden transport
  result. Frames the tax as **unproven, not zero**.
- **New "Evidence base" expander:** a 6-row table of every method we stress-tested (dose-response, country-trend,
  transport dose, Sweden anchor, Nordic SC, EU-ETS SDID) with the ETS-robust / tax-weak verdict, plus the two
  methodological lessons (identification depends on the variation you have; aggregate CO₂ is the wrong outcome for
  the tax). Points to the docs.
- Verified: parses + boots clean (health 200).

The dashboard's core remains uncertainty-first: confidence tag → CI → point; price is the lever; country drives
confidence; extrapolation beyond €50 ETS is flagged.


## §3b — Sectoral mechanism: the ETS bites hardest where it actually covers (coal/power) (DONE)

Decomposed the dose-response by emission source (3-yr forward dlog, country+year FE, ±country trends):

| outcome | ETS (base / +trend) | tax (base / +trend) |
|---|---|---|
| Total CO₂ | −0.0109 / −0.0081 (robust) | −0.0026 / +0.002 (weak) |
| **Coal CO₂ (power/industry)** | **−0.0238 / −0.0200** (biggest, p softens to 0.17 under trends) | −0.0036 / +0.003 (null) |
| Gas CO₂ | −0.0125 / −0.0179 (suggestive) | +0.005 (null) |
| Oil CO₂ (transport) | −0.0107 / −0.0113 (robust) | −0.0008 (null) |

**Reading:** the ETS effect is **~2× larger on coal** than on total — and coal/power is *exactly* the sector the
EU ETS covers. That magnitude ordering (coal > gas ≈ total ≈ oil) is **coherent mechanism evidence**: the ETS
works mainly through coal-to-clean switching in electricity. (Coal's statistical significance softens under
country trends — the coal series is noisier — so this is *suggestive mechanism*, not a second robust headline; the
robust ETS headlines remain total + oil.) The tax is null in every sector, consistent with §3.

**Why oil also moves under the ETS** (a caveat, not a contradiction): EU ETS doesn't cover road transport pre-2027,
so the oil signal is likely non-road oil in covered sectors (industry/shipping/aviation/heat) and/or the ETS price
proxying broader EU decarbonization — don't read it as a causal road-transport effect.


---

# PART II — Learning synthesis (read this to *understand* and *recreate*)

## A. Executive summary — the whole night in six lines

1. **SDID / synthetic control cannot identify the EU ETS** — there is no comparable un-priced economy to use as a
   control (every rich country priced carbon at once in 2005). A gold-standard method *failed informatively*.
2. **That failure validated our engine:** for this data, identification must come from **within-country price
   variation** (the ETS price crash/recovery), which our dose-response engine uses — not a control group.
3. **We expanded the data back to 1965** so the Nordic carbon-tax adopters get a real pre-period, then ran a
   synthetic control for the *tax*. On total CO₂ it is null; on transport (oil) it *looked* large…
4. **…but cross-method scrutiny demoted that:** our dose engine on oil CO₂ shows no tax-transport effect either,
   and the SC oil estimates were insignificant + pre-tax-confounded. **The tax is weak everywhere in our data.**
5. **The ETS is robust and mechanistically coherent:** it survives every control and bites *hardest on coal*
   (power/industry — exactly its coverage).
6. **Bottom line, now battle-tested:** **ETS works (≈ −7 to −10% per €30, robust); the carbon tax is unproven in
   aggregate data** (Andersson's within-Sweden transport design is the only solid tax evidence, and we can't
   reproduce it cross-country). The binding constraint is *data* (no controls / no sectoral coverage), not method.

## B. The methods, taught (so you can rebuild them from scratch)

### B1. Synthetic control (Abadie, Diamond, Hainmueller)
**Idea:** to estimate the effect on one treated unit, build a fake "synthetic" version of it from a weighted blend
of untreated *donor* units, with weights chosen to match the treated unit's **pre-treatment** path. Post-treatment,
`effect = actual − synthetic`.

**The optimization (the whole method in one solve):**

    minimize_w  sum_{t < treat} ( y_treated,t  −  sum_j w_j * y_donor_j,t )^2
    subject to  w_j >= 0,  sum_j w_j = 1

`w >= 0, sum w = 1` keeps the synthetic inside the donors' convex hull (no extrapolation) and gives sparse,
interpretable weights. Solve with `scipy.optimize.minimize(method='SLSQP')` using a sum-to-one equality
constraint and `(0,1)` bounds. That is the entire method.

**The two traps we hit (remember these):**
- *Overfitting:* with many donors and few pre-periods you get a near-perfect pre-fit from an absurd blend
  (Germany ≈ Qatar + Zimbabwe). **A perfect pre-fit is a red flag.** Fix: restrict the donor pool to comparable
  units and/or match on covariates, not just the outcome line.
- *No comparable donors:* if nothing resembles the treated unit (a mature, decarbonizing economy), even a good
  optimizer gives garbage. **Synthetic control cannot work without real controls.**

### B2. Synthetic DiD (Arkhangelsky, Athey, Hirshberg, Imbens, Wager 2021)
Extends SC with three upgrades that make it robust: (1) an **intercept shift** so it matches the *trend*, not the
level; (2) **time weights** `lambda_t` so pre-periods that predict the post-period count more; (3) a **ridge
penalty** `zeta^2 * ||w||^2` with `zeta = (N_tr * T_post)^(1/4) * sd(diff(controls))`. The estimate is a weighted
DiD:

    tau = mean_treated(g_i)  −  sum_donors w_i * g_i
    where  g_i = (post-mean of unit i)  −  sum_t lambda_t * (pre value of unit i)

We coded both weight solves as the same simplex optimization with the intercept *concentrated out* (subtract the
mean of the residual before squaring). See notebook **Step 14**.

### B3. Inference without a formula: placebo tests
You cannot write a clean standard error for these, so you **simulate the null**:
- *In-space placebo (Abadie):* pretend each *donor* was the treated unit, run the whole SC, and record its
  post/pre RMSPE ratio. The real treated unit is "significant" only if its ratio ranks near the top. p ≈ rank / N.
- *SDID placebo:* randomly re-assign "treatment" to control units many times, recompute `tau`, and use the spread
  of those placebo taus as the standard error. We used both (Steps 14–15).
- **Lesson we learned the hard way:** a placebo "p = 0.000" is meaningless if the placebo pool does not contain the
  real confound (our EU-vs-developing-world artefact). Inference is only as good as the comparison set.

### B4. The dose-response engine (why it is the right tool here)
Instead of a control group, it identifies off **within-country price variation**: regress the 3-yr-forward change
in log CO₂ on the carbon *price* (per $10/tonne) with country + year fixed effects and a Student-t likelihood. The
ETS price crashing (€30 → €5) then recovering (→ €47) is variation a smooth trend *cannot* mimic — so the ETS slope
is identified even after we add country-specific trends. The tax price only ever rose smoothly → collinear with a
trend → not identified. **This is the core methodological moral of the whole project.**

### B5. The sectoral-decomposition trick (cheap, powerful)
To test a *mechanism*, re-run the same dose regression on **sub-components of the outcome** (coal / oil / gas CO₂
from OWID). If a policy's effect concentrates in the sector it targets (ETS → coal/power; a fuel tax → oil/
transport), that is mechanism evidence. It also disciplines suggestive results — it *demoted* our tax-transport
claim. Do this whenever you have a decomposable outcome.

## C. How everything fits — the unified story

    Is there a comparable CONTROL GROUP?
      |                                  |
     YES                                NO   (EU ETS: every rich country priced at once, 2005)
   synthetic control / SDID        -> control-group methods FAIL (Step 14)
   works (but we don't have it)    -> must use WITHIN-unit variation instead
                                          |
                      Is there usable within-unit treatment VARIATION?
                       |                                        |
            ETS price crashed/recovered              tax price only rose smoothly
            -> dose-response identifies it           -> collinear with a linear trend
            -> ROBUST effect (−7 to −10% @ €30)      -> NOT identified -> "unproven"
            -> concentrated in coal/power            -> Andersson finds it in transport,
               (its actual coverage)                    but we cannot reproduce it cross-country

## D. Where the project stands + recommended next steps

- **Engine:** validated, honest, deploy-ready (dashboard). ETS is the robust deliverable; the tax is flagged unproven.
- **The real frontier is DATA, not more estimators** (we proved estimators hit a wall):
  1. **Sub-national / installation-level EU ETS (EUTL) data** — covered vs uncovered installations *within* a
     country gives the control group that cross-country data lacks. Highest-value unlock.
  2. **Proper sectoral emissions** (we touched this with coal/oil) — sharpen the mechanism story.
  3. **Tax:** accept that aggregate cross-country data cannot prove it; cite Andersson for the transport channel.
- **Ship:** deploy the dashboard (Streamlit Community Cloud) + this doc as the written story → a strong portfolio
  artefact that demonstrates causal reasoning *and* intellectual honesty.

## E. Reproducibility map (where each piece lives)

| result | code | output |
|---|---|---|
| Bayesian dose engine | `notebooks/phase3_bayesian_engine.ipynb` Step 13 | `dashboard/posterior.npz` |
| LOCO validation | Step 12 (guarded `RUN_LOCO`) | `outputs/loco_validation.csv` |
| Synthetic control / SDID (ETS, negative result) | Step 14 | inline |
| Nordic tax synthetic control | Step 15 | `outputs/nordic_tax_oil_sc.png` |
| Sweden anchor, country-trend, oil/coal cross-checks | this doc §3 / §3b (scratch, deleted) | FINDINGS_LOG |
| Dashboard | `dashboard/app.py`, `dashboard/build_artifacts.py` | `uv run streamlit run dashboard/app.py` |
| Full narrative | `docs/FINDINGS_LOG.md`, this file | — |

*All commits are on branch `phase1-robustness-fixes`; each step was committed separately for a clean history.*

## F. If you only re-derive one thing, re-derive this
The single most transferable idea from tonight: **your identification strategy is dictated by the variation your
data actually contains, not by which method is fanciest.** We *wanted* synthetic control (prestigious, causal-clean)
but the data had no control group, so it failed. The humble dose-response worked because the ETS price *moved
non-monotonically*. Before reaching for a method, ask: *what variation in this dataset is plausibly exogenous, and
which method exploits exactly that?* Everything tonight is a corollary of that question.

## Summary figure

`outputs/sectoral_dose_effects.png` — carbon-pricing dose-response by sector and spec. Left (ETS): all
negative, **coal/power largest (~-2.4 per $10)**, robust under country-trends (red) on total/oil. Right (tax):
bars hug zero and flip positive under trends. One picture: **ETS robust and coal-concentrated; tax weak everywhere.**
(Companion: `outputs/nordic_tax_oil_sc.png` — the Nordic tax synthetic control.)

**SESSION STATUS:** §1-4 + §3b + Part II complete and committed. Core asks delivered: SDID ported/logged, tax
data-expansion done, deepening (oil/coal cross-checks), dashboard improved, full learning doc written.
