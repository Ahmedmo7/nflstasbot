import duckdb
import pandas as pd
from backend.config import DUCKDB_PATH

def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Run a SQL query against the DuckDB DB and return a DataFrame."""
    con = duckdb.connect(str(DUCKDB_PATH))
    try:
        if params:
            df = con.execute(sql, params).df()
        else:
            df = con.execute(sql).df()
    finally:
        con.close()
    return df

if __name__ == "__main__":
    # Quick manual tests
    print("All rows:")
    print(run_query("SELECT * FROM qb_season_stats LIMIT 5;"))

    print("\nTop 3 seasons by epa_per_play (min 200 dropbacks):")
    sql = """
        SELECT
            player_name,
            season,
            team,
            epa_per_play,
            dropbacks
        FROM qb_season_stats
        WHERE dropbacks >= 200
        ORDER BY epa_per_play DESC
        LIMIT 3;
    """
    print(run_query(sql))
