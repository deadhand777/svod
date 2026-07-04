# SVOD USA Market Analysis 2021–2022 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible SVOD-market analysis pipeline inside the `svod` package (`svod analyze` CLI) that produces interactive charts + methodology pages on the zensical docs site and a typst 1-page PDF for the Dataxis take-home.

**Architecture:** Implementation lives in `svod._internal` (data → analysis → charts → report orchestration), re-exported through `svod/__init__.py`. All tests run on a synthetic fixture (real data is gitignored). `svod analyze <xlsx>` regenerates every artifact.

**Tech Stack:** pandas + openpyxl (load), duckdb (SQL aggregates), scikit-learn (k-means, RandomForest surrogate), shap (segment interpretability), plotly + kaleido (charts, interactive HTML + PNG), typst (1-pager PDF), zensical (docs site), pytest (TDD).

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-04-svod-market-analysis-design.md`.
- Raw data (`data/`) is NEVER committed or published — gitignore it in Task 1. Site/repo carry derived aggregates only.
- `AI_POLICY.md` + repo CLAUDE.md: commits are authored by the human, no AI attribution anywhere (no `Co-Authored-By: Claude`, no "Generated with" lines). Commit steps below give the message; the human runs them (or has explicitly delegated staging+message).
- Commit messages: Angular/Karma convention (`<type>: Subject`), per `CONTRIBUTING.md`.
- Public objects in `svod._internal` MUST be re-exported in `src/svod/__init__.py` `__all__` (enforced by `tests/test_api.py`). Module-level helpers/constants not meant for the public API get a `_` prefix.
- Internal modules (`src/svod/_internal/*.py`) must NOT have module-level docstrings (enforced by `test_no_module_docstrings_in_internal_api`). Public functions/classes need Google-style docstrings (ruff `select = ["ALL"]`, ignores in `config/ruff.toml`).
- Relative imports banned; `from __future__ import annotations` at top of every module (matches existing style).
- Test commands: single test `uv run pytest tests/test_X.py::test_name -c config/pytest.ini -p no:randomly`; full suite `make test`. `config/pytest.ini` sets `filterwarnings = error` — third-party warnings must be silenced with targeted ignores (Task 1).
- Dev tasks run against ALL of `PYTHON_VERSIONS` (3.10–3.15). shap/kaleido/duckdb wheels may not exist for 3.14/3.15. Fallback (apply in Task 1 only if `make setup` fails): `export PYTHON_VERSIONS="3.11 3.12 3.13"` in `.envrc` before `make setup` — the env var overrides the default in `scripts/make.py:17`.
- `uv run ...` uses the default venv directly; that is fine for all steps below.

## File Structure

| File | Responsibility |
|---|---|
| `src/svod/_internal/data.py` | Load xlsx → tidy panel; QC report (dupes, nulls, coverage, lifecycle) |
| `src/svod/_internal/analysis.py` | Market aggregates, concentration (HHI/CR4/CR8), actor features, k-means clustering, SHAP surrogate, net-adds |
| `src/svod/_internal/charts.py` | Plotly figure builders (pure: DataFrame in → `go.Figure` out) |
| `src/svod/_internal/report.py` | Orchestration: run pipeline, write HTML/PNG/JSON artifacts, compile typst PDF |
| `src/svod/_internal/cli.py` | Add `analyze` subcommand |
| `src/svod/__init__.py` | Public API re-exports |
| `report/onepager.typ` | Typst 1-pager template |
| `tests/conftest.py` | Add `synthetic_panel` + `synthetic_xlsx` fixtures |
| `tests/test_data.py`, `tests/test_analysis.py`, `tests/test_charts.py`, `tests/test_report.py` | Unit + smoke tests |
| `docs/analysis.md`, `docs/methodology.md` | Site pages; nav added in `zensical.toml` |
| `docs/charts/*.html`, `report/assets/*.png` | Generated artifacts (committed — derived aggregates only) |

---

### Task 1: Repo bootstrap — git, gitignore, dependencies, warning filters

**Files:**
- Modify: `.gitignore`, `pyproject.toml:31`, `config/pytest.ini`
- Create: git repository (init)

**Interfaces:**
- Produces: importable `pandas`, `numpy`, `duckdb`, `sklearn`, `plotly`, `kaleido`, `shap`, `matplotlib`, `openpyxl` in the project venv.

- [ ] **Step 1: Protect the data before git exists**

Append to `.gitignore`:

```
# proprietary input data — never commit
/data/
```

- [ ] **Step 2: Init git and verify data is ignored**

```bash
cd /Users/c.schulz/programming/svod
git init -b main
git status --porcelain | grep -c "data/" # expected: 0
git check-ignore data/"Dataxis_Test 2026.xlsx" # expected: prints the path (= ignored)
```

- [ ] **Step 3: Add runtime dependencies**

In `pyproject.toml`, replace `dependencies = []` with:

```toml
dependencies = [
    "duckdb>=1.1",
    "kaleido>=1.0",
    "matplotlib>=3.8",
    "numpy>=1.26",
    "openpyxl>=3.1",
    "pandas>=2.2",
    "plotly>=6.1",
    "scikit-learn>=1.5",
    "shap>=0.46",
]
```

- [ ] **Step 4: Add targeted warning ignores**

`config/pytest.ini` has `filterwarnings = error`; heavy libs emit warnings. Append these lines to the existing `filterwarnings` list:

```ini
  ignore::DeprecationWarning:sklearn
  ignore::FutureWarning:sklearn
  ignore::DeprecationWarning:shap
  ignore::UserWarning:shap
  ignore::DeprecationWarning:numba
  ignore::DeprecationWarning:plotly
  ignore::DeprecationWarning:pandas
  ignore::UserWarning:openpyxl
```

(If a later task still fails on a third-party warning, add a similarly narrow `ignore::<Class>:<module>` line — never blanket-ignore.)

- [ ] **Step 5: Sync and verify imports**

```bash
uv sync
uv run python -c "import pandas, duckdb, sklearn, plotly, shap, matplotlib, openpyxl; print('ok')"
```
Expected: `ok`. If `uv sync` fails resolving shap/kaleido for Python 3.14/3.15 during a later `make setup`, apply the `PYTHON_VERSIONS` fallback from Global Constraints.

- [ ] **Step 6: Verify existing suite still green**

```bash
uv run pytest -c config/pytest.ini
```
Expected: all existing tests pass.

- [ ] **Step 7: Commit (human)**

```bash
git add -A
git commit -m "chore: Initial commit with analysis dependencies"
```

---

### Task 2: Data layer — `load_panel` + `qc_report`

**Files:**
- Create: `src/svod/_internal/data.py`, `tests/test_data.py`
- Modify: `tests/conftest.py`, `src/svod/__init__.py`

**Interfaces:**
- Produces: `load_panel(xlsx_path: str | Path) -> pd.DataFrame` — tidy panel with columns `actor` (str), `quarter` (str, e.g. `"2021Q1"`), `subscribers` (int64), sorted by actor/quarter. `qc_report(panel: pd.DataFrame) -> QCReport` — dataclass with fields `n_rows: int`, `n_actors: int`, `duplicates: int`, `nulls: int`, `quarters: list[str]`, `full_coverage_actors: list[str]`, `partial_actors: dict[str, int]`.

- [ ] **Step 1: Add fixtures to `tests/conftest.py`**

Append (keep the existing module docstring — `tests/` is not `_internal`):

```python
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pytest

if TYPE_CHECKING:
    from pathlib import Path

_QUARTER_ENDS = [
    "2021-03-31", "2021-06-30", "2021-09-30", "2021-12-31",
    "2022-03-31", "2022-06-30", "2022-09-30", "2022-12-31",
]

# Actors chosen so cluster structure is unambiguous:
# giants (huge, decelerating), challengers (mid, accelerating), niche (small, flat).
_SYNTHETIC_SUBS = {
    "Giant A": [60_000_000, 61_000_000, 62_000_000, 63_000_000, 62_500_000, 62_000_000, 61_500_000, 61_000_000],
    "Giant B": [40_000_000, 41_000_000, 42_000_000, 43_000_000, 43_500_000, 44_000_000, 44_500_000, 45_000_000],
    "Challenger A": [5_000_000, 6_000_000, 7_500_000, 9_000_000, 11_000_000, 13_500_000, 16_000_000, 19_000_000],
    "Challenger B": [3_000_000, 3_600_000, 4_400_000, 5_400_000, 6_600_000, 8_000_000, 9_700_000, 11_500_000],
    "Niche A": [200_000, 201_000, 202_000, 203_000, 203_500, 204_000, 204_500, 205_000],
    "Niche B": [150_000, 149_000, 148_000, 147_000, 146_000, 145_000, 144_000, 143_000],
}


@pytest.fixture
def synthetic_panel() -> pd.DataFrame:
    """Tidy quarterly panel with 6 full-coverage actors and 1 partial actor.

    Returns:
        The synthetic panel.
    """
    rows = [
        {"actor": actor, "quarter": f"{pd.Timestamp(date).year}Q{pd.Timestamp(date).quarter}", "subscribers": subs}
        for actor, series in _SYNTHETIC_SUBS.items()
        for date, subs in zip(_QUARTER_ENDS, series)
    ]
    rows += [
        {"actor": "Partial", "quarter": q, "subscribers": s}
        for q, s in [("2022Q2", 10_000), ("2022Q3", 20_000), ("2022Q4", 40_000)]
    ]
    return pd.DataFrame(rows).sort_values(["actor", "quarter"], ignore_index=True)


@pytest.fixture
def synthetic_xlsx(tmp_path: Path, synthetic_panel: pd.DataFrame) -> Path:
    """Raw-schema xlsx file mimicking the Dataxis export.

    Parameters:
        tmp_path: Pytest temporary directory.
        synthetic_panel: The synthetic panel fixture.

    Returns:
        Path to the written xlsx file.
    """
    quarter_to_date = {f"{pd.Timestamp(d).year}Q{pd.Timestamp(d).quarter}": d for d in _QUARTER_ENDS}
    raw = pd.DataFrame(
        {
            "Actor_label": synthetic_panel["actor"],
            "Country_label": "USA",
            "Kpi_label_corporate": "SVOD subscribers",
            "Fact_date": pd.to_datetime(synthetic_panel["quarter"].map(quarter_to_date)),
            "Kpi_value": synthetic_panel["subscribers"],
        }
    )
    path = tmp_path / "synthetic.xlsx"
    raw.to_excel(path, sheet_name="Data", index=False)
    return path
```

- [ ] **Step 2: Write failing tests — `tests/test_data.py`**

```python
"""Tests for the data layer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from svod import load_panel, qc_report

if TYPE_CHECKING:
    from pathlib import Path

    import pandas as pd


def test_load_panel_schema(synthetic_xlsx: Path) -> None:
    """Panel has tidy columns and one row per actor-quarter."""
    panel = load_panel(synthetic_xlsx)
    assert list(panel.columns) == ["actor", "quarter", "subscribers"]
    assert len(panel) == 6 * 8 + 3
    assert panel["quarter"].str.fullmatch(r"20\d\dQ[1-4]").all()
    assert panel["subscribers"].dtype == "int64"


def test_qc_report_coverage(synthetic_panel: pd.DataFrame) -> None:
    """QC report flags full vs partial coverage and clean data."""
    report = qc_report(synthetic_panel)
    assert report.n_rows == 51
    assert report.n_actors == 7
    assert report.duplicates == 0
    assert report.nulls == 0
    assert report.quarters == ["2021Q1", "2021Q2", "2021Q3", "2021Q4", "2022Q1", "2022Q2", "2022Q3", "2022Q4"]
    assert "Giant A" in report.full_coverage_actors
    assert report.partial_actors == {"Partial": 3}
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/test_data.py -c config/pytest.ini -p no:randomly
```
Expected: FAIL — `ImportError: cannot import name 'load_panel' from 'svod'`.

- [ ] **Step 4: Implement `src/svod/_internal/data.py`**

No module docstring (internal-module rule):

```python
from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from pathlib import Path

_EXPECTED_COLUMNS = ("Actor_label", "Country_label", "Kpi_label_corporate", "Fact_date", "Kpi_value")


@dataclasses.dataclass(frozen=True)
class QCReport:
    """Data-quality summary of a subscriber panel.

    Attributes:
        n_rows: Number of rows in the panel.
        n_actors: Number of distinct actors.
        duplicates: Number of duplicated (actor, quarter) rows.
        nulls: Number of missing subscriber values.
        quarters: Sorted list of quarters present.
        full_coverage_actors: Actors observed in every quarter.
        partial_actors: Actors with incomplete coverage, mapped to their observation count.
    """

    n_rows: int
    n_actors: int
    duplicates: int
    nulls: int
    quarters: list[str]
    full_coverage_actors: list[str]
    partial_actors: dict[str, int]


def load_panel(xlsx_path: str | Path) -> pd.DataFrame:
    """Load a Dataxis SVOD export into a tidy quarterly panel.

    Parameters:
        xlsx_path: Path to the xlsx file (expects a `Data` sheet with the Dataxis schema).

    Returns:
        DataFrame with columns `actor`, `quarter` (like `"2021Q1"`) and `subscribers`,
        sorted by actor and quarter.

    Raises:
        ValueError: If expected columns are missing from the `Data` sheet.
    """
    raw = pd.read_excel(xlsx_path, sheet_name="Data")
    missing = set(_EXPECTED_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing expected columns in Data sheet: {sorted(missing)}")
    dates = pd.to_datetime(raw["Fact_date"])
    panel = pd.DataFrame(
        {
            "actor": raw["Actor_label"].astype(str),
            "quarter": dates.dt.year.astype(str) + "Q" + dates.dt.quarter.astype(str),
            "subscribers": raw["Kpi_value"].astype("int64"),
        }
    )
    return panel.sort_values(["actor", "quarter"], ignore_index=True)


def qc_report(panel: pd.DataFrame) -> QCReport:
    """Compute a data-quality report for a subscriber panel.

    Parameters:
        panel: Tidy panel as returned by `load_panel`.

    Returns:
        The quality report.
    """
    quarters = sorted(panel["quarter"].unique())
    counts = panel.groupby("actor").size()
    full = counts[counts == len(quarters)]
    partial = counts[counts < len(quarters)]
    return QCReport(
        n_rows=len(panel),
        n_actors=panel["actor"].nunique(),
        duplicates=int(panel.duplicated(["actor", "quarter"]).sum()),
        nulls=int(panel["subscribers"].isna().sum()),
        quarters=list(quarters),
        full_coverage_actors=sorted(full.index),
        partial_actors=dict(partial.sort_index()),
    )
```

- [ ] **Step 5: Re-export in `src/svod/__init__.py`**

```python
"""svod package.

SVOD (Subscription Video on Demand) subscribers in the USA
"""

from __future__ import annotations

from svod._internal.cli import get_parser, main
from svod._internal.data import QCReport, load_panel, qc_report

__all__: list[str] = ["QCReport", "get_parser", "load_panel", "main", "qc_report"]
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
uv run pytest tests/test_data.py -c config/pytest.ini -p no:randomly
```
Expected: 2 passed.

- [ ] **Step 7: Commit (human)**

```bash
git add src/svod/__init__.py src/svod/_internal/data.py tests/test_data.py tests/conftest.py
git commit -m "feat: Add data layer with panel loading and QC report"
```

---

### Task 3: Market metrics — `market_summary` + `concentration`

**Files:**
- Create: `src/svod/_internal/analysis.py`, `tests/test_analysis.py`
- Modify: `src/svod/__init__.py`

**Interfaces:**
- Consumes: tidy panel from `load_panel` (Task 2).
- Produces: `market_summary(panel) -> pd.DataFrame` with columns `quarter`, `total_subscribers` (int), `active_actors` (int), `qoq_growth` (float, NaN first row), `yoy_growth` (float, NaN first 4 rows). `concentration(panel) -> pd.DataFrame` with columns `quarter`, `hhi` (float, 0–10000 scale), `cr4`, `cr8` (floats, 0–1).

- [ ] **Step 1: Write failing tests — `tests/test_analysis.py`**

```python
"""Tests for the analysis module."""

from __future__ import annotations

import pandas as pd
import pytest

from svod import concentration, market_summary


def test_market_summary_totals_and_growth(synthetic_panel: pd.DataFrame) -> None:
    """Totals aggregate all actors; growth columns behave."""
    summary = market_summary(synthetic_panel)
    assert list(summary["quarter"]) == sorted(synthetic_panel["quarter"].unique())
    q1 = summary.loc[summary["quarter"] == "2021Q1", "total_subscribers"].item()
    assert q1 == 60_000_000 + 40_000_000 + 5_000_000 + 3_000_000 + 200_000 + 150_000
    assert pd.isna(summary["qoq_growth"].iloc[0])
    assert summary["yoy_growth"].iloc[4] == pytest.approx(
        summary["total_subscribers"].iloc[4] / summary["total_subscribers"].iloc[0] - 1
    )


def test_concentration_known_values() -> None:
    """HHI/CR4 verified against hand-computed values."""
    panel = pd.DataFrame(
        {
            "actor": ["A", "B", "C", "D"],
            "quarter": ["2021Q1"] * 4,
            "subscribers": [50, 30, 15, 5],
        }
    )
    conc = concentration(panel)
    # shares: .5, .3, .15, .05 -> HHI = (0.25 + 0.09 + 0.0225 + 0.0025) * 10000 = 3650
    assert conc["hhi"].item() == pytest.approx(3650.0)
    assert conc["cr4"].item() == pytest.approx(1.0)
    assert conc["cr8"].item() == pytest.approx(1.0)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_analysis.py -c config/pytest.ini -p no:randomly
```
Expected: FAIL — `ImportError: cannot import name 'concentration' from 'svod'`.

- [ ] **Step 3: Implement in `src/svod/_internal/analysis.py`**

No module docstring:

```python
from __future__ import annotations

import duckdb
import pandas as pd


def market_summary(panel: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the panel into market-level totals and growth rates.

    Parameters:
        panel: Tidy panel with `actor`, `quarter`, `subscribers` columns.

    Returns:
        One row per quarter with total subscribers, active actor count,
        quarter-over-quarter growth and year-over-year growth.
    """
    con = duckdb.connect()
    con.register("panel", panel)
    summary = con.execute(
        """
        SELECT quarter,
               SUM(subscribers)::BIGINT AS total_subscribers,
               COUNT(*)::BIGINT AS active_actors
        FROM panel
        GROUP BY quarter
        ORDER BY quarter
        """
    ).df()
    con.close()
    summary["qoq_growth"] = summary["total_subscribers"].pct_change()
    summary["yoy_growth"] = summary["total_subscribers"].pct_change(periods=4)
    return summary


def concentration(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute market-concentration metrics per quarter.

    Parameters:
        panel: Tidy panel with `actor`, `quarter`, `subscribers` columns.

    Returns:
        One row per quarter with `hhi` (Herfindahl–Hirschman index on the
        0–10000 scale), `cr4` and `cr8` (top-4 / top-8 subscriber share).
    """
    con = duckdb.connect()
    con.register("panel", panel)
    shares = con.execute(
        """
        SELECT quarter,
               subscribers / SUM(subscribers) OVER (PARTITION BY quarter) AS share,
               ROW_NUMBER() OVER (PARTITION BY quarter ORDER BY subscribers DESC) AS rank
        FROM panel
        """
    ).df()
    con.close()
    grouped = shares.groupby("quarter")
    return pd.DataFrame(
        {
            "hhi": grouped["share"].apply(lambda s: float((s**2).sum() * 10_000)),
            "cr4": shares[shares["rank"] <= 4].groupby("quarter")["share"].sum(),
            "cr8": shares[shares["rank"] <= 8].groupby("quarter")["share"].sum(),
        }
    ).reset_index()
```

- [ ] **Step 4: Re-export**

In `src/svod/__init__.py`, add to imports/`__all__`:

```python
from svod._internal.analysis import concentration, market_summary
```
`__all__` becomes: `["QCReport", "concentration", "get_parser", "load_panel", "main", "market_summary", "qc_report"]`

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_analysis.py -c config/pytest.ini -p no:randomly
```
Expected: 2 passed.

- [ ] **Step 6: Commit (human)**

```bash
git add src/svod/__init__.py src/svod/_internal/analysis.py tests/test_analysis.py
git commit -m "feat: Add market summary and concentration metrics"
```

---

### Task 4: Actor features + k-means clustering

**Files:**
- Modify: `src/svod/_internal/analysis.py`, `tests/test_analysis.py`, `src/svod/__init__.py`

**Interfaces:**
- Produces: `actor_features(panel) -> pd.DataFrame` — index `actor` (full-coverage actors only, rows with non-finite growth dropped), columns `log_size`, `growth_2021`, `growth_2022`, `deceleration` (floats; growth columns winsorized to [-1.0, 2.0], `deceleration` computed after winsorizing). `cluster_actors(features, *, k_min=2, k_max=6, random_state=0) -> ClusterResult` — dataclass with `labels: pd.Series` (index actor, name `"cluster"`), `k: int`, `silhouette: float`, `centers: pd.DataFrame` (in original feature units).

- [ ] **Step 1: Write failing tests — append to `tests/test_analysis.py`**

```python
def test_actor_features_full_coverage_only(synthetic_panel: pd.DataFrame) -> None:
    """Partial actors excluded; feature math verified for one actor."""
    features = actor_features(synthetic_panel)
    assert "Partial" not in features.index
    assert len(features) == 6
    challenger = features.loc["Challenger A"]
    assert challenger["growth_2021"] == pytest.approx(9_000_000 / 5_000_000 - 1)
    # raw 2022 growth is 19m/9m - 1 ~ 1.11, inside the [-1, 2] winsor bounds
    assert challenger["growth_2022"] == pytest.approx(19_000_000 / 9_000_000 - 1)
    assert challenger["deceleration"] == pytest.approx(challenger["growth_2022"] - challenger["growth_2021"])


def test_cluster_actors_separates_regimes(synthetic_panel: pd.DataFrame) -> None:
    """Challengers land in one cluster, distinct from niche actors."""
    features = actor_features(synthetic_panel)
    result = cluster_actors(features)
    assert 2 <= result.k <= 6
    assert -1.0 <= result.silhouette <= 1.0
    assert set(result.labels.index) == set(features.index)
    assert result.labels["Challenger A"] == result.labels["Challenger B"]
    assert result.labels["Challenger A"] != result.labels["Niche B"]
    assert list(result.centers.columns) == list(features.columns)
```

Update the import line at the top of the file:

```python
from svod import actor_features, cluster_actors, concentration, market_summary
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_analysis.py -c config/pytest.ini -p no:randomly
```
Expected: FAIL — `ImportError: cannot import name 'actor_features'`.

- [ ] **Step 3: Implement — append to `src/svod/_internal/analysis.py`**

Add imports at top of file:

```python
import dataclasses

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
```

Append:

```python
_GROWTH_BOUNDS = (-1.0, 2.0)


@dataclasses.dataclass(frozen=True)
class ClusterResult:
    """Result of segmenting actors into growth regimes.

    Attributes:
        labels: Cluster label per actor (index = actor).
        k: Number of clusters selected.
        silhouette: Silhouette score of the selected clustering.
        centers: Cluster centers expressed in original feature units.
    """

    labels: pd.Series
    k: int
    silhouette: float
    centers: pd.DataFrame


def actor_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Build per-actor growth features for clustering.

    Only actors observed in every quarter are included. Growth rates are
    winsorized to [-1, 2] so extreme small-base growth does not dominate
    the standardized feature space.

    Parameters:
        panel: Tidy panel with `actor`, `quarter`, `subscribers` columns.

    Returns:
        DataFrame indexed by actor with columns `log_size`, `growth_2021`,
        `growth_2022` and `deceleration`.
    """
    quarters = sorted(panel["quarter"].unique())
    counts = panel.groupby("actor").size()
    full = counts[counts == len(quarters)].index
    wide = panel[panel["actor"].isin(full)].pivot(index="actor", columns="quarter", values="subscribers")
    features = pd.DataFrame(index=wide.index)
    features["log_size"] = np.log10(wide["2022Q4"] + 1)
    features["growth_2021"] = wide["2021Q4"] / wide["2021Q1"] - 1
    features["growth_2022"] = wide["2022Q4"] / wide["2021Q4"] - 1
    features = features.replace([np.inf, -np.inf], np.nan).dropna()
    features[["growth_2021", "growth_2022"]] = features[["growth_2021", "growth_2022"]].clip(*_GROWTH_BOUNDS)
    features["deceleration"] = features["growth_2022"] - features["growth_2021"]
    return features


def cluster_actors(
    features: pd.DataFrame,
    *,
    k_min: int = 2,
    k_max: int = 6,
    random_state: int = 0,
) -> ClusterResult:
    """Segment actors into growth regimes with k-means.

    Features are standardized; k is selected by maximum silhouette score
    over the candidate range.

    Parameters:
        features: Feature matrix as returned by `actor_features`.
        k_min: Smallest candidate cluster count.
        k_max: Largest candidate cluster count.
        random_state: Seed for reproducible clustering.

    Returns:
        The selected clustering.
    """
    scaler = StandardScaler()
    x = scaler.fit_transform(features)
    best: tuple[float, int, KMeans] | None = None
    for k in range(k_min, min(k_max, len(features) - 1) + 1):
        model = KMeans(n_clusters=k, n_init=10, random_state=random_state).fit(x)
        score = float(silhouette_score(x, model.labels_))
        if best is None or score > best[0]:
            best = (score, k, model)
    if best is None:
        raise ValueError("Not enough actors to cluster.")
    score, k, model = best
    centers = pd.DataFrame(scaler.inverse_transform(model.cluster_centers_), columns=features.columns)
    labels = pd.Series(model.labels_, index=features.index, name="cluster")
    return ClusterResult(labels=labels, k=k, silhouette=score, centers=centers)
```

- [ ] **Step 4: Re-export**

Add `ClusterResult`, `actor_features`, `cluster_actors` to `src/svod/__init__.py` imports and `__all__` (keep `__all__` sorted).

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_analysis.py -c config/pytest.ini -p no:randomly
```
Expected: 4 passed.

- [ ] **Step 6: Commit (human)**

```bash
git add src/svod/__init__.py src/svod/_internal/analysis.py tests/test_analysis.py
git commit -m "feat: Add actor growth features and k-means segmentation"
```

---

### Task 5: SHAP surrogate interpretability + net-adds

**Files:**
- Modify: `src/svod/_internal/analysis.py`, `tests/test_analysis.py`, `src/svod/__init__.py`

**Interfaces:**
- Produces: `shap_summary(features, labels, output_png) -> Path` — trains a `RandomForestClassifier` surrogate on cluster labels, writes a SHAP summary plot PNG, returns the path. (RandomForest instead of the spec's HistGradientBoosting: `shap.TreeExplainer` has mature multiclass support for RandomForest — note this in the Methodology page, Task 12.) `net_adds(panel, *, start="2021Q4", end="2022Q4", top=12) -> pd.DataFrame` — columns `actor`, `net_adds` (int); the `top` largest absolute contributors present in both quarters, plus an `"Others"` residual row; sorted by `net_adds` descending with `"Others"` last.

- [ ] **Step 1: Write failing tests — append to `tests/test_analysis.py`**

```python
def test_net_adds_waterfall(synthetic_panel: pd.DataFrame) -> None:
    """Net adds computed between quarters, Others row closes the ledger."""
    adds = net_adds(synthetic_panel, top=3)
    assert list(adds.columns) == ["actor", "net_adds"]
    assert adds["actor"].iloc[-1] == "Others"
    challenger_a = adds.loc[adds["actor"] == "Challenger A", "net_adds"].item()
    assert challenger_a == 19_000_000 - 9_000_000
    # ledger closes: sum of rows equals total market delta between the quarters
    panel = synthetic_panel
    total_start = panel.loc[panel["quarter"] == "2021Q4", "subscribers"].sum()
    total_end = panel.loc[
        (panel["quarter"] == "2022Q4") & (panel["actor"] != "Partial"), "subscribers"
    ].sum()
    assert adds["net_adds"].sum() == total_end - total_start


def test_shap_summary_writes_png(synthetic_panel: pd.DataFrame, tmp_path: Path) -> None:
    """Surrogate + SHAP produces a summary image."""
    pytest.importorskip("shap")
    features = actor_features(synthetic_panel)
    result = cluster_actors(features)
    out = shap_summary(features, result.labels, tmp_path / "shap.png")
    assert out.exists()
    assert out.stat().st_size > 0
```

Update the top of `tests/test_analysis.py`:

```python
from typing import TYPE_CHECKING

from svod import actor_features, cluster_actors, concentration, market_summary, net_adds, shap_summary

if TYPE_CHECKING:
    from pathlib import Path
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_analysis.py -c config/pytest.ini -p no:randomly
```
Expected: FAIL — `ImportError: cannot import name 'net_adds'`.

- [ ] **Step 3: Implement — append to `src/svod/_internal/analysis.py`**

Add to imports at top:

```python
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
```

Append:

```python
def net_adds(
    panel: pd.DataFrame,
    *,
    start: str = "2021Q4",
    end: str = "2022Q4",
    top: int = 12,
) -> pd.DataFrame:
    """Compute per-actor net subscriber additions between two quarters.

    Only actors present in both quarters are attributed individually; the
    remainder is aggregated into an `Others` row so the rows sum to the
    market delta across those actors.

    Parameters:
        panel: Tidy panel with `actor`, `quarter`, `subscribers` columns.
        start: Baseline quarter.
        end: Comparison quarter.
        top: Number of largest absolute contributors to list individually.

    Returns:
        DataFrame with `actor` and `net_adds` columns, `Others` last.
    """
    wide = panel[panel["quarter"].isin([start, end])].pivot(index="actor", columns="quarter", values="subscribers")
    delta = (wide[end] - wide[start]).dropna().astype("int64")
    ranked = delta.reindex(delta.abs().sort_values(ascending=False).index)
    head = ranked.head(top).sort_values(ascending=False)
    others = int(ranked.iloc[top:].sum())
    rows = [{"actor": actor, "net_adds": int(value)} for actor, value in head.items()]
    rows.append({"actor": "Others", "net_adds": others})
    return pd.DataFrame(rows)


def shap_summary(features: pd.DataFrame, labels: pd.Series, output_png: str | Path) -> Path:
    """Explain cluster membership with a surrogate model and SHAP.

    A random-forest classifier is fit to predict cluster labels from the
    clustering features; SHAP values on the surrogate show which features
    drive each segment. This validates that segments are feature-driven
    rather than artifacts.

    Parameters:
        features: Feature matrix used for clustering.
        labels: Cluster labels aligned to `features`.
        output_png: Where to write the SHAP summary plot.

    Returns:
        Path of the written PNG.
    """
    import matplotlib  # noqa: PLC0415

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: PLC0415
    import shap  # noqa: PLC0415

    surrogate = RandomForestClassifier(n_estimators=200, random_state=0)
    surrogate.fit(features, labels)
    explainer = shap.TreeExplainer(surrogate)
    shap_values = explainer.shap_values(features)
    plt.figure()
    shap.summary_plot(shap_values, features, plot_type="bar", show=False, class_names=[f"cluster {c}" for c in sorted(labels.unique())])
    output = Path(output_png)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=200, bbox_inches="tight")
    plt.close("all")
    return output
```

- [ ] **Step 4: Re-export**

Add `net_adds`, `shap_summary` to `src/svod/__init__.py` imports and sorted `__all__`.

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_analysis.py -c config/pytest.ini -p no:randomly
```
Expected: 6 passed. If a shap/numba warning escalates to error, add a targeted ignore in `config/pytest.ini` (see Task 1 Step 4 pattern).

- [ ] **Step 6: Commit (human)**

```bash
git add src/svod/__init__.py src/svod/_internal/analysis.py tests/test_analysis.py
git commit -m "feat: Add net-adds attribution and SHAP segment interpretability"
```

---

### Task 6: Plotly chart builders

**Files:**
- Create: `src/svod/_internal/charts.py`, `tests/test_charts.py`
- Modify: `src/svod/__init__.py`

**Interfaces:**
- Consumes: `market_summary`, `concentration`, `actor_features` + `ClusterResult`, `net_adds` outputs (Tasks 3–5).
- Produces: `fig_market_overview(market: pd.DataFrame) -> go.Figure`, `fig_concentration(conc: pd.DataFrame) -> go.Figure`, `fig_cluster_scatter(features: pd.DataFrame, labels: pd.Series) -> go.Figure`, `fig_waterfall(adds: pd.DataFrame) -> go.Figure`. Pure functions, no I/O.

- [ ] **Step 0: Read the dataviz skill**

Invoke/read the `dataviz` skill before writing chart code; apply its palette and mark guidance to the layouts below (colors and layout polish may be refined; structure and function signatures stay as specified).

- [ ] **Step 1: Write failing tests — `tests/test_charts.py`**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_charts.py -c config/pytest.ini -p no:randomly
```
Expected: FAIL — `ImportError: cannot import name 'fig_market_overview'`.

- [ ] **Step 3: Implement `src/svod/_internal/charts.py`**

No module docstring:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go
from plotly.subplots import make_subplots

if TYPE_CHECKING:
    import pandas as pd

_TEMPLATE = "plotly_white"


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
        marker_color="#4269d0",
    )
    fig.add_scatter(
        x=market["quarter"],
        y=market["yoy_growth"],
        name="YoY growth",
        mode="lines+markers",
        line_color="#efb118",
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
    fig.add_scatter(x=conc["quarter"], y=conc["hhi"], name="HHI", mode="lines+markers", line_color="#4269d0")
    fig.add_scatter(x=conc["quarter"], y=conc["cr4"], name="CR4", mode="lines+markers", line_color="#efb118", secondary_y=True)
    fig.add_scatter(x=conc["quarter"], y=conc["cr8"], name="CR8", mode="lines+markers", line_color="#ff725c", secondary_y=True)
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
    palette = ["#4269d0", "#efb118", "#ff725c", "#6cc5b0", "#a463f2", "#97bbf5"]
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
            marker={"size": 10, "color": palette[cluster % len(palette)]},
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
            increasing={"marker": {"color": "#6cc5b0"}},
            decreasing={"marker": {"color": "#ff725c"}},
        )
    )
    fig.update_layout(
        template=_TEMPLATE,
        title="Who moved the market: net subscriber adds 2021Q4 to 2022Q4",
        yaxis_title="Net adds",
    )
    return fig
```

- [ ] **Step 4: Re-export**

Add `fig_cluster_scatter`, `fig_concentration`, `fig_market_overview`, `fig_waterfall` to `src/svod/__init__.py` imports and sorted `__all__`.

- [ ] **Step 5: Run test to verify it passes**

```bash
uv run pytest tests/test_charts.py -c config/pytest.ini -p no:randomly
```
Expected: 1 passed.

- [ ] **Step 6: Commit (human)**

```bash
git add src/svod/__init__.py src/svod/_internal/charts.py tests/test_charts.py
git commit -m "feat: Add plotly chart builders for market analysis"
```

---

### Task 7: Report orchestration — `build_report`

**Files:**
- Create: `src/svod/_internal/report.py`, `tests/test_report.py`
- Modify: `src/svod/__init__.py`

**Interfaces:**
- Consumes: everything from Tasks 2–6.
- Produces: `build_report(xlsx_path, *, docs_dir="docs", report_dir="report", skip_pdf=False) -> dict` — runs the full pipeline and writes: `<docs_dir>/charts/{market,concentration,clusters,waterfall}.html` (interactive, `include_plotlyjs="cdn"`), `<report_dir>/assets/{market,concentration,clusters,waterfall}.png` (kaleido) + `<report_dir>/assets/shap.png`, `<report_dir>/metrics.json`. Compiles `<report_dir>/onepager.typ` → `<report_dir>/svod-analysis-2021-2022.pdf` via `typst compile` when typst is on PATH, the template exists, and `skip_pdf` is false. Returns the metrics dict (also what's in `metrics.json`): keys `market` (list of row dicts), `concentration` (list of row dicts), `clusters` (`{"k": int, "silhouette": float, "sizes": {label: count}, "members": {label: [actors]}, "centers": [row dicts]}`), `net_adds` (list of row dicts), `qc` (QCReport as dict).

- [ ] **Step 1: Write failing tests — `tests/test_report.py`**

```python
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
    for name in ["market", "concentration", "clusters", "waterfall"]:
        assert (docs_dir / "charts" / f"{name}.html").exists()
        assert (report_dir / "assets" / f"{name}.png").exists()
    assert (report_dir / "assets" / "shap.png").exists()
    on_disk = json.loads((report_dir / "metrics.json").read_text())
    assert on_disk["clusters"]["k"] == metrics["clusters"]["k"]
    assert on_disk["qc"]["n_actors"] == 7
    assert len(on_disk["market"]) == 8
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_report.py -c config/pytest.ini -p no:randomly
```
Expected: FAIL — `ImportError: cannot import name 'build_report'`.

- [ ] **Step 3: Implement `src/svod/_internal/report.py`**

No module docstring:

```python
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

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
    metrics = {
        "market": market.to_dict(orient="records"),
        "concentration": conc.to_dict(orient="records"),
        "clusters": {
            "k": clusters.k,
            "silhouette": clusters.silhouette,
            "sizes": {label: len(actors) for label, actors in members.items()},
            "members": members,
            "centers": clusters.centers.to_dict(orient="records"),
        },
        "net_adds": adds.to_dict(orient="records"),
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
```

- [ ] **Step 4: Re-export**

Add `build_report` to `src/svod/__init__.py` imports and sorted `__all__`.

- [ ] **Step 5: Run test to verify it passes**

```bash
uv run pytest tests/test_report.py -c config/pytest.ini -p no:randomly
```
Expected: 1 passed (first run downloads kaleido's headless chromium — allow a minute).

- [ ] **Step 6: Commit (human)**

```bash
git add src/svod/__init__.py src/svod/_internal/report.py tests/test_report.py
git commit -m "feat: Add report orchestration writing charts, metrics and PDF"
```

---

### Task 8: CLI `analyze` subcommand

**Files:**
- Modify: `src/svod/_internal/cli.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `build_report` (Task 7).
- Produces: `svod analyze <xlsx> [--docs-dir DIR] [--report-dir DIR] [--skip-pdf]` CLI. Existing `svod` behavior (no subcommand → print parsed opts, exit 0) unchanged.

- [ ] **Step 1: Write failing test — append to `tests/test_cli.py`**

Also add to the imports at the top of `tests/test_cli.py`:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
```

```python
def test_analyze_subcommand(synthetic_xlsx: Path, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Analyze subcommand runs the pipeline end to end.

    Parameters:
        synthetic_xlsx: Fixture path to a synthetic raw xlsx.
        tmp_path: Pytest temporary directory.
        capsys: Pytest fixture to capture output.
    """
    exit_code = main(
        [
            "analyze",
            str(synthetic_xlsx),
            "--docs-dir",
            str(tmp_path / "docs"),
            "--report-dir",
            str(tmp_path / "report"),
            "--skip-pdf",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "actors" in captured.out
    assert (tmp_path / "report" / "metrics.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_cli.py::test_analyze_subcommand -c config/pytest.ini -p no:randomly
```
Expected: FAIL — argparse error `invalid choice` / unrecognized arguments (exits 2).

- [ ] **Step 3: Extend `src/svod/_internal/cli.py`**

In `get_parser()`, before `return parser`:

```python
    subparsers = parser.add_subparsers(dest="command")
    analyze = subparsers.add_parser("analyze", help="Run the SVOD market analysis pipeline.")
    analyze.add_argument("xlsx", help="Path to the raw Dataxis xlsx export.")
    analyze.add_argument("--docs-dir", default="docs", help="Docs root for interactive chart HTML.")
    analyze.add_argument("--report-dir", default="report", help="Report root for PNGs, metrics and PDF.")
    analyze.add_argument("--skip-pdf", action="store_true", help="Skip typst PDF compilation.")
```

In `main()`, replace `print(opts)` handling:

```python
    parser = get_parser()
    opts = parser.parse_args(args=args)
    if getattr(opts, "command", None) == "analyze":
        from svod._internal.report import build_report  # noqa: PLC0415

        metrics = build_report(
            opts.xlsx,
            docs_dir=opts.docs_dir,
            report_dir=opts.report_dir,
            skip_pdf=opts.skip_pdf,
        )
        qc = metrics["qc"]
        clusters = metrics["clusters"]
        print(f"Analyzed {qc['n_actors']} actors over {len(qc['quarters'])} quarters.")
        print(f"Segments: k={clusters['k']} (silhouette {clusters['silhouette']:.2f}); artifacts written to {opts.docs_dir} and {opts.report_dir}.")
        return 0
    print(opts)
    return 0
```

(The lazy import keeps `svod -V`/`--debug-info` fast — no pandas/sklearn import on startup.)

- [ ] **Step 4: Run the full CLI test file (old behavior must survive)**

```bash
uv run pytest tests/test_cli.py -c config/pytest.ini -p no:randomly
```
Expected: 5 passed (4 existing + 1 new).

- [ ] **Step 5: Commit (human)**

```bash
git add src/svod/_internal/cli.py tests/test_cli.py
git commit -m "feat: Add analyze CLI subcommand"
```

---

### Task 9: Public API gates — docs inventory + full quality suite

**Files:**
- Modify: `docs/reference/api.md` only if mkdocstrings does not pick up new symbols automatically (it documents the `svod` module — new re-exports appear automatically).

- [ ] **Step 1: Rebuild the docs inventory**

```bash
uv run zensical build --clean
```
Expected: build succeeds, `site/objects.inv` regenerated.

- [ ] **Step 2: Run the API test**

```bash
uv run pytest tests/test_api.py -c config/pytest.ini -p no:randomly
```
Expected: PASS. If it fails listing missing/extra objects: any helper unintentionally public in `_internal` gets a `_` prefix; anything intentionally public gets added to `__all__` — then rebuild (Step 1) and rerun.

- [ ] **Step 3: Format and full check**

```bash
make format
make run duty check-quality check-types check-docs check-api
uv run pytest -c config/pytest.ini
```
Expected: all green. Fix ruff/ty complaints inline (likely: import sorting, missing annotations). Do not add blanket `# noqa` — fix or use the narrowest rule code.

- [ ] **Step 4: Commit (human)**

```bash
git add -A
git commit -m "chore: Pass quality gates for analysis API"
```

---

### Task 10: Run the real pipeline + verify the thesis

**Files:**
- Create (generated): `docs/charts/*.html`, `report/assets/*.png`, `report/metrics.json`

- [ ] **Step 1: Install typst**

```bash
brew install typst
typst --version
```
Expected: version prints. (PDF compiles in Task 11 — template doesn't exist yet, `build_report` skips it silently.)

- [ ] **Step 2: Run the pipeline on real data**

```bash
uv run svod analyze "data/Dataxis_Test 2026.xlsx"
```
Expected: summary lines print; `docs/charts/`, `report/assets/`, `report/metrics.json` populated.

- [ ] **Step 3: Verify the thesis against the numbers**

Read `report/metrics.json` and answer explicitly (record answers in the task notes for Tasks 11–12):
1. Does total market YoY growth decelerate through 2022? (thesis: yes)
2. Does Netflix show negative net adds in 2022 in this dataset? (`net_adds` rows)
3. Do clusters separate giants / challengers / tail? (inspect `clusters.members` — name each segment from its centers: e.g. high `log_size` + negative `deceleration` = "saturating giants")
4. Does HHI/CR4 fall or rise 2021→2022?

**Guardrail from the spec: if any answer contradicts thesis A, the narrative in Tasks 11–12 follows the data, not the thesis.** Record the four answers + the actual figures (total subs 2021Q1/2021Q4/2022Q4, YoY 2022Q4, HHI endpoints, top-3 and bottom-3 net-adds actors, chosen k, silhouette, segment names with sizes).

- [ ] **Step 4: Sanity-check the charts visually**

Open `docs/charts/market.html` and the other three in a browser; confirm axes, hover labels, and that the cluster scatter is readable (if two segments overlap badly, adjust marker opacity/size in `charts.py` — keep signatures unchanged).

- [ ] **Step 5: Commit generated derived artifacts (human)**

```bash
git add docs/charts report/assets report/metrics.json
git commit -m "feat: Add generated analysis artifacts from Dataxis dataset"
```
(These are aggregates/derived charts — allowed by the governance rule; the raw xlsx stays ignored.)

---

### Task 11: Typst 1-pager

**Files:**
- Create: `report/onepager.typ`
- Create (generated): `report/svod-analysis-2021-2022.pdf`

**Interfaces:**
- Consumes: `report/assets/market.png`, `report/assets/clusters.png` (or `waterfall.png` if it tells the correction story better — pick the 2 strongest per Task 10 findings), numbers recorded in Task 10 Step 3.

- [ ] **Step 1: Write `report/onepager.typ`**

Template below; replace every `⟨...⟩` placeholder with the REAL numbers and segment names recorded in Task 10 Step 3 before compiling — the finished file must contain no `⟨⟩` markers:

```typst
#set page(paper: "a4", margin: (x: 1.6cm, y: 1.4cm))
#set text(font: "Libertinus Serif", size: 9.5pt)
#show heading: set text(weight: "bold")
#set par(justify: true)

#align(center)[
  #text(size: 15pt, weight: "bold")[The US SVOD Market 2021–2022: The Great Correction]
  #v(2pt)
  #text(size: 9pt, fill: gray)[Dataxis take-home · quarterly subscriber data, 131 platforms · full reproducible pipeline: ⟨site URL⟩]
]
#v(4pt)

== The market in one number
Total US SVOD subscriptions grew from ⟨X⟩M (2021Q1) to ⟨Y⟩M (2022Q4), but YoY growth fell from ⟨a⟩% to ⟨b⟩% — 2021 was the tail of the post-COVID boom, 2022 the correction. ⟨One sentence: what Netflix / the largest actor did.⟩

#figure(image("assets/market.png", width: 88%))

== A two-speed market
K-means segmentation of the ⟨N⟩ fully-observed platforms (features: size, 2021 growth, 2022 growth, growth change; k=⟨k⟩ by silhouette) separates ⟨segment story: e.g. "saturating giants, still-scaling challengers, and a stagnant long tail of ~⟨n⟩ niche services"⟩. ⟨Two sentences: who is in which segment, what it means for the market.⟩ A surrogate-model SHAP check confirms segments are driven by growth dynamics, not size alone.

#figure(image("assets/clusters.png", width: 88%))

== Structure: ⟨concentration finding⟩
⟨Two-three sentences: HHI from ⟨h1⟩ to ⟨h2⟩, CR4 from ⟨c1⟩% to ⟨c2⟩%; who moved the market per net-adds; implication for 2023.⟩

#v(2pt)
#text(size: 8pt, fill: gray)[
  Method: duckdb aggregation · winsorized growth features · k-means (silhouette-selected k) · RandomForest+SHAP interpretability check.
  Interactive charts and methodology: ⟨site URL⟩. Raw Dataxis data excluded from the public repository.
]
```

- [ ] **Step 2: Compile and check length**

```bash
uv run svod analyze "data/Dataxis_Test 2026.xlsx"
```
Expected: `report/svod-analysis-2021-2022.pdf` produced (build_report now finds template + typst). Open it: exactly 1 page, both charts legible. If it overflows, shrink figure widths to 80% or trim a sentence — 1 page is a hard requirement from Dataxis.

(If the `Libertinus Serif` font is unavailable, typst falls back with a warning — switch the `#set text` font to `"New Computer Modern"`, which ships with typst.)

- [ ] **Step 3: Commit (human)**

```bash
git add report/onepager.typ report/svod-analysis-2021-2022.pdf
git commit -m "feat: Add typst one-pager with market analysis"
```

---

### Task 12: Docs site — Analysis + Methodology pages

**Files:**
- Create: `docs/analysis.md`, `docs/methodology.md`
- Modify: `zensical.toml` (nav), `docs/index.md` (link to analysis)
- Copy: `report/assets/shap.png` → `docs/charts/shap.png`

- [ ] **Step 1: Write `docs/analysis.md`**

Structure below; fill every `⟨...⟩` with the real Task 10 numbers (no markers may remain). Interactive charts embedded as iframes:

```markdown
# US SVOD Market 2021–2022: The Great Correction

*Analysis of Dataxis quarterly subscriber data — 131 US platforms, 2021Q1–2022Q4.*
*[Download the one-page PDF](https://github.com/deadhand777/svod/blob/main/report/svod-analysis-2021-2022.pdf).*

## The market in one number

⟨Same narrative as the 1-pager, expanded to 2 short paragraphs with the real figures.⟩

<iframe src="../charts/market.html" width="100%" height="520" frameborder="0"></iframe>

## A two-speed market

⟨Segment narrative: names, sizes, who's in each; 2 paragraphs.⟩

<iframe src="../charts/clusters.html" width="100%" height="520" frameborder="0"></iframe>

## Who moved the market

⟨Net-adds narrative.⟩

<iframe src="../charts/waterfall.html" width="100%" height="520" frameborder="0"></iframe>

## Structure and concentration

⟨HHI/CR4 narrative.⟩

<iframe src="../charts/concentration.html" width="100%" height="520" frameborder="0"></iframe>

*Methodology, quality checks and reproducibility: see [Methodology](methodology.md).*
```

- [ ] **Step 2: Write `docs/methodology.md`**

```markdown
# Methodology

## Reproducibility

Everything on the [Analysis](analysis.md) page is generated by one command:

```bash
svod analyze "data/Dataxis_Test 2026.xlsx"
```

The pipeline (`svod` package: `load_panel → qc_report → market_summary / concentration / actor_features → cluster_actors → shap_summary → charts → typst PDF`) is unit-tested against a synthetic fixture; see the [API reference](reference/api.md).

## Data governance

The raw Dataxis dataset is **excluded from this public repository** (gitignored). Only derived aggregates — market totals, concentration indices, segment assignments and net-adds — are published here.

## Data quality

⟨From qc metrics: 951 rows, 131 actors, 8 quarters, 0 duplicates, 0 nulls; ⟨n⟩ actors with full coverage; partial actors (launches/exits) listed and excluded from clustering.⟩

## Metric definitions

- **HHI** — sum of squared subscriber shares × 10,000 (antitrust convention; >2,500 = highly concentrated).
- **CR4 / CR8** — combined subscriber share of the top 4 / 8 platforms.
- **Growth features** — per-actor 2021 growth (2021Q1→Q4), 2022 growth (2021Q4→2022Q4), deceleration (difference), log10 size. Growth winsorized to [-1, 2] so small-base outliers don't dominate.

## Segmentation

K-means on standardized features; k chosen by silhouette score (k=⟨k⟩, silhouette ⟨s⟩). Only fully-observed actors are clustered (⟨n⟩ of 131); partial actors are reported separately. No forecasting is attempted — eight quarterly observations per actor cannot support it.

## Segment interpretability (SHAP)

Clusters are unsupervised, so we validate their interpretability with a surrogate model: a random-forest classifier is trained to predict cluster membership from the clustering features, and SHAP values on the surrogate show which features define each segment. (Random forest rather than gradient boosting: mature multiclass support in `shap.TreeExplainer`.)

![SHAP feature importance per segment](charts/shap.png)

⟨One sentence interpreting the plot: e.g. "membership is driven primarily by growth deceleration and 2022 growth — segments capture growth regimes, not just size."⟩
```

- [ ] **Step 3: Copy the SHAP image + update nav**

```bash
cp report/assets/shap.png docs/charts/shap.png
```

In `zensical.toml`, change the `nav` to:

```toml
nav = [
  { "Home" = [
    { "Overview" = "index.md" },
    { "Changelog" = "changelog.md" },
    { "Credits" = "credits.md" },
    { "License" = "license.md" },
  ] },
  { "Analysis" = [
    { "SVOD Market 2021-2022" = "analysis.md" },
    { "Methodology" = "methodology.md" },
  ] },
  { "API reference" = "reference/api.md" },
  { "Development" = [
    { "Contributing" = "contributing.md" },
    { "Code of Conduct" = "code_of_conduct.md" },
  ] },
]
```

In `docs/index.md`, add near the top a short pointer paragraph linking to `analysis.md`.

- [ ] **Step 4: Build and inspect**

```bash
uv run zensical build --clean
make run duty docs
```
Open `http://127.0.0.1:8000/svod/analysis/`: iframes render the interactive charts, methodology images load, nav shows the Analysis section. Fix relative paths if an iframe 404s (`../charts/market.html` is relative to the built page URL; with zensical's directory URLs, `analysis/` needs `../charts/`).

- [ ] **Step 5: Full gate re-run**

```bash
make run duty check-quality check-types check-docs check-api
uv run pytest -c config/pytest.ini
```
Expected: green.

- [ ] **Step 6: Commit (human)**

```bash
git add docs/analysis.md docs/methodology.md docs/charts/shap.png docs/index.md zensical.toml
git commit -m "docs: Add analysis and methodology pages"
```

---

### Task 13: Publish — GitHub repo + Pages

**Files:** none (remote operations)

- [ ] **Step 1: Create the public repo and push** *(human confirms account/repo name — pyproject URLs assume `deadhand777/svod`)*

```bash
gh repo create deadhand777/svod --public --source . --push
```
Expected: repo created, `main` pushed. Verify no data leaked: `git ls-files data/` prints nothing.

- [ ] **Step 2: Deploy the site**

```bash
make run duty docs-deploy
```
Expected: builds site, pushes `gh-pages` branch (ghp-import).

- [ ] **Step 3: Enable Pages on gh-pages branch**

```bash
gh api repos/deadhand777/svod/pages -X POST -f source.branch=gh-pages -f source.path=/ 2>/dev/null || gh api repos/deadhand777/svod/pages -X PUT -f source.branch=gh-pages -f source.path=/
sleep 60 && curl -sI https://deadhand777.github.io/svod/analysis/ | head -1
```
Expected: `HTTP/2 200`.

- [ ] **Step 4: Final URL pass**

Replace every `⟨site URL⟩` left in `report/onepager.typ` (and recompile: `uv run svod analyze "data/Dataxis_Test 2026.xlsx"`) and confirm `docs/analysis.md` PDF link resolves. Commit (human):

```bash
git add report/onepager.typ report/svod-analysis-2021-2022.pdf
git commit -m "docs: Link published site in one-pager"
git push
make run duty docs-deploy
```

- [ ] **Step 5: Deliverable check**

Final deliverable to Dataxis = `report/svod-analysis-2021-2022.pdf` (1 page) + site link `https://deadhand777.github.io/svod/analysis/`. Open both once more; confirm the PDF is 1 page, charts legible, site interactive, no raw data anywhere public.
