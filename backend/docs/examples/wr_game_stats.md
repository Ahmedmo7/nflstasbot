# Table: wr_game_stats

Grain: **one row per receiver per game**.  
Source: NFL play-by-play filtered to pass attempts where receiver_player_id is present.

Keys:

- `season` (INTEGER)
- `game_id` (TEXT)
- `week` (INTEGER)
- `game_date` (TEXT)
- `team` (TEXT): Offense team.
- `opponent_team` (TEXT): Defense team.
- `player_id` (TEXT): Receiver ID.
- `player_name` (TEXT): Receiver name.

**Per-game volume:**

- `targets`, `receptions`
- `receiving_yards`, `receiving_tds`

**Per-game EPA & success:**

- `epa_total`, `epa_per_target`
- `success_plays`, `success_rate`

**Per-game air/YAC:**

- `total_air_yards`, `total_yac_yards`
- `avg_air_yards`
- `avg_yac_per_reception`

**Situational per game:**

- `first_downs`
- `explosive_plays`
- `red_zone_targets`
- `red_zone_tds`

**Notes**

- Use for WR game logs: e.g., “Chase’s best EPA per target games in 2022”.
