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
