"""Carbon-pricing policy recommendation engine — Streamlit dashboard.

Price sliders drive the predicted effect (continuous dose-response, full posterior).
The country picker drives the HONESTY: a confidence tag from the reference-class diagnostic.

Run:  uv run streamlit run dashboard/app.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load():
    pz = np.load(os.path.join(HERE, 'posterior.npz'))
    sup = pd.read_csv(os.path.join(HERE, 'country_support.csv'))
    return pz['b_tax'], pz['b_ets'], pz['b_int'], sup

b_tax, b_ets, b_int, sup = load()

TAG_STYLE = {
    'DATA-INFORMED': ('#1a7f37', '🟢', 'This country (or close peers) actually adopted carbon pricing — the estimate is data-informed.'),
    'NEAR-SUPPORT':  ('#9a6700', '🟡', 'No direct data, but this country sits near the cloud of observed adopters — extrapolation is plausible but wider.'),
    'FAR':           ('#cf222e', '🔴', 'This country is far outside the observed-adopter cloud — treat the number as a weak prior, not a prediction.'),
}

def effect_draws(tax_price, ets_price):
    """Posterior draws of the annual log-CO2/capita effect of facing these prices."""
    pt, pe = tax_price / 10.0, ets_price / 10.0
    return b_tax * pt + b_ets * pe + b_int * pt * pe

# ---------------- UI ----------------
st.set_page_config(page_title='Carbon-Pricing Recommendation Engine', layout='wide')
st.title('Carbon-Pricing Policy Recommendation Engine')
st.caption('Set a carbon price, pick a country, get a predicted CO₂ effect with honest uncertainty. '
           'Effect = pooled dose-response from a Bayesian Student-t panel model (country + year fixed effects).')

with st.sidebar:
    st.header('Policy levers')
    countries = sup['country'].tolist()
    default = countries.index('Sweden') if 'Sweden' in countries else 0
    country = st.selectbox('Country', countries, index=default)
    row = sup[sup['country'] == country].iloc[0]
    st.markdown('---')
    ets_price = st.slider('ETS carbon price ($/tonne)', 0, 100, 30, step=5)
    tax_price = st.slider('Carbon tax price ($/tonne)', 0, 150, 0, step=5)
    st.markdown('---')
    st.caption(f"**{country} today:** ETS ${row.latest_ets_price:.0f}/t · tax ${row.latest_tax_price:.0f}/t · "
               f"governance z={row.impl_capacity_z:+.1f}")

# confidence banner first (uncertainty-first)
color, icon, blurb = TAG_STYLE[row.tag]
st.markdown(
    f"<div style='padding:0.6rem 1rem;border-left:6px solid {color};background:{color}14;border-radius:4px'>"
    f"<b>{icon} Confidence: {row.tag}</b> — {blurb}<br><span style='color:#666'>Reason: {row.reason}</span></div>",
    unsafe_allow_html=True)
st.write('')

eff = effect_draws(tax_price, ets_price)
pct3 = eff * 3 * 100           # % change in CO2/capita over the 3-year outcome window
lo, hi = np.percentile(pct3, 5), np.percentile(pct3, 95)
p_reduce = float((eff < 0).mean())

c1, c2, c3 = st.columns(3)
c1.metric('Predicted CO₂/capita change (3 yr)', f'{pct3.mean():+.1f}%', help='Posterior mean of the 3-year effect.')
c2.metric('90% credible interval', f'[{lo:+.1f}%, {hi:+.1f}%]')
c3.metric('P(reduces emissions)', f'{p_reduce:.0%}')

st.caption('Central estimate. Under a stricter spec (country-specific decarbonization trends) the **ETS** effect is '
           '~25% smaller (e.g. €30 → ~−7% rather than −9%) — read the headline as the upper end of a robust range.')

if tax_price > 0:
    st.caption('⚠️ **Carbon-tax caveat:** the tax\'s effect is **weak across every design we tried** — it fails the '
               'country-trend control on total CO₂, is null in a transport-CO₂ dose test, and is insignificant in a '
               'pre-1990 Nordic synthetic control. Andersson (2019) finds a real *transport* effect within Sweden, but '
               'our cross-country data can\'t reproduce it. **The robust lever is ETS; treat the tax contribution as unproven.**')

if tax_price == 0 and ets_price == 0:
    st.info('Set a non-zero price to see an effect. At $0 the model predicts ~no price effect (the dose passes through the origin).')

# dose-response curve: effect vs ETS price at the chosen tax price
# observed price range — beyond this the dose-response shape is unidentified (linear assumption is extrapolating)
ETS_OBS_MAX, TAX_OBS_MAX = 50, 130
if ets_price > ETS_OBS_MAX or tax_price > TAX_OBS_MAX:
    st.warning(
        f"⚠️ **Extrapolating beyond observed prices** (data tops out near €{ETS_OBS_MAX} ETS / €{TAX_OBS_MAX} tax). "
        "The model assumes a *linear* dose, but above the observed range the curve shape is unidentified — "
        "a diminishing-returns curve fits the data equally well and predicts roughly **half** this effect at high prices. "
        "Treat high-price numbers as the optimistic end of a wide range, not a point estimate.")

st.subheader('Dose-response — effect vs. ETS price')
grid = np.arange(0, 101, 2)
means, los, his = [], [], []
for p in grid:
    e = effect_draws(tax_price, p) * 3 * 100
    means.append(e.mean()); los.append(np.percentile(e, 5)); his.append(np.percentile(e, 95))
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.fill_between(grid, los, his, alpha=0.18, color=color, label='90% CI')
ax.plot(grid, means, color=color, lw=2)
if ETS_OBS_MAX < grid.max():   # shade the extrapolation zone
    ax.axvspan(ETS_OBS_MAX, grid.max(), color='#888', alpha=0.10)
    ax.text(ETS_OBS_MAX + 1, ax.get_ylim()[0] if False else min(means) * 0.15,
            'beyond observed\nprices (extrapolation)', fontsize=7.5, color='#666', va='bottom')
ax.axvline(ets_price, ls='--', color='#444', lw=1)
ax.scatter([ets_price], [pct3.mean()], color=color, zorder=5)
ax.axhline(0, color='#999', lw=0.8)
ax.set_xlabel('ETS price ($/tonne)'); ax.set_ylabel('CO₂/capita change over 3 yr (%)')
ax.set_title(f'at carbon tax = ${tax_price}/tonne  ·  solid where data supports it, shaded = extrapolation', fontsize=9)
ax.grid(alpha=0.25)
st.pyplot(fig)

with st.expander('How to read this — and what it cannot tell you'):
    st.markdown("""
- **Price is the lever, not the country.** The effect comes from the carbon *price*. We validated (leave-one-country-out)
  that country covariates **cannot** predict which country beats the average, so the engine deliberately does **not** personalize
  the effect by country — it personalizes the **confidence** instead.
- **The ETS effect is era-stable.** The price-response is statistically the same pre-2008 and post-2010; the mid-2010s "null"
  was the €5 price collapse, not a dead policy. A modern high-price ETS is predicted to bite.
- **ETS is robust; the tax is not.** The ETS effect survives Student-t, era-splits, *and* country-specific decarbonization
  trends (attenuating ~25% to ~−7% at €30, still p<0.001). The carbon-**tax** effect on total CO₂ *collapses* under country
  trends and against Sweden's own data (Andersson's tax effect is transport-only) — so the engine treats the tax as unproven.
- **Tax vs. ETS are substitutes, not complements** (sub-additive interaction): stacking a tax on top of an ETS adds little.
- **The curve shape is only pinned where there's data (≲ €50 ETS).** Leave-one-out cross-validation can't distinguish a
  linear dose from a diminishing-returns (log) one — they fit observed prices equally well and only diverge in the
  extrapolation zone (the shaded region), where they disagree by ~2×. So below ~€50 the number is solid; above it,
  read the linear estimate as the *optimistic* edge.
- **Honest limits:** identification rests on ~26 tax / 29 ETS countries, almost all high-income EU. For 🔴 FAR countries
  the number is a weak prior. Effects are 3-year, on CO₂ per capita.
""")

with st.expander('Evidence base — how hard we tried to break this (and what survived)'):
    st.markdown("""
We stress-tested the engine with five independent methods. The story is consistent across all of them:

| method | ETS | carbon tax |
|---|---|---|
| Bayesian dose-response (this engine) | robust, −7 to −10% @ €30 | weak, marginal |
| Country-specific-trend control | **survives** (p<0.001) | **collapses** (flips sign) |
| Transport (oil) CO₂ dose test | robust | null (p=0.37) |
| Sweden external anchor (Andersson) | — | over-attributes; tax is transport-only |
| Pre-1990 Nordic synthetic control | (no control group) | insignificant (Abadie p>0.25) |
| EU-ETS synthetic control / SDID | *can't* identify — **no comparable control group exists** | — |

**Two methodological lessons baked into this tool:**
1. **Identification depends on the variation you have.** The ETS *price crashed and recovered* (€30→€5→€47) — variation a
   trend can't fake — so a dose-response identifies it. The EU all adopted ETS *at once*, so a control-group method (synthetic
   control / SDID) **cannot** work: there is no comparable un-priced economy to compare against.
2. **The carbon tax is weak in *aggregate* data everywhere we looked** — but Andersson (2019) shows it works on *transport*
   within Sweden. Aggregate CO₂ is simply the wrong outcome to see it. We report the tax as **unproven**, not as zero.

*(Full write-up: `docs/OVERNIGHT_SESSION_2026-06-11.md` and `docs/FINDINGS_LOG.md`.)*
""")
