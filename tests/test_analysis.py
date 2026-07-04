"""Tests for the analysis module."""

from __future__ import annotations

import pandas as pd
import pytest

from svod import actor_features, cluster_actors, concentration, market_summary


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


def test_actor_features_full_coverage_only(synthetic_panel: pd.DataFrame) -> None:
    """Partial actors excluded; feature math verified for one actor."""
    features = actor_features(synthetic_panel)
    assert "Partial" not in features.index
    assert len(features) == 6
    challenger = features.loc["Challenger A"]
    assert challenger["growth_2021"] == pytest.approx(9_000_000 / 5_000_000 - 1)
    # raw 2022 growth is 19m/9m - 1 ~ 1.11, inside the [-1, 2] winsor bounds
    assert challenger["growth_2022"] == pytest.approx(19_000_000 / 9_000_000 - 1)
    assert challenger["deceleration"] == pytest.approx(challenger["growth_2022"] - challenger["growth_2021"])


def test_cluster_actors_separates_regimes(synthetic_panel: pd.DataFrame) -> None:
    """Challengers land in one cluster, distinct from niche actors."""
    features = actor_features(synthetic_panel)
    result = cluster_actors(features)
    assert 2 <= result.k <= 6
    assert -1.0 <= result.silhouette <= 1.0
    assert set(result.labels.index) == set(features.index)
    assert result.labels["Challenger A"] == result.labels["Challenger B"]
    assert result.labels["Challenger A"] != result.labels["Niche B"]
    assert list(result.centers.columns) == list(features.columns)
