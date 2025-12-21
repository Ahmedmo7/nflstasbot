# Table: qb_wr_game_stats

Grain: **one row per QB–WR pair per game**.  
Source: NFL play-by-play where both passer_player_id and receiver_player_id are present.

Keys:

- `season`, `game_id`, `week`, `game_date`
- `team`, `opponent_team`
- `qb_id`, `qb_name`
- `wr_id`, `wr_name`

Metrics (per game for this specific QB–WR connection):

- `targets`, `receptions`
- `receiving_yards`, `receiving_tds`
- `epa_total`, `epa_per_target`
- `success_plays`, `success_rate`
- `total_air_yards`, `total_yac_yards`
- `avg_air_yards`, `avg_yac_per_reception`
- `first_downs`
- `explosive_plays`
- `red_zone_targets`
- `red_zone_tds`

Use for questions like:

- “Which game had the best Allen–Diggs EPA per target in 2021?”
- “Show Mahomes–Kelce game logs with at least 8 targets.”
