# Table: qb_season_stats

This table contains **season-level passing and efficiency stats for quarterbacks**.

## Purpose

- To support queries about QB performance by season.
- To answer questions like:
  - "Who are the top QBs by EPA per play in the last 5 years?"
  - "How did Josh Allen perform in 2021 compared to 2020?"

## Columns

- `season` (INTEGER): NFL season year (e.g., 2020, 2021, 2022, 2023).
- `player_id` (TEXT): Stable ID for the player (e.g., `allenj01`).
- `player_name` (TEXT): Full player name (e.g., "Josh Allen").
- `team` (TEXT): Team abbreviation for that season (e.g., BUF, KC, CIN).
- `position` (TEXT): Player position; for this table, typically "QB".
- `games` (INTEGER): Number of games played in that season.
- `dropbacks` (INTEGER): Total QB dropbacks (pass attempts + sacks + scrambles).
- `attempts` (INTEGER): Pass attempts.
- `completions` (INTEGER): Completed passes.
- `passing_yards` (INTEGER): Passing yards.
- `passing_tds` (INTEGER): Passing touchdowns.
- `interceptions` (INTEGER): Interceptions thrown.
- `epa_per_play` (DOUBLE): Expected points added per QB dropback for the season.
- `success_rate` (DOUBLE): Fraction of dropbacks with positive EPA.

## Usage notes

- Use this table for **season-level** QB metrics, not per-game or per-play queries.
- For leaderboards, it is usually best to **filter out QBs with very low dropbacks** (e.g., less than 200) to avoid small-sample outliers.
- Unless otherwise specified, "efficiency" for quarterbacks should be interpreted as **`epa_per_play`** or sometimes **`success_rate`**.
