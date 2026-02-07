# NFL Stats Bot 🏈

An intelligent conversational assistant that transforms natural language questions about NFL player statistics into SQL queries, executes them against a local DuckDB warehouse, and provides insights with visual charts.

## Overview

NFL Stats Bot is a RAG-enhanced (Retrieval-Augmented Generation) natural language to SQL system that allows users to ask questions about NFL quarterback and wide receiver statistics in plain English. The system leverages Large Language Models (LLMs) to understand questions, generate accurate SQL queries, and provide contextual explanations of the results.

### Key Features

- 🗣️ **Natural Language Interface**: Ask questions in plain English, no SQL knowledge required
- 📊 **Interactive Charts**: Generate EPA vs CPOE scatter plots and other visualizations
- 🤖 **Conversational AI**: Powered by GPT-4 with contextual memory
- 🔍 **RAG-Enhanced Query Generation**: Uses vector similarity search to retrieve relevant schema documentation and examples
- 🔄 **Self-Healing SQL**: Automatically repairs broken queries using LLM-based error analysis
- 📈 **Comprehensive Stats**: Season-level and game-level statistics for QBs, WRs, and QB-WR connections
- 🎯 **Advanced Metrics**: EPA (Expected Points Added), success rate, CPOE, air yards, and more

## Technology Stack

### Core Technologies
- **Python 3.x**: Primary programming language
- **DuckDB**: High-performance analytical database for storing and querying NFL stats
- **LangChain**: Framework for building LLM applications
- **OpenAI GPT-4**: Language model for natural language understanding and SQL generation
- **Chainlit**: Interactive chat interface
- **FastAPI**: REST API framework

### Key Libraries
- **pandas**: Data manipulation and aggregation
- **ChromaDB**: Vector database for storing documentation embeddings
- **matplotlib**: Chart generation
- **python-dotenv**: Environment variable management

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│                    (Chainlit Chat UI)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Conversational Agent Layer                      │
│  - Manages conversation context and memory                   │
│  - Decides when to call tools vs respond directly            │
│  - Provides natural language summaries                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌───────────────────┐     ┌──────────────────┐
│  Chart Generator  │     │ NL-to-SQL Engine │
│  - EPA vs CPOE    │     │                  │
│  - Scatter plots  │     └────────┬─────────┘
└───────────────────┘              │
                                   ▼
                    ┌──────────────────────────────┐
                    │      RAG Retriever            │
                    │  - ChromaDB Vector Store      │
                    │  - Schema documentation       │
                    │  - Query examples             │
                    │  - Metric definitions         │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   SQL Generation (GPT-4)     │
                    │  - Context-aware generation   │
                    │  - Schema validation          │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      SQL Execution            │
                    │      (DuckDB)                 │
                    └──────────────┬───────────────┘
                                   │
                        ┌──────────┴──────────┐
                        ▼                     ▼
                    Success?              Error?
                        │                     │
                        │                     ▼
                        │          ┌────────────────────┐
                        │          │  SQL Repair Agent  │
                        │          │  - Error analysis  │
                        │          │  - Query fixing    │
                        │          └────────┬───────────┘
                        │                   │
                        └───────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   Result Explanation          │
                    │   - Natural language summary  │
                    │   - Season-level analysis     │
                    │   - Follow-up suggestions     │
                    └──────────────────────────────┘
```

### How It Works

#### 1. Natural Language Processing
When a user asks a question like "Top 3 QBs by EPA per play in 2022 (min 200 dropbacks)", the system:
- Parses the question through the conversational agent
- Determines if data retrieval is needed
- Routes to the appropriate handler (chart generation or NL-to-SQL)

#### 2. RAG-Enhanced SQL Generation
The system uses Retrieval-Augmented Generation to improve SQL accuracy:

1. **Document Retrieval**: 
   - User question is embedded using OpenAI embeddings
   - Vector similarity search retrieves relevant documentation from ChromaDB
   - Returns schema definitions, metric explanations, and example queries

2. **Context Assembly**:
   - Retrieved documents provide table schemas and column names
   - Example queries show query patterns
   - Metric definitions explain NFL analytics terms

3. **SQL Generation**:
   - GPT-4 receives the user question + retrieved context
   - Generates DuckDB-compatible SQL
   - Follows patterns from examples to ensure correctness

#### 3. Query Execution & Self-Healing
```python
# Execution flow
try:
    result = execute_sql(generated_sql)
except SQLError as e:
    # Automatic repair attempt
    repaired_sql = repair_sql(
        question=user_question,
        bad_sql=generated_sql,
        error_message=str(e)
    )
    result = execute_sql(repaired_sql)
```

The self-healing mechanism:
- Captures the error message from DuckDB
- Sends original question, broken SQL, and error to GPT-4
- Receives a corrected query that fixes the specific issue
- Common fixes: column name typos, missing table qualifiers, incorrect aggregations

#### 4. Result Processing & Explanation
- Results are formatted with rounded floats for readability
- Internal ID columns are hidden from users
- GPT-4 generates a natural language explanation including:
  - Summary of what the data shows
  - Season-level context and trends
  - Comparisons to league averages
  - Sample size caveats
  - Suggested follow-up questions

## Database Schema

The system uses a DuckDB database with six main tables:

### Season-Level Tables
- **qb_season_stats**: Quarterback aggregate statistics by season
- **wr_season_stats**: Wide receiver aggregate statistics by season  
- **qb_wr_season_stats**: QB-to-WR connection statistics by season

### Game-Level Tables
- **qb_game_stats**: Quarterback statistics by game
- **wr_game_stats**: Wide receiver statistics by game
- **qb_wr_game_stats**: QB-to-WR connection statistics by game

### Key Metrics Tracked
- **EPA (Expected Points Added)**: Value added relative to down/distance/field position
- **Success Rate**: Percentage of plays with positive EPA
- **CPOE (Completion Percentage Over Expected)**: Completion rate vs expected
- **Air Yards**: Depth of target downfield
- **YAC (Yards After Catch)**: Yards gained after reception
- **Traditional Stats**: Completions, attempts, yards, TDs, INTs, etc.

## Project Structure

```
nflstasbot/
├── backend/
│   ├── agent.py                 # Conversational agent orchestrator
│   ├── chainlit_app.py          # Chainlit UI and message handlers
│   ├── api.py                   # FastAPI REST endpoints
│   ├── config.py                # Configuration and paths
│   ├── db_init.py               # DuckDB initialization
│   ├── db_queries.py            # Database query execution
│   ├── build_stats_csv.py       # Data aggregation from play-by-play
│   ├── charts.py                # Chart generation logic
│   │
│   ├── nl_to_sql/
│   │   ├── engine.py            # Main NL-to-SQL engine
│   │   ├── generation.py        # SQL generation with RAG
│   │   ├── explanation.py       # Result explanation generation
│   │   └── __init__.py
│   │
│   ├── rag/
│   │   ├── build_index.py       # Build ChromaDB vector index
│   │   └── retriever.py         # Retrieve relevant documents
│   │
│   ├── docs/
│   │   ├── schema/              # Table and metric documentation
│   │   │   ├── qb_season_stats.md
│   │   │   ├── epa_per_play.md
│   │   │   └── success_rate.md
│   │   ├── examples/            # Example queries for RAG
│   │   │   ├── qb_leaderboard_examples.md
│   │   │   ├── qb_season_stats.md
│   │   │   └── ...
│   │   └── metrics/
│   │       └── epa_and_success_rate.md
│   │
│   ├── data/                    # CSV data files (not in repo)
│   └── requirements.txt         # Python dependencies
│
├── chainlit.md                  # Chainlit welcome screen
├── .gitignore
└── README.md
```

## Installation & Setup

### Prerequisites
- Python 3.9 or higher
- OpenAI API key

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ahmedmo7/nflstasbot.git
   cd nflstasbot
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file in the root directory
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

5. **Prepare the data**
   
   Place your NFL play-by-play CSV files in `backend/data/`:
   ```
   backend/data/
   ├── play_by_play_2020.csv
   ├── play_by_play_2021.csv
   ├── play_by_play_2022.csv
   ├── play_by_play_2023.csv
   └── ...
   ```

6. **Build aggregated statistics**
   ```bash
   cd backend
   python build_stats_csv.py
   ```

7. **Initialize the database**
   ```bash
   python db_init.py
   ```

8. **Build the RAG vector index**
   ```bash
   python -m rag.build_index
   ```

## Usage

### Running the Chainlit Chat Interface

```bash
cd backend
chainlit run chainlit_app.py
```

Then open your browser to `http://localhost:8000`

### Example Queries

**Season-level QB statistics:**
- "Top 3 QBs by EPA per play in 2022 (min 200 dropbacks)"
- "Which QBs had the highest success rate in 2020 (min 500 dropbacks)?"
- "Show me passing yards leaders for 2021"

**Game-level statistics:**
- "Josh Allen game logs for 2023"
- "Patrick Mahomes best games by EPA in 2022"

**QB-WR connections:**
- "Top 5 QB-WR combinations by EPA in 2023"
- "Joe Burrow to Ja'Marr Chase stats by season"

**Visual analytics:**
- "Show me an EPA vs CPOE scatter for 2023"
- "EPA per play vs CPOE chart for 2022"

**Team aggregations:**
- "Average EPA per play by team in 2023"
- "Team passing efficiency rankings for 2022"

### Running the REST API

```bash
cd backend
uvicorn api:app --reload
```

**API Endpoints:**

- `GET /health` - Health check
- `POST /query` - Execute a natural language query

**Example cURL request:**
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "Top 5 QBs by EPA per play in 2023"}'
```

**Response format:**
```json
{
  "question": "Top 5 QBs by EPA per play in 2023",
  "sql": "SELECT player_name, team, epa_per_play...",
  "rows": [
    {"player_name": "Player Name", "team": "TEAM", "epa_per_play": 0.350},
    ...
  ],
  "explanation": "Here are the top 5 quarterbacks by EPA per play..."
}
```

## Implementation Details

### Conversational Agent

The `ConversationalNFLAgent` class manages multi-turn conversations:
- Maintains conversation history for context
- Uses a tool-calling pattern where the LLM decides when to query the database
- Produces natural language responses with domain expertise

### RAG (Retrieval-Augmented Generation)

The RAG system improves SQL generation accuracy:
1. **Documentation corpus** includes:
   - Table schemas with column descriptions
   - Metric definitions (EPA, success rate, CPOE, etc.)
   - Example queries with patterns
   
2. **Embedding and retrieval**:
   - Documents are chunked and embedded using OpenAI embeddings
   - Stored in ChromaDB for fast similarity search
   - Top-k relevant documents retrieved for each query

3. **Context injection**:
   - Retrieved docs are added to the LLM prompt
   - Helps the model understand available tables and columns
   - Provides query patterns to follow

### SQL Repair Mechanism

When SQL queries fail:
1. Error message is captured from DuckDB
2. Repair prompt includes:
   - Original user question
   - Broken SQL query
   - Error message
   - Actual table schemas from the database
3. GPT-4 generates a corrected query
4. Repaired SQL is executed
5. Common error types handled:
   - Column name typos
   - Missing table aliases
   - Incorrect aggregation syntax
   - Correlated subquery issues

### Chart Generation

Special handler for EPA vs CPOE scatter plots:
- Detects chart requests via keyword matching
- Extracts season from the question
- Queries database for QB stats
- Generates matplotlib scatter plot with annotations
- Returns both chart image and underlying data table

## Data Pipeline

### 1. Raw Data → Aggregated CSVs
`build_stats_csv.py` processes play-by-play data:
- Loads multiple seasons of play-by-play data
- Filters to regular season and playoffs only
- Aggregates passing plays by QB, WR, and QB-WR connections
- Computes EPA, success rate, air yards, YAC, etc.
- Outputs season and game-level CSVs

### 2. CSVs → DuckDB
`db_init.py` creates the database:
- Creates six tables from aggregated CSVs
- Uses DuckDB's `read_csv_auto` for type inference
- Creates indexes on frequently queried columns
- Validates schemas and displays table info

### 3. Documentation → Vector Index
`rag/build_index.py` builds the knowledge base:
- Reads markdown files from `docs/` directory
- Chunks documents for optimal retrieval
- Generates embeddings using OpenAI
- Stores in ChromaDB with metadata
- Creates persistent vector store

## Configuration

Key configuration in `backend/config.py`:
```python
DATA_DIR = Path(__file__).parent / "data"
DUCKDB_PATH = DATA_DIR / "nfl_stats.duckdb"
VECTORSTORE_DIR = Path(__file__).parent / "chroma_db"
EMBEDDING_MODEL = "text-embedding-3-small"
```

## Future Enhancements

Potential improvements:
- Add more advanced chart types (time series, team comparisons)
- Support for defensive player statistics
- Real-time data updates from NFL APIs
- Multi-modal analysis (video clips with stats)
- User query history and favorites
- Export results to CSV/Excel
- Team-level analytics and game predictions

## Contributing

Contributions are welcome! Areas where help is needed:
- Adding more example queries to improve RAG
- Expanding documentation for additional metrics
- Implementing new chart types
- Performance optimizations for large queries

## License

[Add your license information here]

## Acknowledgments

- Data sourced from NFL play-by-play datasets
- Built with LangChain, OpenAI, and DuckDB
- Inspired by modern RAG and agentic AI patterns

---

**Note**: This is a demonstration project for educational purposes. Ensure you have appropriate rights to use any NFL data.
