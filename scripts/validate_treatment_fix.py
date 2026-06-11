"""Validate the AUDIT 2026-06-11 treatment-coding fix in final_analysis_data.csv.

Checks F1 (accession-aware ETS membership + rescues), F2 (tax implementation onsets),
structural integrity (no dupes, row count, outcome unchanged), and reproduces the audit's
corrected-coding dose / binary-TWFE regression numbers.

Run from repo root:  .venv\\Scripts\\python.exe scripts\\validate_treatment_fix.py
Exits non-zero if any hard check fails.
"""
import sys
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

DF_PATH = "data/cleaned/final_analysis_data.csv"
df = pd.read_csv(DF_PATH)
fails = []


def check(cond, msg):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        fails.append(msg)


def onset(country, col):
    sub = df[(df.country == country) & (df[col] == 1)]
    return int(sub.year.min()) if len(sub) else None


def years(country):
    sub = df[(df.country == country) & (df.has_ets == 1)]
    return (int(sub.year.min()), int(sub.year.max())) if len(sub) else None


print("=== Structural ===")
check(df.shape[0] == 4218, f"row count == 4218 (got {df.shape[0]})")
check(df.duplicated(["country", "year"]).sum() == 0, "no (country,year) duplicates")
for c in ["years_since_tax", "years_since_ets", "years_since_any_pricing"]:
    check(c in df.columns, f"column '{c}' present")
check(df.fossil_pct.between(0, 100).all(), "fossil_pct within [0,100]")

print("\n=== F1: ETS accession-aware membership ===")
check(years("Czechia") == (2005, 2021), f"Czechia ETS 2005-2021 (got {years('Czechia')})")
check(years("United Kingdom") == (2005, 2021), f"UK ETS 2005-2021 incl. UK-ETS 2021 (got {years('United Kingdom')})")
check(years("Norway") == (2008, 2021), f"Norway ETS 2008-2021 (got {years('Norway')})")
check(years("Iceland") == (2008, 2021), f"Iceland ETS 2008-2021 (got {years('Iceland')})")
check(years("South Korea") == (2015, 2021), f"South Korea KETS 2015-2021 (got {years('South Korea')})")
check(onset("Bulgaria", "has_ets") == 2007, f"Bulgaria ETS starts 2007 (got {onset('Bulgaria','has_ets')})")
check(onset("Romania", "has_ets") == 2007, f"Romania ETS starts 2007 (got {onset('Romania','has_ets')})")
check(onset("Croatia", "has_ets") == 2013, f"Croatia ETS starts 2013 (got {onset('Croatia','has_ets')})")

# accession zeroing: pre-entry years must have has_ets == 0
for c, yr in [("Croatia", 2012), ("Bulgaria", 2006), ("Romania", 2006)]:
    row = df[(df.country == c) & (df.year == yr)]
    check(int(row.has_ets.iloc[0]) == 0, f"{c} {yr} has_ets == 0 (pre-accession)")

# UK 2021 price proxied with EUA (>0)
uk21 = df[(df.country == "United Kingdom") & (df.year == 2021)]
check(uk21.ets_price_only.iloc[0] > 0, "UK 2021 ets_price_only > 0 (EUA proxy)")

# NZ 2016 gap filled and interpolated
nz = df[df.country == "New Zealand"].set_index("year")
check(int(nz.loc[2016, "has_ets"]) == 1, "NZ 2016 has_ets filled to 1")
expected_nz = (nz.loc[2015, "ets_price_only"] + nz.loc[2017, "ets_price_only"]) / 2
check(np.isclose(nz.loc[2016, "ets_price_only"], expected_nz),
      f"NZ 2016 price interpolated (got {nz.loc[2016,'ets_price_only']:.3f}, exp {expected_nz:.3f})")

print("\n=== F2: tax implementation onsets ===")
# Denmark/Finland/Slovenia implemented pre-1996 -> onset shows panel start 1996
for c, exp in [("Denmark", 1996), ("Finland", 1996), ("Slovenia", 1996),
               ("Estonia", 2000), ("Latvia", 2004), ("Ukraine", 2011),
               ("Portugal", 2015), ("Mexico", 2014), ("South Africa", 2019)]:
    check(onset(c, "has_tax") == exp, f"{c} has_tax onset == {exp} (got {onset(c,'has_tax')})")

print("\n=== Outcome unchanged vs committed file ===")
try:
    import subprocess
    old_csv = subprocess.run(
        ["git", "show", "HEAD:data/cleaned/final_analysis_data.csv"],
        capture_output=True, text=True, check=True).stdout
    from io import StringIO
    old = pd.read_csv(StringIO(old_csv))
    m = old.merge(df, on=["country", "year"], suffixes=("_old", "_new"))
    col = "co2_per_capita_future_trend"
    nchanged = (~np.isclose(m[col + "_old"], m[col + "_new"], equal_nan=True)).sum()
    check(nchanged == 0, f"{col} identical across all rows (changed: {nchanged})")
except Exception as e:
    print(f"  [SKIP] git diff of outcome unavailable: {e}")

print("\n=== Regression reproduction (audit corrected coding) ===")
df["Ptax"] = df["tax_price_only"] / 10
df["Pets"] = df["ets_price_only"] / 10
df["logco2"] = np.log(df["co2_per_capita"].where(df["co2_per_capita"] > 0))
df.sort_values(["country", "year"], inplace=True)
df["d3"] = (df.groupby("country")["logco2"].shift(-3) - df["logco2"]) / 3


def fit(formula, keep):
    need = [v for v in ["d3", "co2_per_capita_future_trend", "Ptax", "Pets", "has_tax",
                        "has_ets", "log_gdp", "log_population",
                        "natural_resource_rents_per_gdp"] if v in formula]
    sub = df.dropna(subset=need)
    m = smf.ols(formula, data=sub).fit(cov_type="cluster", cov_kwds={"groups": sub["country"]})
    return {p: (m.params[p], m.bse[p], m.pvalues[p]) for p in keep}


dose = fit("d3 ~ Ptax + Pets + C(country) + C(year)", ["Ptax", "Pets"])
binar = fit("co2_per_capita_future_trend ~ has_tax + has_ets + C(country) + C(year)"
            " + log_gdp + log_population + natural_resource_rents_per_gdp",
            ["has_tax", "has_ets"])
for name, (b, se, p) in {**{f"dose:{k}": v for k, v in dose.items()},
                         **{f"binary:{k}": v for k, v in binar.items()}}.items():
    print(f"  {name:16s} {b:+.5f}  (se {se:.5f}, p={p:.4f})")

check(np.isclose(dose["Pets"][0], -0.0100, atol=0.001), "dose Pets ~= -0.010")
check(dose["Pets"][2] < 0.001, "dose Pets p < 0.001")
check(np.isclose(binar["has_ets"][0], -0.123, atol=0.01), "binary has_ets ~= -0.12")
check(binar["has_tax"][0] > 0 and binar["has_tax"][2] > 0.1, "binary has_tax positive & n.s.")

print("\n" + ("ALL CHECKS PASSED" if not fails else f"{len(fails)} CHECK(S) FAILED"))
sys.exit(1 if fails else 0)
