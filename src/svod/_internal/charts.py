from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

if TYPE_CHECKING:
    import pandas as pd

# Categorical palette (fixed order, never cycled): navy, orange, teal, burnt
# orange, light steel, sand, mid navy, ochre. Dataxis brand: navy + orange led.
_CATEGORICAL = [
    "#253861",
    "#EA993F",
    "#2A9D8F",
    "#C36E28",
    "#7E93B8",
    "#E9C46A",
    "#37506E",
    "#B5651D",
]
_STATUS_GOOD = "#0ca30c"
_STATUS_CRITICAL = "#d03b3b"

_BRAND_NAVY = "#142F4E"
_GRID = "#E6E9EF"

# Deep-copy so we don't mutate the globally-shared plotly_white template.
_TEMPLATE = copy.deepcopy(pio.templates["plotly_white"])
_TEMPLATE.layout.colorway = _CATEGORICAL
_TEMPLATE.layout.font.color = _BRAND_NAVY
_TEMPLATE.layout.title.font.color = _BRAND_NAVY
_TEMPLATE.layout.xaxis.gridcolor = _GRID
_TEMPLATE.layout.yaxis.gridcolor = _GRID


def _steepest_deceleration(market: pd.DataFrame) -> tuple[str, float] | None:
    """Find the quarter of steepest YoY-growth drop, or None if uncomputable."""
    drops = market["yoy_growth"].diff().dropna()
    if drops.empty:
        return None
    idx = drops.idxmin()
    return str(market.loc[idx, "quarter"]), float(market.loc[idx, "yoy_growth"])


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
    fig.update_layout(
        template=_TEMPLATE,
        title="US SVOD market: total subscribers and YoY growth",
        legend_orientation="h",
        hovermode="x unified",
    )
    fig.update_xaxes(showspikes=True, spikemode="across", spikethickness=1)
    callout = _steepest_deceleration(market)
    if callout is not None:
        quarter, value = callout
        fig.add_annotation(
            x=quarter,
            y=value,
            yref="y2",
            text="Steepest YoY deceleration",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-40,
            font={"color": _CATEGORICAL[1]},
        )
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
        x=conc["quarter"],
        y=conc["cr4"],
        name="CR4",
        mode="lines+markers",
        line_color=_CATEGORICAL[1],
        secondary_y=True,
    )
    fig.add_scatter(
        x=conc["quarter"],
        y=conc["cr8"],
        name="CR8",
        mode="lines+markers",
        line_color=_CATEGORICAL[2],
        secondary_y=True,
    )
    fig.update_layout(
        template=_TEMPLATE,
        title="Market concentration: HHI and top-N subscriber share",
        legend_orientation="h",
        hovermode="x unified",
    )
    fig.update_xaxes(showspikes=True, spikemode="across", spikethickness=1)
    fig.update_yaxes(title_text="HHI (0-10000)", secondary_y=False)
    fig.update_yaxes(title_text="Top-N share", tickformat=".0%", secondary_y=True)
    return fig


def fig_cluster_scatter(features: pd.DataFrame, labels: pd.Series) -> go.Figure:
    """Chart actor segments as size vs growth-delta scatter.

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
    movers = adds[adds["actor"] != "Others"]
    if not movers.empty:
        top = movers.loc[movers["net_adds"].idxmax()]
        bottom = movers.loc[movers["net_adds"].idxmin()]
        fig.add_annotation(
            x=top["actor"],
            y=int(top["net_adds"]),
            text="Largest gain",
            showarrow=True,
            arrowhead=2,
            ay=-30,
            font={"color": _STATUS_GOOD},
        )
        fig.add_annotation(
            x=bottom["actor"],
            y=int(bottom["net_adds"]),
            text="Largest loss",
            showarrow=True,
            arrowhead=2,
            ay=30,
            font={"color": _STATUS_CRITICAL},
        )
    return fig


def fig_share_treemap(shift: pd.DataFrame) -> go.Figure:
    """Chart ending market share as a treemap, colored by share change.

    Parameters:
        shift: Output of `share_shift`.

    Returns:
        Treemap figure; tile area is ending share, tile color is the
        share-point change over the window (orange = gaining share, red =
        losing). The `Others` residual is excluded from the tiles.
    """
    tiles = shift[shift["actor"] != "Others"]
    fig = go.Figure(
        go.Treemap(
            labels=list(tiles["actor"]),
            parents=[""] * len(tiles),
            values=list(tiles["share_end"]),
            marker={
                "colors": list(tiles["share_delta"]),
                "colorscale": [[0.0, _STATUS_CRITICAL], [0.5, _GRID], [1.0, _CATEGORICAL[1]]],
                "cmid": 0,
                "colorbar": {"title": "Share change"},
            },
            hovertemplate="%{label}<br>tracked share: %{value:.1%}<extra></extra>",
        ),
    )
    fig.update_layout(
        template=_TEMPLATE,
        title="Market share by platform (2022Q4), colored by 2021Q4-2022Q4 share change",
    )
    return fig
