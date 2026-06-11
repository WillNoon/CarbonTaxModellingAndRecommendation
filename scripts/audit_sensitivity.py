"""Audit 2026-06-11: sensitivity of headline results to corrected treatment coding.

Two confirmed coding errors in final_analysis_data.csv:
  F1. has_ets/ets_price_only miss Czechia, UK, Norway, Iceland, South Korea entirely
      (name-mismatch in the EU-expansion merge) and treat Bulgaria/Romania/Croatia
      from 2005 instead of their accession years (2007/2007/2013).
  F2. has_tax onset = first year WB reports a price, not implementation year
      (Denmark 2007 vs 1992, Finland 2000 vs 1990, etc.).

This script re-runs (a) the dose-response regression behind the dashboard and
(b) the binary tax-vs-ETS TWFE, under original vs corrected coding, plus
(c) the outstanding SUSPECT fossil-dependence heterogeneity with real fossil_pct.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

df = pd.read_csv('data/cleaned/final_analysis_data.csv')

# ---------- corrected coding ----------
cor = df.copy()
eua = cor.loc[cor.country == 'Germany', ['year', 'ets_price_only']] \
         .set_index('year')['ets_price_only']

# KETS prices from raw WB file (row 'ETS_KR'), col 31 = 2015 ... col 41 = 2025
raw = pd.read_csv('data/raw/carbon_tax_wb_prices.csv', header=None)
kr = raw[raw[0] == 'ETS_KR'].iloc[0]
kets = {2015 + i: float(kr[31 + i]) for i in range(7)}  # 2015-2021

def set_ets(d, country, years, price_map):
    m = (d.country == country) & (d.year.isin(years))
    d.loc[m, 'has_ets'] = 1
    d.loc[m, 'ets_price_only'] = d.loc[m, 'year'].map(price_map).fillna(0)

yrs = range(1996, 2022)
set_ets(cor, 'Czechia', [y for y in yrs if y >= 2005], eua)
set_ets(cor, 'United Kingdom', [y for y in yrs if 2005 <= y], eua)  # 2021 = UK ETS ~ EUA proxy
set_ets(cor, 'Norway', [y for y in yrs if y >= 2008], eua)
set_ets(cor, 'Iceland', [y for y in yrs if y >= 2008], eua)
set_ets(cor, 'South Korea', [y for y in yrs if y >= 2015], pd.Series(kets))

# late accessions: not in EU ETS before entry
for c, entry in [('Bulgaria', 2007), ('Romania', 2007), ('Croatia', 2013)]:
    m = (cor.country == c) & (cor.year < entry)
    cor.loc[m, ['has_ets', 'ets_price_only']] = 0

# corrected tax onsets (implementation years; price stays 0 where WB lacks it,
# so the binary spec is corrected but the dose spec still lacks early prices)
tax_onset = {'Denmark': 1992, 'Finland': 1990, 'Slovenia': 1996, 'Estonia': 2000,
             'Latvia': 2004, 'Ukraine': 2011, 'Portugal': 2015, 'Mexico': 2014,
             'South Africa': 2019}
for c, y0 in tax_onset.items():
    cor.loc[(cor.country == c) & (cor.year >= y0), 'has_tax'] = 1

# ---------- common pieces ----------
for d in (df, cor):
    d['Ptax'] = d['tax_price_only'] / 10
    d['Pets'] = d['ets_price_only'] / 10
    d['logco2'] = np.log(d['co2_per_capita'].where(d['co2_per_capita'] > 0))
    d.sort_values(['country', 'year'], inplace=True)
    d['d3'] = (d.groupby('country')['logco2'].shift(-3) - d['logco2']) / 3

def fit(formula, d, label):
    need = [v for v in ['d3', 'co2_per_capita_future_trend', 'Ptax', 'Pets', 'has_tax',
                        'has_ets', 'fossil_z', 'log_gdp', 'log_population',
                        'natural_resource_rents_per_gdp'] if v in formula]
    sub = d.dropna(subset=need)
    m = smf.ols(formula, data=sub).fit(cov_type='cluster',
                                       cov_kwds={'groups': sub['country']})
    keep = [p for p in m.params.index if p in
            ('Ptax', 'Pets', 'has_tax', 'has_ets', 'has_ets:fossil_z', 'has_tax:fossil_z',
             'fossil_z')]
    print(f'\n--- {label} (n={int(m.nobs)}) ---')
    for p in keep:
        print(f'  {p:18s} {m.params[p]:+.5f}  (se {m.bse[p]:.5f}, p={m.pvalues[p]:.4f})')
    return m

# ---------- (a) dose-response: the dashboard engine ----------
dose = 'd3 ~ Ptax + Pets + C(country) + C(year)'
fit(dose, df, 'DOSE original coding')
fit(dose, cor, 'DOSE corrected ETS coding')

# ---------- (b) binary tax vs ETS TWFE ----------
binar = ('co2_per_capita_future_trend ~ has_tax + has_ets + C(country) + C(year)'
         ' + log_gdp + log_population + natural_resource_rents_per_gdp')
fit(binar, df, 'BINARY original coding')
fit(binar, cor, 'BINARY corrected tax+ETS coding')

# ---------- (c) SUSPECT fossil heterogeneity, re-run with REAL fossil_pct ----------
df['fossil_z'] = (df['fossil_pct'] - df['fossil_pct'].mean()) / df['fossil_pct'].std()
het = ('co2_per_capita_future_trend ~ has_tax * fossil_z + has_ets * fossil_z'
       ' + C(country) + C(year) + log_gdp + log_population + natural_resource_rents_per_gdp')
fit(het, df.dropna(subset=['fossil_z']), 'FOSSIL heterogeneity, real fossil_pct (original coding)')
cor['fossil_z'] = (cor['fossil_pct'] - cor['fossil_pct'].mean()) / cor['fossil_pct'].std()
fit(het, cor.dropna(subset=['fossil_z']), 'FOSSIL heterogeneity, real fossil_pct (corrected coding)')
