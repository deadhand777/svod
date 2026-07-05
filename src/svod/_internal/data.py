from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from pathlib import Path

_EXPECTED_COLUMNS = ("Actor_label", "Country_label", "Kpi_label_corporate", "Fact_date", "Kpi_value")


@dataclasses.dataclass(frozen=True)
class QCReport:
    """Data-quality summary of a subscriber panel.

    Attributes:
        n_rows: Number of rows in the panel.
        n_actors: Number of distinct actors.
        duplicates: Number of duplicated (actor, quarter) rows.
        nulls: Number of missing subscriber values.
        quarters: Sorted list of quarters present.
        full_coverage_actors: Actors observed in every quarter.
        partial_actors: Actors with incomplete coverage, mapped to their observation count.
    """

    n_rows: int
    n_actors: int
    duplicates: int
    nulls: int
    quarters: list[str]
    full_coverage_actors: list[str]
    partial_actors: dict[str, int]


def load_panel(xlsx_path: str | Path) -> pd.DataFrame:
    """Load a Dataxis SVOD export into a tidy quarterly panel.

    Parameters:
        xlsx_path: Path to the xlsx file (expects a `Data` sheet with the Dataxis schema).

    Returns:
        DataFrame with columns `actor`, `quarter` (like `"2021Q1"`) and `subscribers`,
        sorted by actor and quarter.

    Raises:
        ValueError: If expected columns are missing from the `Data` sheet, or if
            the `Kpi_value` column contains null values.
    """
    raw = pd.read_excel(xlsx_path, sheet_name="Data")
    missing = set(_EXPECTED_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing expected columns in Data sheet: {sorted(missing)}")
    n_null = int(raw["Kpi_value"].isna().sum())
    if n_null:
        raise ValueError(f"Data sheet contains {n_null} rows with missing Kpi_value; clean the export first.")
    dates = pd.to_datetime(raw["Fact_date"])
    panel = pd.DataFrame(
        {
            "actor": raw["Actor_label"].astype(str),
            "quarter": dates.dt.year.astype(str) + "Q" + dates.dt.quarter.astype(str),
            "subscribers": raw["Kpi_value"].astype("int64"),
        },
    )
    return panel.sort_values(["actor", "quarter"], ignore_index=True)


def qc_report(panel: pd.DataFrame) -> QCReport:
    """Compute a data-quality report for a subscriber panel.

    Parameters:
        panel: Tidy panel as returned by `load_panel`.

    Returns:
        The quality report.
    """
    quarters = sorted(panel["quarter"].unique())
    counts = panel.groupby("actor").size()
    full = counts[counts == len(quarters)]
    partial = counts[counts < len(quarters)]
    return QCReport(
        n_rows=len(panel),
        n_actors=panel["actor"].nunique(),
        duplicates=int(panel.duplicated(["actor", "quarter"]).sum()),
        nulls=int(panel["subscribers"].isna().sum()),
        quarters=list(quarters),
        full_coverage_actors=sorted(full.index),
        partial_actors={str(actor): int(count) for actor, count in partial.sort_index().items()},
    )
