"""Tests for the analysis module."""

from __future__ import annotations

import pandas as pd
import pytest

from svod import concentration, market_summary


def test_market_summary_totals_and_growth(synthetic_panel: pd.DataFrame) -> None:
    """Totals aggregate all actors; growth columns behave."""
    summary = market_summary(synthetic_panel)
    assert list(summary["quarter"]) == sorted(synthetic_panel["quarter"].unique())
    q1 = summary.loc[summary["quarter"] == "2021Q1", "total_subscribers"].item()
    assert q1 == 60_000_000 + 40_000_000 + 5_000_000 + 3_000_000 + 200_000 + 150_000
    assert summary.loc[summary["quarter"] == "2021Q1", "active_actors"].item() == 6
    assert summary.loc[summary["quarter"] == "2022Q2", "active_actors"].item() == 7
    assert pd.isna(summary["qoq_growth"].iloc[0])
    assert summary["yoy_growth"].iloc[4] == pytest.approx(
        summary["total_subscribers"].iloc[4] / summary["total_subscribers"].iloc[0] - 1
    )


def test_concentration_known_values() -> None:
    """HHI/CR4 verified against hand-computed values."""
    panel = pd.DataFrame(
        {
            "actor": ["A", "B", "C", "D"],
            "quarter": ["2021Q1"] * 4,
            "subscribers": [50, 30, 15, 5],
        }
    )
    conc = concentration(panel)
    # shares: .5, .3, .15, .05 -> HHI = (0.25 + 0.09 + 0.0225 + 0.0025) * 10000 = 3650
    assert conc["hhi"].item() == pytest.approx(3650.0)
    assert conc["cr4"].item() == pytest.approx(1.0)
    assert conc["cr8"].item() == pytest.approx(1.0)
