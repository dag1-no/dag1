---
title: Norsk lønn i USA
---
La oss gjøre et tankeeksperiment. Hva om du tar en norsk gjennomsnittslønn, veksler den til dollar og så kjøper varer og tjenester i USA. Hvor mye får du da for pengene dine?

Vi kan se at siden 2013 har det vært en vesentlig reduksjon i denne indikasjonen på verdien av arbeid utført i Norge. Det som er helt sikkert er at det for de fleste nordmenn har blitt betydelig dyrere å dra på ferie til USA.

Linjen US Wages Adjusted viser utviklingen av en amerikansk gjennomsnittslønn i samme periode.

```sql joined_us_nok_wages
with us_cpi_2024 as (
    select value as cpi_2024
    from us_cpi
    where cast(date as date) = '2024-12-31'
)
select
    coalesce(cast(mean_wages_no_yearly.date as date), cast(us_mean_wages.date as date), cast(mean_wages_no_monthly_annualized.date as date)) as dato,
    case
        when mean_wages_no_yearly.value is null or nok_usd.value is null or us_cpi.value is null then null
        else ((mean_wages_no_yearly.value / nok_usd.value)) / (us_cpi.value / (select value from us_cpi where date = '2024-12-31'))
    end as norwegian_wages_usd_adjusted1,
     case
        when mean_wages_no_monthly_annualized.value is null or nok_usd.value is null or us_cpi.value is null then null
        else ((mean_wages_no_monthly_annualized.value / nok_usd.value)) / (us_cpi.value / (select value from us_cpi where date = '2024-12-31'))
    end as norwegian_wages_usd_adjusted2,
    (us_mean_wages.value / us_cpi.value) * (select cpi_2024 from us_cpi_2024) as us_wages_adjusted,
from mean_wages_no_yearly
full outer join nok_usd
    on cast(mean_wages_no_yearly.date as date) = cast(nok_usd.date as date)
full outer join us_cpi
    on cast(mean_wages_no_yearly.date as date) = cast(us_cpi.date as date)
full outer join us_mean_wages
    on cast(mean_wages_no_yearly.date as date) = cast(us_mean_wages.date as date)
    or cast(us_mean_wages.date as date) = cast(us_cpi.date as date)
full outer join mean_wages_no_monthly_annualized
    on cast(mean_wages_no_yearly.date as date) = cast(mean_wages_no_monthly_annualized.date as date)
where cast(coalesce(mean_wages_no_yearly.date, us_mean_wages.date, mean_wages_no_monthly_annualized.date) as date) >= '2006-01-01'
order by dato
```


<LineChart
  title="Gjennomsnittslønn i USD og justert for inflasjon til 2024-dollar"
  data={joined_us_nok_wages}
  x="dato"
  y1="norwegian_wages_usd_adjusted1"
  y2="norwegian_wages_usd_adjusted2"
  y3="us_wages_adjusted"
  chartAreaHeight={500}
/>



```sql wages_mean_usd_cpi_adjusted

select cast(mean_wages_no_yearly.date as date) as dato,
    case
        when mean_wages_no_yearly.value is null or nok_usd.value is null or us_cpi.value is null
            or (select value from us_cpi where date = '2024-12-31') is null then null
        else ((mean_wages_no_yearly.value / nok_usd.value)) /
             ((us_cpi.value / (select value from us_cpi where date = '2024-12-31')))
    end as lønn_usd_adjusted
from mean_wages_no_yearly
join nok_usd
    on cast(mean_wages_no_yearly.date as date) = cast(nok_usd.date as date)
join us_cpi
    on cast(mean_wages_no_yearly.date as date) = cast(us_cpi.date as date)
order by dato

```





<LineChart
title="Norsk gjennomsnittslønn vekslet til dollar og inflasjonsjustert til 2024-dollar"
  data={wages_mean_usd_cpi_adjusted}
  x=dato
  y=lønn_usd_adjusted
  chartAreaHeight={500}
/>

Her ser vi hvordan denne utviklingen har vært historisk. En norsk brutto norsk gjennomsnittslønn brukt til å kjøpe varer og tjenester i USA hadde en voldsom økning frem til 1978. Deretter en dip og så stagnering frem til 2002, fulgt av en kraftig vekst frem til 2011.

Vi kan sammenligne dette med utvikling i [reallønn](../reallønn) Der reallønnen viser hva en gjennomsnittlig lønn kan kjøpe i Norge, kan denne grafen være en indikasjon på hvordan andre land verdsetter norsk arbeid.



*(Vi sammenligner bruttolønn, det vil si at vi ikke tar høyde for skatt, som i realiteten gjør at en person med gjennomsnittlig norsk lønn ville sitte igjen med betydelig mindre enn en gjennomsnittlig lønnsmottaker i USA. For å gjøre tallene sammenlignbare oppgir vi tallene i inflasjonsjusterte 2024-dollar.)*
