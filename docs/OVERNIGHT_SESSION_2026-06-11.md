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
