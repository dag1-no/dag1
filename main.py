#!/usr/bin/env python
from calendar import monthrange
from csv import DictWriter
from datetime import date
from pathlib import Path

from httpx import get, post, Response
from polars import read_csv
import polars as pl


def main() -> None:
    get_absence_from_work_due_to_illness()
    get_nok_eur()
    get_nok_usd()
    get_cpi()
    get_us_cpi()
    get_mean_wages_no_yearly()
    get_mean_wages_no_monthly_annualized()
    get_real_wages()
    get_government_expenses_from_ssb()
    get_petroleum_fund_data()
    get_us_mean_wages()


def get_absence_from_work_due_to_illness() -> None:
    csv_url = "https://sdmx.oecd.org/public/rest/data/OECD.ELS.HD,DSD_HEALTH_STAT@DF_AWDI,1.0/DNK+SWE+NOR.A.CAWI..........?startPeriod=2007&format=csvfile"
    response = get(csv_url)
    dataframe = read_csv(response.content).sort(
        ["TIME_PERIOD", "REF_AREA"], descending=[True, False]
    )
    observations = []
    for row in dataframe.to_dicts():
        year = row["TIME_PERIOD"]
        _date = date(year, 12, 31)
        value = row["OBS_VALUE"]
        country = row["REF_AREA"]
        if country == "NOR":
            country = "Norge"
        elif country == "SWE":
            country = "Sverige"
        elif country == "DNK":
            country = "Danmark"
        observations.append(
            {
                "date": _date,
                "value": value,
                "country": country,
            }
        )
    delete_and_write_csv(observations, Path("sources/oecd/absence_illness.csv"))


def get_nok_eur() -> None:
    response = get(
        "https://data.norges-bank.no/api/data/EXR/A.EUR.NOK.SP?format=sdmx-json&lastNObservations=30&locale=en"
    )
    json = response.json()
    labels = json["data"]["structure"]["dimensions"]["observation"][0]["values"]
    values = json["data"]["dataSets"][0]["series"]["0:0:0:0"]["observations"]
    observations = []
    for index, label in enumerate(labels):
        value = values[str(index)][0]  # Get value or None if missing
        _date = label["end"].split("T")[0]
        observations.append(
            {
                "date": _date,
                "value": float(value),
            }
        )
    delete_and_write_csv(observations, Path("sources/norges_bank/nok_eur.csv"))


def get_nok_usd() -> None:
    response = get(
        "https://data.norges-bank.no/api/data/EXR/A.USD.NOK.SP?format=sdmx-json&startPeriod=1970-01-01&endPeriod=2025-03-08&locale=no"
    )
    json = response.json()
    labels = json["data"]["structure"]["dimensions"]["observation"][0]["values"]
    values = json["data"]["dataSets"][0]["series"]["0:0:0:0"]["observations"]
    observations = []
    for index, label in enumerate(labels):
        value = values[str(index)][0]  # Get value or None if missing
        _date = label["end"].split("T")[0]
        observations.append(
            {
                "date": _date,
                "value": float(value),
            }
        )
    delete_and_write_csv(observations, Path("sources/norges_bank/nok_usd.csv"))


def get_cpi() -> None:
    response = _post(
        "https://data.ssb.no/api/v0/no/table/03013/",
        [
            {
                "code": "Konsumgrp",
                "selection": {
                    "filter": "vs:CoiCop2016niva1",
                    "values": ["TOTAL"],
                },
            },
            {
                "code": "ContentsCode",
                "selection": {
                    "filter": "item",
                    "values": ["Tolvmanedersendring"],
                },
            },
        ],
    )
    observations = simplify_jsonstat2(response)
    delete_and_write_csv(observations, Path("sources/ssb/cpi.csv"))


def get_mean_wages_no_yearly() -> None:
    # nominal mean yearly wages in Norway from SSB yearly time series from 1970 to 2021
    response = _post(
        "https://data.ssb.no/api/v0/no/table/09786/",
        [
            {
                "code": "ContentsCode",
                "selection": {
                    "filter": "item",
                    "values": ["Arslonn"],
                },
            }
        ],
    )
    observations = simplify_jsonstat2(response)
    for observation in observations:
        if observation["value"] is not None:
            observation["value"] *= 1_000
    delete_and_write_csv(observations, Path("sources/ssb/mean_wages_no_yearly.csv"))


def get_mean_wages_no_monthly_annualized() -> None:
    # Nominal average monthly wages in Norway from SSB from 2015 to present
    response = _post(
        "https://data.ssb.no/api/v0/no/table/11419/",
        [
            {
                "code": "MaaleMetode",
                "selection": {
                    "filter": "item",
                    "values": ["02"],
                },
            },
            {
                "code": "NACE2007",
                "selection": {"filter": "vs:NACELonnalle02", "values": []},
            },
            {
                "code": "ContentsCode",
                "selection": {"filter": "item", "values": ["Manedslonn"]},
            },
        ],
    )
    observations = simplify_jsonstat2(response)
    for observation in observations:
        observation["value"] *= 12
    delete_and_write_csv(
        observations, Path("sources/ssb/mean_wages_no_monthly_annualized.csv")
    )


def get_real_wages() -> None:
    response = _post(
        "https://data.ssb.no/api/v0/no/table/09786/",
        [
            {
                "code": "ContentsCode",
                "selection": {
                    "filter": "item",
                    "values": ["RealArslonn"],
                },
            }
        ],
    )
    observations = simplify_jsonstat2(response)
    for observation in observations:
        observation["value"] *= 1_000
    delete_and_write_csv(observations, Path("sources/ssb/real_wages.csv"))


def get_petroleum_fund_data() -> None:
    url = "https://www.nbim.no/en/investments/the-funds-value/"
    response = get(url)
    text = response.text
    observations = parse_petroleum_fund_data(text)
    delete_and_write_csv(observations, Path("sources/nbim/fund_value.csv"))


def get_government_expenses_from_ssb() -> None:
    response = _post(
        "https://data.ssb.no/api/v0/no/table/10725/",
        [{"code": "Formaal", "selection": {"filter": "item", "values": ["COF0"]}}],
    )
    observations = simplify_jsonstat2(response)
    for observation in observations:
        observation["value"] = observation["value"] / 1000
    delete_and_write_csv(observations, Path("sources/ssb/government_expenses.csv"))


def get_us_mean_wages() -> None:
    """
    Fetch US mean hourly earnings for all employees from BLS API (2006–2024), convert to yearly averages,
    and save as CSV. Uses CEU0500000003 (nominal average hourly earnings, monthly, all private employees).
    Splits requests to handle BLS 10-year limit without a key.
    """
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    date_ranges = [("2006", "2015"), ("2016", "2024")]  # Split into two chunks
    all_data = []

    for start_year, end_year in date_ranges:
        payload = {
            "seriesid": ["CEU0500000003"],
            "startyear": start_year,
            "endyear": end_year,
            "registrationkey": None,  # No key; split avoids limit
        }
        response = post(url, json=payload)
        data = response.json()

        if "Results" not in data or not data["Results"]["series"]:
            raise ValueError(
                f"No data returned from BLS API for CEU0500000003 ({start_year}–{end_year})."
            )

        all_data.extend(data["Results"]["series"][0]["data"])

    # Parse into Polars DataFrame
    df = pl.DataFrame(
        [
            {
                "date": f"{obs['year']}-{obs['period'][1:]}-01",
                "hourly_value": float(obs["value"]),
            }
            for obs in all_data
        ]
    )

    # Convert to yearly wages and aggregate
    df = df.with_columns(
        [
            pl.col("date").str.strptime(pl.Date, "%Y-%m-%d").alias("date_obj"),
            (pl.col("hourly_value") * 2080).alias("yearly_value"),  # 40 hrs/wk * 52 wks
        ]
    ).with_columns([pl.col("date_obj").dt.year().alias("year")])

    yearly_df = df.group_by("year").agg([pl.col("yearly_value").mean().alias("value")])

    # Format observations
    observations = [
        {"date": f"{row['year']}-12-31", "value": row["value"]}
        for row in yearly_df.sort("year").to_dicts()
    ]

    # Save to CSV
    delete_and_write_csv(observations, Path("sources/us_bls/us_mean_wages.csv"))


def get_us_cpi() -> None:
    """
    Fetch US CPI data from FRED (1970–2024), aggregate to yearly averages, and save as CSV.
    Uses CPIAUCSL (seasonally adjusted) series.
    """
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL&cosd=1970-01-01&coed=2024-12-31"
    response = _get(url)

    # Parse CSV with Polars
    df = read_csv(response.content)

    # Ensure expected columns are present
    if "observation_date" not in df.columns or "CPIAUCSL" not in df.columns:
        print("Column names in CSV:", df.columns)
        raise KeyError(
            "Expected columns 'observation_date' and 'CPIAUCSL' not found in FRED CSV data."
        )

    # Convert observation_date to datetime and extract year
    df = df.with_columns(
        [
            pl.col("observation_date")
            .str.strptime(pl.Date, "%Y-%m-%d")
            .alias("date_obj"),
            pl.col("CPIAUCSL").cast(pl.Float64).alias("value"),
        ]
    ).with_columns([pl.col("date_obj").dt.year().alias("year")])

    # Group by year and calculate mean CPI
    yearly_df = df.group_by("year").agg([pl.col("value").mean().alias("value")])

    # Create year-end date strings (e.g., "1970-12-31")
    observations = [
        {"date": f"{row['year']}-12-31", "value": row["value"]}
        for row in yearly_df.sort("year").to_dicts()
    ]

    # Save to CSV
    delete_and_write_csv(observations, Path("sources/us_fred/us_cpi.csv"))


def parse_petroleum_fund_data(text: str) -> list[dict]:
    line: str | None = None
    for _line in text.splitlines():
        if _line.startswith("data: [[Date.UTC(1998,11, 31),172]"):
            line = _line
            break
    assert isinstance(line, str)
    line = line[8:]
    line = line[:-2]
    rows = line.split("],[")
    observations: list[dict] = []
    for row in rows:
        cells = row.split("),")
        year = cells[0][9:13]
        year = int(year)
        value = int(cells[1])
        observations.append({"date": date(year, 12, 31), "value": value})
    return observations


def _get(url: str) -> Response:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    response = get(url, headers=headers)
    response.raise_for_status()
    return response


def _post(url: str, query: list[dict]) -> Response:
    response = post(
        url,
        json={
            "query": query,
            "response": {"format": "json-stat2"},
        },
    )
    response.raise_for_status()
    return response


def simplify_jsonstat2(response: Response) -> list[dict]:
    json = response.json()
    time_periods = json["dimension"]["Tid"]["category"]["index"]
    values = json["value"]
    observations: list[dict] = []
    for time_period, index in time_periods.items():
        observation = {}
        try:
            observation["date"] = date(int(time_period), 12, 31)
        except ValueError:
            year, month = time_period.split("M")
            year = int(year)
            month = int(month)
            last_day = monthrange(year, month)[1]
            observation["date"] = date(year, month, last_day)
        observation["value"] = values[index]
        observations.append(observation)
    return observations


def delete_and_write_csv(observations: list[dict], path: Path) -> None:
    delete_file_if_exists(path)
    with path.open(mode="w", newline="", encoding="utf-8") as file:
        writer = DictWriter(
            file,  # type: ignore
            fieldnames=observations[0].keys(),
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(observations)


def delete_file_if_exists(path) -> None:
    path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
