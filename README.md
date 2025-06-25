# Carbon Tax Policy & Emissions Dataset

This repository contains a comprehensive dataset curated to support machine learning models that explore the effectiveness of carbon tax policies on national CO₂ emissions. The dataset brings together energy mix, economic, environmental, and governance indicators from 1990 to present for over 180 countries.

## Dataset Overview

**Main Goal:**  
To enable predictive modeling of whether carbon tax policies are effective at reducing emissions, and to simulate the expected impact of introducing carbon taxes in countries without them.

### Data Sources
- **Carbon tax policy data:** Extracted from OECD, IMF, and World Bank policy databases.
- **CO₂ emissions & energy statistics:** Our World in Data (OWID)
- **Energy mix (renewables, fossil, nuclear):** World Bank & International Energy Agency
- **Additional indicators:** GDP, population, fuel subsidies, governance scores, etc. (in progress)

### Key Features

| Feature                      | Description                                     |
|-----------------------------|-------------------------------------------------|
| `country`, `year`           | Country name and year                          |
| `co2_per_capita`, `co2_per_gdp` | Main emissions metrics                        |
| `tax_price`, `tax_type`, `years_since_tax` | Details on carbon tax implementation |
| `fossil_pct`, `renewable_pct`, `nuclear_pct` | Energy mix breakdown         |
| `co2_per_capita_future_trend` | 5-year emission trend after tax               |
| `energy_per_gdp`, `land_use_change_co2`, etc. | Supporting environmental/economic indicators |

### Data Integrity
- Missing values have been carefully interpolated and validated.
- Countries without nuclear power have `nuclear_pct = 0`.
- Rows where energy share sums slightly differ from 100% are normalized.

---

## Use Cases

- **ML modeling:** Classify whether a country should implement a carbon tax.
- **Time-series forecasting:** Predict emission trends under policy scenarios.
- **Policy evaluation:** Analyze real-world effects of existing tax regimes.

---

## In Progress

- Adding education, governance, fuel subsidy, and climate commitment indicators
- Building a predictive model (classification and regression)
- Dashboard for visual insights (future)
