from __future__ import annotations

import dataclasses

import duckdb
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
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
