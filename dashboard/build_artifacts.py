"""Fit the continuous-price dose engine once and persist everything the dashboard needs.

Outputs (in dashboard/):
  posterior.npz        - b_tax, b_ets, b_int posterior draws (per $10/tonne)
  country_support.csv  - per country: confidence tag, reason, adopter flag, latest prices, covariates

Run:  uv run python dashboard/build_artifacts.py
"""
import os
os.environ['PYTENSOR_FLAGS'] = 'cxx='
import numpy as np, pandas as pd, pymc as pm
import statsmodels.formula.api as smf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'dashboard')

df = pd.read_csv(os.path.join(ROOT, 'data/cleaned/final_analysis_data.csv')).sort_values(['country', 'year']).copy()
df['log_T'] = np.log(df['co2_per_capita'])
_f = df[['country', 'year', 'log_T']].copy(); _f['year'] -= 3; _f = _f.rename(columns={'log_T': 'log_T_p3'})
df = df.merge(_f, on=['country', 'year'], how='left'); df['d_T'] = (df['log_T_p3'] - df['log_T']) / 3.0
for p in ['tax_price_only', 'ets_price_only']:
    df[p] = df[p].fillna(0.0)
md = df[df[['d_T', 'tax_price_only', 'ets_price_only']].notna().all(axis=1)].copy()
md['Ptax'] = md['tax_price_only'] / 10.0
md['Pets'] = md['ets_price_only'] / 10.0
ci, cl = pd.factorize(md['country']); ti, tl = pd.factorize(md['year']); nc, ny = len(cl), len(tl)

# ---- fit the dose engine (pooled linear dose, Student-t, country+year FE) ----
with pm.Model():
    alpha = pm.Normal('mu_a', 0, .5) + pm.HalfNormal('sigma_a', .2) * pm.Normal('z_a', 0, 1, shape=nc)
    gamma = pm.HalfNormal('sigma_g', .1) * pm.Normal('z_g', 0, 1, shape=ny)
    b_tax = pm.Normal('b_tax', 0, .01); b_ets = pm.Normal('b_ets', 0, .01); b_int = pm.Normal('b_int', 0, .01)
    sigma = pm.HalfNormal('sigma', .2); nu = pm.Gamma('nu', 2, .1)
    mu_i = alpha[ci] + gamma[ti] + b_tax * md['Ptax'].values + b_ets * md['Pets'].values + b_int * md['Ptax'].values * md['Pets'].values
    pm.StudentT('y_obs', nu=nu, mu=mu_i, sigma=sigma, observed=md['d_T'].values)
    idata = pm.sample(1000, tune=1500, chains=4, target_accept=.95, random_seed=42, nuts_sampler='nutpie', progressbar=False)

div = int(idata.sample_stats['diverging'].sum())
po = idata.posterior

# Extract raw posterior draws before widening
raw_b_tax = po['b_tax'].values.ravel()
raw_b_ets = po['b_ets'].values.ravel()
raw_b_int = po['b_int'].values.ravel()

iid_sds = {
    'b_tax': float(raw_b_tax.std()),
    'b_ets': float(raw_b_ets.std()),
    'b_int': float(raw_b_int.std()),
}
print(f"\nRaw posterior (iid Student-t assumption):")
print(f"  b_tax: mean={raw_b_tax.mean():.6f}, sd={iid_sds['b_tax']:.6f}")
print(f"  b_ets: mean={raw_b_ets.mean():.6f}, sd={iid_sds['b_ets']:.6f}")
print(f"  b_int: mean={raw_b_int.mean():.6f}, sd={iid_sds['b_int']:.6f}")

# ---- AUDIT FIX H-3: widen posterior to account for MA(2) serial correlation ----
#
# WHY: The 3-year overlapping outcome windows (d_T = log-diff over 3 yr) induce MA(2)
# autocorrelation in within-country residuals (measured lag1≈0.56, lag2≈0.20).  The PyMC
# model assumes iid Student-t errors, so its posterior variance is ~30-35% too small (the
# audit measured sd(b_ets)=0.0013 Bayesian vs 0.0019 cluster-robust OLS).
#
# CHEAP HONEST FIX (AUDIT 2026-06-11 §H-3):
#   1. Fit the identical parametric spec (Ptax + Pets + Ptax*Pets + country FE + year FE)
#      via OLS with cluster-robust SEs (clustered by country, the right unit of replication).
#   2. For each slope s ∈ {b_tax, b_ets, b_int}: ratio = clustered_SE(s) / posterior_sd(s).
#      If ratio > 1 the posterior is too tight; rescale draws around their posterior mean
#      by the ratio so the posterior spread matches the sampling uncertainty.
#   3. Keep keys b_tax, b_ets, b_int (dashboard depends on exact names).
#
# NOTE: We only widen — if the Bayesian posterior is already wider (ratio < 1) we leave it
# alone (conservative direction).  The posterior mean is unchanged; only the spread grows.

ols_spec = "d_T ~ Ptax + Pets + Ptax:Pets + C(country) + C(year)"
ols_res = smf.ols(ols_spec, data=md).fit(
    cov_type='cluster', cov_kwds={'groups': md['country']}
)
clustered_ses = {
    'b_tax': float(ols_res.bse['Ptax']),
    'b_ets': float(ols_res.bse['Pets']),
    'b_int': float(ols_res.bse['Ptax:Pets']),
}

print(f"\nCluster-robust OLS SEs (clustered by country):")
for k, v in clustered_ses.items():
    print(f"  {k}: SE={v:.6f}")

def widen(draws, clustered_se, iid_sd):
    """Rescale posterior draws around their mean by max(1, clustered_SE/iid_sd)."""
    ratio = clustered_se / iid_sd
    if ratio <= 1.0:
        return draws  # posterior already wide enough
    mean = draws.mean()
    return mean + (draws - mean) * ratio

b_tax_w = widen(raw_b_tax, clustered_ses['b_tax'], iid_sds['b_tax'])
b_ets_w = widen(raw_b_ets, clustered_ses['b_ets'], iid_sds['b_ets'])
b_int_w = widen(raw_b_int, clustered_ses['b_int'], iid_sds['b_int'])

print(f"\nWidened posterior (after H-3 cluster-robust scaling):")
print(f"  b_tax: mean={b_tax_w.mean():.6f}, sd={b_tax_w.std():.6f}  (ratio={clustered_ses['b_tax']/iid_sds['b_tax']:.3f})")
print(f"  b_ets: mean={b_ets_w.mean():.6f}, sd={b_ets_w.std():.6f}  (ratio={clustered_ses['b_ets']/iid_sds['b_ets']:.3f})")
print(f"  b_int: mean={b_int_w.mean():.6f}, sd={b_int_w.std():.6f}  (ratio={clustered_ses['b_int']/iid_sds['b_int']:.3f})")

np.savez(os.path.join(OUT, 'posterior.npz'),
         b_tax=b_tax_w, b_ets=b_ets_w, b_int=b_int_w)
print(f"\nsaved posterior.npz  (divergences={div}, draws={po['b_ets'].size})")

# ---- per-country confidence (reference class, Step-10 logic) ----
df['log_gdp_pc'] = np.log(df['gdp'] / df['population'])
cc_cols = ['log_gdp_pc', 'implementation_capacity_z']
cov = df.dropna(subset=cc_cols).sort_values('year').groupby('country')[cc_cols].last()
ever = df.groupby('country').agg(tax=('has_tax', 'max'), ets=('has_ets', 'max'))
priced = ever[(ever['tax'] == 1) | (ever['ets'] == 1)].index
pin = cov.index.intersection(priced)
P = cov.loc[pin].values; mu = P.mean(axis=0); Sinv = np.linalg.inv(np.cov(P, rowvar=False))
cov['maha'] = [float(np.sqrt((x - mu) @ Sinv @ (x - mu))) for x in cov.values]
thresh = float(cov.loc[pin, 'maha'].quantile(0.90))

def pctile(country, col):
    return (cov.loc[pin, col] < cov.loc[country, col]).mean() * 100

def tag_reason(country):
    if country in priced:
        return 'DATA-INFORMED', 'observed adopting carbon pricing'
    reasons = []
    for col, name in [('log_gdp_pc', 'income'), ('implementation_capacity_z', 'governance')]:
        p = pctile(country, col)
        if p < 1: reasons.append(f'{name} below observed range')
        elif p > 99: reasons.append(f'{name} above observed range')
        elif p <= 10: reasons.append(f'low-{name} edge')
    tag = 'NEAR-SUPPORT' if cov.loc[country, 'maha'] <= thresh else 'FAR'
    return tag, ('; '.join(reasons) if reasons else 'inside cloud but unobserved')

# latest observed prices (most recent year) for "current policy" context
latest = df.sort_values('year').groupby('country').last()
rows = []
for c in cov.index:
    tag, why = tag_reason(c)
    rows.append(dict(country=c, tag=tag, reason=why,
                     adopter=(c in priced),
                     latest_tax_price=round(float(latest.loc[c, 'tax_price_only']), 1) if c in latest.index else 0.0,
                     latest_ets_price=round(float(latest.loc[c, 'ets_price_only']), 1) if c in latest.index else 0.0,
                     log_gdp_pc=round(float(cov.loc[c, 'log_gdp_pc']), 2),
                     impl_capacity_z=round(float(cov.loc[c, 'implementation_capacity_z']), 2)))
sup = pd.DataFrame(rows).sort_values(['adopter', 'country'], ascending=[False, True])
sup.to_csv(os.path.join(OUT, 'country_support.csv'), index=False)
print(f"saved country_support.csv  ({len(sup)} countries; {sup['adopter'].sum()} adopters; maha thresh={thresh:.2f})")
print(sup['tag'].value_counts().to_string())
