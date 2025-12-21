# backend/db_init.py

import sys
from pathlib import Path
from typing import List

import duckdb

from backend.config import DUCKDB_PATH, DATA_DIR

# ---------------------------------------------------------------------
# CSV locations (must match your build_all output)
# ---------------------------------------------------------------------
QB_SEASON_CSV = DATA_DIR / "qb_season_stats_real.csv"
QBWR_SEASON_CSV = DATA_DIR / "qb_wr_season_stats_real.csv"
WR_SEASON_CSV = DATA_DIR / "wr_season_stats_real.csv"

QB_GAME_CSV = DATA_DIR / "qb_game_stats_real.csv"
QBWR_GAME_CSV = DATA_DIR / "qb_wr_game_stats_real.csv"
WR_GAME_CSV = DATA_DIR / "wr_game_stats_real.csv"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _check_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Expected CSV not found: {path}")


def _table_has_columns(con: duckdb.DuckDBPyConnection, table: str, cols: List[str]) -> List[str]:
    """
    Return the subset of `cols` that actually exist in `table`.
    """
    info = con.execute(f"PRAGMA table_info('{table}')").fetchall()
    existing = {row[1] for row in info}  # column_name is at index 1
    return [c for c in cols if c in existing]


def _create_index_if_possible(
    con: duckdb.DuckDBPyConnection,
    table: str,
    index_name: str,
    candidate_columns: List[str],
):
    """
    Create an index on the subset of candidate_columns that actually exist.
    If none of them exist, skip and print a warning.
    """
    cols = _table_has_columns(con, table, candidate_columns)
    if not cols:
        print(f"Skipping index {index_name}: none of {candidate_columns} exist in {table}")
        return

    cols_sql = ", ".join(cols)
    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({cols_sql});"
    try:
        print(f"Creating index {index_name} on {table}({cols_sql})")
        con.execute(sql)
    except Exception as e:
        print(f"Warning: could not create {index_name} on {table}: {e}")


# ---------------------------------------------------------------------
# Main init
# ---------------------------------------------------------------------
def init_db():
    """
    Initialize DuckDB database from pre-aggregated CSVs.

    This will:
      - DROP and recreate:
          qb_season_stats
          qb_wr_season_stats
          wr_season_stats
          qb_game_stats
          qb_wr_game_stats
          wr_game_stats
      - Let DuckDB infer column types via read_csv_auto
      - Create some helpful indexes (only on columns that exist)
      - Print table schemas at the end
    """
    print(f"Using DuckDB file: {DUCKDB_PATH}")
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Ensure CSVs exist
    for p in [
        QB_SEASON_CSV,
        QBWR_SEASON_CSV,
        WR_SEASON_CSV,
        QB_GAME_CSV,
        QBWR_GAME_CSV,
        WR_GAME_CSV,
    ]:
        _check_file(p)

    con = duckdb.connect(str(DUCKDB_PATH))

    # -----------------------------------------------------------------
    # Drop old tables (if they exist)
    # -----------------------------------------------------------------
    for t in [
        "qb_season_stats",
        "qb_wr_season_stats",
        "wr_season_stats",
        "qb_game_stats",
        "qb_wr_game_stats",
        "wr_game_stats",
    ]:
        print(f"Dropping table if exists: {t}")
        con.execute(f"DROP TABLE IF EXISTS {t};")

    # -----------------------------------------------------------------
    # Create new tables from CSVs
    # -----------------------------------------------------------------
    print("Creating qb_season_stats from", QB_SEASON_CSV)
    con.execute(
        """
        CREATE TABLE qb_season_stats AS
        SELECT *
        FROM read_csv_auto(?, header = TRUE);
        """,
        [str(QB_SEASON_CSV)],
    )

    print("Creating qb_wr_season_stats from", QBWR_SEASON_CSV)
    con.execute(
        """
        CREATE TABLE qb_wr_season_stats AS
        SELECT *
        FROM read_csv_auto(?, header = TRUE);
        """,
        [str(QBWR_SEASON_CSV)],
    )

    print("Creating wr_season_stats from", WR_SEASON_CSV)
    con.execute(
        """
        CREATE TABLE wr_season_stats AS
        SELECT *
        FROM read_csv_auto(?, header = TRUE);
        """,
        [str(WR_SEASON_CSV)],
    )

    print("Creating qb_game_stats from", QB_GAME_CSV)
    con.execute(
        """
        CREATE TABLE qb_game_stats AS
        SELECT *
        FROM read_csv_auto(?, header = TRUE);
        """,
        [str(QB_GAME_CSV)],
    )

    print("Creating qb_wr_game_stats from", QBWR_GAME_CSV)
    con.execute(
        """
        CREATE TABLE qb_wr_game_stats AS
        SELECT *
        FROM read_csv_auto(?, header = TRUE);
        """,
        [str(QBWR_GAME_CSV)],
    )

    print("Creating wr_game_stats from", WR_GAME_CSV)
    con.execute(
        """
        CREATE TABLE wr_game_stats AS
        SELECT *
        FROM read_csv_auto(?, header = TRUE);
        """,
        [str(WR_GAME_CSV)],
    )

    # -----------------------------------------------------------------
    # Indexes (only on columns that actually exist)
    # -----------------------------------------------------------------
    # QB season
    _create_index_if_possible(
        con,
        table="qb_season_stats",
        index_name="idx_qb_season_main",
        candidate_columns=["season", "season_type", "player_name", "team"],
    )

    # WR season
    _create_index_if_possible(
        con,
        table="wr_season_stats",
        index_name="idx_wr_season_main",
        candidate_columns=["season", "season_type", "player_name", "team"],
    )

    # QB–WR season
    _create_index_if_possible(
        con,
        table="qb_wr_season_stats",
        index_name="idx_qbwr_season_main",
        candidate_columns=["season", "season_type", "qb_name", "wr_name", "team"],
    )

    # QB game
    _create_index_if_possible(
        con,
        table="qb_game_stats",
        index_name="idx_qb_game_main",
        candidate_columns=[
            "season",
            "season_type",
            "qb_name",
            "team",
            "opponent_team",
            "week",
        ],
    )

    # QB–WR game
    _create_index_if_possible(
        con,
        table="qb_wr_game_stats",
        index_name="idx_qbwr_game_main",
        candidate_columns=[
            "season",
            "season_type",
            "qb_name",
            "wr_name",
            "team",
            "opponent_team",
            "week",
        ],
    )

    # WR game
    _create_index_if_possible(
        con,
        table="wr_game_stats",
        index_name="idx_wr_game_main",
        candidate_columns=[
            "season",
            "season_type",
            "player_name",
            "team",
            "opponent_team",
            "week",
        ],
    )

    # -----------------------------------------------------------------
    # Sanity: show schemas
    # -----------------------------------------------------------------
    print("\n=== Table schemas after init ===\n")
    for t in [
        "qb_season_stats",
        "qb_wr_season_stats",
        "wr_season_stats",
        "qb_game_stats",
        "qb_wr_game_stats",
        "wr_game_stats",
    ]:
        print(f"Schema for {t}:")
        print(con.execute(f"PRAGMA table_info('{t}')").fetchdf())
        print()

    con.close()
    print("DuckDB initialization complete.")


if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        print("Error during DB init:", e)
        sys.exit(1)
