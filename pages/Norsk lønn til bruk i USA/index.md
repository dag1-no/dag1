---
title: Norsk lønn i USA
---

```sql nominal_wages_usd_cpi_adjusted

select cast(nominal_wages.date as date) as dato,
    case
        when nominal_wages.value is null or nok_usd.value is null or us_cpi.value is null
            or (select value from us_cpi where date = '2024-12-31') is null then null
        else ((nominal_wages.value / nok_usd.value) * 1000) /
             ((us_cpi.value / (select value from us_cpi where date = '2024-12-31')) * 100 / 100)
    end as lønn_usd_adjusted
from nominal_wages
join nok_usd
    on cast(nominal_wages.date as date) = cast(nok_usd.date as date)
join us_cpi
    on cast(nominal_wages.date as date) = cast(us_cpi.date as date)

```

<LineChart
title=""
  data={nominal_wages_usd_cpi_adjusted}
  x=dato
  y=lønn_usd_adjusted
  chartAreaHeight={500}
/>
