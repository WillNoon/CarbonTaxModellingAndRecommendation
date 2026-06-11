# Pre-trend correction — Phase 4 within-country sector DiD (audit finding C-1)

**Date:** 2026-06-11
**Script:** `scripts/within_country_ets_did.py` (upgraded)
**Figure:** `outputs/ets_covered_vs_uncovered_eventstudy.png` (regenerated, honest annotation)
**Scope of this change:** the script + figure + this summary only. A separate docs agent folds this into
`docs/FINDINGS_LOG.md` and the dashboard. Numbers below all reproduce when running the script end-to-end.

---

## The bug

The published claim — **"pre-trends pass, χ²(8)=8.3, p=0.41"** — reproduces *exactly* as the **diagonal**
Wald statistic Σ(bᵢ/seᵢ)² over the 8 pre-period event-study coefficients (1996–2003). That statistic
**ignores the off-diagonal covariances** between the coefficients, so it is not a valid joint test.

## The corrected test

The **full-covariance Wald** uses the cluster-robust (CRV1 by country) covariance matrix of the same 8
pre-period coefficients, on the **identical committed spec** (`i(year, covered, ref=2004) | gy + gs`,
clustered by `geo`):

| Test | Statistic | p | Reading |
|---|---|---|---|
| **Previous (incorrect)** diagonal Σ(bᵢ/seᵢ)² | χ²(8) = 8.30 | 0.405 | "pre-trends pass" — artefact |
| **Corrected** full-covariance Wald | χ²(8) = **31.23** | **0.0001** | parallel trends **REJECTED** |
| **Corrected** small-cluster F(8, G−1), G=27 | F(8,26) = **3.90** | **0.0038** | rejects (conservative) |
| Wild-cluster bootstrap of the joint Wald (Rademacher, 999 reps, restricted null) | — | **0.019** | rejects under few clusters |

## Why it rejects — a pre-existing covered-sector trend

The pre-2005 covered-vs-uncovered gaps decline **monotonically** (+13% in 1995 / +9% in 1996 → +1.3% by
2003). A **pre-period-only** regression (1995–2004) of `logco2 ~ covered:yr_c | gy + gs` gives a
covered-specific trend of:

- **−1.25 %/yr (SE 0.72, p = 0.093)**
- Extrapolated 2005 → 2021 (16 yrs): **−20.0 %**, which **equals/exceeds the entire observed −19.1 %
  endpoint.** The pre-existing trend alone can account for the whole "treatment" effect.

This is exactly why `covered:Pets` **collapses to −0.0014 (p = 0.81)** when a covered-specific linear
trend is added to the full sample. The previous write-up excused that collapse as "over-controlling
because pre-trends are flat" — that excuse fails now that the pre-trends formally reject.

## Rambachan–Roth relative-magnitudes sensitivity (ported from `phase1_robustness_checks.ipynb`)

Worst pre-period violation (consecutive-coefficient jump) **δ̄ = 0.0561**. Breakdown M̄ = the multiple of
δ̄ a post-period violation must reach before the effect / its CI includes zero (level bound (h+1)·M·δ̄):

| Endpoint (2021, h = 17) | Breakdown M̄ |
|---|---|
| Point estimate | **0.19** |
| Robust 95% CI | **0.04** |

**M̄ ≪ 1** means a post-period covered trend *smaller* than the violations already visible **before** 2005
is enough to erase the effect. Extremely fragile — coherent with the Wald rejection.

## Corrected verdict (wording suitable for FINDINGS_LOG)

> **CORRECTION (audit C-1):** the Phase-4 within-country sector DiD is **NOT clean identification** of the
> EU ETS. The "pre-trends pass, χ²(8)=8.3, p=0.41" claim used a diagonal Wald that ignored coefficient
> covariances; the correct **full-covariance Wald rejects** parallel trends (χ²(8)=31.2, p=0.0001;
> conservatively F(8,26)=3.90, p=0.004; wild-cluster-bootstrap p=0.019). The pre-2005 covered-vs-uncovered
> gaps decline monotonically, and a pre-existing **covered-specific trend of −1.25 %/yr** extrapolates to
> −20 % by 2021 — on its own enough to account for the entire −19 % endpoint. Rambachan–Roth confirms the
> fragility (robust-CI breakdown M̄ ≈ 0.04 at the endpoint). The design therefore **inherits the same
> price-vs-trend non-identifiability as the carbon tax** (consistent with `covered:Pets` → −0.0014, p=0.81
> under a covered-specific trend); the earlier "over-controlling" defence no longer holds. **Demote from
> "clean ID ⭐" to the same epistemic status as the tax.**
>
> The genuinely trend-resistant residue is the **sector decomposition**: refining ≈ null (+0.0012, p=0.95)
> vs power/heat (−0.049, p=0.018) and manufacturing (−0.046, p=0.005) — **suggestive mechanism evidence**
> (effects land where abatement options exist, not on a pure secular trend), not a clean magnitude.

## Reproduction

`uv run python scripts/within_country_ets_did.py` (or `.venv\Scripts\python.exe scripts/within_country_ets_did.py`).
Prints the diagonal-vs-full Wald, the pre-period trend + extrapolation, the RR breakdown table, and the
wild-cluster bootstrap p; regenerates the figure with the fitted pre-trend line and a rejection note in
the title. All numbers above reproduced exactly on the committed data.
