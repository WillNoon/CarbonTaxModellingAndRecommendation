"""Phase 4b — EUTL installation-level: the 2013 auctioning DiD (gold-standard data, honest result).

Data: EU ETS Data Package (Abrell, Zenodo rec 20509231). We keep a COMPACT installation-year panel
(data/raw/eutl_installation_panel.csv.gz) extracted from compliance.csv + installations.csv; the full
492MB package (incl. 408MB transactions) is NOT committed.

Design: in EU ETS Phase 3 (2013), power/combustion installations lost free allocation (full auctioning)
while energy-intensive industry kept it. DiD: did combustion abate more than industry after 2013, with
installation + year FE (which absorb the aggregate price trend)?

HONEST RESULT: combustion -27% vs industry post-2013 (p<0.001) — but (1) pre-trends noisy (2009-10 crisis),
(2) confounded by the power-sector renewables transition (auctioning was assigned to the sector with the most
NON-ETS decarbonisation). So it's an UPPER BOUND confirming direction, not clean ETS isolation. The genuinely
clean design is an RD on the ~20MW/25kt inclusion threshold (barely-covered vs barely-uncovered installations;
Colmer/Martin/Muuls/Wagner 2024) — the true gold standard and the honest next frontier.

Run: uv run python scripts/eutl_auctioning_did.py
"""
import os
import numpy as np, pandas as pd, pyfixest as pf
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pd.read_csv(os.path.join(ROOT, 'data/raw/eutl_installation_panel.csv.gz'))
d['logv'] = np.log(d['verified']); d['post2013'] = (d['year'] >= 2013).astype(int)
print(f"panel: {len(d)} inst-years, {d.installation_id.nunique()} installations "
      f"({d[d.combustion==1].installation_id.nunique()} combustion / {d[d.combustion==0].installation_id.nunique()} industry)")
m = pf.feols("logv ~ combustion:post2013 | installation_id + year", data=d, vcov={'CRV1': 'registry_name'})
r = m.tidy().loc['combustion:post2013']
print(f"DiD combustion:post2013 = {r['Estimate']:+.4f} (p={r['Pr(>|t|)']:.3f}) => {(np.exp(r['Estimate'])-1)*100:+.1f}% vs industry")
es = pf.feols("logv ~ i(year, combustion, ref=2012) | installation_id + year", data=d, vcov={'CRV1': 'registry_name'})
td = es.tidy(); yrs, bb, lo, hi = [2012], [0.], [0.], [0.]
for y in range(2008, 2023):
    k = [i for i in td.index if f'year::{y}' in i]
    if k:
        rr = td.loc[k[0]]; yrs.append(y); bb.append(rr['Estimate']*100); lo.append(rr['2.5%']*100); hi.append(rr['97.5%']*100)
o = np.argsort(yrs); yrs, bb, lo, hi = (np.array(a)[o] for a in (yrs, bb, lo, hi))
fig, ax = plt.subplots(figsize=(9, 4))
ax.fill_between(yrs, lo, hi, alpha=.15, color='#2ca02c'); ax.plot(yrs, bb, 'o-', color='#2ca02c', ms=4, lw=1.8)
ax.axvline(2013, color='r', ls=':', lw=1.2); ax.axhline(0, color='k', lw=.6)
ax.set_xlabel('year'); ax.set_ylabel('combustion vs industry emissions gap (%, ref 2012)')
ax.set_title('EUTL: power/combustion vs industry around the 2013 auctioning shock\n'
             '(installation + year FE; large effect but pre-trends noisy + power-renewables confound)', fontsize=9.5)
ax.grid(alpha=.25); plt.tight_layout(); plt.savefig(os.path.join(ROOT, 'outputs/eutl_auctioning_eventstudy.png'), dpi=115)
print("saved outputs/eutl_auctioning_eventstudy.png")
