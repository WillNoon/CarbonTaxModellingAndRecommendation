# Dashboard redesign — "Paris Agreement" map-first, honest-by-design

> Implements Part 4 of `docs/AUDIT_2026-06-11.md`. Owns `dashboard/app.py`,
> `dashboard/requirements.txt`, root `requirements.txt`, and `.streamlit/config.toml`.
> Does NOT touch `dashboard/build_artifacts.py` or `dashboard/posterior.npz` (another agent
> owns them); depends only on the posterior keys `b_tax` / `b_ets` / `b_int`.

## Structure — three pages (`st.navigation` / `st.Page`)

### ① Engine (default page)
- **Dark world choropleth** (plotly `go.Choropleth`, `locationmode='ISO-3'`) as the centerpiece /
  country picker, beside a `st.selectbox`. Coloured by **evidence/policy status only** — three
  traces: `Adopter — data-informed` (teal), `Near support` (blue), `Far from support` (slate).
  Flat `z` so colour carries *status*, never effect size (LOCO-compliant). Hover shows the
  country's current observed tax / ETS prices.
- A plain-language line right at the picker: *"the country you pick sets the confidence, not the
  effect"* — so users never discover the no-personalization rule confused.
- A designed **confidence badge** (pill) + reason + "country today" prices.
- **HERO impact number** in big teal/amber type, with:
  - a **gradient credible-interval bar** (teal→aqua→amber) instead of three identical metric boxes,
    showing the 5/95 interval and the mean marker;
  - **P(reduction)** as a secondary stat;
  - the robust **−10% to −7% per \$30** ETS range built into the presentation.
- **Plotly dose-response curve** (effect vs ETS price) with a shaded extrapolation band beyond
  the observed-support ceiling and a marker at the current ETS price. Not coloured by country.

### ② Evidence
- The 7-method evidence as **readable status cards** (badge per method: SUPPORTIVE / ROBUST /
  UPPER BOUND / CONTEXT / NULL ID), each with an ETS line and a carbon-tax line.
- The committed **event-study image** (`outputs/ets_covered_vs_uncovered_eventstudy.png`,
  guarded with `os.path.exists`).
- The headline told plainly: **ETS works; the tax is unproven** — and *why* (identification
  comes from price variation; the tax never separates from a country's own trend).

### ③ Methods & honesty
- Three columns: **Survived / Demoted / Unproven-null** — the project's differentiator.
- The **identifying assumption** stated in one honest paragraph (EUA price is a market
  equilibrium price; identification leans on within-country price swings net of country & year
  FE; all EU members share one price path ⇒ robust-association-plus-mechanism, not an RCT).
- "How to read the engine" notes (price is the lever, confidence-tag logic, support ceiling).

## Design decisions
- **Theme** in `.streamlit/config.toml` at **repo root** (Streamlit Cloud reads it there): deep
  navy base `#0a1628`, teal/aqua primary `#2dd4bf`, clean sans typography. Restrained, no emoji.
- Confidence is a **designed badge**, not coloured text. The dose-response curve is **never**
  coloured by country tag (that would imply per-country effects — the exact LOCO misread).
- **Plotly everywhere** (interactive hover). **matplotlib dropped entirely** from the app and
  from both `requirements.txt` files; `plotly` added to both. Deps kept light (4 runtime deps).
- **Responsiveness:** the slider → hero → CI bar → dose-curve block is wrapped in
  **`@st.fragment`**, so slider moves rerun only that fragment — the heavy map does **not** rebuild.
  Artifact loading and the choropleth figure are `@st.cache_data`-cached. Per-interaction work is
  pure numpy on the 4,000 posterior draws (trivial; the dose grid is vectorised draws×grid).
- **Country names:** all 163 names in `country_support.csv` mapped to **ISO-3** via an explicit
  embedded dict (`ISO3`) and verified to render with `locationmode='ISO-3'` (0 missing, 0
  exceptions). ISO-3 chosen over `'country names'` because plotly deprecation-warns the name lookup.

## Correctness fixes (all audit findings)
- **A1 — interaction guard.** Kept the full posterior model (it is the fitted model). Added:
  (a) a **joint-support extrapolation warning** that fires when both prices > 0 and the median
  interaction contribution exceeds 15% of the median total ("estimated from very little joint
  variation — treat combined-lever results as illustrative"); (b) whenever the **marginal tax
  contribution is positive** (it flips at ETS ≈ \$27.7, so it's positive at the default ETS=30),
  an explicit message that the science verdict is **'unproven', not 'harmful'**. The tax caveat
  always shows whenever tax > 0.
- **A2 — percent conversion.** `pct_change_3yr = 100*expm1(eff*3)` used everywhere, including the
  dose-response curve. Default ETS=30/tax=0 now shows **−9.0%** (was −9.4% under the linear bug).
- **A3 — extrapolation thresholds.** `ETS_OBS_MAX = 35.0`, `TAX_OBS_MAX = 169.0`, with `>=`
  boundaries. **Verified from data** (`data/cleaned/final_analysis_data.csv`, year ≤ 2018 dose
  sample): ETS p99 = \$34.5, exactly one point above (\$55.5, Switzerland 2014 — the sparse
  \$35–55 zone); tax max = \$168.8 (Sweden 2008). The €47 EUA recovery is flagged as outside the
  estimation sample. Hardcoded with a comment.
- **A4 — empty state.** At zero prices the hero shows "—" + "Set a price to see the predicted
  impact." — no "P(reduces)=0%".
- **A5 — hygiene.** matplotlib dropped entirely; the npz handle is opened with a `with` block and
  arrays `.copy()`d out (handle closed); upper-bound pins added to both `requirements.txt` files.

### Science-constraint wording
- ETS robust **≈ −7 to −10% per \$30**; carbon tax kept caveated as **unproven** whenever tax > 0.
- No covariate personalization — stated plainly at the picker; the map encodes policy/evidence
  status only, never per-country effect size.
- "Tax & ETS are substitutes" labelled **suggestive, not fact** (Methods page).
- Sector-DiD row uses the corrected wording: *"Within-country sector DiD: −3.4%/\$10 (p=0.03), but
  the 2026-06-11 audit found the original pre-trend test was miscomputed — the full-covariance
  test rejects (p≈0.004) and a pre-existing covered-sector trend can account for the endpoint.
  Supportive, not clean identification."* The old "⭐ clean ID — pre-trends pass" is gone.
- All prices standardized on **US\$**; € equivalents noted only in a caption.

## Verification (headless boot + Playwright)
- Booted headless: `.venv\Scripts\python.exe -m streamlit run dashboard/app.py
  --server.headless true --server.port 8799`. `/_stcore/health` returned **200 (ok)**.
- **Default sanity check:** ETS=30, tax=0 → hero **−9.0%** (matches
  `100*expm1(3*30/10*mean(b_ets))` with mean(b_ets) ≈ −0.01045 → −8.97%). ✓
- **Map renders** with all three status colours (verified screenshot + 163/163 ISO-3 mapped).
- **Slider reactivity (fragment):** ETS 30→35 moved the hero −9.0% → −10.4%; the map did not
  rebuild. ✓
- **A3:** at ETS=\$35 the extrapolation info fires (\$35/\$55 render as literal dollars, no LaTeX
  `$...$` artifact, bold applied). ✓
- **A1:** at ETS=100, tax=40 both the "tax is raising the number → unproven not harmful" warning
  and the "combined-lever result is illustrative" joint-support warning fire. ✓
- **A4:** at ETS=0, tax=0 the hero is "—" with the empty-state text and no "P(reduces)=0%". ✓
- **Evidence page:** 7 cards, corrected sector-DiD wording present ("p≈0.004"), old "clean ID —
  pre-trends pass" absent, event-study image present. ✓
- **Methods page:** identifying-assumption paragraph, common-path caveat, "substitutes →
  suggestive, not fact", "price is the lever" all present. ✓
- Server killed after verification.

Screenshots in `docs/audit_fixes/dashboard_screenshots/`:
`1_engine_default.png`, `1_engine_hero.png`, `2_engine_warnings.png`, `3_evidence.png`,
`4_methods.png`, `5_engine_emptystate.png`.

## Note on the `$` LaTeX gotcha
Streamlit markdown treats paired `$...$` as LaTeX. Any `st.markdown/info/warning/caption` string
containing two dollar amounts (e.g. "\$30 … \$50") would render the middle as math. Fixed by
escaping `\$` in those pure-markdown strings. Dollar signs inside `unsafe_allow_html` HTML spans
are not LaTeX-parsed and were left as-is.
