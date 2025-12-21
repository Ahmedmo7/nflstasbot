# Example: EPA per play

These examples show how to answer natural language questions about epa per play using the `qb_season_stats` table.

## Example 1

**Question:**  
"Over the last 3 seasons, which quarterbacks have the highest EPA per play (min 400 dropbacks each season)?"

**Intended SQL:**

```sql
SELECT
  player_name,
  season,
  epa_per_play,
  dropbacks
FROM qb_season_stats
WHERE season >= 2021
  AND dropbacks >= 400
ORDER BY epa_per_play DESC;
```
