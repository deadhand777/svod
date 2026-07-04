"""Configuration for the pytest test suite."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pytest

if TYPE_CHECKING:
    from pathlib import Path

_QUARTER_ENDS = [
    "2021-03-31", "2021-06-30", "2021-09-30", "2021-12-31",
    "2022-03-31", "2022-06-30", "2022-09-30", "2022-12-31",
]

# Actors chosen so cluster structure is unambiguous:
# giants (huge, decelerating), challengers (mid, accelerating), niche (small, flat).
_SYNTHETIC_SUBS = {
    "Giant A": [60_000_000, 61_000_000, 62_000_000, 63_000_000, 62_500_000, 62_000_000, 61_500_000, 61_000_000],
    "Giant B": [40_000_000, 41_000_000, 42_000_000, 43_000_000, 43_500_000, 44_000_000, 44_500_000, 45_000_000],
    "Challenger A": [5_000_000, 6_000_000, 7_500_000, 9_000_000, 11_000_000, 13_500_000, 16_000_000, 19_000_000],
    "Challenger B": [3_000_000, 3_600_000, 4_400_000, 5_400_000, 6_600_000, 8_000_000, 9_700_000, 11_500_000],
    "Niche A": [200_000, 201_000, 202_000, 203_000, 203_500, 204_000, 204_500, 205_000],
    "Niche B": [150_000, 149_000, 148_000, 147_000, 146_000, 145_000, 144_000, 143_000],
}


@pytest.fixture
def synthetic_panel() -> pd.DataFrame:
    """Tidy quarterly panel with 6 full-coverage actors and 1 partial actor.

    Returns:
        The synthetic panel.
    """
    rows = [
        {"actor": actor, "quarter": f"{pd.Timestamp(date).year}Q{pd.Timestamp(date).quarter}", "subscribers": subs}
        for actor, series in _SYNTHETIC_SUBS.items()
        for date, subs in zip(_QUARTER_ENDS, series)
    ]
    rows += [
        {"actor": "Partial", "quarter": q, "subscribers": s}
        for q, s in [("2022Q2", 10_000), ("2022Q3", 20_000), ("2022Q4", 40_000)]
    ]
    return pd.DataFrame(rows).sort_values(["actor", "quarter"], ignore_index=True)


@pytest.fixture
def synthetic_xlsx(tmp_path: Path, synthetic_panel: pd.DataFrame) -> Path:
    """Raw-schema xlsx file mimicking the Dataxis export.

    Parameters:
        tmp_path: Pytest temporary directory.
        synthetic_panel: The synthetic panel fixture.

    Returns:
        Path to the written xlsx file.
    """
    quarter_to_date = {f"{pd.Timestamp(d).year}Q{pd.Timestamp(d).quarter}": d for d in _QUARTER_ENDS}
    raw = pd.DataFrame(
        {
            "Actor_label": synthetic_panel["actor"],
            "Country_label": "USA",
            "Kpi_label_corporate": "SVOD subscribers",
            "Fact_date": pd.to_datetime(synthetic_panel["quarter"].map(quarter_to_date)),
            "Kpi_value": synthetic_panel["subscribers"],
        }
    )
    raw = raw.sample(frac=1, random_state=0).reset_index(drop=True)
    path = tmp_path / "synthetic.xlsx"
    raw.to_excel(path, sheet_name="Data", index=False)
    return path
