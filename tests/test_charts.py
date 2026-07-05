"""Tests for chart builders."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from svod import (
    actor_features,
    cluster_actors,
    concentration,
    fig_cluster_scatter,
    fig_concentration,
    fig_market_overview,
    fig_share_treemap,
    fig_waterfall,
    market_summary,
    net_adds,
    share_shift,
)


def test_chart_builders_return_figures(synthetic_panel: pd.DataFrame) -> None:
    """Each builder returns a plotly figure with at least one trace."""
    features = actor_features(synthetic_panel)
    result = cluster_actors(features)
    figures = [
        fig_market_overview(market_summary(synthetic_panel)),
        fig_concentration(concentration(synthetic_panel)),
        fig_cluster_scatter(features, result.labels),
        fig_waterfall(net_adds(synthetic_panel, top=3)),
    ]
    for fig in figures:
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1


def test_share_treemap_returns_figure(synthetic_panel: pd.DataFrame) -> None:
    """Treemap builder returns a figure with one treemap trace."""
    fig = fig_share_treemap(share_shift(synthetic_panel))
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].type == "treemap"


def test_market_overview_annotation_degrades() -> None:
    """A summary too short to compute YoY still builds, without annotations."""
    market = pd.DataFrame(
        {
            "quarter": ["2021Q1", "2021Q2"],
            "total_subscribers": [100, 110],
            "active_actors": [2, 2],
            "qoq_growth": [float("nan"), 0.1],
            "yoy_growth": [float("nan"), float("nan")],
        },
    )
    fig = fig_market_overview(market)
    assert isinstance(fig, go.Figure)
    assert len(fig.layout.annotations) == 0
