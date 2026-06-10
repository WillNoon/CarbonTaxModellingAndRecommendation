"""Fit the continuous-price dose engine once and persist everything the dashboard needs.

Outputs (in dashboard/):
  posterior.npz        - b_tax, b_ets, b_int posterior draws (per $10/tonne)
  country_support.csv  - per country: confidence tag, reason, adopter flag, latest prices, covariates

Run:  uv run python dashboard/build_artifacts.py
"""
import os
os.environ['PYTENSOR_FLAGS'] = 'cxx='
import numpy as np, pandas as pd, pymc as pm

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
np.savez(os.path.join(OUT, 'posterior.npz'),
         b_tax=po['b_tax'].values.ravel(), b_ets=po['b_ets'].values.ravel(), b_int=po['b_int'].values.ravel())
print(f"saved posterior.npz  (divergences={div}, draws={po['b_ets'].size})")

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
