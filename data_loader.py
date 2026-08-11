from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

from constants import FACTOR_ELEC, FACTOR_GAS, FACTOR_WATER, TWO_BED_HOME_MONTHLY_KWH

DEFAULT_DATA_PATH = Path(__file__).resolve().parent / "campus_data.json"
MAIN_VIEW_ID = 157


class InvalidCampusDataError(ValueError):
    pass


@dataclass(frozen=True)
class MonthlyRecord:
    date: datetime
    month_label: str
    electricity_kwh: float
    gas_kwh: float
    water_m3: float
    homes_equivalent: float
    carbon_tonnes: float


def _carbon_tonnes(electricity_kwh: float, gas_kwh: float, water_m3: float) -> float:
    elec_c = electricity_kwh * FACTOR_ELEC
    gas_c = gas_kwh * FACTOR_GAS
    water_c = water_m3 * FACTOR_WATER
    return (elec_c + gas_c + water_c) / 1000


def load_monthly_records(path: Path | str = DEFAULT_DATA_PATH) -> list[MonthlyRecord]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if "views" not in raw:
        raise InvalidCampusDataError(
            f"'{path.name}' doesn't look like a real Siemens export (no 'views' key). "
            "This usually means the sender.py/catcher.py demo pipeline overwrote it with "
            "dummy data — point data_loader at campus_data.json instead."
        )

    main_view = next((v for v in raw["views"] if v.get("viewId") == MAIN_VIEW_ID), None)
    if main_view is None:
        raise InvalidCampusDataError(f"No view with viewId={MAIN_VIEW_ID} found in '{path.name}'.")

    dates, _energy_total, gas_kwh_values, electricity_kwh_values, water_m3_values = main_view["data"]

    records = []
    for date_str, gas_kwh, electricity_kwh, water_m3 in zip(
        dates, gas_kwh_values, electricity_kwh_values, water_m3_values
    ):
        date = datetime.strptime(date_str, "%m/%d/%Y %I:%M:%S %p")
        records.append(
            MonthlyRecord(
                date=date,
                month_label=date.strftime("%b %Y"),
                electricity_kwh=electricity_kwh,
                gas_kwh=gas_kwh,
                water_m3=water_m3,
                homes_equivalent=electricity_kwh / TWO_BED_HOME_MONTHLY_KWH,
                carbon_tonnes=_carbon_tonnes(electricity_kwh, gas_kwh, water_m3),
            )
        )
    return records


def compute_ranges(records: list[MonthlyRecord]) -> dict[str, tuple[float, float]]:
    """Min/max per metric across the dataset, used to scale gauges/meters to this
    campus's own range rather than an arbitrary absolute scale."""
    return {
        "electricity_kwh": (
            min(r.electricity_kwh for r in records),
            max(r.electricity_kwh for r in records),
        ),
        "gas_kwh": (min(r.gas_kwh for r in records), max(r.gas_kwh for r in records)),
        "water_m3": (min(r.water_m3 for r in records), max(r.water_m3 for r in records)),
        "carbon_tonnes": (
            min(r.carbon_tonnes for r in records),
            max(r.carbon_tonnes for r in records),
        ),
    }


if __name__ == "__main__":
    for record in load_monthly_records():
        print(
            f"{record.month_label}: {record.electricity_kwh:>10.1f} kWh elec, "
            f"{record.carbon_tonnes:>6.2f}t CO2e, ~{record.homes_equivalent:>6.0f} homes"
        )
