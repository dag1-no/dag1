#!/usr/bin/env python
from csv import DictWriter
from datetime import date
from pathlib import Path

from httpx import post, Response


def main() -> None:
    get_government_expenses_from_ssb()


def get_government_expenses_from_ssb() -> None:
    response = post(
        "https://data.ssb.no/api/v0/no/table/10725/",
        json={
            "query": [
                {"code": "Formaal", "selection": {"filter": "item", "values": ["COF0"]}}
            ],
            "response": {"format": "json-stat2"},
        },
    )
    response.raise_for_status()
    observations = simplify_jsonstat2(response)
    write_csv(observations, Path("sources/ssb/government_expenses.csv"))


def simplify_jsonstat2(response: Response) -> list[dict]:
    json = response.json()
    years = json["dimension"]["Tid"]["category"]["index"]
    values = json["value"]
    observations: list[dict] = []
    for year, index in years.items():
        observations.append({"date": date(int(year), 12, 31), "value": values[index]})
    return observations


def write_csv(observations: list[dict], path: Path) -> None:
    delete_file_if_exists(path)
    with path.open(mode="w", newline="", encoding="utf-8") as file:
        writer = DictWriter(file, fieldnames=observations[0].keys(), delimiter=";")
        writer.writeheader()
        writer.writerows(observations)


def delete_file_if_exists(path) -> None:
    path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
