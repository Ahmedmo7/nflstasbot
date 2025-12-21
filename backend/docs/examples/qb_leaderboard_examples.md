# Example: QB EPA leaderboards

These examples show how to answer natural language questions about QB leaderboards using the `qb_season_stats` table.

## Example 1

**Question:**  
"Who are the top 3 quarterbacks by EPA per play in the 2022 regular season (minimum 200 dropbacks)?"

**Intended SQL:**

```sql
SELECT
  player_name,
  team,
  season,
  epa_per_play,
  dropbacks
FROM qb_season_stats
WHERE season = 2022
  AND dropbacks >= 200
ORDER BY epa_per_play DESC
LIMIT 3;
```
