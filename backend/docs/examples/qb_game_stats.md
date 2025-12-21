# Table: qb_game_stats

Grain: **one row per quarterback per game**.  
Source: NFL play-by-play filtered to pass attempts by each QB in each game.

Keys:

- `season` (INTEGER): NFL season year.
- `game_id` (TEXT): Game identifier from the play-by-play.
- `week` (INTEGER): Week number (regular or postseason, depending on data).
- `game_date` (TEXT): Date of the game (string representation).
- `team` (TEXT): Offense team abbreviation (posteam).
- `opponent_team` (TEXT): Defense team abbreviation (defteam).
- `qb_id` (TEXT): QB identifier.
- `qb_name` (TEXT): QB name.

**Per-game passing stats:**

- `dropbacks`, `attempts`, `completions`
- `passing_yards`, `passing_tds`, `interceptions`

**Per-game EPA & success:**

- `epa_total`, `epa_per_play`
- `success_plays`, `success_rate`

**Per-game air/YAC:**

- `total_air_yards`, `total_yac_yards`
- `avg_air_yards`
- `avg_yac_per_completion`
- `air_epa_total`, `yac_epa_total`
- `air_epa_per_play`, `yac_epa_per_play`

**Situational per game:**

- `first_down_passes`, `explosive_passes`
- `third_down_attempts`, `third_down_conversions`, `third_down_conversion_rate`
- `red_zone_targets`, `red_zone_pass_tds`

**Notes**

- Use this table for “game logs”: e.g., “Mahomes’ EPA per game vs the Bills since 2020”.
- Use filters on `season`, `week`, `team`, `opponent_team`, `qb_name` / `qb_id`.
