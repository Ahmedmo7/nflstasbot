# Example: Success Rate Example

These examples show how to answer natural language questions about success rate using the `qb_season_stats` table.

## Example 1

**Question:**  
"Among QBs with at least 500 dropbacks in 2020, who had the highest success rate?"

**Intended SQL:**

```sql
SELECT
  player_name,
  team,
  season,
  success_rate,
  dropbacks
FROM qb_season_stats
WHERE season = 2020
  AND dropbacks >= 500
ORDER BY success_rate DESC
LIMIT 1;

```
