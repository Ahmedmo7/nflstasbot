# Table: qb_season_stats

Grain: **one row per quarterback per season per team**.  
Source: Aggregated from NFL play-by-play data (pass attempts only).

**Intended use**: season-level QB efficiency and volume; rankings by EPA, success rate, etc.

Columns:

- `season` (INTEGER): NFL season year (e.g., 2018, 2019, …).
- `player_id` (TEXT): Stable QB identifier from the play-by-play (passer_player_id).
- `player_name` (TEXT): Quarterback's name.
- `team` (TEXT): Offense team abbreviation (same as posteam: e.g., KC, BUF, CIN).
- `position` (TEXT): Position string, typically `"QB"`.
- `games` (INTEGER): Currently NULL / unknown. **Do not rely on this column.**

**Volume & box-score-ish stats:**

- `dropbacks` (INTEGER): Number of pass plays for that QB-season (one per pass_attempt row).
- `attempts` (INTEGER): Pass attempts.
- `completions` (INTEGER): Completed passes.
- `passing_yards` (INTEGER): Total passing yards.
- `passing_tds` (INTEGER): Passing touchdowns.
- `interceptions` (INTEGER): Interceptions thrown.

**EPA & success:**

- `epa_total` (DOUBLE): Sum of per-play EPA over all dropbacks.
- `epa_per_play` (DOUBLE): `epa_total / dropbacks`.
- `success_plays` (INTEGER): Count of pass plays marked as successful (success == 1).
- `success_rate` (DOUBLE): `success_plays / dropbacks`.

**Air yards & YAC:**

- `total_air_yards` (DOUBLE): Sum of `air_yards` over all pass attempts.
- `total_yac_yards` (DOUBLE): Sum of `yards_after_catch` over all pass attempts.
- `avg_air_yards` (DOUBLE): `total_air_yards / attempts` (average depth of target, aDOT).
- `avg_yac_per_completion` (DOUBLE): `total_yac_yards / completions`.

**EPA split into air vs YAC:**

- `air_epa_total` (DOUBLE): Sum of `air_epa`.
- `yac_epa_total` (DOUBLE): Sum of `yac_epa`.
- `air_epa_per_play` (DOUBLE): `air_epa_total / dropbacks`.
- `yac_epa_per_play` (DOUBLE): `yac_epa_total / dropbacks`.

**Down & distance / situational:**

- `first_down_passes` (INTEGER): Pass plays that resulted in a first down (first_down_pass == 1).
- `explosive_passes` (INTEGER): Pass plays with `yards_gained >= 20`.
- `third_down_attempts` (INTEGER): Approximate number of third-down pass attempts.
- `third_down_conversions` (INTEGER): Third-down pass plays that were converted (third_down_converted == 1).
- `third_down_conversion_rate` (DOUBLE): `third_down_conversions / third_down_attempts` (denominator clipped to at least 1 to avoid divide-by-zero).

**Red zone:**

- `red_zone_targets` (INTEGER): Pass attempts inside the opponent’s 20-yard line (yardline_100 <= 20).
- `red_zone_pass_tds` (INTEGER): Passing touchdowns thrown from the red zone.

**Notes and best practices**

- Use `epa_per_play` and `success_rate` to compare QB efficiency.
- Use `dropbacks` as the main volume / sample size filter (e.g., require `dropbacks >= 200`).
- Avoid using `games` until a reliable games-played field is added.
- For deep passing, use `avg_air_yards`; for YAC-heavy QBs, use `avg_yac_per_completion`.
