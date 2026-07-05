"""Tests for the analysis module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pytest

from svod import (
    actor_features,
    cluster_actors,
    concentration,
    market_summary,
    momentum,
    net_adds,
    shap_summary,
    share_shift,
)

if TYPE_CHECKING:
    from pathlib import Path


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
        summary["total_subscribers"].iloc[4] / summary["total_subscribers"].iloc[0] - 1,
    )


def test_concentration_known_values() -> None:
    """HHI/CR4 verified against hand-computed values."""
    panel = pd.DataFrame(
        {
            "actor": ["A", "B", "C", "D"],
            "quarter": ["2021Q1"] * 4,
            "subscribers": [50, 30, 15, 5],
        },
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


def test_actor_features_winsorizes_and_drops_nonfinite() -> None:
    """Extreme growth is clipped to [-1, 2]; zero-base actors are dropped."""
    quarters = ["2021Q1", "2021Q2", "2021Q3", "2021Q4", "2022Q1", "2022Q2", "2022Q3", "2022Q4"]
    rocket = [100, 200, 400, 1000, 800, 500, 200, 100]
    zero_start = [0, 10, 20, 30, 40, 50, 60, 70]
    rows = []
    for quarter, r_subs, z_subs in zip(quarters, rocket, zero_start, strict=True):
        rows.append({"actor": "Rocket", "quarter": quarter, "subscribers": r_subs})
        rows.append({"actor": "ZeroStart", "quarter": quarter, "subscribers": z_subs})
    panel = pd.DataFrame(rows)
    features = actor_features(panel)
    # ZeroStart has 0 subscribers in 2021Q1 -> infinite growth_2021 -> row dropped
    assert "ZeroStart" not in features.index
    rocket_features = features.loc["Rocket"]
    # raw growth_2021 is 1000/100 - 1 = 9.0, winsorized down to the 2.0 bound
    assert rocket_features["growth_2021"] == pytest.approx(2.0)
    assert rocket_features["growth_2022"] == pytest.approx(100 / 1000 - 1)
    # deceleration computed AFTER winsorizing: -0.9 - 2.0
    assert rocket_features["deceleration"] == pytest.approx(-2.9)


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


def test_net_adds_waterfall(synthetic_panel: pd.DataFrame) -> None:
    """Net adds computed between quarters, Others row closes the ledger."""
    adds = net_adds(synthetic_panel, top=3)
    assert list(adds.columns) == ["actor", "net_adds"]
    assert adds["actor"].iloc[-1] == "Others"
    challenger_a = adds.loc[adds["actor"] == "Challenger A", "net_adds"].item()
    assert challenger_a == 19_000_000 - 9_000_000
    # a decliner beyond the top-3 positive contributors must still surface individually
    assert "Giant A" in adds["actor"].to_numpy()
    giant_a = adds.loc[adds["actor"] == "Giant A", "net_adds"].item()
    assert giant_a == -2_000_000
    # ledger closes: sum of rows equals total market delta between the quarters
    panel = synthetic_panel
    total_start = panel.loc[panel["quarter"] == "2021Q4", "subscribers"].sum()
    total_end = panel.loc[
        (panel["quarter"] == "2022Q4") & (panel["actor"] != "Partial"),
        "subscribers",
    ].sum()
    assert adds["net_adds"].sum() == total_end - total_start


def test_momentum_adds_acceleration(synthetic_panel: pd.DataFrame) -> None:
    """qoq_acceleration is the second difference of QoQ growth; leading NaNs."""
    market = market_summary(synthetic_panel)
    out = momentum(market)
    assert "qoq_acceleration" in out.columns
    assert pd.isna(out["qoq_acceleration"].iloc[0])
    assert pd.isna(out["qoq_acceleration"].iloc[1])
    assert out["qoq_acceleration"].iloc[2] == pytest.approx(
        out["qoq_growth"].iloc[2] - out["qoq_growth"].iloc[1],
    )
    # original frame is untouched
    assert "qoq_acceleration" not in market.columns


def test_share_shift_is_additive(synthetic_panel: pd.DataFrame) -> None:
    """Shares sum to 1, deltas sum to 0, Others closes the frame."""
    shift = share_shift(synthetic_panel)
    assert list(shift.columns) == ["actor", "share_start", "share_end", "share_delta"]
    assert shift["actor"].iloc[-1] == "Others"
    assert "Partial" not in set(shift["actor"])
    assert shift["share_end"].sum() == pytest.approx(1.0)
    assert shift["share_delta"].sum() == pytest.approx(0.0)
    # Challenger A grew from ~7.5% to ~13.9% -> positive share delta
    challenger = shift.loc[shift["actor"] == "Challenger A", "share_delta"].item()
    assert challenger > 0


def test_shap_summary_writes_png(synthetic_panel: pd.DataFrame, tmp_path: Path) -> None:
    """Surrogate + SHAP produces a summary image."""
    pytest.importorskip("shap")
    features = actor_features(synthetic_panel)
    result = cluster_actors(features)
    out = shap_summary(features, result.labels, tmp_path / "shap.png")
    assert out.exists()
    assert out.stat().st_size > 0
