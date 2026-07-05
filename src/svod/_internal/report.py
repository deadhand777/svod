from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from svod._internal.analysis import (
    actor_features,
    cluster_actors,
    concentration,
    market_summary,
    net_adds,
    shap_summary,
)
from svod._internal.charts import fig_cluster_scatter, fig_concentration, fig_market_overview, fig_waterfall
from svod._internal.data import load_panel, qc_report

if TYPE_CHECKING:
    import pandas as pd

_PDF_NAME = "svod-analysis-2021-2022.pdf"


def build_report(
    xlsx_path: str | Path,
    *,
    docs_dir: str | Path = "docs",
    report_dir: str | Path = "report",
    skip_pdf: bool = False,
) -> dict:
    """Run the full analysis pipeline and write every artifact.

    Writes interactive chart HTML into the docs tree, PNG chart exports and
    a metrics JSON into the report tree, and compiles the typst one-pager
    to PDF when the `typst` binary and template are available.

    Parameters:
        xlsx_path: Path to the raw Dataxis xlsx export.
        docs_dir: Documentation root receiving `charts/*.html`.
        report_dir: Report root receiving `assets/*.png` and `metrics.json`.
        skip_pdf: Skip the typst PDF compilation step.

    Returns:
        The computed metrics (same content as `metrics.json`).
    """
    docs_dir = Path(docs_dir)
    report_dir = Path(report_dir)
    charts_dir = docs_dir / "charts"
    assets_dir = report_dir / "assets"
    charts_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    panel = load_panel(xlsx_path)
    qc = qc_report(panel)
    market = market_summary(panel)
    conc = concentration(panel)
    features = actor_features(panel)
    clusters = cluster_actors(features)
    adds = net_adds(panel)

    figures = {
        "market": fig_market_overview(market),
        "concentration": fig_concentration(conc),
        "clusters": fig_cluster_scatter(features, clusters.labels),
        "waterfall": fig_waterfall(adds),
    }
    for name, fig in figures.items():
        fig.write_html(charts_dir / f"{name}.html", include_plotlyjs="cdn")
        fig.write_image(assets_dir / f"{name}.png", width=900, height=500, scale=2)
    shap_summary(features, clusters.labels, assets_dir / "shap.png")

    members: dict[str, list[str]] = {}
    for actor, label in clusters.labels.items():
        members.setdefault(str(label), []).append(str(actor))

    def _records(frame: pd.DataFrame) -> list[dict]:
        """Convert a frame to records with NaN replaced by None (valid JSON null)."""
        return frame.astype(object).where(frame.notna(), None).to_dict(orient="records")

    metrics = {
        "market": _records(market),
        "concentration": _records(conc),
        "clusters": {
            "k": clusters.k,
            "silhouette": clusters.silhouette,
            "sizes": {label: len(actors) for label, actors in members.items()},
            "members": members,
            "centers": _records(clusters.centers),
        },
        "net_adds": _records(adds),
        "qc": {
            "n_rows": qc.n_rows,
            "n_actors": qc.n_actors,
            "duplicates": qc.duplicates,
            "nulls": qc.nulls,
            "quarters": qc.quarters,
            "full_coverage_actors": qc.full_coverage_actors,
            "partial_actors": qc.partial_actors,
        },
    }
    (report_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, default=float), encoding="utf-8")

    template = report_dir / "onepager.typ"
    if not skip_pdf and template.exists() and shutil.which("typst"):
        subprocess.run(  # noqa: S603
            ["typst", "compile", str(template), str(report_dir / _PDF_NAME)],  # noqa: S607
            check=True,
        )
    return metrics
