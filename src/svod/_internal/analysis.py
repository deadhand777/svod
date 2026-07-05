from __future__ import annotations

import dataclasses
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


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
        """,
    ).df()
    con.close()
    summary["qoq_growth"] = summary["total_subscribers"].pct_change()
    summary["yoy_growth"] = summary["total_subscribers"].pct_change(periods=4)
    return summary


_HHI_SCALE = 10_000
_CR4_TOP_N = 4
_CR8_TOP_N = 8


def concentration(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute market-concentration metrics per quarter.

    Parameters:
        panel: Tidy panel with `actor`, `quarter`, `subscribers` columns.

    Returns:
        One row per quarter with `hhi` (Herfindahl-Hirschman index on the
        0-10000 scale), `cr4` and `cr8` (top-4 / top-8 subscriber share).
    """
    con = duckdb.connect()
    con.register("panel", panel)
    shares = con.execute(
        """
        SELECT quarter,
               subscribers / SUM(subscribers) OVER (PARTITION BY quarter) AS share,
               ROW_NUMBER() OVER (PARTITION BY quarter ORDER BY subscribers DESC) AS rank
        FROM panel
        """,
    ).df()
    con.close()
    grouped = shares.groupby("quarter")
    return pd.DataFrame(
        {
            "hhi": grouped["share"].apply(lambda s: float((s**2).sum() * _HHI_SCALE)),
            "cr4": shares[shares["rank"] <= _CR4_TOP_N].groupby("quarter")["share"].sum(),
            "cr8": shares[shares["rank"] <= _CR8_TOP_N].groupby("quarter")["share"].sum(),
        },
    ).reset_index()


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
    # pivot_table silently aggregates duplicate (actor, quarter) rows instead of raising; pivot fails loudly.
    wide = panel[panel["actor"].isin(full)].pivot(  # noqa: PD010
        index="actor",
        columns="quarter",
        values="subscribers",
    )
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


def net_adds(
    panel: pd.DataFrame,
    *,
    start: str = "2021Q4",
    end: str = "2022Q4",
    top: int = 12,
) -> pd.DataFrame:
    """Compute per-actor net subscriber additions between two quarters.

    Only actors present in both quarters are attributed individually. The
    listed rows are the `top` positive contributors individually, every
    declining actor, and an Others residual so the rows sum to the market
    delta across those actors.

    Parameters:
        panel: Tidy panel with `actor`, `quarter`, `subscribers` columns.
        start: Baseline quarter.
        end: Comparison quarter.
        top: Number of largest positive contributors to list individually.

    Returns:
        DataFrame with `actor` and `net_adds` columns, `Others` last.
    """
    # pivot_table silently aggregates duplicate (actor, quarter) rows instead of raising; pivot fails loudly.
    wide = panel[panel["quarter"].isin([start, end])].pivot(  # noqa: PD010
        index="actor",
        columns="quarter",
        values="subscribers",
    )
    delta = (wide[end] - wide[start]).dropna().astype("int64")
    positive = delta[delta > 0].sort_values(ascending=False)
    negative = delta[delta < 0].sort_values(ascending=False)
    shown = pd.concat([positive.head(top), negative])
    others = int(delta.sum() - shown.sum())
    rows = [{"actor": actor, "net_adds": int(value)} for actor, value in shown.items()]
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
    import matplotlib as mpl  # noqa: PLC0415

    mpl.use("Agg")
    import matplotlib.pyplot as plt  # noqa: PLC0415
    import shap  # noqa: PLC0415

    surrogate = RandomForestClassifier(n_estimators=200, random_state=0)
    surrogate.fit(features, labels)
    explainer = shap.TreeExplainer(surrogate)
    shap_values = explainer.shap_values(features)
    if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:  # noqa: PLR2004
        # Modern shap returns (n_samples, n_features, n_classes); summary_plot expects
        # a list of per-class (n_samples, n_features) arrays for multiclass bar charts.
        shap_values = list(np.moveaxis(shap_values, -1, 0))
    plt.figure()
    shap.summary_plot(
        shap_values,
        features,
        plot_type="bar",
        show=False,
        class_names=[f"cluster {c}" for c in sorted(labels.unique())],
    )
    output = Path(output_png)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=200, bbox_inches="tight")
    plt.close("all")
    return output
