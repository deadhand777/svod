from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go
from plotly.subplots import make_subplots

if TYPE_CHECKING:
    import pandas as pd

_TEMPLATE = "plotly_white"

# Categorical palette (fixed order, never cycled): blue, aqua, yellow, green,
# violet, red, magenta, orange.
_CATEGORICAL = [
    "#2a78d6",
    "#1baf7a",
    "#eda100",
    "#008300",
    "#4a3aa7",
    "#e34948",
    "#e87ba4",
    "#eb6834",
]
_STATUS_GOOD = "#0ca30c"
_STATUS_CRITICAL = "#d03b3b"


def fig_market_overview(market: pd.DataFrame) -> go.Figure:
    """Chart total market size with year-over-year growth overlay.

    Parameters:
        market: Output of `market_summary`.

    Returns:
        Figure with subscriber bars (left axis) and YoY growth line (right axis).
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(
        x=market["quarter"],
        y=market["total_subscribers"],
        name="Total SVOD subscribers",
        marker_color=_CATEGORICAL[0],
    )
    fig.add_scatter(
        x=market["quarter"],
        y=market["yoy_growth"],
        name="YoY growth",
        mode="lines+markers",
        line_color=_CATEGORICAL[1],
        secondary_y=True,
    )
    fig.update_layout(template=_TEMPLATE, title="US SVOD market: total subscribers and YoY growth", legend_orientation="h")
    fig.update_yaxes(title_text="Subscribers", secondary_y=False)
    fig.update_yaxes(title_text="YoY growth", tickformat=".0%", secondary_y=True)
    return fig


def fig_concentration(conc: pd.DataFrame) -> go.Figure:
    """Chart market-concentration evolution.

    Parameters:
        conc: Output of `concentration`.

    Returns:
        Figure with HHI (left axis) and CR4/CR8 shares (right axis).
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_scatter(x=conc["quarter"], y=conc["hhi"], name="HHI", mode="lines+markers", line_color=_CATEGORICAL[0])
    fig.add_scatter(
        x=conc["quarter"], y=conc["cr4"], name="CR4", mode="lines+markers", line_color=_CATEGORICAL[1], secondary_y=True,
    )
    fig.add_scatter(
        x=conc["quarter"], y=conc["cr8"], name="CR8", mode="lines+markers", line_color=_CATEGORICAL[2], secondary_y=True,
    )
    fig.update_layout(template=_TEMPLATE, title="Market concentration: HHI and top-N subscriber share", legend_orientation="h")
    fig.update_yaxes(title_text="HHI (0-10000)", secondary_y=False)
    fig.update_yaxes(title_text="Top-N share", tickformat=".0%", secondary_y=True)
    return fig


def fig_cluster_scatter(features: pd.DataFrame, labels: pd.Series) -> go.Figure:
    """Chart actor segments as size vs growth-deceleration scatter.

    Parameters:
        features: Output of `actor_features`.
        labels: Cluster labels from `cluster_actors`.

    Returns:
        Scatter figure, one trace per cluster, actor names on hover.
    """
    fig = go.Figure()
    for cluster in sorted(labels.unique()):
        actors = labels[labels == cluster].index
        subset = features.loc[actors]
        fig.add_scatter(
            x=subset["log_size"],
            y=subset["deceleration"],
            mode="markers",
            name=f"Segment {cluster}",
            text=list(actors),
            hovertemplate="%{text}<br>log10 size: %{x:.2f}<br>growth delta: %{y:.2f}<extra></extra>",
            marker={"size": 10, "color": _CATEGORICAL[cluster % len(_CATEGORICAL)]},
        )
    fig.update_layout(
        template=_TEMPLATE,
        title="Growth regimes: platform size vs growth change 2022 minus 2021",
        xaxis_title="log10 subscribers (2022Q4)",
        yaxis_title="Growth 2022 - growth 2021",
        legend_orientation="h",
    )
    return fig


def fig_waterfall(adds: pd.DataFrame) -> go.Figure:
    """Chart net subscriber additions per actor as a waterfall.

    Parameters:
        adds: Output of `net_adds`.

    Returns:
        Waterfall figure of contributions to market net adds.
    """
    fig = go.Figure(
        go.Waterfall(
            x=adds["actor"],
            y=adds["net_adds"],
            measure=["relative"] * len(adds),
            increasing={"marker": {"color": _STATUS_GOOD}},
            decreasing={"marker": {"color": _STATUS_CRITICAL}},
        ),
    )
    fig.update_layout(
        template=_TEMPLATE,
        title="Who moved the market: net subscriber adds 2021Q4 to 2022Q4",
        yaxis_title="Net adds",
    )
    return fig
