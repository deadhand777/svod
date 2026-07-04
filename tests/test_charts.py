"""Tests for chart builders."""

from __future__ import annotations

import pandas as pd  # noqa: TC002 -- task brief mandates this runtime import verbatim; only used in annotations here
import plotly.graph_objects as go

from svod import (
    actor_features,
    cluster_actors,
    concentration,
    fig_cluster_scatter,
    fig_concentration,
    fig_market_overview,
    fig_waterfall,
    market_summary,
    net_adds,
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
