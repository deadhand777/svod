# svod

[![ci](https://github.com/deadhand777/svod/workflows/ci/badge.svg)](https://github.com/deadhand777/svod/actions?query=workflow%3Aci)
[![documentation](https://img.shields.io/badge/docs-zensical-FF9100.svg?style=flat)](https://deadhand777.github.io/svod/)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

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

## Technology stack

`svod` targets **Python >= 3.13** and is built around a small, focused set of
libraries. Each tool is chosen for a specific stage of the pipeline.

### Data & analysis

- [`duckdb`](https://duckdb.org/) — in-process SQL engine used for panel
  aggregation and market-concentration metrics; keeps heavy grouping/rollups
  in fast columnar SQL instead of Python loops.
- [`pandas`](https://pandas.pydata.org/) &
  [`numpy`](https://numpy.org/) — dataframe wrangling and numeric operations
  that glue the ingestion, analysis, and charting stages together.
- [`openpyxl`](https://openpyxl.readthedocs.io/) — reads the raw Dataxis
  `.xlsx` subscriber panel during ingestion.
- [`scikit-learn`](https://scikit-learn.org/) — clusters market actors into
  growth regimes for segmentation.
- [`shap`](https://shap.readthedocs.io/) — explains the surrogate model behind
  each segment, making the clustering interpretable.

### Visualization & reporting

- [`plotly`](https://plotly.com/python/) — interactive HTML charts published to
  the docs site.
- [`kaleido`](https://github.com/plotly/Kaleido) &
  [`matplotlib`](https://matplotlib.org/) — static PNG export of the charts for
  the PDF deliverable.
- [`typst`](https://typst.app/) — compiles the one-page PDF report from the
  computed metrics and exported assets.

### Tooling & development

- [`uv`](https://docs.astral.sh/uv/) &
  [`direnv`](https://direnv.net/) — environment and dependency management; a
  single `uv sync` provisions the project.
- [`duty`](https://pawamoy.github.io/duty/) — task runner behind the `make`
  wrapper (`scripts/make.py`), exposing `make setup`, `make check`, `make test`,
  and friends.
- [`ruff`](https://docs.astral.sh/ruff/) — linter and formatter
  (`select = ["ALL"]`).
- [`ty`](https://github.com/astral-sh/ty) — Astral's static type checker (used
  instead of mypy/pyright).
- [`pytest`](https://docs.pytest.org/) with
  [`pytest-xdist`](https://pytest-xdist.readthedocs.io/),
  [`pytest-cov`](https://pytest-cov.readthedocs.io/), and
  [`pytest-randomly`](https://github.com/pytest-dev/pytest-randomly) —
  parallelized, coverage-tracked, order-randomized test suite.
- [`zensical`](https://pawamoy.github.io/zensical/) &
  [`mkdocstrings`](https://mkdocstrings.github.io/) — documentation site and
  API reference generation.
- [`pdm-backend`](https://backend.pdm-project.org/) — build backend with
  dynamic versioning (`scripts/get_version.py`).
- [`git-changelog`](https://pawamoy.github.io/git-changelog/) — changelog
  generation from Conventional/Angular commit messages.

## Project structure

```text
svod/
├── src/svod/
│   ├── __init__.py        # public API surface (only names in __all__ are exported)
│   ├── __main__.py        # console entry point, re-imports main from _internal.cli
│   ├── py.typed           # PEP 561 marker: ships type information
│   └── _internal/         # implementation, kept out of the public namespace
│       ├── data.py        # load & quality-check the raw subscriber panel
│       ├── analysis.py    # market summary, concentration, growth-regime clustering
│       ├── charts.py      # Plotly figures for market, concentration, clusters
│       ├── report.py      # orchestrates the pipeline and writes all artifacts
│       ├── cli.py         # argparse-based command-line interface
│       └── debug.py       # environment/debug-info reporting
├── tests/                 # pytest suite, one module per _internal component
├── config/                # all tool configs (ruff.toml, ty.toml, pytest.ini, coverage.ini)
├── scripts/               # make.py (duty wrapper), get_version.py, gen_credits.py
├── docs/                  # documentation sources, charts, and reference pages
├── site/                  # built documentation site (zensical output)
├── report/                # generated report artifacts (metrics.json, PDF, assets)
├── data/                  # raw Dataxis dataset (excluded from version control)
├── pyproject.toml         # project metadata, dependencies, and tool settings
├── duties.py              # task definitions run by duty
└── zensical.toml          # documentation site configuration
```

The package deliberately separates a thin **public API** (`src/svod/__init__.py`)
from the implementation in **`src/svod/_internal/`**. Anything meant for
consumers is re-exported through `__init__.py`; everything else stays internal.

## Support

- 📖 **Documentation**: <https://deadhand777.github.io/svod>
- 🐛 **Issues**: [GitHub Issues](https://github.com/deadhand777/svod/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/deadhand777/svod/discussions)


---

**Made with ❤️ by [@deadhand777](https://github.com/deadhand777)**
