# Metric: epa_per_play

`epa_per_play` stands for **expected points added per play** for a quarterback.

## Definition

- EPA measures the change in a team's expected points before and after a play.
- For QBs, `epa_per_play` is calculated by:
  - Looking at all QB dropbacks (pass attempts, sacks, scrambles),
  - Computing EPA for each play,
  - Averaging over all dropbacks in the season.

In this project, `epa_per_play` is **already precomputed** and stored as a numeric column in the `qb_season_stats` table.

## Interpretation

- Higher `epa_per_play` means the quarterback is more efficient at increasing expected points.
- Negative values indicate a QB is hurting the offense on average.
- Typical seasonal values for good QBs might be around **0.20–0.35** EPA/play.

## Usage patterns

- When a user asks for:

  - "efficiency per play",
  - "value per snap",
  - "who was the best QB",
  - "who added the most value per pass play",

  you should interpret this as a request involving **`epa_per_play`**.

- Leaderboards typically:
  - Filter to QBs with `dropbacks >= 200`,
  - Order by `epa_per_play` in descending order.
