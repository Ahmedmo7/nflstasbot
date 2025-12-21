# Metric: success_rate

`success_rate` is the fraction of plays with **positive EPA**.

## Definition

- For each QB dropback, compute EPA.
- A play is "successful" if **EPA > 0**.
- `success_rate` is the number of successful plays divided by total dropbacks.

In this project, `success_rate` is **already precomputed** and stored as a numeric column in the `qb_season_stats` table.

## Interpretation

- Higher `success_rate` means the QB consistently produces positive outcomes.
- It is less sensitive to extreme big plays than `epa_per_play`.

## Usage patterns

- When a user asks for:

  - "consistency",
  - "percent of positive plays",
  - "success rate",
  - "how often does QB X have successful pass plays",

  you should interpret this as a request involving **`success_rate`**.

- Leaderboards usually:
  - Filter to QBs with `dropbacks >= 200`,
  - Order by `success_rate` in descending order.
