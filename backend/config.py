from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DUCKDB_PATH = BASE_DIR / "nfl_stats.duckdb"
DATA_DIR = BASE_DIR / "data"
QB_STATS_CSV = DATA_DIR / "qb_stats.csv"

DOCS_DIR = BASE_DIR / "docs"
VECTORSTORE_DIR = BASE_DIR / "chroma_db"

EMBEDDING_MODEL = "text-embedding-3-small"  # or similar
