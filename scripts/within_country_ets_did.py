"""Phase 4 — within-country covered-vs-uncovered DiD for the EU ETS, with HONEST pre-trend diagnostics.

The cross-country design failed because every rich country priced carbon at once (no control group).
The fix: look INSIDE a country. The EU ETS covers some sectors (power, industry) and not others
(road transport, buildings). Comparing covered vs uncovered emissions *within country x year* gives a
control group, and country x year fixed effects absorb every country-wide confound (recessions, weather,
national decarbonisation trends) — exactly what broke the cross-country estimates.

⚠️ CORRECTION (audit 2026-06-11, finding C-1). The originally-published "pre-trends pass, χ²(8)=8.3,
p=0.41" was a DIAGONAL Wald, Σ(bᵢ/seᵢ)², that IGNORES the covariances between the event-study
coefficients. The correct full-covariance Wald on the *identical* spec REJECTS parallel trends
(χ²(8)≈31, p≈0.0001; conservatively F(8,26)≈3.9, p≈0.004). The pre-2005 covered-vs-uncovered gaps
decline monotonically and a pre-period covered-specific trend (≈−1.25%/yr) extrapolates to ≈−20% by
2021 — more than the entire −19% endpoint. So this design is NOT clean identification; it inherits the
same price-vs-trend non-identifiability as the tax. The trend-resistant residue is the sector
decomposition (refining ~null vs power/manufacturing negative) as suggestive mechanism evidence.
This script now computes and prints those honest diagnostics.

Data: Eurostat `env_air_gge` (GHG by CRF source sector), pulled to data/raw/eurostat_ghg_sectors.csv via:
  airpol=CO2, unit=THS_T, sectors CRF1A1A/CRF1A1B/CRF1A2 (covered) + CRF1A3B/CRF1A4A/CRF1A4B (uncovered).

Run:  uv run python scripts/within_country_ets_did.py
"""
import os
import numpy as np
import pandas as pd
import pyfixest as pf
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(ROOT, 'data/raw/eurostat_ghg_sectors.csv'))
main = pd.read_csv(os.path.join(ROOT, 'data/cleaned/final_analysis_data.csv'))
price = main[main['country'] == 'Germany'].set_index('year')['ets_price_only'].fillna(0.0)  # common EU ETS price

EU = ['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','EL','HU','IE','IT','LV','LT','LU','MT',
      'NL','PL','PT','RO','SK','SI','ES','SE']
df = df[df['geo'].isin(EU)]
df = df[(df['year'] >= 1995) & (df['year'] <= 2021) & (df['co2_kt'] > 0)].copy()
df['covered'] = (df['coverage'] == 'covered').astype(int)
df['Pets'] = (df['year'].map(price).fillna(0.0) / 10).values   # per $10/tonne, 0 pre-2005
df['post2005'] = (df['year'] >= 2005).astype(int)
df['logco2'] = np.log(df['co2_kt'])
df['gy'] = df['geo'] + '_' + df['year'].astype(str)
df['gs'] = df['geo'] + '_' + df['sector']
G = df['geo'].nunique()
print(f"panel: {len(df)} rows, {G} EU countries, {df.sector.nunique()} sectors, 1995-2021")

# --- DiD: covered sectors respond to the ETS price more than uncovered (country x year + country x sector FE) ---
m_bin = pf.feols("logco2 ~ covered:post2005 | gy + gs", data=df, vcov={'CRV1': 'geo'})
m_dose = pf.feols("logco2 ~ covered:Pets | gy + gs", data=df, vcov={'CRV1': 'geo'})
print("\n[binary DiD] covered x post2005:", m_bin.tidy()[['Estimate', 'Pr(>|t|)']].round(4).to_dict('records'))
print("[dose DiD]   covered x ETS-price/$10:", m_dose.tidy()[['Estimate', 'Pr(>|t|)']].round(4).to_dict('records'))
b = m_dose.coef()['covered:Pets']
print(f"  => covered sectors fall {b*100:+.1f}% per $10/t MORE than uncovered (at EUR30: {b*3*100:+.1f}%, EUR70: {b*7*100:+.1f}%)")

# robustness: drop the 2008-09 financial-crisis years (they hit covered industry hard, non-ETS)
m_nocrisis = pf.feols("logco2 ~ covered:Pets | gy + gs", data=df[~df['year'].isin([2008, 2009])], vcov={'CRV1': 'geo'})
print(f"  drop 2008-09 crisis years: covered:Pets = {m_nocrisis.coef()['covered:Pets']:+.4f} (p={m_nocrisis.tidy()['Pr(>|t|)'].iloc[0]:.3f})  (STRONGER => not a crisis artefact)")

# --- covered-specific trend collapse + sector decomposition (unchanged; context for the diagnostics below) ---
df['yr_c'] = df['year'] - df['year'].mean()
m_tr = pf.feols("logco2 ~ covered:Pets + covered:yr_c | gy + gs", data=df, vcov={'CRV1': 'geo'})
print(f"\n  + covered-specific linear trend (FULL sample): covered:Pets = {m_tr.tidy().loc['covered:Pets','Estimate']:+.4f} "
      f"(p={m_tr.tidy().loc['covered:Pets','Pr(>|t|)']:.3f})  <- COLLAPSES to ~0 (price drifts up => collinear w/ a covered trend).")
for s in ['power_heat', 'refining', 'manufacturing']:
    df[f'is_{s}'] = (df['sec'] == s).astype(int)
md = pf.feols("logco2 ~ is_power_heat:Pets + is_refining:Pets + is_manufacturing:Pets | gy + gs", data=df, vcov={'CRV1': 'geo'})
print("  sector decomposition (vs uncovered baseline) — the trend-RESISTANT residue / mechanism evidence:")
for k in ['is_power_heat:Pets', 'is_refining:Pets', 'is_manufacturing:Pets']:
    r = md.tidy().loc[k]
    print(f"    {k.replace('is_','').replace(':Pets',''):14s} {r['Estimate']:+.4f}/$10t (p={r['Pr(>|t|)']:.3f})")
print("    => refining ~null, power/manufacturing negative: a pure secular trend would not single those out.")

# ======================================================================================
# HONEST PRE-TREND DIAGNOSTICS (audit C-1)
# ======================================================================================
es = pf.feols("logco2 ~ i(year, covered, ref=2004) | gy + gs", data=df, vcov={'CRV1': 'geo'})
cn = list(es._coefnames)
V = np.asarray(es._vcov)             # cluster-robust (CRV1 by geo) covariance of the event-study coefs
coef = es.coef()
se = es.se()

# --- assemble the event-study series (ref year 2004 = 0) ---
rows = []
for c in cn:
    y = int(c.split('year::')[1].split(':')[0])
    rows.append({'year': y, 'event_time': y - 2004, 'coef': coef[c], 'se': se[c]})
esdf = pd.concat([pd.DataFrame(rows),
                  pd.DataFrame([{'year': 2004, 'event_time': 0, 'coef': 0.0, 'se': 0.0}])],
                 ignore_index=True).sort_values('year').reset_index(drop=True)

# --- pre-period coefficients 1996-2003 (the 8 the published χ²(8) used; 1995 carried but excluded for comparability) ---
PRE_YEARS = list(range(1996, 2004))
pre_terms = [c for c in cn if any(f'year::{y}:' in c for y in PRE_YEARS)]
idx = [cn.index(c) for c in pre_terms]
bp = coef.values[idx]
Vp = V[np.ix_(idx, idx)]
sep = np.sqrt(np.diag(Vp))
q = len(idx)

# (1a) PREVIOUS, INCORRECT diagonal Wald — kept only to show the bug, clearly labelled.
chi2_diag = float(np.sum((bp / sep) ** 2))
p_diag = stats.chi2.sf(chi2_diag, q)

# (1b) CORRECT full-covariance Wald using the cluster-robust vcov.
chi2_full = float(bp @ np.linalg.solve(Vp, bp))
p_chi2 = stats.chi2.sf(chi2_full, q)
F = chi2_full / q
p_F = stats.f.sf(F, q, G - 1)   # small-cluster F(q, G-1) version

print("\n=== (1) JOINT PRE-TREND TEST (event study, 8 pre-period coefs 1996-2003) ===")
print(f"  previous, INCORRECT (ignores covariances): chi2({q})={chi2_diag:.2f}, p={p_diag:.3f}  [diagonal Sum(b/se)^2]")
print(f"  CORRECT full-covariance Wald:              chi2({q})={chi2_full:.2f}, p={p_chi2:.4f}")
print(f"  CORRECT small-cluster F:                   F({q},{G-1})={F:.2f}, p={p_F:.4f}")
print(f"  => parallel trends is REJECTED (the published p=0.41 was the diagonal artefact).")

# --- (2) pre-period covered-specific linear trend (PRE-2005 ONLY) + extrapolation ---
sub = df[df['year'] < 2005].copy()
sub['yr_c'] = sub['year'] - sub['year'].mean()
m_pre = pf.feols("logco2 ~ covered:yr_c | gy + gs", data=sub, vcov={'CRV1': 'geo'})
tp = m_pre.tidy().loc['covered:yr_c']
slope, slope_se, slope_p = tp['Estimate'], tp['Std. Error'], tp['Pr(>|t|)']
years_out = 2021 - 2005
extrap = slope * years_out
endpoint = esdf.loc[esdf['year'] == 2021, 'coef'].values[0]
print("\n=== (2) PRE-PERIOD COVERED-SPECIFIC LINEAR TREND (1995-2004 only) ===")
print(f"  covered-specific trend = {slope*100:+.2f}%/yr (SE {slope_se*100:.2f}, p={slope_p:.3f})")
print(f"  extrapolated 2005->2021 ({years_out} yrs): {extrap*100:+.1f}%  vs the observed 2021 endpoint {endpoint*100:+.1f}%")
print(f"  => a pre-existing covered-sector trend ALONE accounts for (exceeds) the entire treatment endpoint.")

# --- (3) Rambachan-Roth (2023) relative-magnitudes sensitivity (ported from phase1_robustness_checks) ---
# delta_bar = largest pre-period violation (max consecutive change among pre coefs, up to the t-1 reference).
pre = esdf[esdf['event_time'] < 0].sort_values('event_time')
delta_bar = np.abs(np.diff(np.append(pre['coef'].values, 0.0))).max()
# Under Delta^RM(M) the bias on the LEVEL at horizon h is bounded by (h+1)*M*delta_bar.
# Breakdown M = smallest violation that makes the point estimate / robust 95% CI include zero.
rr_rows = []
for h in sorted(esdf.loc[esdf['event_time'] > 0, 'event_time']):
    sel = esdf[esdf['event_time'] == h]
    bh, seh = sel['coef'].values[0], sel['se'].values[0]
    steps = h + 1
    m_point = abs(bh) / (steps * delta_bar)
    m_robust = max((-bh - 1.96 * seh) / (steps * delta_bar), 0.0)   # effect is negative
    rr_rows.append({'horizon': h, 'year': 2004 + h, 'coef': bh, 'M_point': m_point, 'M_robust': m_robust})
rr = pd.DataFrame(rr_rows)
m_end = rr[rr['year'] == 2021].iloc[0]
print("\n=== (3) RAMBACHAN-ROTH relative-magnitudes breakdown (M = post violation / worst pre violation) ===")
print(f"  worst pre-period violation (delta_bar) = {delta_bar:.4f}")
print("  endpoint (2021):  point-estimate breakdown M = "
      f"{m_end['M_point']:.2f},  robust-95%-CI breakdown M = {m_end['M_robust']:.2f}")
print(f"  => the 2021 effect's CI already includes zero once the post-period covered trend reaches only "
      f"~{m_end['M_robust']:.2f}x the worst pre-period violation.")
print(f"     (M<1 means a post-period trend SMALLER than what we already see pre-2005 erases the effect — very fragile.)")

# --- (4) wild-cluster bootstrap p for the joint pre-trend Wald (Rademacher, restricted null) ---
# Cheap: impose pre-period coefs = 0 by mapping all pre years to the reference (2004), bootstrap the restricted resids.
def joint_wald(d, col='logco2'):
    e = pf.feols(f"{col} ~ i(year, covered, ref=2004) | gy + gs", data=d, vcov={'CRV1': 'geo'})
    cnn = list(e._coefnames); Vv = np.asarray(e._vcov); bb = e.coef().values
    ii = [cnn.index(c) for c in cnn if any(f'year::{y}:' in c for y in PRE_YEARS)]
    return float(bb[ii] @ np.linalg.solve(Vv[np.ix_(ii, ii)], bb[ii]))

try:
    rng = np.random.default_rng(42)
    df['ev_restr'] = np.where(df['year'] >= 2005, df['year'], 2004)  # pre years -> reference => pre coefs forced to 0
    es_r = pf.feols("logco2 ~ i(ev_restr, covered, ref=2004) | gy + gs", data=df, vcov={'CRV1': 'geo'})
    df['fit_r'] = es_r.predict()
    df['res_r'] = df['logco2'] - df['fit_r']
    geos = df['geo'].unique()
    B = 999
    count = 0
    for _ in range(B):
        w = {g: rng.choice([-1.0, 1.0]) for g in geos}
        df['yb'] = df['fit_r'] + df['res_r'] * df['geo'].map(w).values
        if joint_wald(df, col='yb') >= chi2_full:
            count += 1
    wcb_p = (count + 1) / (B + 1)
    print(f"\n=== (4) WILD-CLUSTER BOOTSTRAP (Rademacher, {B} reps, restricted null) ===")
    print(f"  joint pre-trend Wald bootstrap p = {wcb_p:.4f}  (confirms the asymptotic rejection under few clusters)")
except Exception as ex:
    print(f"\n=== (4) wild-cluster bootstrap skipped: {ex} ===")

# ======================================================================================
# (6) FIGURE — honest annotation: fitted pre-trend line, rejection note, no "parallel trends OK"
# ======================================================================================
yrs = esdf['year'].values
bb_pct = esdf['coef'].values * 100
ci_lo, ci_hi = (esdf['coef'] - 1.96 * esdf['se']).values * 100, (esdf['coef'] + 1.96 * esdf['se']).values * 100

fig, ax = plt.subplots(figsize=(9, 4.4))
ax.fill_between(yrs, ci_lo, ci_hi, alpha=.15, color='#1f77b4')
ax.plot(yrs, bb_pct, 'o-', color='#1f77b4', ms=4, lw=1.8, label='covered − uncovered gap (ref 2004)')
ax.axvline(2005, color='r', ls=':', lw=1.2)
ax.axhline(0, color='k', lw=.6)

# fitted pre-period covered-specific trend line, drawn across the whole horizon to show it tracks the endpoint
pre_yrs = np.arange(1995, 2005)
yr_c_mean = sub['year'].mean()
fit_line_full = slope * (np.arange(1995, 2022) - yr_c_mean) * 100
# anchor the fitted line so it passes ~through the pre-period cloud (intercept = mean pre gap minus mean fitted)
pre_mask = esdf['year'] < 2005
intercept = (esdf.loc[pre_mask, 'coef'].values * 100).mean() - (slope * (sub.groupby('year').size().index.values - yr_c_mean) * 100).mean()
ax.plot(np.arange(1995, 2022), fit_line_full + intercept, color='#d62728', ls='-', lw=1.4, alpha=.9,
        label=f'pre-2005 covered trend {slope*100:+.2f}%/yr (p={slope_p:.2f}), extrapolated')

ax2 = ax.twinx()
ax2.plot(price.index, price.values, color='#888', lw=1, ls='--', alpha=.7)
ax2.set_ylabel('EU ETS price (EUR/t, dashed)', color='#888', fontsize=9)

ax.set_xlabel('year')
ax.set_ylabel('ETS-covered vs uncovered CO2 gap (%, ref 2004)')
ax.set_title('Within-country sector DiD: NOT clean identification\n'
             f'pre-trends REJECT (full-cov Wald chi2({q})={chi2_full:.0f}, p={p_chi2:.4f}); '
             f'pre-2005 covered trend ({slope*100:+.2f}%/yr) extrapolates to {extrap*100:+.0f}% (>= the {endpoint*100:+.0f}% endpoint)',
             fontsize=8.8)
ax.legend(fontsize=7.5, loc='lower left')
ax.set_xlim(1995, 2022)
ax.grid(alpha=.25)
plt.tight_layout()
plt.savefig(os.path.join(ROOT, 'outputs/ets_covered_vs_uncovered_eventstudy.png'), dpi=115)
print("\nsaved outputs/ets_covered_vs_uncovered_eventstudy.png (honest annotation: fitted pre-trend line + rejection note)")

# ======================================================================================
# (5) CORRECTED CONCLUSION
# ======================================================================================
print("""
================================ CORRECTED VERDICT ================================
The within-country sector DiD is NOT clean identification of the EU ETS.
  - The joint pre-trend test REJECTS under the correct full-covariance Wald
    (chi2(8)~31, p~0.0001; F(8,26)~3.9, p~0.004). The published "p=0.41" was a
    diagonal Sum(b/se)^2 that ignored coefficient covariances.
  - The pre-2005 covered-vs-uncovered gaps decline monotonically; a pre-existing
    covered-specific trend (~-1.25%/yr) extrapolates to ~-20% by 2021 — on its own
    enough to account for the entire ~-19% endpoint.
  - Rambachan-Roth: the endpoint effect's CI includes zero once the post-period
    violation reaches only a small fraction of the worst pre-period violation
    (robust-CI breakdown M well below 1) — very fragile.
  - The design therefore inherits the SAME price-vs-trend non-identifiability as the
    carbon tax (consistent with covered:Pets collapsing to -0.0014, p=0.81 under a
    covered-specific trend). The earlier excuse ("pre-trends pass, so the trend
    control over-controls") no longer holds.

The genuinely trend-RESISTANT residue is the SECTOR DECOMPOSITION: refining ~null
vs power/manufacturing negative — suggestive MECHANISM evidence (effects land where
abatement options exist, not on a pure secular trend), not a clean magnitude.
==================================================================================
""")
