# Table: qb_wr_season_stats

Grain: **one row per QB–WR pair per season per team**.  
Source: NFL play-by-play where both passer_player_id and receiver_player_id are present.

**Intended use**: analyzing specific QB–receiver connections (e.g., Allen–Diggs, Mahomes–Kelce).

Keys:

- `season` (INTEGER): NFL season year.
- `team` (TEXT): Offense team abbreviation (posteam).
- `qb_id` (TEXT): QB identifier (passer_player_id).
- `qb_name` (TEXT): QB name.
- `wr_id` (TEXT): Receiver identifier (receiver_player_id).
- `wr_name` (TEXT): Receiver name.

**Volume:**

- `targets` (INTEGER): Pass attempts from this QB to this WR.
- `receptions` (INTEGER): Completed passes from this QB to this WR.
- `receiving_yards` (INTEGER): Receiving yards on these plays.
- `receiving_tds` (INTEGER): Receiving touchdowns on these plays.

**EPA & success:**

- `epa_total` (DOUBLE): Sum of EPA on plays where this QB targeted this WR.
- `epa_per_target` (DOUBLE): `epa_total / targets`.
- `success_plays` (INTEGER): Count of successful plays (success == 1) for this QB–WR connection.
- `success_rate` (DOUBLE): `success_plays / targets`.

**Air yards & YAC:**

- `total_air_yards` (DOUBLE): Sum of `air_yards` on targets from this QB to this WR.
- `total_yac_yards` (DOUBLE): Sum of `yards_after_catch` for these plays.
- `avg_air_yards` (DOUBLE): `total_air_yards / targets`.
- `avg_yac_per_reception` (DOUBLE): `total_yac_yards / receptions`.

**Situational:**

- `first_downs` (INTEGER): Plays from this QB to this WR that gained a first down.
- `explosive_plays` (INTEGER): Plays with `yards_gained >= 20`.
- `red_zone_targets` (INTEGER): Targets inside the opponent’s 20.
- `red_zone_tds` (INTEGER): Receiving TDs from the red zone for this connection.

**Notes**

- Use `targets` as the main sample-size filter for QB–WR pairs (e.g., `targets >= 40`).
- Questions like “best QB–WR duos” should be answered from this table using `epa_per_target` and `success_rate`.
