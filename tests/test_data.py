"""Tests for the data layer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pytest

from svod import load_panel, qc_report

if TYPE_CHECKING:
    from pathlib import Path


def test_load_panel_schema(synthetic_xlsx: Path) -> None:
    """Panel has tidy columns and one row per actor-quarter."""
    panel = load_panel(synthetic_xlsx)
    assert list(panel.columns) == ["actor", "quarter", "subscribers"]
    assert len(panel) == 6 * 8 + 3
    assert panel["quarter"].str.fullmatch(r"20\d\dQ[1-4]").all()
    assert panel["subscribers"].dtype == "int64"
    assert panel.equals(panel.sort_values(["actor", "quarter"], ignore_index=True))


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
    assert all(type(v) is int for v in report.partial_actors.values())


def test_load_panel_rejects_null_values(synthetic_xlsx: Path, tmp_path: Path) -> None:
    """Null subscriber values fail fast with a clear error."""
    raw = pd.read_excel(synthetic_xlsx, sheet_name="Data")
    raw.loc[0, "Kpi_value"] = None
    path = tmp_path / "with_nulls.xlsx"
    raw.to_excel(path, sheet_name="Data", index=False)
    with pytest.raises(ValueError, match="missing Kpi_value"):
        load_panel(path)
