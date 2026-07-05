"""Tests for report orchestration."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from svod import build_report

if TYPE_CHECKING:
    from pathlib import Path


def test_build_report_writes_artifacts(synthetic_xlsx: Path, tmp_path: Path) -> None:
    """End-to-end pipeline writes charts, PNGs and metrics."""
    docs_dir = tmp_path / "docs"
    report_dir = tmp_path / "report"
    metrics = build_report(synthetic_xlsx, docs_dir=docs_dir, report_dir=report_dir, skip_pdf=True)
    for name in ["market", "concentration", "clusters", "waterfall", "treemap"]:
        assert (docs_dir / "charts" / f"{name}.html").exists()
        assert (report_dir / "assets" / f"{name}.png").exists()
    assert (report_dir / "assets" / "shap.png").exists()
    on_disk = json.loads((report_dir / "metrics.json").read_text())
    assert on_disk["clusters"]["k"] == metrics["clusters"]["k"]
    assert on_disk["qc"]["n_actors"] == 7
    assert len(on_disk["market"]) == 8
    assert "momentum" in on_disk
    assert "share_shift" in on_disk
    assert on_disk["share_shift"][-1]["actor"] == "Others"
