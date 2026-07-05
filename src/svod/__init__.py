"""svod package.

SVOD (Subscription Video on Demand) subscribers in the USA
"""

from __future__ import annotations

from svod._internal.analysis import (
    ClusterResult,
    actor_features,
    cluster_actors,
    concentration,
    market_summary,
    momentum,
    net_adds,
    shap_summary,
    share_shift,
)
from svod._internal.charts import (
    fig_cluster_scatter,
    fig_concentration,
    fig_market_overview,
    fig_waterfall,
)
from svod._internal.cli import get_parser, main
from svod._internal.data import QCReport, load_panel, qc_report
from svod._internal.report import build_report

__all__: list[str] = [
    "ClusterResult",
    "QCReport",
    "actor_features",
    "build_report",
    "cluster_actors",
    "concentration",
    "fig_cluster_scatter",
    "fig_concentration",
    "fig_market_overview",
    "fig_waterfall",
    "get_parser",
    "load_panel",
    "main",
    "market_summary",
    "momentum",
    "net_adds",
    "qc_report",
    "shap_summary",
    "share_shift",
]
