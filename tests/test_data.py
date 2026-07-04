"""Tests for the data layer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from svod import load_panel, qc_report

if TYPE_CHECKING:
    from pathlib import Path

    import pandas as pd


def test_load_panel_schema(synthetic_xlsx: Path) -> None:
    """Panel has tidy columns and one row per actor-quarter."""
    panel = load_panel(synthetic_xlsx)
    assert list(panel.columns) == ["actor", "quarter", "subscribers"]
    assert len(panel) == 6 * 8 + 3
    assert panel["quarter"].str.fullmatch(r"20\d\dQ[1-4]").all()
    assert panel["subscribers"].dtype == "int64"


def test_qc_report_coverage(synthetic_panel: pd.DataFrame) -> None:
    """QC report flags full vs partial coverage and clean data."""
    report = qc_report(synthetic_panel)
    assert report.n_rows == 51
    assert report.n_actors == 7
    assert report.duplicates == 0
    assert report.nulls == 0
    assert report.quarters == ["2021Q1", "2021Q2", "2021Q3", "2021Q4", "2022Q1", "2022Q2", "2022Q3", "2022Q4"]
    assert "Giant A" in report.full_coverage_actors
    assert report.partial_actors == {"Partial": 3}
