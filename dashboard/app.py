"""Carbon-pricing policy engine — Streamlit dashboard.

Pages: Engine (map picker + sliders + predicted impact), Evidence (method-by-method
results + event study), Methods (identifying assumption, what survived/was demoted).

The effect depends only on the carbon prices (pooled dose-response, Bayesian Student-t
panel model with country + year FE). The selected country changes only the confidence
tag, never the effect (leave-one-country-out validation).

Run:  streamlit run dashboard/app.py
"""
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# In-sample dose support (final_analysis_data.csv, yr<=2018 — the dose sample needs
# CO2 at t+3). ets_price_only p99 = $34.5, one point above ($55.5, Switzerland 2014);
# the 2021 €47 EUA price is outside the estimation sample. tax_price_only max = $168.8
# (Sweden 2008). All prices US$/tonne (World Bank).
ETS_OBS_MAX = 35.0    # $/tonne — in-sample ETS support ceiling (p99 ≈ $34.5)
ETS_SPARSE_MAX = 55.0  # one lone Swiss point sits in the $35–55 sparse zone
TAX_OBS_MAX = 169.0   # $/tonne — max observed tax (Sweden $168.8)

ROBUST_LO, ROBUST_HI = -10.0, -7.0  # robust ETS range, % per $30/tonne over 3 yr

STATUS_COLOR = {
    'Adopter — data-informed': '#2dd4bf',   # teal
    'Near support':            '#3b82f6',   # blue
    'Far from support':        '#475569',   # slate
}

TAG_STYLE = {
    'DATA-INFORMED': ('#2dd4bf', 'DATA-INFORMED',
                      'This country (or close peers) actually adopted carbon pricing — the estimate is data-informed.'),
    'NEAR-SUPPORT':  ('#60a5fa', 'NEAR SUPPORT',
                      'No direct data, but this country sits near the cloud of observed adopters — extrapolation is plausible but wider.'),
    'FAR':           ('#94a3b8', 'FAR FROM SUPPORT',
                      'This country is far outside the observed-adopter cloud — treat the number as a weak prior, not a prediction.'),
}

# OWID country name → ISO-3 for the choropleth (all 163 names in country_support.csv map)
ISO3 = {
    'Argentina': 'ARG', 'Australia': 'AUS', 'Austria': 'AUT', 'Belgium': 'BEL',
    'Bulgaria': 'BGR', 'Canada': 'CAN', 'Chile': 'CHL', 'Colombia': 'COL',
    'Croatia': 'HRV', 'Cyprus': 'CYP', 'Denmark': 'DNK', 'Estonia': 'EST',
    'Finland': 'FIN', 'France': 'FRA', 'Germany': 'DEU', 'Greece': 'GRC',
    'Hungary': 'HUN', 'Iceland': 'ISL', 'Ireland': 'IRL', 'Italy': 'ITA',
    'Japan': 'JPN', 'Kazakhstan': 'KAZ', 'Latvia': 'LVA', 'Lithuania': 'LTU',
    'Luxembourg': 'LUX', 'Malta': 'MLT', 'Mexico': 'MEX', 'Netherlands': 'NLD',
    'New Zealand': 'NZL', 'Norway': 'NOR', 'Poland': 'POL', 'Portugal': 'PRT',
    'Romania': 'ROU', 'Singapore': 'SGP', 'Slovakia': 'SVK', 'Slovenia': 'SVN',
    'South Africa': 'ZAF', 'Spain': 'ESP', 'Sweden': 'SWE', 'Switzerland': 'CHE',
    'Ukraine': 'UKR', 'United Kingdom': 'GBR', 'Afghanistan': 'AFG', 'Albania': 'ALB',
    'Algeria': 'DZA', 'Angola': 'AGO', 'Armenia': 'ARM', 'Azerbaijan': 'AZE',
    'Bahrain': 'BHR', 'Bangladesh': 'BGD', 'Barbados': 'BRB', 'Belarus': 'BLR',
    'Benin': 'BEN', 'Bolivia': 'BOL', 'Bosnia and Herzegovina': 'BIH',
    'Botswana': 'BWA', 'Brazil': 'BRA', 'Burkina Faso': 'BFA', 'Burundi': 'BDI',
    'Cambodia': 'KHM', 'Cameroon': 'CMR', 'Cape Verde': 'CPV',
    'Central African Republic': 'CAF', 'Chad': 'TCD', 'China': 'CHN',
    'Comoros': 'COM', 'Congo': 'COG', 'Costa Rica': 'CRI', "Cote d'Ivoire": 'CIV',
    'Cuba': 'CUB', 'Czechia': 'CZE', 'Democratic Republic of Congo': 'COD',
    'Djibouti': 'DJI', 'Dominica': 'DMA', 'Dominican Republic': 'DOM',
    'Ecuador': 'ECU', 'Egypt': 'EGY', 'El Salvador': 'SLV',
    'Equatorial Guinea': 'GNQ', 'Eswatini': 'SWZ', 'Ethiopia': 'ETH',
    'Gabon': 'GAB', 'Gambia': 'GMB', 'Georgia': 'GEO', 'Ghana': 'GHA',
    'Guatemala': 'GTM', 'Guinea': 'GIN', 'Guinea-Bissau': 'GNB', 'Haiti': 'HTI',
    'Honduras': 'HND', 'Hong Kong': 'HKG', 'India': 'IND', 'Indonesia': 'IDN',
    'Iran': 'IRN', 'Iraq': 'IRQ', 'Israel': 'ISR', 'Jamaica': 'JAM',
    'Jordan': 'JOR', 'Kenya': 'KEN', 'Kuwait': 'KWT', 'Kyrgyzstan': 'KGZ',
    'Laos': 'LAO', 'Lebanon': 'LBN', 'Lesotho': 'LSO', 'Liberia': 'LBR',
    'Libya': 'LBY', 'Madagascar': 'MDG', 'Malawi': 'MWI', 'Malaysia': 'MYS',
    'Mali': 'MLI', 'Mauritania': 'MRT', 'Mauritius': 'MUS', 'Moldova': 'MDA',
    'Mongolia': 'MNG', 'Montenegro': 'MNE', 'Morocco': 'MAR', 'Mozambique': 'MOZ',
    'Myanmar': 'MMR', 'Namibia': 'NAM', 'Nepal': 'NPL', 'Nicaragua': 'NIC',
    'Niger': 'NER', 'Nigeria': 'NGA', 'North Korea': 'PRK',
    'North Macedonia': 'MKD', 'Oman': 'OMN', 'Pakistan': 'PAK', 'Palestine': 'PSE',
    'Panama': 'PAN', 'Paraguay': 'PRY', 'Peru': 'PER', 'Philippines': 'PHL',
    'Qatar': 'QAT', 'Russia': 'RUS', 'Rwanda': 'RWA', 'Saint Lucia': 'LCA',
    'Sao Tome and Principe': 'STP', 'Saudi Arabia': 'SAU', 'Senegal': 'SEN',
    'Serbia': 'SRB', 'Seychelles': 'SYC', 'Sierra Leone': 'SLE',
    'South Korea': 'KOR', 'Sri Lanka': 'LKA', 'Syria': 'SYR', 'Tajikistan': 'TJK',
    'Tanzania': 'TZA', 'Thailand': 'THA', 'Togo': 'TGO',
    'Trinidad and Tobago': 'TTO', 'Tunisia': 'TUN', 'Turkey': 'TUR',
    'Turkmenistan': 'TKM', 'Uganda': 'UGA', 'United Arab Emirates': 'ARE',
    'United States': 'USA', 'Uruguay': 'URY', 'Uzbekistan': 'UZB',
    'Venezuela': 'VEN', 'Vietnam': 'VNM', 'Yemen': 'YEM', 'Zambia': 'ZMB',
    'Zimbabwe': 'ZWE',
}


@st.cache_data
def load_artifacts():
    """Posterior draws (4,000 each) + per-country support table."""
    with np.load(os.path.join(HERE, 'posterior.npz')) as pz:
        b_tax = pz['b_tax'].copy()
        b_ets = pz['b_ets'].copy()
        b_int = pz['b_int'].copy()
    sup = pd.read_csv(os.path.join(HERE, 'country_support.csv'))
    sup = sup.sort_values('country').reset_index(drop=True)
    return b_tax, b_ets, b_int, sup


def status_of(row):
    if row.tag == 'DATA-INFORMED':
        return 'Adopter — data-informed'
    if row.tag == 'NEAR-SUPPORT':
        return 'Near support'
    return 'Far from support'


@st.cache_data
def build_choropleth():
    """World map, cached so it never rebuilds on slider moves. Coloured by evidence
    status only — LOCO rules out per-country effect sizes."""
    _, _, _, sup = load_artifacts()
    d = sup.copy()
    d['iso'] = d['country'].map(ISO3)
    d['status'] = d.apply(status_of, axis=1)
    order = ['Adopter — data-informed', 'Near support', 'Far from support']
    d['status'] = pd.Categorical(d['status'], categories=order, ordered=True)
    d = d.sort_values('status')

    fig = go.Figure()
    for status in order:
        sub = d[d['status'] == status]
        custom = np.stack([sub['country'].values,
                           sub['latest_tax_price'].values,
                           sub['latest_ets_price'].values], axis=-1)
        fig.add_trace(go.Choropleth(
            locations=sub['iso'], locationmode='ISO-3',
            z=np.ones(len(sub)),  # flat — colour carries status, not a value
            customdata=custom,
            name=status,
            colorscale=[[0, STATUS_COLOR[status]], [1, STATUS_COLOR[status]]],
            showscale=False,
            marker_line_color='#0a1628', marker_line_width=0.4,
            hovertemplate=('<b>%{customdata[0]}</b><br>' + status +
                           '<br>tax $%{customdata[1]:.0f}/t · ETS $%{customdata[2]:.0f}/t'
                           '<extra></extra>'),
        ))
    fig.update_geos(
        projection_type='natural earth', showframe=False, showcoastlines=False,
        bgcolor='rgba(0,0,0,0)', landcolor='#11203a', showland=True,
        showocean=True, oceancolor='#0a1628', lakecolor='#0a1628',
        showcountries=True, countrycolor='#0a1628',
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0), height=440,
        paper_bgcolor='rgba(0,0,0,0)', geo_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', y=-0.02, x=0.5, xanchor='center',
                    font=dict(color='#e6edf6', size=12), bgcolor='rgba(0,0,0,0)'),
        font=dict(color='#e6edf6'), dragmode=False,
    )
    return fig


def effect_draws(b_tax, b_ets, b_int, tax_price, ets_price):
    """Posterior draws of the annual dlog CO2/capita effect of facing these prices."""
    pt, pe = tax_price / 10.0, ets_price / 10.0
    return b_tax * pt + b_ets * pe + b_int * pt * pe


def pct_change_3yr(eff):
    """3-yr compounded change in percent: 100*(exp(3*eff)-1), not log-points."""
    return 100.0 * np.expm1(eff * 3.0)


def inject_css():
    st.markdown("""
    <style>
      .block-container { padding-top: 2.2rem; max-width: 1280px; }
      h1, h2, h3 { letter-spacing: -0.02em; }
      .eyebrow { letter-spacing: 0.04em; font-size: 0.78rem;
                 color: #5eead4; font-weight: 600; margin-bottom: 0.2rem; }
      .hero-num { font-size: 4.2rem; font-weight: 700; line-height: 1;
                  letter-spacing: -0.03em; margin: 0.1rem 0; }
      .hero-sub { color: #93a4bd; font-size: 0.95rem; }
      .badge { display:inline-block; padding: 0.22rem 0.6rem; border-radius: 3px;
               font-weight: 700; font-size: 0.78rem; }
      .cibar-track { position: relative; height: 10px; border-radius: 2px;
                     background: #16294a; margin: 0.6rem 0 0.3rem 0; }
      .cibar-fill { position:absolute; top:0; bottom:0; border-radius:2px;
                    background: rgba(45,212,191,0.8); }
      .cibar-mid { position:absolute; top:-4px; width:3px; height:18px; background:#e6edf6; }
      .muted { color:#93a4bd; font-size:0.85rem; }
      .card { background:#11203a; border:1px solid #1e3a5f; border-radius:4px;
              padding:1.0rem 1.2rem; margin-bottom:0.8rem; }
      .card h4 { margin:0 0 0.35rem 0; color:#5eead4; font-size:1.0rem; }
      .pill { display:inline-block; font-size:0.7rem; padding:0.12rem 0.5rem; border-radius:3px;
              font-weight:600; }
    </style>
    """, unsafe_allow_html=True)


def badge_html(tag):
    color, label, _ = TAG_STYLE[tag]
    return (f"<span class='badge' style='background:{color}22;color:{color};"
            f"border:1px solid {color}66'>{label}</span>")


def page_engine():
    b_tax, b_ets, b_int, sup = load_artifacts()
    inject_css()

    st.markdown("<div class='eyebrow'>Carbon-pricing policy engine</div>", unsafe_allow_html=True)
    st.markdown("## What does a carbon price do to emissions?")
    st.markdown(
        "<span class='muted'>Set a price. The predicted 3-year CO₂/capita effect comes from "
        "the <b>price</b> — a pooled Bayesian dose-response. "
        "<b>The country you pick sets the confidence, not the effect</b> "
        "(validated leave-one-country-out: country traits can't predict who beats the average). "
        "Prices are US$/tonne.</span>", unsafe_allow_html=True)
    st.write('')

    map_col, ctrl_col = st.columns([1.45, 1], gap='large')

    with map_col:
        st.markdown("<div class='eyebrow'>Pick a country</div>", unsafe_allow_html=True)
        fig = build_choropleth()
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.caption('Colour = evidence status (adopter / near / far) — NOT effect size. '
                   'The effect is the same everywhere; the map only tells you how much to trust it.')

    with ctrl_col:
        countries = sup['country'].tolist()
        default = countries.index('Sweden') if 'Sweden' in countries else 0
        country = st.selectbox('Country (sets confidence only)', countries, index=default)
        row = sup[sup['country'] == country].iloc[0]

        color, label, blurb = TAG_STYLE[row.tag]
        st.markdown(badge_html(row.tag), unsafe_allow_html=True)
        st.markdown(f"<div class='muted' style='margin-top:0.4rem'>{blurb}<br>"
                    f"<span style='color:#6b7c97'>Reason: {row.reason}</span></div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='muted' style='margin-top:0.5rem'><b>{country} today:</b> "
                    f"ETS ${row.latest_ets_price:.0f}/t · tax ${row.latest_tax_price:.0f}/t · "
                    f"governance z={row.impl_capacity_z:+.1f}</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:0.9rem 0;border-color:#1e3a5f'>", unsafe_allow_html=True)

        _engine_fragment(b_tax, b_ets, b_int, color)


@st.fragment
def _engine_fragment(b_tax, b_ets, b_int, tag_color):
    """Sliders + predicted impact. A fragment, so slider moves don't rerun the map."""
    ets_price = st.slider('ETS carbon price (US$/tonne)', 0, 100, 30, step=5)
    tax_price = st.slider('Carbon tax price (US$/tonne)', 0, 175, 0, step=5)

    eff = effect_draws(b_tax, b_ets, b_int, tax_price, ets_price)
    pct = pct_change_3yr(eff)
    mean_pct = float(pct.mean())
    lo, hi = float(np.percentile(pct, 5)), float(np.percentile(pct, 95))
    p_reduce = float((eff < 0).mean())

    if tax_price == 0 and ets_price == 0:
        st.markdown("<div class='hero-num' style='color:#475569'>—</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-sub'>Set a price to see the predicted impact.</div>",
                    unsafe_allow_html=True)
        return

    hcol = '#2dd4bf' if mean_pct < 0 else '#fbbf24'
    st.markdown(f"<div class='hero-num' style='color:{hcol}'>{mean_pct:+.1f}%</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='hero-sub'>predicted CO₂/capita change over 3 years</div>",
                unsafe_allow_html=True)

    # credible-interval bar
    span = max(abs(lo), abs(hi), 1.0) * 1.15
    def x(v):  # map % onto 0..100 of the bar (centred on 0)
        return float(np.clip(50.0 + 50.0 * v / span, 0, 100))
    x_lo, x_hi, x_mid = x(lo), x(hi), x(mean_pct)
    left, width = min(x_lo, x_hi), abs(x_hi - x_lo)
    st.markdown(
        f"<div style='margin-top:1rem'>"
        f"<div class='muted'>90% credible interval</div>"
        f"<div class='cibar-track'>"
        f"<div class='cibar-fill' style='left:{left}%;width:{width}%'></div>"
        f"<div class='cibar-mid' style='left:{x_mid}%'></div>"
        f"</div>"
        f"<div class='muted' style='display:flex;justify-content:space-between'>"
        f"<span>{lo:+.1f}%</span><span>0%</span><span>{hi:+.1f}%</span></div>"
        f"</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='muted' style='margin-top:0.6rem'>"
                f"<b style='color:#e6edf6'>P(reduces emissions) = {p_reduce:.0%}</b></div>",
                unsafe_allow_html=True)

    st.markdown(f"<div class='muted' style='margin-top:0.5rem'>The robust ETS headline is "
                f"<b style='color:#5eead4'>{ROBUST_LO:.0f}% to {ROBUST_HI:.0f}% per $30</b> over 3 years. "
                f"Under a stricter spec (country-specific decarbonization trends) the ETS effect is "
                f"~25% smaller — read a single point as the optimistic edge of that range.</div>",
                unsafe_allow_html=True)

    # marginal tax contribution flips positive at ETS ≈ $28 (b_tax + b_int*Pets > 0)
    pt, pe = tax_price / 10.0, ets_price / 10.0
    marg_tax = (b_tax + b_int * pe) * pt
    marg_tax_pct = float(np.median(marg_tax)) * 3 * 100
    if tax_price > 0 and marg_tax_pct > 0:
        st.warning(
            "At this ETS price the fitted tax×ETS interaction pushes the tax contribution positive. "
            "That reflects very thin joint data, not evidence that a tax backfires — the verdict on "
            "the carbon tax is *unproven*, not harmful.")

    # warn when the interaction term carries a material share of a combined-lever result
    if tax_price > 0 and ets_price > 0:
        total = b_tax * pt + b_ets * pe + b_int * pt * pe
        int_term = b_int * pt * pe
        med_total = float(np.median(total))
        med_int = float(np.median(int_term))
        if abs(med_total) > 1e-9 and abs(med_int) > 0.15 * abs(med_total):
            st.warning(
                "Combined-lever results are illustrative: the tax×ETS interaction is estimated from "
                "very little joint variation (almost no country ran a high tax and a high ETS at once).")

    if tax_price > 0:
        st.caption("Carbon-tax caveat: the tax effect is weak in every cross-country design here "
                   "(fails the country-trend control on total CO₂, null in a transport-CO₂ dose test). "
                   "Andersson (2019) finds a real transport effect within Sweden, but cross-country data "
                   "can't reproduce it. The robust lever is the ETS; treat the tax contribution as unproven.")

    if ets_price >= ETS_OBS_MAX or tax_price >= TAX_OBS_MAX:
        msg = []
        if ets_price >= ETS_OBS_MAX:
            msg.append(f"ETS support tops out near \\${ETS_OBS_MAX:.0f} in the estimation sample "
                       f"(one Swiss point in the \\${ETS_OBS_MAX:.0f}–\\${ETS_SPARSE_MAX:.0f} zone; "
                       f"the 2021 €47 EUA price is outside the sample).")
        if tax_price >= TAX_OBS_MAX:
            msg.append(f"tax support tops out at \\${TAX_OBS_MAX:.0f} (Sweden).")
        st.info("Extrapolating beyond observed prices. " + " ".join(msg) +
                " The linear dose is unidentified up here — a diminishing-returns curve fits the data "
                "equally well and predicts a smaller effect.")

    st.markdown("<div class='eyebrow' style='margin-top:0.8rem'>Dose-response · effect vs. ETS price</div>",
                unsafe_allow_html=True)
    grid = np.arange(0, 101, 2.0)
    pe_g = grid / 10.0
    # vectorised: draws × grid
    eff_g = (b_tax[:, None] * pt + b_ets[:, None] * pe_g[None, :]
             + b_int[:, None] * pt * pe_g[None, :])
    pct_g = 100.0 * np.expm1(eff_g * 3.0)
    means = pct_g.mean(axis=0)
    los = np.percentile(pct_g, 5, axis=0)
    his = np.percentile(pct_g, 95, axis=0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.concatenate([grid, grid[::-1]]),
                             y=np.concatenate([his, los[::-1]]),
                             fill='toself', fillcolor='rgba(45,212,191,0.12)',
                             line=dict(width=0), hoverinfo='skip', showlegend=False))
    fig.add_trace(go.Scatter(x=grid, y=means, mode='lines',
                             line=dict(color='#2dd4bf', width=2.5), name='mean',
                             hovertemplate='ETS $%{x:.0f}/t → %{y:+.1f}%<extra></extra>'))
    # extrapolation shade beyond observed support
    fig.add_vrect(x0=ETS_OBS_MAX, x1=100, fillcolor='#475569', opacity=0.16,
                  line_width=0, annotation_text='beyond observed prices',
                  annotation_position='top right',
                  annotation_font=dict(size=10, color='#93a4bd'))
    fig.add_vline(x=ets_price, line=dict(color='#e6edf6', width=1, dash='dash'))
    fig.add_hline(y=0, line=dict(color='#475569', width=1))
    fig.add_trace(go.Scatter(x=[ets_price], y=[mean_pct], mode='markers',
                             marker=dict(color='#2dd4bf', size=11,
                                         line=dict(color='#0a1628', width=2)),
                             showlegend=False, hoverinfo='skip'))
    fig.update_layout(
        height=300, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#93a4bd', size=11),
        xaxis=dict(title='ETS price (US$/tonne)', gridcolor='#1e3a5f', zeroline=False),
        yaxis=dict(title='CO₂/capita change over 3 yr (%)', gridcolor='#1e3a5f', zeroline=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.caption(f"At carbon tax = \\${tax_price}/tonne. Solid where data supports it; shaded ≥ \\${ETS_OBS_MAX:.0f} "
               "is extrapolation. The curve is one pooled effect — it is NOT coloured by country (effects don't "
               "vary by country here).")


def page_evidence():
    inject_css()
    st.markdown("<div class='eyebrow'>The evidence</div>", unsafe_allow_html=True)
    st.markdown("## ETS works. The carbon tax is unproven.")
    st.markdown(
        "<span class='muted'>We stress-tested the ETS effect with <b>seven</b> independent methods. "
        "The story is consistent: the <b>EU ETS</b> robustly cuts emissions (≈ −7 to −10% per $30 over 3 years); "
        "the <b>carbon tax</b> is weak in cross-country aggregate data — identification comes from "
        "<b>price variation</b>, and the tax never separates from a country's underlying trend.</span>",
        unsafe_allow_html=True)
    st.write('')

    methods = [
        ("Within-country sector DiD (Eurostat)", "SUPPORTIVE", "#60a5fa",
         "−3.4%/$10 (p=0.03), but the 2026-06-11 audit found the original pre-trend test was miscomputed — "
         "the full-covariance test rejects (p≈0.004) and a pre-existing covered-sector trend can account for "
         "the endpoint. Supportive, not clean identification.", "n/a"),
        ("EUTL installation 2013 auctioning", "UPPER BOUND", "#94a3b8",
         "−27% power vs industry — but survivor-biased and renewables-confounded; an upper bound, not a clean magnitude.",
         "—"),
        ("Bayesian dose-response (this engine)", "ROBUST", "#2dd4bf",
         "ETS robust, −7 to −10% per $30. Carbon tax weak / marginal.", "weak, marginal"),
        ("Country-specific-trend control", "ROBUST", "#2dd4bf",
         "ETS survives (p<0.001, attenuates ~25%). Tax collapses — flips sign once country trends are absorbed.",
         "collapses (flips sign)"),
        ("Transport (oil) CO₂ dose test", "ROBUST", "#2dd4bf",
         "ETS robust. Tax null on transport CO₂ (p=0.37) in our cross-country data.", "null (p=0.37)"),
        ("Sweden external anchor (Andersson 2019)", "CONTEXT", "#94a3b8",
         "Andersson finds a real −6.3% transport effect within Sweden — but aggregate CO₂ over-attributes; "
         "the tax effect is transport-only.", "transport-only"),
        ("Pre-1990 Nordic SC / EU-ETS SDID", "NULL ID", "#475569",
         "Can't identify cross-country — every EU member priced at once, so there is no comparable control group.",
         "insignificant"),
    ]
    for name, tag, col, ets_text, tax_text in methods:
        st.markdown(
            f"<div class='card'>"
            f"<h4>{name} "
            f"<span class='pill' style='background:{col}22;color:{col};border:1px solid {col}55'>{tag}</span></h4>"
            f"<div class='muted'><b style='color:#e6edf6'>ETS:</b> {ets_text}</div>"
            f"<div class='muted' style='margin-top:0.25rem'><b style='color:#e6edf6'>Carbon tax:</b> {tax_text}</div>"
            f"</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Why the tax is unproven (and ETS is not)")
    st.markdown(
        "Identification comes from the **price variation we actually have**, not the fanciest method. "
        "Cross-country control-group designs *fail* here — every EU country priced carbon at once, so there is "
        "no clean control group. What *works* is **within-country price variation**: the EUA price swings up and "
        "down, and forward emissions track it, net of country and year fixed effects. The carbon **tax** never "
        "separates from a country's own decarbonization trend, so we report it as **unproven, not zero**.")

    es = os.path.join(ROOT, 'outputs', 'ets_covered_vs_uncovered_eventstudy.png')
    if os.path.exists(es):
        st.markdown("### Within-country event study")
        st.image(es, caption='ETS-covered sectors vs uncovered, within the same country. Supportive evidence — '
                             'but the 2026-06-11 audit demoted this from "clean ID": the corrected full-covariance '
                             'pre-trend test rejects (p≈0.004), and a pre-existing covered-sector trend can account '
                             'for the endpoint.')


def page_methods():
    inject_css()
    st.markdown("<div class='eyebrow'>Methods</div>", unsafe_allow_html=True)
    st.markdown("## What we tested, what survived, what we demoted")
    st.write('')

    c1, c2, c3 = st.columns(3, gap='medium')
    with c1:
        st.markdown("<div class='card'><h4 style='color:#2dd4bf'>Survived</h4>"
                    "<div class='muted'>"
                    "• ETS dose-response, ≈ −7 to −10% per $30<br>"
                    "• Survives Student-t errors, era-splits, country-specific trends (attenuates ~25%)<br>"
                    "• Survives dropping the 2008–12 price crash entirely<br>"
                    "• ETS effect statistically era-stable</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='card'><h4 style='color:#fbbf24'>Demoted</h4>"
                    "<div class='muted'>"
                    "• Sector-DiD \"clean ID\" → <b>supportive only</b> (pre-trend test was miscomputed; "
                    "corrected test rejects, p≈0.004)<br>"
                    "• \"Tax & ETS are substitutes\" → <b>suggestive</b>, not fact<br>"
                    "• \"Fossil dependence hurts\" → retired (was an imputation-flag artifact)</div></div>",
                    unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='card'><h4 style='color:#94a3b8'>Unproven / null</h4>"
                    "<div class='muted'>"
                    "• Carbon tax on aggregate CO₂ — weak everywhere we looked<br>"
                    "• Cross-country control-group designs (SDID, Nordic SC) — no comparable control group<br>"
                    "• Per-country effect personalization — LOCO says country traits can't predict it</div></div>",
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### The identifying assumption, stated plainly")
    st.markdown(
        "> The ETS price is a **market equilibrium price**, not a randomized treatment. Our identification leans on "
        "**within-country price swings, net of country and year fixed effects** — the assumption is that, conditional "
        "on those fixed effects, the timing and size of EUA price movements are not driven by the same forces that "
        "independently move a country's forward emissions. Because **all EU countries share one EUA price path**, the "
        "effective number of independent treated price-paths is small (leave-one-country-out cannot fix common-path "
        "confounding). So this is **robust association plus a coherent mechanism — not a randomized experiment.** "
        "We report the ETS as robustly real, ≈ −7 to −10% per \\$30, and are honest about the residual uncertainty.")

    st.markdown("### How to read the engine")
    st.markdown(
        "- **Price is the lever, not the country.** The effect comes from the carbon *price*. We deliberately do "
        "**not** personalize the effect by country — leave-one-country-out validation showed country covariates "
        "cannot predict which country beats the average. The country sets the **confidence** instead.\n"
        "- **Confidence tags are a reference-class diagnostic.** A country is *data-informed* if it (or close peers) "
        "actually adopted pricing; *near support* / *far* are Mahalanobis distance from the adopter cloud on income "
        "and governance, thresholded at the adopters' own 90th percentile.\n"
        "- **The curve is pinned only where there's data (≲ \\$35 ETS).** Above that the linear dose is extrapolating; "
        "a diminishing-returns curve fits observed prices equally well.\n"
        "- **Effects are 3-year, on CO₂ per capita.** Identification rests on ~26 tax / ~29 ETS countries, almost "
        "all high-income EU. For *far* countries the number is a weak prior.")
    st.caption("Prices are US\\$/tonne (World Bank). For rough context, the ETS slider's \\$30 ≈ €28 at recent rates; "
               "the 2021 €47 EUA price (≈ \\$50) sits outside this engine's estimation sample.")


st.set_page_config(page_title='Carbon-pricing policy engine', layout='wide',
                   initial_sidebar_state='expanded')

nav = st.navigation([
    st.Page(page_engine, title='Engine', default=True),
    st.Page(page_evidence, title='Evidence'),
    st.Page(page_methods, title='Methods'),
])
nav.run()
