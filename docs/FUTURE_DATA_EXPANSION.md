# Phase 2 Data Inventory & Expansion Guide

Inventory of policy data for the multi-policy phase (carbon tax, ETS, fuel subsidies), done 2 June 2026. Answers: what we already have, what's genuinely missing, and where to source it.

## Headline finding: the Phase 1 treatment conflates carbon tax with EU ETS

`post_carbon_tax` (511 obs) is **not** a clean carbon-tax indicator. For EU countries it switches on in 2005 — the EU ETS launch — regardless of whether the country has a national carbon tax:

| Country | post_carbon_tax | has_tax (real national tax) | has_ets | reading |
|---------|-----------------|------------------------------|---------|---------|
| Germany | from 2005 | never (no national tax until 2021, out of range) | from 2005 | "treatment" is purely EU ETS |
| France | from 2005 | from 2014 | from 2005 | tax 9 yrs after "treatment" |
| Ireland | from 2005 | from 2010 | from 2005 | tax 5 yrs after "treatment" |
| Sweden | from 1996 | from 1996 | from 2005 | genuine tax |
| Mexico / Canada | = has_tax | = has_tax | none | genuine tax |

`tax_price` is also conflated — for Germany it is the EU ETS allowance price ($1.25–$34.5), not a carbon tax rate.

**Implication:** the Phase 1 headline (-0.15) is a **carbon-pricing** effect (tax OR ETS, heavily EU-ETS-driven), not specifically a carbon-tax effect. The clean indicators `has_tax` (211 obs) and `has_ets` (410 obs) already exist in the data and should be the basis for Phase 2 (and arguably for relabelling Phase 1).

## What we already have

| Lever | Variable(s) | Coverage | Source | Notes |
|-------|-------------|----------|--------|-------|
| Carbon tax (clean) | `has_tax` | 211 country-years, 15+ countries | World Bank carbon pricing | the genuine national tax indicator |
| ETS (clean) | `has_ets` | 410 country-years, 29 countries, 2005–2019 | World Bank | independent of tax |
| Carbon price | `tax_price` | continuous, but mixes tax rate and ETS price | WB prices | needs splitting (see gaps) |
| Fuel subsidies | `fuel_subsidy_gdp`, `fuel_subsidy_usd_million` | 1,610 obs, 161 countries, **2010–2019 only** | `fuel_subsidy_ffst.csv` | short window is the limitation |
| Coverage rate | `carbon_tax_coverage.csv` | **23 countries, cross-section (no year)** | WB Carbon Pricing Dashboard | thin and static — weakest input |

## Multi-policy design is feasible NOW (no expansion needed to separate tax vs ETS)

Cross-tabulating `has_tax` x `has_ets` gives a clean, well-populated 4-cell design:

| Cell | Country-years | Countries |
|------|---------------|-----------|
| None (control) | 3,388 | majority |
| Tax only | 94 | 15 (Argentina, Canada, Chile, Colombia, Finland, Iceland, Japan, Mexico, Norway, Poland, Singapore, Sweden, Switzerland, Ukraine, UK) |
| ETS only | 293 | 25 (mostly EU) |
| Both | 117 | 12 |

This maps directly onto the planned `ForestDRLearner` categorical treatment (0=none, 1=tax, 2=ETS, 3=both). The tax/ETS separation needs **no new data** — only a clean re-derivation of the treatment from existing flags.

## Genuine gaps and where to source them

| Gap | Why it matters | Source | Effort |
|-----|----------------|--------|--------|
| **Time-varying coverage rate** | Currently 23 countries, no year. Effective price = price x coverage needs this; matched only ~52% of treated obs in Phase 1 | World Bank Carbon Pricing Dashboard (carbonpricingdashboard.worldbank.org) — has coverage by jurisdiction over time; OECD Effective Carbon Rates | Medium |
| **Separate ETS price vs carbon tax rate** | `tax_price` mixes them; dose-response needs distinct price levers | ICAP Allowance Price Explorer (icapcarbonaction.com) for ETS; WB Carbon Pricing Dashboard for tax rates | Medium |
| **Fuel subsidies pre-2010** | Current window 2010–2019 is short; limits the subsidy interaction (already underpowered) | IMF Fossil Fuel Subsidies database; IEA Fossil Fuel Subsidies; OECD Inventory of Support Measures for Fossil Fuels | Medium |
| **Green innovation (optional)** | Mechanism control / outcome for Phase 2/3 | OECD green patents (PATSTAT) | Low priority |

## Recommended Phase 2 sequence

1. **Re-derive treatments cleanly.** Build `treatment_4cat` from `has_tax`/`has_ets`; split `tax_price` into `carbon_tax_rate` (tax-only) and `ets_price` (ETS). This alone unblocks multi-policy work and should be done first.
2. **Relabel/re-run the Phase 1 estimate** on `has_tax` vs `has_ets` separately, to report a genuine carbon-tax effect distinct from the pooled pricing effect. (Decision point — may warrant a short Phase 1 addendum.)
3. **Multi-policy model:** `ForestDRLearner` on the 4-cell categorical treatment with the validated confounders; compare tax vs ETS vs both, with heterogeneity by the Phase 1 moderators (capacity, fossil dependence).
4. **Dose-response:** once ETS price and tax rate are separated, continuous-treatment causal forest with `PolynomialFeatures(degree=2)`.
5. **Source the gaps** (coverage time series, subsidies pre-2010) in parallel; they improve the effective-price and subsidy-interaction analyses but are not blockers for steps 1–3.
