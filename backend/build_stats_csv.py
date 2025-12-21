import pandas as pd
from .config import DATA_DIR

SEASONS = list(range(2020, 2026))

QB_SEASON_CSV = DATA_DIR / "qb_season_stats_real.csv"
QBWR_SEASON_CSV = DATA_DIR / "qb_wr_season_stats_real.csv"
WR_SEASON_CSV = DATA_DIR / "wr_season_stats_real.csv"

QB_GAME_CSV = DATA_DIR / "qb_game_stats_real.csv"
QBWR_GAME_CSV = DATA_DIR / "qb_wr_game_stats_real.csv"
WR_GAME_CSV = DATA_DIR / "wr_game_stats_real.csv"


def load_one_season_csv(season: int) -> pd.DataFrame:
    fp = DATA_DIR / f"play_by_play_{season}.csv"
    print(f"Loading {fp}")
    df = pd.read_csv(fp, low_memory=False)

    if "season" not in df.columns:
        df["season"] = season

    return df


def ensure_column(df: pd.DataFrame, col: str, default=0):
    if col not in df.columns:
        df[col] = default
    return df


def build_all():
    # 1) Stack all seasons
    dfs = [load_one_season_csv(s) for s in SEASONS]
    df = pd.concat(dfs, ignore_index=True)
    print(f"Combined PBP rows: {len(df)}")

    # Ensure season_type exists and filter to REG/POST only
    df = ensure_column(df, "season_type", default="REG")
    df = df[df["season_type"].isin(["REG", "POST"])].copy()

    # Ensure key columns exist (defensive coding)
    for col in [
        "pass_attempt",
        "passer_player_id",
        "passer_player_name",
        "posteam",
        "defteam",
        "yards_gained",
        "epa",
        "success",
        "air_yards",
        "yards_after_catch",
        "air_epa",
        "yac_epa",
        "first_down_pass",
        "third_down_converted",
        "third_down_failed",
        "yardline_100",
        "pass_touchdown",
        "interception",
        "complete_pass",
        "receiver_player_id",
        "receiver_player_name",
        "receiving_yards",
        "game_id",
        "week",
        "game_date",
    ]:
        df = ensure_column(
            df,
            col,
            default=0 if col not in ("receiver_player_name", "game_date") else "",
        )

    # Normalize some types
    df["pass_attempt"] = df["pass_attempt"].fillna(0).astype(int)
    df["complete_pass"] = df["complete_pass"].fillna(0).astype(int)
    df["pass_touchdown"] = df["pass_touchdown"].fillna(0).astype(int)
    df["interception"] = df["interception"].fillna(0).astype(int)
    df["success"] = df["success"].fillna(0).astype(int)
    df["third_down_converted"] = df["third_down_converted"].fillna(0).astype(int)
    df["third_down_failed"] = df["third_down_failed"].fillna(0).astype(int)

    # ----------------------------------------------------------------------------------
    # PART A: QB SEASON STATS (ENHANCED)
    # ----------------------------------------------------------------------------------

    qb_df = df[(df["pass_attempt"] == 1) & df["passer_player_id"].notna()].copy()
    print(f"QB pass rows: {len(qb_df)}")

    qb_df["dropbacks"] = 1
    qb_df["success_flag"] = qb_df["success"].astype(int)
    qb_df["explosive_flag"] = (qb_df["yards_gained"] >= 20).astype(int)

    if "down" in qb_df.columns:
        qb_df["third_down_attempt_flag"] = (
            (qb_df["down"] == 3) & (qb_df["pass_attempt"] == 1)
        ).astype(int)
    else:
        qb_df["third_down_attempt_flag"] = 0

    qb_df["red_zone_flag"] = (qb_df["yardline_100"] <= 20).astype(int)
    qb_df["red_zone_target_flag"] = (qb_df["red_zone_flag"] == 1).astype(int)
    qb_df["red_zone_td_flag"] = (
        (qb_df["red_zone_flag"] == 1) & (qb_df["pass_touchdown"] == 1)
    ).astype(int)

    # Season-level QB aggregation (include season_type)
    qb_season = qb_df.groupby(
        ["season", "season_type", "passer_player_id", "passer_player_name", "posteam"],
        dropna=False,
        as_index=False,
    ).agg(
        dropbacks=("dropbacks", "sum"),
        attempts=("pass_attempt", "sum"),
        completions=("complete_pass", "sum"),
        passing_yards=("yards_gained", "sum"),
        passing_tds=("pass_touchdown", "sum"),
        interceptions=("interception", "sum"),
        epa_total=("epa", "sum"),
        success_plays=("success_flag", "sum"),
        total_air_yards=("air_yards", "sum"),
        total_yac_yards=("yards_after_catch", "sum"),
        air_epa_total=("air_epa", "sum"),
        yac_epa_total=("yac_epa", "sum"),
        first_down_passes=("first_down_pass", "sum"),
        explosive_passes=("explosive_flag", "sum"),
        third_down_attempts=("third_down_attempt_flag", "sum"),
        third_down_conversions=("third_down_converted", "sum"),
        red_zone_targets=("red_zone_target_flag", "sum"),
        red_zone_pass_tds=("red_zone_td_flag", "sum"),
    )

    qb_season["epa_per_play"] = qb_season["epa_total"] / qb_season["dropbacks"]
    qb_season["success_rate"] = qb_season["success_plays"] / qb_season["dropbacks"]

    qb_season["avg_air_yards"] = qb_season["total_air_yards"] / qb_season["attempts"].clip(lower=1)
    qb_season["avg_yac_per_completion"] = qb_season["total_yac_yards"] / qb_season["completions"].clip(lower=1)

    qb_season["air_epa_per_play"] = qb_season["air_epa_total"] / qb_season["dropbacks"].clip(lower=1)
    qb_season["yac_epa_per_play"] = qb_season["yac_epa_total"] / qb_season["dropbacks"].clip(lower=1)

    qb_season["third_down_conversion_rate"] = qb_season["third_down_conversions"] / qb_season[
        "third_down_attempts"
    ].clip(lower=1)

    qb_season["position"] = "QB"
    qb_season["games"] = None

    qb_season = qb_season.rename(
        columns={
            "passer_player_id": "player_id",
            "passer_player_name": "player_name",
            "posteam": "team",
        }
    )

    qb_season = qb_season[
        [
            "season",
            "season_type",
            "player_id",
            "player_name",
            "team",
            "position",
            "games",
            "dropbacks",
            "attempts",
            "completions",
            "passing_yards",
            "passing_tds",
            "interceptions",
            "epa_per_play",
            "success_rate",
            "epa_total",
            "success_plays",
            "total_air_yards",
            "total_yac_yards",
            "avg_air_yards",
            "avg_yac_per_completion",
            "air_epa_total",
            "yac_epa_total",
            "air_epa_per_play",
            "yac_epa_per_play",
            "first_down_passes",
            "explosive_passes",
            "third_down_attempts",
            "third_down_conversions",
            "third_down_conversion_rate",
            "red_zone_targets",
            "red_zone_pass_tds",
        ]
    ]

    # ----------------------------------------------------------------------------------
    # PART B: QB-WR SEASON STATS
    # ----------------------------------------------------------------------------------

    qbwr_df = df[
        (df["pass_attempt"] == 1)
        & df["passer_player_id"].notna()
        & df["receiver_player_id"].notna()
    ].copy()
    print(f"QB-WR pass rows: {len(qbwr_df)}")

    qbwr_df["target"] = 1
    qbwr_df["reception_flag"] = qbwr_df["complete_pass"].astype(int)
    qbwr_df["success_flag"] = qbwr_df["success"].astype(int)
    qbwr_df["explosive_flag"] = (qbwr_df["yards_gained"] >= 20).astype(int)

    qbwr_df["red_zone_flag"] = (qbwr_df["yardline_100"] <= 20).astype(int)
    qbwr_df["red_zone_target_flag"] = (qbwr_df["red_zone_flag"] == 1).astype(int)
    qbwr_df["red_zone_td_flag"] = (
        (qbwr_df["red_zone_flag"] == 1) & (qbwr_df["pass_touchdown"] == 1)
    ).astype(int)

    qbwr_season = qbwr_df.groupby(
        [
            "season",
            "season_type",
            "passer_player_id",
            "passer_player_name",
            "receiver_player_id",
            "receiver_player_name",
            "posteam",
        ],
        dropna=False,
        as_index=False,
    ).agg(
        targets=("target", "sum"),
        receptions=("reception_flag", "sum"),
        receiving_yards=("receiving_yards", "sum"),
        receiving_tds=("pass_touchdown", "sum"),
        total_air_yards=("air_yards", "sum"),
        total_yac_yards=("yards_after_catch", "sum"),
        epa_total=("epa", "sum"),
        success_plays=("success_flag", "sum"),
        first_downs=("first_down_pass", "sum"),
        explosive_plays=("explosive_flag", "sum"),
        red_zone_targets=("red_zone_target_flag", "sum"),
        red_zone_tds=("red_zone_td_flag", "sum"),
    )

    qbwr_season["epa_per_target"] = qbwr_season["epa_total"] / qbwr_season["targets"].clip(lower=1)
    qbwr_season["success_rate"] = qbwr_season["success_plays"] / qbwr_season["targets"].clip(lower=1)
    qbwr_season["avg_air_yards"] = qbwr_season["total_air_yards"] / qbwr_season["targets"].clip(lower=1)
    qbwr_season["avg_yac_per_reception"] = qbwr_season["total_yac_yards"] / qbwr_season["receptions"].clip(lower=1)

    qbwr_season = qbwr_season.rename(
        columns={
            "passer_player_id": "qb_id",
            "passer_player_name": "qb_name",
            "receiver_player_id": "wr_id",
            "receiver_player_name": "wr_name",
            "posteam": "team",
        }
    )

    qbwr_season = qbwr_season[
        [
            "season",
            "season_type",
            "team",
            "qb_id",
            "qb_name",
            "wr_id",
            "wr_name",
            "targets",
            "receptions",
            "receiving_yards",
            "receiving_tds",
            "epa_total",
            "epa_per_target",
            "success_plays",
            "success_rate",
            "total_air_yards",
            "total_yac_yards",
            "avg_air_yards",
            "avg_yac_per_reception",
            "first_downs",
            "explosive_plays",
            "red_zone_targets",
            "red_zone_tds",
        ]
    ]

    # ----------------------------------------------------------------------------------
    # PART C: WR SEASON STATS
    # ----------------------------------------------------------------------------------

    wr_df = df[(df["pass_attempt"] == 1) & df["receiver_player_id"].notna()].copy()
    print(f"WR pass rows: {len(wr_df)}")

    wr_df["target"] = 1
    wr_df["reception_flag"] = wr_df["complete_pass"].astype(int)
    wr_df["success_flag"] = wr_df["success"].astype(int)
    wr_df["explosive_flag"] = (wr_df["yards_gained"] >= 20).astype(int)

    wr_df["red_zone_flag"] = (wr_df["yardline_100"] <= 20).astype(int)
    wr_df["red_zone_target_flag"] = (wr_df["red_zone_flag"] == 1).astype(int)
    wr_df["red_zone_td_flag"] = (
        (wr_df["red_zone_flag"] == 1) & (wr_df["pass_touchdown"] == 1)
    ).astype(int)

    wr_season = wr_df.groupby(
        ["season", "season_type", "receiver_player_id", "receiver_player_name", "posteam"],
        dropna=False,
        as_index=False,
    ).agg(
        targets=("target", "sum"),
        receptions=("reception_flag", "sum"),
        receiving_yards=("receiving_yards", "sum"),
        receiving_tds=("pass_touchdown", "sum"),
        total_air_yards=("air_yards", "sum"),
        total_yac_yards=("yards_after_catch", "sum"),
        epa_total=("epa", "sum"),
        success_plays=("success_flag", "sum"),
        first_downs=("first_down_pass", "sum"),
        explosive_plays=("explosive_flag", "sum"),
        red_zone_targets=("red_zone_target_flag", "sum"),
        red_zone_tds=("red_zone_td_flag", "sum"),
    )

    wr_season["epa_per_target"] = wr_season["epa_total"] / wr_season["targets"].clip(lower=1)
    wr_season["success_rate"] = wr_season["success_plays"] / wr_season["targets"].clip(lower=1)
    wr_season["avg_air_yards"] = wr_season["total_air_yards"] / wr_season["targets"].clip(lower=1)
    wr_season["avg_yac_per_reception"] = wr_season["total_yac_yards"] / wr_season["receptions"].clip(lower=1)

    wr_season = wr_season.rename(
        columns={
            "receiver_player_id": "player_id",
            "receiver_player_name": "player_name",
            "posteam": "team",
        }
    )

    wr_season = wr_season[
        [
            "season",
            "season_type",
            "player_id",
            "player_name",
            "team",
            "targets",
            "receptions",
            "receiving_yards",
            "receiving_tds",
            "epa_total",
            "epa_per_target",
            "success_plays",
            "success_rate",
            "total_air_yards",
            "total_yac_yards",
            "avg_air_yards",
            "avg_yac_per_reception",
            "first_downs",
            "explosive_plays",
            "red_zone_targets",
            "red_zone_tds",
        ]
    ]

    # ----------------------------------------------------------------------------------
    # PART D: QB GAME LOGS
    # ----------------------------------------------------------------------------------

    qb_game = qb_df.groupby(
        [
            "season",
            "season_type",
            "game_id",
            "week",
            "posteam",
            "defteam",
            "passer_player_id",
            "passer_player_name",
        ],
        dropna=False,
        as_index=False,
    ).agg(
        game_date=("game_date", "first"),
        dropbacks=("dropbacks", "sum"),
        attempts=("pass_attempt", "sum"),
        completions=("complete_pass", "sum"),
        passing_yards=("yards_gained", "sum"),
        passing_tds=("pass_touchdown", "sum"),
        interceptions=("interception", "sum"),
        epa_total=("epa", "sum"),
        success_plays=("success_flag", "sum"),
        total_air_yards=("air_yards", "sum"),
        total_yac_yards=("yards_after_catch", "sum"),
        air_epa_total=("air_epa", "sum"),
        yac_epa_total=("yac_epa", "sum"),
        first_down_passes=("first_down_pass", "sum"),
        explosive_passes=("explosive_flag", "sum"),
        third_down_attempts=("third_down_attempt_flag", "sum"),
        third_down_conversions=("third_down_converted", "sum"),
        red_zone_targets=("red_zone_target_flag", "sum"),
        red_zone_pass_tds=("red_zone_td_flag", "sum"),
    )

    qb_game["epa_per_play"] = qb_game["epa_total"] / qb_game["dropbacks"].clip(lower=1)
    qb_game["success_rate"] = qb_game["success_plays"] / qb_game["dropbacks"].clip(lower=1)
    qb_game["avg_air_yards"] = qb_game["total_air_yards"] / qb_game["attempts"].clip(lower=1)
    qb_game["avg_yac_per_completion"] = qb_game["total_yac_yards"] / qb_game["completions"].clip(lower=1)
    qb_game["air_epa_per_play"] = qb_game["air_epa_total"] / qb_game["dropbacks"].clip(lower=1)
    qb_game["yac_epa_per_play"] = qb_game["yac_epa_total"] / qb_game["dropbacks"].clip(lower=1)
    qb_game["third_down_conversion_rate"] = qb_game["third_down_conversions"] / qb_game[
        "third_down_attempts"
    ].clip(lower=1)

    qb_game = qb_game.rename(
        columns={
            "passer_player_id": "qb_id",
            "passer_player_name": "qb_name",
            "posteam": "team",
            "defteam": "opponent_team",
        }
    )

    qb_game = qb_game[
        [
            "season",
            "season_type",
            "game_id",
            "week",
            "game_date",
            "team",
            "opponent_team",
            "qb_id",
            "qb_name",
            "dropbacks",
            "attempts",
            "completions",
            "passing_yards",
            "passing_tds",
            "interceptions",
            "epa_total",
            "epa_per_play",
            "success_plays",
            "success_rate",
            "total_air_yards",
            "total_yac_yards",
            "avg_air_yards",
            "avg_yac_per_completion",
            "air_epa_total",
            "yac_epa_total",
            "air_epa_per_play",
            "yac_epa_per_play",
            "first_down_passes",
            "explosive_passes",
            "third_down_attempts",
            "third_down_conversions",
            "third_down_conversion_rate",
            "red_zone_targets",
            "red_zone_pass_tds",
        ]
    ]

    # ----------------------------------------------------------------------------------
    # PART E: QB-WR GAME LOGS
    # ----------------------------------------------------------------------------------

    qbwr_game = qbwr_df.groupby(
        [
            "season",
            "season_type",
            "game_id",
            "week",
            "posteam",
            "defteam",
            "passer_player_id",
            "passer_player_name",
            "receiver_player_id",
            "receiver_player_name",
        ],
        dropna=False,
        as_index=False,
    ).agg(
        game_date=("game_date", "first"),
        targets=("target", "sum"),
        receptions=("reception_flag", "sum"),
        receiving_yards=("receiving_yards", "sum"),
        receiving_tds=("pass_touchdown", "sum"),
        total_air_yards=("air_yards", "sum"),
        total_yac_yards=("yards_after_catch", "sum"),
        epa_total=("epa", "sum"),
        success_plays=("success_flag", "sum"),
        first_downs=("first_down_pass", "sum"),
        explosive_plays=("explosive_flag", "sum"),
        red_zone_targets=("red_zone_target_flag", "sum"),
        red_zone_tds=("red_zone_td_flag", "sum"),
    )

    qbwr_game["epa_per_target"] = qbwr_game["epa_total"] / qbwr_game["targets"].clip(lower=1)
    qbwr_game["success_rate"] = qbwr_game["success_plays"] / qbwr_game["targets"].clip(lower=1)
    qbwr_game["avg_air_yards"] = qbwr_game["total_air_yards"] / qbwr_game["targets"].clip(lower=1)
    qbwr_game["avg_yac_per_reception"] = qbwr_game["total_yac_yards"] / qbwr_game["receptions"].clip(lower=1)

    qbwr_game = qbwr_game.rename(
        columns={
            "passer_player_id": "qb_id",
            "passer_player_name": "qb_name",
            "receiver_player_id": "wr_id",
            "receiver_player_name": "wr_name",
            "posteam": "team",
            "defteam": "opponent_team",
        }
    )

    qbwr_game = qbwr_game[
        [
            "season",
            "season_type",
            "game_id",
            "week",
            "game_date",
            "team",
            "opponent_team",
            "qb_id",
            "qb_name",
            "wr_id",
            "wr_name",
            "targets",
            "receptions",
            "receiving_yards",
            "receiving_tds",
            "epa_total",
            "epa_per_target",
            "success_plays",
            "success_rate",
            "total_air_yards",
            "total_yac_yards",
            "avg_air_yards",
            "avg_yac_per_reception",
            "first_downs",
            "explosive_plays",
            "red_zone_targets",
            "red_zone_tds",
        ]
    ]

    # ----------------------------------------------------------------------------------
    # PART F: WR GAME LOGS
    # ----------------------------------------------------------------------------------

    wr_game = wr_df.groupby(
        [
            "season",
            "season_type",
            "game_id",
            "week",
            "posteam",
            "defteam",
            "receiver_player_id",
            "receiver_player_name",
        ],
        dropna=False,
        as_index=False,
    ).agg(
        game_date=("game_date", "first"),
        targets=("target", "sum"),
        receptions=("reception_flag", "sum"),
        receiving_yards=("receiving_yards", "sum"),
        receiving_tds=("pass_touchdown", "sum"),
        total_air_yards=("air_yards", "sum"),
        total_yac_yards=("yards_after_catch", "sum"),
        epa_total=("epa", "sum"),
        success_plays=("success_flag", "sum"),
        first_downs=("first_down_pass", "sum"),
        explosive_plays=("explosive_flag", "sum"),
        red_zone_targets=("red_zone_target_flag", "sum"),
        red_zone_tds=("red_zone_td_flag", "sum"),
    )

    wr_game["epa_per_target"] = wr_game["epa_total"] / wr_game["targets"].clip(lower=1)
    wr_game["success_rate"] = wr_game["success_plays"] / wr_game["targets"].clip(lower=1)
    wr_game["avg_air_yards"] = wr_game["total_air_yards"] / wr_game["targets"].clip(lower=1)
    wr_game["avg_yac_per_reception"] = wr_game["total_yac_yards"] / wr_game["receptions"].clip(lower=1)

    wr_game = wr_game.rename(
        columns={
            "receiver_player_id": "player_id",
            "receiver_player_name": "player_name",
            "posteam": "team",
            "defteam": "opponent_team",
        }
    )

    wr_game = wr_game[
        [
            "season",
            "season_type",
            "game_id",
            "week",
            "game_date",
            "team",
            "opponent_team",
            "player_id",
            "player_name",
            "targets",
            "receptions",
            "receiving_yards",
            "receiving_tds",
            "epa_total",
            "epa_per_target",
            "success_plays",
            "success_rate",
            "total_air_yards",
            "total_yac_yards",
            "avg_air_yards",
            "avg_yac_per_reception",
            "first_downs",
            "explosive_plays",
            "red_zone_targets",
            "red_zone_tds",
        ]
    ]

    # ----------------------------------------------------------------------------------
    # WRITE OUTPUTS
    # ----------------------------------------------------------------------------------

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"QB-season rows: {len(qb_season)}")
    qb_season.to_csv(QB_SEASON_CSV, index=False)
    print(f"Saved QB season stats CSV to: {QB_SEASON_CSV}")

    print(f"QB-WR-season rows: {len(qbwr_season)}")
    qbwr_season.to_csv(QBWR_SEASON_CSV, index=False)
    print(f"Saved QB-WR season stats CSV to: {QBWR_SEASON_CSV}")

    print(f"WR-season rows: {len(wr_season)}")
    wr_season.to_csv(WR_SEASON_CSV, index=False)
    print(f"Saved WR season stats CSV to: {WR_SEASON_CSV}")

    print(f"QB-game rows: {len(qb_game)}")
    qb_game.to_csv(QB_GAME_CSV, index=False)
    print(f"Saved QB game stats CSV to: {QB_GAME_CSV}")

    print(f"QB-WR-game rows: {len(qbwr_game)}")
    qbwr_game.to_csv(QBWR_GAME_CSV, index=False)
    print(f"Saved QB-WR game stats CSV to: {QBWR_GAME_CSV}")

    print(f"WR-game rows: {len(wr_game)}")
    wr_game.to_csv(WR_GAME_CSV, index=False)
    print(f"Saved WR game stats CSV to: {WR_GAME_CSV}")


if __name__ == "__main__":
    build_all()
