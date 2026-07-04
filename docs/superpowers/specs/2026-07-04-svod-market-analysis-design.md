# SVOD USA Market Analysis 2021–2022 — Design

**Date:** 2026-07-04
**Context:** Dataxis Data Team Lead take-home. Dataset: `data/Dataxis_Test 2026.xlsx` — 951 rows, 131 US SVOD platforms, quarterly subscriber counts, 2021-Q1 → 2022-Q4, single KPI (`SVOD subscribers`), no duplicates or nulls; 115+ actors have full 8-quarter coverage, the rest launched or disappeared mid-period.

## Deliverables

1. **1-page PDF** (typst): the analysis itself — thesis, 3 short sections, 2 charts, footer linking the docs site. This is what gets sent to Dataxis; it respects their 1-page constraint.
2. **Public docs site** (zensical, GitHub Pages): "Analysis" page (full story, interactive charts) + "Methodology" page (QC, metric definitions, clustering rationale, SHAP interpretability check, data-exclusion statement). Demonstrates the reproducible pipeline.
3. **Reproducible package**: analysis implemented inside the `svod` package with a `svod analyze` CLI that regenerates every artifact from the raw xlsx.

## Thesis (A — "The Great Correction + Two-Speed Market")

2021 shows the tail of post-COVID streaming growth; 2022 shows the correction — incumbent giants stall or shrink (Netflix's first subscriber losses) while a cohort of challengers (e.g. Paramount+, Peacock, Apple TV+) keeps scaling, and a long tail of ~100 niche services stagnates. Clustering segments the 131 actors into growth regimes; concentration metrics (HHI/CR4) track how market structure shifted.

**Guardrail:** the thesis must be verified against the actual numbers first (does US Netflix dip in 2022 in this dataset?). If the data disagrees, the story bends to the data, not vice versa.

## Architecture

All implementation in `svod._internal`, re-exported through `svod/__init__.py` per the repo's enforced public-API convention (`tests/test_api.py`). No module-level docstrings in `_internal` modules.

### `svod._internal.data`
- Load xlsx via pandas/openpyxl, register as duckdb in-memory tables.
- QC report: duplicate (actor, date) check, null check, per-actor coverage matrix, lifecycle flags (launched mid-period, disappeared mid-period).
- Output: tidy quarterly panel (actor, quarter, subscribers).
- Raw data path is an input parameter; `data/` is gitignored and never committed.

### `svod._internal.analysis`
- **Market aggregates** (duckdb SQL): total subscribers per quarter, QoQ and YoY growth.
- **Concentration per quarter**: HHI, CR4, CR8.
- **Per-actor features** (full-coverage actors only): log size, 2021 growth, 2022 growth, growth deceleration (2022 minus 2021 growth), normalized trajectory-shape vector.
- **Clustering**: k-means on standardized features; k selected by silhouette score. Expected segments: saturating giants / scaling challengers / stagnant-declining tail. Partial-coverage actors labeled separately, not force-clustered.
- **Interpretability check**: surrogate `HistGradientBoostingClassifier` (sklearn) predicting cluster labels from the same features; SHAP values on the surrogate show which features define each segment. Framed strictly as cluster-interpretability validation — one beeswarm chart on the Methodology page, at most one sentence in the 1-pager.
- **Contribution waterfall**: net subscriber adds per actor 2021→2022, top contributors vs detractors.

### `svod._internal.charts`
Plotly figures, one codebase, two render targets (interactive HTML for site, PNG via kaleido for PDF):
1. Market total + YoY growth ("the correction")
2. Cluster scatter (size × growth-delta, colored by cluster) or trajectory small-multiples — whichever reads better with real data
3. HHI / CR4 evolution
4. Net-adds waterfall
5. SHAP beeswarm (Methodology page only)

Site embeds all interactive; 1-pager takes the 2 strongest as PNG.

### CLI
`svod analyze <path-to-xlsx>`: runs pipeline → writes interactive chart HTML + metrics into `docs/`, exports PNGs, compiles typst → `analysis.pdf`. Extends the existing argparse CLI in `svod._internal.cli`.

## Dependencies

Add: `pandas`, `openpyxl`, `duckdb`, `scikit-learn`, `plotly`, `kaleido`, `shap`. System: `typst` via brew.

## Testing

Real data is gitignored, so CI never sees it — all tests run on a **synthetic fixture** dataset mimicking the schema (few actors, 8 quarters, known values).
- Unit: HHI/CR4 against hand-computed values; feature builder; QC flags (dupes, partial coverage).
- Smoke: `svod analyze` end-to-end on the fixture (PDF step skipped if typst absent).

## Site & Deploy

- `git init`, public GitHub repo, GitHub Pages workflow building the zensical site.
- Docs: new **Analysis** and **Methodology** pages; Methodology states explicitly that the raw Dataxis dataset is excluded from the repo and only derived aggregates are published.

## Governance & Risks

- **Data governance**: raw xlsx never committed or published; site shows derived analysis only, with an explicit exclusion note.
- **Method defensibility**: every method carries a one-sentence justification (interview-ready). Clustering: "unsupervised segmentation of growth regimes." SHAP: "surrogate-model interpretability check confirming segments are feature-driven, not artifacts." No forecasting — 8 quarterly points per actor cannot support it.
- **AI disclosure**: this repo's `AI_POLICY.md` requires disclosure of AI-assisted work; commits are authored by the human.
- **Thesis risk**: numbers verified before narrative is written (see Guardrail above).
