# backend/charts.py

from pathlib import Path
from typing import List, Dict, Any

import matplotlib.pyplot as plt

from backend.db_queries import run_query


def get_qb_epa_vs_cpoe(
    season: int,
    min_dropbacks: int = 200,
) -> List[Dict[str, Any]]:
    """
    Return data points for a QB EPA vs CPOE scatter plot for a given season.

    CPOE here is approximated as:
      completion_pct - league_avg_completion_pct (within that season),
    expressed in percentage points.
    """
    # NOTE: adjust column names if your qb_season_stats schema differs
    sql = f"""
    SELECT
        season,
        player_name AS qb_name,
        team,
        epa_per_play,
        (completions * 100.0 / NULLIF(attempts, 0)) 
          - AVG(completions * 100.0 / NULLIF(attempts, 0)) OVER (PARTITION BY season)
          AS cpoe
    FROM qb_season_stats
    WHERE season = {season}
      AND dropbacks >= {min_dropbacks}
      AND attempts > 0
    ORDER BY epa_per_play DESC;
    """

    df = run_query(sql)
    return df.to_dict(orient="records")


def plot_qb_epa_vs_cpoe(
    points: List[Dict[str, Any]],
    season: int,
    output_path: Path,
) -> Path:
    """
    Given rows from get_qb_epa_vs_cpoe, render a scatter plot and save to output_path.
    Returns the output_path for convenience.
    """
    # Filter rows with both metrics present
    filtered = [
        p
        for p in points
        if p.get("epa_per_play") is not None and p.get("cpoe") is not None
    ]

    if not filtered:
        raise ValueError("No valid points with both epa_per_play and cpoe.")

    x = [p["epa_per_play"] for p in filtered]
    y = [p["cpoe"] for p in filtered]
    labels = [p["qb_name"] for p in filtered]

    plt.figure(figsize=(8, 6))
    plt.scatter(x, y)

    # Label points (small font so it doesn't get too messy)
    for xv, yv, name in zip(x, y, labels):
        plt.annotate(name, (xv, yv), fontsize=8)

    plt.xlabel("EPA per Play")
    plt.ylabel("CPOE vs League Avg (percentage points)")
    plt.title(f"QB EPA vs CPOE — Season {season}")
    plt.axvline(0.0, linestyle="--", linewidth=0.8)
    plt.axhline(0.0, linestyle="--", linewidth=0.8)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()

    return output_path
