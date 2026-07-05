# svod

[![ci](https://github.com/deadhand777/svod/workflows/ci/badge.svg)](https://github.com/deadhand777/svod/actions?query=workflow%3Aci)
[![documentation](https://img.shields.io/badge/docs-zensical-FF9100.svg?style=flat)](https://deadhand777.github.io/svod/)

Analysis of the US SVOD (Subscription Video on Demand) subscriber market,
2021-2022, built on a Dataxis subscriber panel. The package exposes a
reproducible pipeline (`svod analyze`) that ingests the raw panel and
produces market-concentration metrics, growth-regime segmentation, and a
one-page PDF summary.

Full write-up, methodology, and interactive charts: <https://deadhand777.github.io/svod>

## Quickstart

```bash
uv sync
uv run svod analyze "data/<file>.xlsx"
```

This writes interactive charts to `docs/charts/`, PNG exports and
`metrics.json` to `report/`, and compiles a one-page PDF deliverable to
`report/svod-analysis-2021-2022.pdf`.

The raw Dataxis dataset is excluded from this repository; only derived
aggregates are published in the docs site and report artifacts.

## Toolchain

- [`duckdb`](https://duckdb.org/) for panel aggregation and market metrics
- [`scikit-learn`](https://scikit-learn.org/) for growth-regime clustering
- [`shap`](https://shap.readthedocs.io/) for surrogate-model segment interpretability
- [`plotly`](https://plotly.com/python/) for interactive and exported charts
- [`typst`](https://typst.app/) for the one-page PDF report
