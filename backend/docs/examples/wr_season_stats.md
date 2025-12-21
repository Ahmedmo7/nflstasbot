# Table: wr_season_stats

Grain: **one row per receiver per season per team**.  
Source: Aggregated from NFL play-by-play data (pass attempts where receiver_player_id is present).

**Intended use**: season-level WR volume and efficiency (targets, EPA per target, aDOT, YAC, etc.).

Key columns:

- `season` (INTEGER): NFL season year.
- `player_id` (TEXT): Receiver identifier (receiver_player_id).
- `player_name` (TEXT): Receiver's name.
- `team` (TEXT): Offense team abbreviation (posteam).

**Volume:**

- `targets` (INTEGER): Number of pass attempts with this receiver as the target.
- `receptions` (INTEGER): Completed passes to this receiver.
- `receiving_yards` (INTEGER): Sum of `receiving_yards`.
- `receiving_tds` (INTEGER): Receiving touchdowns (from `pass_touchdown` on plays targeted to this receiver).

**EPA & success:**

- `epa_total` (DOUBLE): Sum of EPA on plays targeting this receiver.
- `epa_per_target` (DOUBLE): `epa_total / targets`.
- `success_plays` (INTEGER): Count of successful plays (success == 1) targeting this receiver.
- `success_rate` (DOUBLE): `success_plays / targets`.

**Air yards & YAC:**

- `total_air_yards` (DOUBLE): Sum of `air_yards` on targets to this receiver.
- `total_yac_yards` (DOUBLE): Sum of `yards_after_catch` on receptions.
- `avg_air_yards` (DOUBLE): `total_air_yards / targets` (receiver aDOT).
- `avg_yac_per_reception` (DOUBLE): `total_yac_yards / receptions`.

**Situational:**

- `first_downs` (INTEGER): Receptions that gained a first down (first_down_pass == 1).
- `explosive_plays` (INTEGER): Targets with `yards_gained >= 20`.
- `red_zone_targets` (INTEGER): Targets inside the opponent’s 20 (yardline_100 <= 20).
- `red_zone_tds` (INTEGER): Receiving touchdowns from the red zone.

**Notes**

- For high-usage WRs, filter on `targets` (e.g., `targets >= 80`).
- For efficiency-only questions, focus on `epa_per_target` and `success_rate`.
- `avg_air_yards` vs `avg_yac_per_reception` helps distinguish deep threats vs YAC monsters.
