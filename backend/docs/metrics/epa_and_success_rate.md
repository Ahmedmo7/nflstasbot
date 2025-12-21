# Metrics: EPA, success rate, air yards, YAC

**EPA (Expected Points Added)**:

- Per-play measure of value relative to down, distance, and field position.
- Positive EPA means the offense improved its expected points; negative means it hurt them.
- In these tables:
  - `epa_total` is the sum of per-play EPA over all relevant plays (season or game, QB or WR, etc.).
  - `epa_per_play` or `epa_per_target` is a rate stat: `epa_total / number_of_plays`.

**Success rate**:

- Success is typically defined as EPA > 0 on a given play.
- `success_plays` counts the number of such plays.
- `success_rate = success_plays / total_plays`.

**Air yards (aDOT) and YAC**:

- `air_yards`: depth of target downfield from the line of scrimmage.
- `yards_after_catch` (YAC): yards gained after the reception.
- For QBs:
  - `avg_air_yards` is average air yards per attempt.
  - `avg_yac_per_completion` is YAC per completion.
- For WRs / QB–WR pairs:
  - `avg_air_yards` is average depth of target.
  - `avg_yac_per_reception` is YAC per reception.

**Explosive plays**:

- Plays with `yards_gained >= 20` yards.
- Useful marker for big-play ability.

**Red zone**:

- Plays where the offense is inside the opponent's 20-yard line (yardline_100 <= 20).
- We track `red_zone_targets` and `red_zone_tds` (passing TDs from that area).
